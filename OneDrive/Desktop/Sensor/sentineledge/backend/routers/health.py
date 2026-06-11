"""
routers/health.py — /api/health endpoint.

Returns comprehensive system health including module statuses,
uptime, connected clients, alert count, last reading, and delivery stats.

Rate limiting (slowapi): 120/minute per IP (mobile app polls frequently).
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

import database
from config import MODULE_STATUS, APP_ENV, APP_VERSION, SMS_METHOD, SMTP_USER
from middleware.rate_limit import limiter
from modules.inapp.manager import active_connections

router = APIRouter(prefix="/api")
logger = logging.getLogger("sentineledge.routers.health")

# Server start time for uptime calculation
_START_TIME = datetime.now(timezone.utc)

# Last sensor reading — updated by main.py WebSocket handler
last_reading: dict = {}


def _format_uptime() -> str:
    """Return a human-readable uptime string like '2h 34m 12s'."""
    delta = datetime.now(timezone.utc) - _START_TIME
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def _overall_status() -> str:
    """
    Compute overall system status:
      "ok"       — all built modules reporting ok
      "degraded" — at least one built module in error
      "error"    — database or sensor is down
    """
    critical = {MODULE_STATUS.get("database"), MODULE_STATUS.get("sensor")}
    if any(s and s.startswith("error") for s in critical):
        return "error"

    has_error = any(
        v.startswith("error")
        for v in MODULE_STATUS.values()
        if v and v != "not_built"
    )
    return "degraded" if has_error else "ok"


@router.get("/health")
@limiter.limit("120/minute")
async def health(request: Request):
    """Full system health check."""
    connected = len(active_connections)

    # Build module status dict with websocket client count
    modules = dict(MODULE_STATUS)
    if modules.get("websocket") == "ok" or connected > 0:
        modules["websocket"] = f"ok -- {connected} client(s) connected"
        MODULE_STATUS["websocket"] = "ok"

    # Email module status
    from config import SMTP_HOST
    if SMTP_HOST and SMTP_USER:
        modules["email"] = "ok -- Configured"
    else:
        modules["email"] = "warning -- Not configured"

    # Enrich SMS status with method label when not already set by transport
    sms_status = modules.get("sms", "not_built")
    if sms_status in ("not_built", "starting", "", None):
        modules["sms"] = "not_configured"

    # Alerts today
    try:
        alerts_today = database.get_alerts_today_count()
    except Exception:
        alerts_today = 0

    # Delivery stats
    try:
        delivery_stats = database.get_delivery_stats_today()
    except Exception:
        delivery_stats = {}

    # GSM modem status (gammu mode only)
    try:
        from modules.sms.sender import _mock_mode as gsm_mock, _modem_port as gsm_port
        gsm_modem_info = {
            "connected": not gsm_mock,
            "port":      gsm_port if gsm_port else "not detected",
            "mode":      "live" if not gsm_mock else "mock",
        }
    except Exception:
        gsm_modem_info = {"connected": False, "port": "unknown", "mode": "mock"}

    return {
        "status":               _overall_status(),
        "version":              APP_VERSION,
        "environment":          APP_ENV,
        "uptime":               _format_uptime(),
        "timestamp":            datetime.now(timezone.utc).isoformat(),
        "modules":              modules,
        "connected_clients":    connected,
        "alerts_today":         alerts_today,
        "last_reading":         last_reading if last_reading else None,
        "delivery_stats_today": delivery_stats,
        "smtp_user":            SMTP_USER,
        "sms_method":           SMS_METHOD,
        "gsm_modem":            gsm_modem_info,
    }
