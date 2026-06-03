"""
database/queries/alerts.py — Alert CRUD queries.

Uses execute_write / execute_read so the shared connection is never closed.
"""

from datetime import datetime, timezone
from typing import Optional

from database.connection import execute_write, execute_read, get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def insert_alert(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    cooldown_until: str,
    severity: str = "WARNING",
) -> int:
    """Insert a new alert and return its row id."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = execute_write(
            """
            INSERT INTO alerts
                (parameter, value, threshold, direction, severity, timestamp,
                 acknowledged, escalation_level, max_escalated, cooldown_until)
            VALUES (?, ?, ?, ?, ?, ?, 0, 1, 0, ?)
            """,
            (parameter, value, threshold, direction, severity, ts, cooldown_until),
        )
        return cur.lastrowid
    except Exception as exc:
        logger.error("insert_alert failed: %s", exc)
        return -1


def get_alert(alert_id: int) -> Optional[dict]:
    """Return a single alert by id, or None if not found."""
    try:
        rows = execute_read("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        return rows[0] if rows else None
    except Exception as exc:
        logger.error("get_alert failed: %s", exc)
        return None


def get_unacknowledged_alerts() -> list:
    """Return all alerts that have not been acknowledged yet."""
    try:
        return execute_read(
            "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY id ASC"
        )
    except Exception as exc:
        logger.error("get_unacknowledged_alerts failed: %s", exc)
        return []


def acknowledge_alert(alert_id: int, acknowledged_by: str) -> bool:
    """Mark an alert as acknowledged. Returns True on success."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        execute_write(
            """
            UPDATE alerts
            SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
            WHERE id = ?
            """,
            (acknowledged_by, ts, alert_id),
        )
        return True
    except Exception as exc:
        logger.error("acknowledge_alert failed: %s", exc)
        return False


def update_escalation_level(alert_id: int, level: int) -> bool:
    """Update the current escalation level of an alert."""
    try:
        execute_write(
            "UPDATE alerts SET escalation_level = ? WHERE id = ?",
            (level, alert_id),
        )
        return True
    except Exception as exc:
        logger.error("update_escalation_level failed: %s", exc)
        return False


def set_max_escalated(alert_id: int) -> bool:
    """Mark that maximum escalation has been reached for an alert."""
    try:
        execute_write(
            "UPDATE alerts SET max_escalated = 1 WHERE id = ?", (alert_id,)
        )
        return True
    except Exception as exc:
        logger.error("set_max_escalated failed: %s", exc)
        return False


def get_recent_alerts(limit: int = 50) -> list:
    """Return the most recent `limit` alerts, newest first."""
    try:
        return execute_read(
            "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
        )
    except Exception as exc:
        logger.error("get_recent_alerts failed: %s", exc)
        return []


def get_alerts_today_count() -> int:
    """Return the number of alerts created today (UTC)."""
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        rows = execute_read(
            "SELECT COUNT(*) as cnt FROM alerts WHERE timestamp >= ?", (today,)
        )
        return rows[0]["cnt"] if rows else 0
    except Exception as exc:
        logger.error("get_alerts_today_count failed: %s", exc)
        return 0
