"""
database/queries/receipts.py — Delivery receipt CRUD.

Tracks sent/failed counts for email and SMS channels.
Uses execute_write / execute_read so the shared connection is never closed.
"""

from datetime import datetime, timezone
from typing import Optional

from database.connection import execute_write, execute_read
from utils.logger import get_logger

logger = get_logger(__name__)


def insert_receipt(
    alert_id: int,
    channel: str,
    subscriber_id: int,
    escalation_level: int,
    success: bool,
    error_message: Optional[str] = None,
) -> int:
    """Insert a delivery receipt and return its row id."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = execute_write(
            """
            INSERT INTO delivery_receipts
                (alert_id, channel, subscriber_id, escalation_level,
                 sent_at, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (alert_id, channel, subscriber_id, escalation_level,
             ts, int(success), error_message),
        )
        return cur.lastrowid
    except Exception as exc:
        logger.error("insert_receipt failed: %s", exc)
        return -1


def get_receipts_for_alert(alert_id: int) -> list[dict]:
    """Return all delivery receipts for a specific alert."""
    try:
        return execute_read(
            "SELECT * FROM delivery_receipts WHERE alert_id = ? ORDER BY sent_at ASC",
            (alert_id,),
        )
    except Exception as exc:
        logger.error("get_receipts_for_alert failed: %s", exc)
        return []


def get_delivery_stats_today() -> dict:
    """
    Return sent/failed counts for email and SMS channels for today (UTC).

    Returns:
    {
        "email": {"sent": 10, "failed": 2},
        "sms":   {"sent": 8,  "failed": 4}
    }
    """
    today = datetime.now(timezone.utc).date().isoformat()
    result: dict = {
        "email": {"sent": 0, "failed": 0},
        "sms":   {"sent": 0, "failed": 0},
    }
    try:
        rows = execute_read(
            """
            SELECT channel, success, COUNT(*) as cnt
            FROM delivery_receipts
            WHERE sent_at >= ?
            GROUP BY channel, success
            """,
            (today,),
        )
        for row in rows:
            channel = row["channel"]
            if channel not in result:
                continue
            if row["success"]:
                result[channel]["sent"] += row["cnt"]
            else:
                result[channel]["failed"] += row["cnt"]
        return result
    except Exception as exc:
        logger.error("get_delivery_stats_today failed: %s", exc)
        return result
