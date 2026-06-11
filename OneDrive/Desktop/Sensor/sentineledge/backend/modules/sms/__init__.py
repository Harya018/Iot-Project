"""backend/modules/sms — Module 3: SMS Alert Delivery.

Supports three transport methods configured via SMS_METHOD in .env:
    adb     — Android phone via USB (demo / development)
    gammu   — USB GSM modem/dongle (production)
    gateway — Android SMS Gateway REST API (LAN, original method)

Public API:
    send_sms(phone, message)                               → bool (sync)
    send_alert_sms(phone, value, threshold, dir, ts)       → bool (sync)
    send_alert_sms_async(phone, value, threshold, dir, ts) → bool (async)
    build_sms_message(value, threshold, dir, ts)           → str
    send_sms_async(phone, message)                         → bool (legacy async)
    send_sms_to_all(subscribers, value, threshold, dir, ts)→ list (parallel batch)
    start_gsm_worker()                                     → None (call at startup)
    stop_gsm_worker()                                      → None (call at shutdown)
"""

from modules.sms.sender import (
    send_sms,
    send_alert_sms,
    send_alert_sms_async,
    build_sms_message,
    send_sms_to_all,
    start_gsm_worker,
    stop_gsm_worker,
    initialize_gsm_modem,
    detect_gsm_modem,
)
from modules.sms.gateway import send_sms_async  # legacy async shim for escalation.py

__all__ = [
    "send_sms",
    "send_alert_sms",
    "send_alert_sms_async",
    "build_sms_message",
    "send_sms_async",
    "send_sms_to_all",
    "start_gsm_worker",
    "stop_gsm_worker",
    "initialize_gsm_modem",
    "detect_gsm_modem",
]
