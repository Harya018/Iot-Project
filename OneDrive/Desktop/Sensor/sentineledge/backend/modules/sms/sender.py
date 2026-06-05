"""
modules/sms/sender.py — SentinelEdge Module 3: SMS Alert Sender.

Routes SMS delivery to the correct transport based on SMS_METHOD in config:

    SMS_METHOD=adb     → adb_sender.py  (Android phone via USB — demo/dev)
    SMS_METHOD=gammu   → gammu_sender.py (USB GSM modem — production)
    SMS_METHOD=gateway → gateway.py      (Android SMS Gateway REST API — LAN)

Public API
----------
    send_sms(phone, message)                    → bool  (sync)
    build_sms_message(value, threshold,
                      direction, timestamp_utc) → str
    send_alert_sms(phone, value, threshold,
                   direction, timestamp_utc)    → bool  (sync)
    send_alert_sms_async(...)                   → bool  (async, non-blocking)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta

from config import SMS_METHOD
from utils.logger import get_logger

logger = get_logger("sms.sender")

# IST = UTC + 05:30
_IST_OFFSET = timedelta(hours=5, minutes=30)


# ─── Message building ─────────────────────────────────────────────────────────

def _utc_to_ist(timestamp_utc: str) -> str:
    """Convert a UTC ISO string to IST formatted as 'HH:MM IST DD-Mon-YYYY'."""
    try:
        dt = datetime.fromisoformat(timestamp_utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist = dt + _IST_OFFSET
        return ist.strftime("%H:%M IST %d-%b-%Y")
    except Exception:
        return timestamp_utc  # fallback: return as-is


def build_sms_message(
    value: float,
    threshold: float,
    direction: str,
    timestamp_utc: str,
) -> str:
    """
    Build a formatted SMS alert message strictly under 160 characters.

    LOW direction  → machine ready (cooled below threshold)
    HIGH direction → overheating danger

    Parameters
    ----------
    value         : float  — measured temperature in °C
    threshold     : float  — the threshold that was breached
    direction     : str    — "low" or "high"
    timestamp_utc : str    — UTC ISO 8601 timestamp of the breach

    Returns
    -------
    str — formatted message, always under 160 chars
    """
    time_ist = _utc_to_ist(timestamp_utc)
    val_str   = f"{value:.1f}"
    thr_str   = f"{threshold:.1f}"

    if direction.lower() == "low":
        message = (
            f"SentinelEdge Alert\n"
            f"Machine READY: {val_str}C\n"
            f"Below threshold {thr_str}C\n"
            f"Time: {time_ist}\n"
            f"-SentinelEdge"
        )
    else:  # "high" (overheating)
        message = (
            f"SentinelEdge Alert\n"
            f"HIGH TEMP: {val_str}C\n"
            f"Above threshold {thr_str}C\n"
            f"Time: {time_ist}\n"
            f"-SentinelEdge"
        )

    # Safety check — SMS standard is 160 chars for GSM-7 encoding
    if len(message) > 160:
        # Truncate time_ist to save space — very rare edge case
        short_time = time_ist[:8]  # just "HH:MM IS"
        if direction.lower() == "low":
            message = (
                f"SentinelEdge: Machine READY {val_str}C "
                f"(below {thr_str}C) at {short_time} -SentinelEdge"
            )
        else:
            message = (
                f"SentinelEdge: HIGH TEMP {val_str}C "
                f"(above {thr_str}C) at {short_time} -SentinelEdge"
            )
        logger.warning(
            "SMS message truncated to fit 160 chars (%d chars original)",
            len(message),
        )

    logger.debug("SMS message built (%d chars): %r", len(message), message[:60])
    return message


# ─── Transport router ─────────────────────────────────────────────────────────

def send_sms(phone: str, message: str) -> bool:
    """
    Route an SMS to the correct transport based on SMS_METHOD.

    Parameters
    ----------
    phone   : str — destination phone number
    message : str — plain-text SMS body (should be under 160 chars)

    Returns
    -------
    bool — True if SMS was accepted by the transport, False otherwise.
           Never raises — all transport errors are logged and return False.
    """
    method = (SMS_METHOD or "adb").lower().strip()
    logger.info("send_sms called: phone=%s method=%s", phone, method)

    if method == "adb":
        from modules.sms.adb_sender import send_sms_adb
        return send_sms_adb(phone, message)

    elif method == "gammu":
        from modules.sms.gammu_sender import send_sms_gammu
        return send_sms_gammu(phone, message)

    elif method == "gateway":
        from modules.sms.gateway import send_sms as send_sms_gateway
        return send_sms_gateway(phone, message)

    else:
        logger.error(
            "Unknown SMS_METHOD: '%s'. Valid values: adb, gammu, gateway. "
            "Check your .env file.",
            SMS_METHOD,
        )
        return False


# ─── Alert helpers ────────────────────────────────────────────────────────────

def send_alert_sms(
    phone: str,
    value: float,
    threshold: float,
    direction: str,
    timestamp_utc: str,
) -> bool:
    """
    Build and send an alert SMS synchronously.

    Parameters
    ----------
    phone         : str   — destination phone number
    value         : float — current sensor reading (°C)
    threshold     : float — breached threshold (°C)
    direction     : str   — "low" or "high"
    timestamp_utc : str   — UTC ISO timestamp of the breach

    Returns
    -------
    bool — True on success
    """
    message = build_sms_message(value, threshold, direction, timestamp_utc)
    return send_sms(phone, message)


async def send_alert_sms_async(
    phone: str,
    value: float,
    threshold: float,
    direction: str,
    timestamp_utc: str,
) -> bool:
    """
    Build and send an alert SMS asynchronously (non-blocking).

    Runs `send_alert_sms` in a thread-pool executor so it never blocks
    the async event loop during USB/serial I/O.

    Parameters
    ----------
    phone         : str   — destination phone number
    value         : float — current sensor reading (°C)
    threshold     : float — breached threshold (°C)
    direction     : str   — "low" or "high"
    timestamp_utc : str   — UTC ISO timestamp of the breach

    Returns
    -------
    bool — True on success
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        send_alert_sms,
        phone, value, threshold, direction, timestamp_utc,
    )
