# -*- coding: utf-8 -*-
"""
core/escalation.py — SentinelEdge alert delivery engine (simplified).

DELIVERY RULE: When a threshold breach fires, ALL THREE channels
(Email, SMS, In-App WebSocket) are sent to ALL active subscribers
simultaneously using asyncio.gather(). Failure of one channel never
blocks the others.

ONE-SHOT DELIVERY: Alerts fire exactly once (level 1) and stop.
No background re-alert timers. No level 2 or level 3.
The escalation_level column always stays at 1.

ACKNOWLEDGE: Admin can manually mark alerts as seen from the dashboard.
The system never calls acknowledge automatically.

DELIVERY RECEIPTS: Logged per alert per subscriber per channel.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import database
from modules.email.smtp import send_alert_email_async
from modules.email.smtp import send_email_async  # kept for daily reports / legacy
from modules.sms.sender import send_alert_sms_async
from modules.inapp.broadcaster import send_push_async
from utils.formatter import format_alert_message   # used by _build_message (SMS body)
from config import ALERT_COOLDOWN_SECONDS, RUNTIME_THRESHOLDS
from models import BreachEvent

logger = logging.getLogger("sentineledge.escalation")

# No background escalation tasks — kept as empty dict for API compatibility
active_escalations: dict[int, asyncio.Task] = {}


# ─── Message formatting ───────────────────────────────────────────────────────

def _build_message(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    severity: str = "WARNING",
) -> str:
    """Build the SMS/plain-text alert body. Always level 1 language."""
    unit = "°C" if parameter == "temperature" else "%"
    base = format_alert_message(parameter, value, threshold, direction, severity, unit)
    return f"SentinelEdge Alert: {base}. Please check the dashboard."


# ─── Per-subscriber channel dispatcher ───────────────────────────────────────

async def _notify_subscriber(
    alert_id: int,
    subscriber: dict,
    message: str,
    alert_meta: dict | None = None,
) -> None:
    """
    Fire ALL THREE channels (email, SMS, in-app) to one subscriber in parallel.
    Each channel failure is logged independently and never blocks the others.
    """
    sub_id = subscriber["id"]
    level  = 1  # always level 1

    # ── Channel 1: HTML Email ─────────────────────────────────────────────────
    async def _email() -> None:
        err: Optional[str] = None
        try:
            meta = alert_meta or {}
            ok = await send_alert_email_async(
                recipient_email=subscriber["email"],
                recipient_name=subscriber.get("name", "Operator"),
                temperature=float(meta.get("value", 0.0)),
                threshold=float(meta.get("threshold", 0.0)),
                direction=str(meta.get("direction", "high")),
                severity=str(meta.get("severity", "WARNING")),
                escalation_level=level,
                timestamp_utc=str(meta.get("timestamp", "") or ""),
            )
        except Exception as exc:
            ok = False
            err = str(exc)
        database.log_escalation(alert_id, level, sub_id, "email", ok)
        database.insert_receipt(alert_id, "email", sub_id, level, ok, err)
        if not ok:
            logger.warning(
                "Email to %s (sub %d) failed",
                subscriber["email"], sub_id,
            )

    # ── Channel 2: SMS ───────────────────────────────────────────────────────────
    async def _sms() -> None:
        err: Optional[str] = None
        try:
            meta = alert_meta or {}
            ok = await send_alert_sms_async(
                phone=subscriber["phone"],
                value=float(meta.get("value", 0.0)),
                threshold=float(meta.get("threshold", 0.0)),
                direction=str(meta.get("direction", "high")),
                timestamp_utc=str(meta.get("timestamp", "") or ""),
            )
        except Exception as exc:
            ok = False
            err = str(exc)
        database.log_escalation(alert_id, level, sub_id, "sms", ok)
        database.insert_receipt(alert_id, "sms", sub_id, level, ok, err)
        if not ok:
            logger.warning(
                "SMS to %s (sub %d) failed",
                subscriber["phone"], sub_id,
            )

    # ── Channel 3: In-App WebSocket push ─────────────────────────────────────
    async def _push() -> None:
        push_sub = subscriber.get("push_subscription")
        err: Optional[str] = None
        if not push_sub:
            database.insert_receipt(
                alert_id, "inapp", sub_id, level, False, "no active connection"
            )
            return
        try:
            subject = "SentinelEdge Alert"
            ok = await send_push_async(push_sub, subject, message, {"alert_id": alert_id})
        except Exception as exc:
            ok = False
            err = str(exc)
        database.log_escalation(alert_id, level, sub_id, "inapp", ok)
        database.insert_receipt(alert_id, "inapp", sub_id, level, ok, err)
        if not ok:
            logger.warning("In-app push to sub %d failed", sub_id)

    # Fire all three in parallel — failure of one never blocks others
    await asyncio.gather(_email(), _sms(), _push(), return_exceptions=True)
    logger.info(
        "All channels dispatched to %s (sub %d, alert_id=%d)",
        subscriber["name"], sub_id, alert_id,
    )


# ─── Broadcast to all active subscribers ─────────────────────────────────────

async def _notify_all_subscribers(
    alert_id: int,
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
) -> None:
    """
    Build the alert message and fire all channels to every
    active subscriber simultaneously. Always fires at level 1.
    """
    # Fetch alert metadata for the HTML email builder
    alert_meta = database.get_alert(alert_id) or {}
    severity   = alert_meta.get("severity", "WARNING")

    message     = _build_message(parameter, value, threshold, direction, severity)
    subscribers = database.get_subscribers_ordered()
    active_subs = [s for s in subscribers if s.get("active", True)]

    if not active_subs:
        logger.warning(
            "No active subscribers to notify for alert %d", alert_id
        )
        return

    # Always set escalation_level = 1
    database.update_escalation_level(alert_id, 1)

    tasks = [
        _notify_subscriber(alert_id, sub, message, alert_meta)
        for sub in active_subs
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(
        "Alert notifications complete for alert %d — %d subscriber(s) notified",
        alert_id, len(active_subs),
    )


# ─── Public API ───────────────────────────────────────────────────────────────

async def trigger_alert(reading: dict, breaches: list) -> list:
    """
    Process all breach events from a single sensor reading.

    For each breach:
      1. Persist alert in DB (threshold read from RUNTIME_THRESHOLDS)
      2. Immediately notify ALL active subscribers on ALL channels
      3. Stop. No background re-alert timers.
    """
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

        # Fire once to all subscribers on all channels — then stop
        await _notify_all_subscribers(
            alert_id,
            breach.parameter, breach.value,
            live_threshold, breach.direction,
        )

    return alert_ids


async def acknowledge(alert_id: int, acknowledged_by: str) -> bool:
    """
    Mark an alert as seen (optional, manual action from dashboard).
    The system never calls this automatically.
    """
    ok = database.acknowledge_alert(alert_id, acknowledged_by)
    if ok:
        logger.info("Alert %d marked as seen by '%s'.", alert_id, acknowledged_by)
    else:
        logger.error("Failed to mark alert %d as seen.", alert_id)
    return ok


async def resume_pending_escalations() -> None:
    """
    Called at startup — no-op in simplified delivery mode.
    Kept for API compatibility with main.py startup sequence.
    """
    logger.info("One-shot delivery mode: no escalation tasks to resume.")


async def shutdown_escalations() -> None:
    """
    Called at server shutdown — no-op in simplified delivery mode.
    """
    pass
