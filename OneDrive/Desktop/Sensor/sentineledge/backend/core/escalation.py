"""
core/escalation.py — SentinelEdge alert escalation engine.

DELIVERY RULE: When a threshold breach fires, ALL THREE channels
(Email, SMS, In-App WebSocket) are sent to ALL active subscribers
simultaneously using asyncio.gather(). Failure of one channel never
blocks the others.

ESCALATION (system-wide re-alert, not per-person routing):
  Level 1: Immediate — all channels fire to all subscribers
  Level 2: After 60s with no acknowledgement — re-alert everyone
  Level 3: After another 60s — final alert to everyone, max_escalated=True

ACKNOWLEDGE: Any subscriber can acknowledge. First acknowledgement
stops all further escalation.

DELIVERY RECEIPTS: Logged per alert per subscriber per channel.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import database
from modules.email.smtp import send_email_async
from modules.email.templates import format_alert_message
from modules.sms.gateway import send_sms_async
from modules.inapp.broadcaster import send_push_async
from config import ESCALATION_TIMEOUT_SECONDS, RUNTIME_THRESHOLDS
from models import BreachEvent

logger = logging.getLogger("sentineledge.escalation")

# Track all running escalation asyncio.Task objects for graceful shutdown
active_escalations: dict[int, asyncio.Task] = {}


# ─── Message formatting ───────────────────────────────────────────────────────

def _build_message(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    level: int,
) -> str:
    base = format_alert_message(parameter, value, threshold, direction)
    timeout_2x = ESCALATION_TIMEOUT_SECONDS * 2

    if level == 1:
        return f"SentinelEdge ALERT: {base}. Please acknowledge in the app."
    elif level == 2:
        return (
            f"SentinelEdge ESCALATION Level 2: {base}. "
            f"No response received. Immediate action required."
        )
    else:
        return (
            f"SentinelEdge CRITICAL Level 3 FINAL: {base}. "
            f"Unacknowledged for {timeout_2x} seconds."
        )


# ─── Per-subscriber channel dispatcher ───────────────────────────────────────

async def _notify_subscriber(
    alert_id: int,
    level: int,
    subscriber: dict,
    message: str,
) -> None:
    """
    Fire ALL THREE channels (email, SMS, in-app) to one subscriber in parallel.
    Each channel failure is logged independently and never blocks the others.
    """
    subject = f"SentinelEdge Alert (Level {level})"
    sub_id = subscriber["id"]

    # ── Channel 1: Email (always) ─────────────────────────────────────────────
    async def _email() -> None:
        err: Optional[str] = None
        try:
            ok = await send_email_async(subscriber["email"], subject, message)
        except Exception as exc:
            ok = False
            err = str(exc)
        database.log_escalation(alert_id, level, sub_id, "email", ok)
        database.insert_receipt(alert_id, "email", sub_id, level, ok, err)
        if not ok:
            logger.warning(
                "Email to %s (sub %d) failed at level %d",
                subscriber["email"], sub_id, level,
            )

    # ── Channel 2: SMS (always) ───────────────────────────────────────────────
    async def _sms() -> None:
        err: Optional[str] = None
        try:
            ok = await send_sms_async(subscriber["phone"], message)
        except Exception as exc:
            ok = False
            err = str(exc)
        database.log_escalation(alert_id, level, sub_id, "sms", ok)
        database.insert_receipt(alert_id, "sms", sub_id, level, ok, err)
        if not ok:
            logger.warning(
                "SMS to %s (sub %d) failed at level %d",
                subscriber["phone"], sub_id, level,
            )

    # ── Channel 3: In-App WebSocket push (always) ─────────────────────────────
    async def _push() -> None:
        push_sub = subscriber.get("push_subscription")
        err: Optional[str] = None
        if not push_sub:
            database.insert_receipt(
                alert_id, "inapp", sub_id, level, False, "no active connection"
            )
            return
        try:
            ok = await send_push_async(push_sub, subject, message, {"alert_id": alert_id})
        except Exception as exc:
            ok = False
            err = str(exc)
        database.log_escalation(alert_id, level, sub_id, "inapp", ok)
        database.insert_receipt(alert_id, "inapp", sub_id, level, ok, err)
        if not ok:
            logger.warning("In-app push to sub %d failed at level %d", sub_id, level)

    # Fire all three in parallel — failure of one never blocks others
    await asyncio.gather(_email(), _sms(), _push(), return_exceptions=True)
    logger.info(
        "All channels dispatched to %s (sub %d, level=%d, alert_id=%d)",
        subscriber["name"], sub_id, level, alert_id,
    )


# ─── Broadcast to all active subscribers ─────────────────────────────────────

async def _notify_all_subscribers(
    alert_id: int,
    level: int,
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
) -> None:
    """
    Build the level-specific message and fire all channels to every
    active subscriber simultaneously.
    """
    message = _build_message(parameter, value, threshold, direction, level)
    subscribers = database.get_subscribers_ordered()
    active_subs = [s for s in subscribers if s.get("active", True)]

    if not active_subs:
        logger.warning(
            "No active subscribers to notify for alert %d (level %d)", alert_id, level
        )
        return

    database.update_escalation_level(alert_id, level)

    tasks = [
        _notify_subscriber(alert_id, level, sub, message)
        for sub in active_subs
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(
        "Level %d notifications complete for alert %d — %d subscriber(s) notified",
        level, alert_id, len(active_subs),
    )


# ─── Escalation background task ──────────────────────────────────────────────

async def run_escalation(alert_id: int, severity: str = "WARNING") -> None:
    """
    System-wide escalation coroutine for a single alert.

    Level 1 was already dispatched by trigger_alert().
    This coroutine handles levels 2 and 3 after timeout intervals.
    """
    try:
        alert = database.get_alert(alert_id)
        if not alert:
            logger.error("run_escalation: alert_id %d not found in DB", alert_id)
            return

        # ── Level 2: wait, then re-alert everyone ─────────────────────────────
        await asyncio.sleep(ESCALATION_TIMEOUT_SECONDS)

        alert = database.get_alert(alert_id)
        if not alert or alert["acknowledged"]:
            logger.info("Alert %d acknowledged before level-2 escalation.", alert_id)
            return

        await _notify_all_subscribers(
            alert_id, 2,
            alert["parameter"], alert["value"],
            alert["threshold"], alert["direction"],
        )

        # ── Level 3: wait again, then final alert ─────────────────────────────
        await asyncio.sleep(ESCALATION_TIMEOUT_SECONDS)

        alert = database.get_alert(alert_id)
        if not alert or alert["acknowledged"]:
            logger.info("Alert %d acknowledged before level-3 escalation.", alert_id)
            return

        await _notify_all_subscribers(
            alert_id, 3,
            alert["parameter"], alert["value"],
            alert["threshold"], alert["direction"],
        )
        database.set_max_escalated(alert_id)
        logger.info("Escalation chain completed (max) for alert %d.", alert_id)

    except asyncio.CancelledError:
        logger.info("Escalation task for alert %d was cancelled.", alert_id)
    except Exception as exc:
        logger.exception(
            "Unexpected error in run_escalation for alert %d: %s", alert_id, exc
        )
    finally:
        active_escalations.pop(alert_id, None)


# ─── Public API ───────────────────────────────────────────────────────────────

async def trigger_alert(reading: dict, breaches: list) -> list:
    """
    Process all breach events from a single sensor reading.

    For each breach:
      1. Persist alert in DB (threshold read from RUNTIME_THRESHOLDS)
      2. Immediately notify ALL active subscribers on ALL channels (level 1)
      3. Spawn background escalation task for levels 2 and 3
    """
    from config import ALERT_COOLDOWN_SECONDS

    alert_ids = []
    now = datetime.now(timezone.utc)
    cooldown_until = (now + timedelta(seconds=ALERT_COOLDOWN_SECONDS)).isoformat()

    for breach in breaches:
        severity = getattr(breach, "severity", "WARNING")

        # Read threshold from RUNTIME_THRESHOLDS (stays current after updates)
        rt = RUNTIME_THRESHOLDS.get("temperature", {})
        if breach.direction == "high":
            live_threshold = rt.get("high", breach.threshold)
        else:
            live_threshold = rt.get("low", breach.threshold)

        alert_id = database.insert_alert(
            parameter=breach.parameter,
            value=breach.value,
            threshold=live_threshold,
            direction=breach.direction,
            cooldown_until=cooldown_until,
            severity=severity,
        )
        if alert_id == -1:
            logger.error("Failed to insert alert for breach: %s", breach)
            continue

        alert_ids.append(alert_id)
        logger.info(
            "Alert %d created: %s=%s (threshold %s, dir=%s, severity=%s)",
            alert_id, breach.parameter, breach.value,
            live_threshold, breach.direction, severity,
        )

        # Level 1 — immediate, all subscribers, all channels
        await _notify_all_subscribers(
            alert_id, 1,
            breach.parameter, breach.value,
            live_threshold, breach.direction,
        )

        # Spawn background escalation for levels 2 and 3
        task = asyncio.create_task(
            run_escalation(alert_id, severity),
            name=f"escalation-{alert_id}",
        )
        active_escalations[alert_id] = task

    return alert_ids


async def acknowledge(alert_id: int, acknowledged_by: str) -> bool:
    """
    Mark an alert as acknowledged.
    The running escalation task polls the DB and stops naturally.
    """
    ok = database.acknowledge_alert(alert_id, acknowledged_by)
    if ok:
        logger.info("Alert %d acknowledged by '%s'.", alert_id, acknowledged_by)
    else:
        logger.error("Failed to acknowledge alert %d.", alert_id)
    return ok


async def resume_pending_escalations() -> None:
    """
    Called once at startup — resume escalation tasks for unacknowledged alerts.
    """
    pending = database.get_unacknowledged_alerts()
    if not pending:
        return

    logger.info(
        "Resuming escalation for %d pending alert(s) after restart.", len(pending)
    )
    for alert in pending:
        if not alert.get("max_escalated"):
            severity = alert.get("severity", "WARNING")
            task = asyncio.create_task(
                run_escalation(alert["id"], severity),
                name=f"escalation-resume-{alert['id']}",
            )
            active_escalations[alert["id"]] = task


async def shutdown_escalations() -> None:
    """
    Called at server shutdown.
    In-flight tasks remain in DB as unacknowledged so
    resume_pending_escalations() picks them up on next restart.
    """
    if not active_escalations:
        return
    logger.info(
        "Shutdown: %d escalation task(s) in flight — they will resume on restart.",
        len(active_escalations),
    )
    active_escalations.clear()
