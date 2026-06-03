"""
database/queries/receipts.py — Delivery receipt CRUD (Addition 4).

Tracks sent/failed counts for email and SMS channels only.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from database.connection import get_connection

logger = logging.getLogger("sentineledge.database")


def insert_receipt(
    alert_id: int,
    channel: str,
    subscriber_id: int,
    escalation_level: int,
    success: bool,
    error_message: Optional[str] = None,
) -> int:
    """Insert a delivery receipt and return its row id."""
    conn = get_connection()
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO delivery_receipts
                (alert_id, channel, subscriber_id, escalation_level,
                 sent_at, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (alert_id, channel, subscriber_id, escalation_level,
             ts, int(success), error_message),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as exc:
        logger.exception("insert_receipt failed: %s", exc)
        return -1
    finally:
        conn.close()


def get_receipts_for_alert(alert_id: int) -> list[dict]:
    """Return all delivery receipts for a specific alert."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM delivery_receipts WHERE alert_id = ? ORDER BY sent_at ASC",
            (alert_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.exception("get_receipts_for_alert failed: %s", exc)
        return []
    finally:
        conn.close()


def get_delivery_stats_today() -> dict:
    """
    Return sent/failed counts for email and SMS channels for today (UTC).

    Returns:
    {
        "email": {"sent": 10, "failed": 2},
        "sms":   {"sent": 8,  "failed": 4}
    }
    """
    conn = get_connection()
    today = datetime.now(timezone.utc).date().isoformat()
    result: dict = {
        "email": {"sent": 0, "failed": 0},
        "sms":   {"sent": 0, "failed": 0},
    }
    try:
        rows = conn.execute(
            """
            SELECT channel, success, COUNT(*) as cnt
            FROM delivery_receipts
            WHERE sent_at >= ?
            GROUP BY channel, success
            """,
            (today,),
        ).fetchall()
        for row in rows:
            channel = row["channel"]
            if channel not in result:
                # inapp/push receipts are stored but not shown in delivery_stats
                continue
            if row["success"]:
                result[channel]["sent"] += row["cnt"]
            else:
                result[channel]["failed"] += row["cnt"]
        return result
    except Exception as exc:
        logger.exception("get_delivery_stats_today failed: %s", exc)
        return result
    finally:
        conn.close()
