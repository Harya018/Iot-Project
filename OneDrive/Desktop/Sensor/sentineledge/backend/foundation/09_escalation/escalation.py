"""
core/escalation.py — SentinelEdge alert escalation engine.

Three notification channels:
  Module 1 — In-app WebSocket alert + audio (broadcast via manager)
  Module 2 — Email via smtplib
  Module 3 — SMS via Android SMS Gateway

Severity-based channel selection:
  WARNING   -> email only
  CRITICAL  -> email + SMS
  EMERGENCY -> email + SMS + in-app push, escalation starts immediately

Delivery receipts inserted after every send attempt (Addition 4).
Active escalation tasks tracked for graceful shutdown (Addition 9).
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
from config import ESCALATION_TIMEOUT_SECONDS
from models import BreachEvent

logger = logging.getLogger("sentineledge.escalation")

# Track all running escalation asyncio.Task objects (Addition 9)
active_escalations: dict[int, asyncio.Task] = {}


# ─── Message formatting ───────────────────────────────────────────────────────

def format_escalation_message(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    level: int,
    subscriber_name: str,
    prev_name: str = "",
) -> str:
    base = format_alert_message(parameter, value, threshold, direction)
    timeout_2x = ESCALATION_TIMEOUT_SECONDS * 2

    if level == 1:
        return f"SentinelEdge ALERT: {base}. Please acknowledge in the app."
    elif level == 2:
        return (
            f"SentinelEdge ESCALATION (Level 2): {base}. "
            f"{prev_name} has not responded. Immediate action required."
        )
    else:
        return (
            f"SentinelEdge CRITICAL (Level 3 - Final): {base}. "
            f"Unacknowledged for {timeout_2x} seconds. All personnel alerted."
        )


# ─── Channel dispatcher ───────────────────────────────────────────────────────

async def _notify_subscriber(
    alert_id: int,
    level: int,
    subscriber: dict,
    message: str,
    severity: str = "WARNING",
) -> None:
    """
    Fire notification channels to a subscriber based on severity.

    WARNING   -> email only
    CRITICAL  -> email + SMS
    EMERGENCY -> email + SMS + in-app Web Push

    Each channel result is recorded in delivery_receipts (Addition 4).
    """
    subject = f"SentinelEdge Alert (Level {level})"
    sub_id = subscriber["id"]

    # ── Email (all severities) ────────────────────────────────────────────────
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

    # ── SMS (CRITICAL + EMERGENCY only) ──────────────────────────────────────
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

    # ── In-app Web Push (EMERGENCY only) ─────────────────────────────────────
    async def _push() -> None:
        push_sub = subscriber.get("push_subscription")
        err: Optional[str] = None
        if not push_sub:
            database.insert_receipt(alert_id, "inapp", sub_id, level, False, "no subscription")
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

    # ── Fire channels based on severity ───────────────────────────────────────
    tasks = [_email()]
    if severity in ("CRITICAL", "EMERGENCY"):
        tasks.append(_sms())
    if severity == "EMERGENCY":
        tasks.append(_push())

    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(
        "Notifications dispatched to %s (order=%d, level=%d, alert_id=%d, severity=%s)",
        subscriber["name"],
        subscriber["escalation_order"],
        level,
        alert_id,
        severity,
    )


# ─── Escalation background task ──────────────────────────────────────────────

async def run_escalation(alert_id: int, severity: str = "WARNING") -> None:
    """
    Full escalation coroutine for a single alert.

    EMERGENCY: skips the initial wait, notifies all 3 levels immediately.
    Normal flow: waits ESCALATION_TIMEOUT_SECONDS between each level.
    Deregisters from active_escalations on completion (Addition 9).
    """
    try:
        alert = database.get_alert(alert_id)
        if not alert:
            logger.error("run_escalation: alert_id %d not found in DB", alert_id)
            return

        # ── EMERGENCY: notify all levels simultaneously without delay ──────────
        if severity == "EMERGENCY":
            subs = {
                order: database.get_subscriber_by_order(order)
                for order in (1, 2, 3)
            }
            for order, sub in subs.items():
                if sub:
                    msg = format_escalation_message(
                        alert["parameter"], alert["value"],
                        alert["threshold"], alert["direction"],
                        level=order, subscriber_name=sub["name"],
                    )
                    database.update_escalation_level(alert_id, order)
                    await _notify_subscriber(alert_id, order, sub, msg, severity="EMERGENCY")
            database.set_max_escalated(alert_id)
            logger.info("EMERGENCY escalation completed immediately for alert %d", alert_id)
            return

        # ── Normal flow: Level 1 was already notified in trigger_alert() ──────
        await asyncio.sleep(ESCALATION_TIMEOUT_SECONDS)

        alert = database.get_alert(alert_id)
        if not alert or alert["acknowledged"]:
            logger.info("Alert %d acknowledged before level-2 escalation.", alert_id)
            return

        sub1 = database.get_subscriber_by_order(1)
        prev_name = sub1["name"] if sub1 else "the primary contact"
        sub2 = database.get_subscriber_by_order(2)

        if sub2:
            msg2 = format_escalation_message(
                alert["parameter"], alert["value"], alert["threshold"],
                alert["direction"], level=2, subscriber_name=sub2["name"],
                prev_name=prev_name,
            )
            database.update_escalation_level(alert_id, 2)
            await _notify_subscriber(alert_id, 2, sub2, msg2, severity)
        else:
            logger.warning(
                "No sub at escalation_order=2 -- skipping L2 for alert %d", alert_id
            )

        await asyncio.sleep(ESCALATION_TIMEOUT_SECONDS)

        alert = database.get_alert(alert_id)
        if not alert or alert["acknowledged"]:
            logger.info("Alert %d acknowledged before level-3 escalation.", alert_id)
            return

        sub2_name = sub2["name"] if sub2 else "the secondary contact"
        sub3 = database.get_subscriber_by_order(3)

        if sub3:
            msg3 = format_escalation_message(
                alert["parameter"], alert["value"], alert["threshold"],
                alert["direction"], level=3, subscriber_name=sub3["name"],
                prev_name=sub2_name,
            )
            database.update_escalation_level(alert_id, 3)
            database.set_max_escalated(alert_id)
            await _notify_subscriber(alert_id, 3, sub3, msg3, severity)
        else:
            logger.warning(
                "No sub at escalation_order=3 -- skipping L3 for alert %d", alert_id
            )
            database.set_max_escalated(alert_id)

        logger.info("Escalation chain completed for alert %d.", alert_id)

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

    Severity-aware channel selection:
      WARNING   -> email only
      CRITICAL  -> email + SMS
      EMERGENCY -> email + SMS + in-app push (immediate, no delay)
    """
    from config import ALERT_COOLDOWN_SECONDS

    alert_ids = []
    now = datetime.now(timezone.utc)
    cooldown_until = (now + timedelta(seconds=ALERT_COOLDOWN_SECONDS)).isoformat()

    for breach in breaches:
        severity = getattr(breach, "severity", "WARNING")

        alert_id = database.insert_alert(
            parameter=breach.parameter,
            value=breach.value,
            threshold=breach.threshold,
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
            breach.threshold, breach.direction, severity,
        )

        # Notify level-1 subscriber immediately (all severities)
        sub1 = database.get_subscriber_by_order(1)
        if sub1:
            msg1 = format_escalation_message(
                breach.parameter, breach.value, breach.threshold,
                breach.direction, level=1, subscriber_name=sub1["name"],
            )
            await _notify_subscriber(alert_id, 1, sub1, msg1, severity)
        else:
            logger.warning(
                "No sub at escalation_order=1 for alert %d", alert_id
            )

        # Spawn escalation task and register for shutdown tracking
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
    The task re-checks DB at each sleep boundary, so interrupted escalations
    continue correctly after restart.
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
    Called at server shutdown (Addition 9).
    In-flight tasks are left registered in DB as unacknowledged so
    resume_pending_escalations() picks them up on next restart.
    """
    if not active_escalations:
        return
    logger.info(
        "Shutdown: %d escalation task(s) in flight -- they will resume on restart.",
        len(active_escalations),
    )
    active_escalations.clear()
