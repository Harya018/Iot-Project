"""
database/queries/alerts.py — Alert CRUD queries.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from database.connection import get_connection

logger = logging.getLogger("sentineledge.database")


def insert_alert(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    cooldown_until: str,
    severity: str = "WARNING",  # Addition 2
) -> int:
    """Insert a new alert and return its row id."""
    conn = get_connection()
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO alerts
                (parameter, value, threshold, direction, severity, timestamp,
                 acknowledged, escalation_level, max_escalated, cooldown_until)
            VALUES (?, ?, ?, ?, ?, ?, 0, 1, 0, ?)
            """,
            (parameter, value, threshold, direction, severity, ts, cooldown_until),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as exc:
        logger.exception("insert_alert failed: %s", exc)
        return -1
    finally:
        conn.close()


def get_alert(alert_id: int) -> Optional[dict]:
    """Return a single alert by id, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM alerts WHERE id = ?", (alert_id,)
        ).fetchone()
        return dict(row) if row else None
    except Exception as exc:
        logger.exception("get_alert failed: %s", exc)
        return None
    finally:
        conn.close()


def get_unacknowledged_alerts() -> list:
    """Return all alerts that have not been acknowledged yet."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.exception("get_unacknowledged_alerts failed: %s", exc)
        return []
    finally:
        conn.close()


def acknowledge_alert(alert_id: int, acknowledged_by: str) -> bool:
    """Mark an alert as acknowledged. Returns True on success."""
    conn = get_connection()
    try:
        ts = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            UPDATE alerts
            SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
            WHERE id = ?
            """,
            (acknowledged_by, ts, alert_id),
        )
        conn.commit()
        return True
    except Exception as exc:
        logger.exception("acknowledge_alert failed: %s", exc)
        return False
    finally:
        conn.close()


def update_escalation_level(alert_id: int, level: int) -> bool:
    """Update the current escalation level of an alert."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE alerts SET escalation_level = ? WHERE id = ?",
            (level, alert_id),
        )
        conn.commit()
        return True
    except Exception as exc:
        logger.exception("update_escalation_level failed: %s", exc)
        return False
    finally:
        conn.close()


def set_max_escalated(alert_id: int) -> bool:
    """Mark that maximum escalation has been reached for an alert."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE alerts SET max_escalated = 1 WHERE id = ?", (alert_id,)
        )
        conn.commit()
        return True
    except Exception as exc:
        logger.exception("set_max_escalated failed: %s", exc)
        return False
    finally:
        conn.close()


def get_recent_alerts(limit: int = 50) -> list:
    """Return the most recent `limit` alerts, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.exception("get_recent_alerts failed: %s", exc)
        return []
    finally:
        conn.close()


def get_alerts_today_count() -> int:
    """Return the number of alerts created today (UTC)."""
    conn = get_connection()
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM alerts WHERE timestamp >= ?",
            (today,),
        ).fetchone()
        return row["cnt"] if row else 0
    except Exception as exc:
        logger.exception("get_alerts_today_count failed: %s", exc)
        return 0
    finally:
        conn.close()
