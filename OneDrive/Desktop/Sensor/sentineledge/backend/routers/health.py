"""
routers/health.py — /api/health endpoint (Addition 5).

Returns comprehensive system health including module statuses,
uptime, connected clients, alert count, last reading, and delivery stats.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

import database
from config import MODULE_STATUS, APP_ENV, APP_VERSION
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
async def health():
    """
    Full system health check (Addition 5).
    """
    connected = len(active_connections)

    # Build module status dict with websocket client count
    modules = dict(MODULE_STATUS)
    if modules.get("websocket") == "ok" or connected > 0:
        modules["websocket"] = f"ok -- {connected} client(s) connected"
        MODULE_STATUS["websocket"] = "ok"

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

    return {
        "status": _overall_status(),
        "version": APP_VERSION,
        "environment": APP_ENV,
        "uptime": _format_uptime(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": modules,
        "connected_clients": connected,
        "alerts_today": alerts_today,
        "last_reading": last_reading if last_reading else None,
        "delivery_stats_today": delivery_stats,
    }
