"""
database/queries/escalation_log.py — Escalation log insert query.
"""

import logging
from datetime import datetime, timezone

from database.connection import get_connection

logger = logging.getLogger("sentineledge.database")


def log_escalation(
    alert_id: int,
    level: int,
    subscriber_id: int,
    channel: str,
    success: bool,
) -> int:
    """Insert an escalation log entry. Returns its row id."""
    conn = get_connection()
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO escalation_log
                (alert_id, escalation_level, subscriber_id, sent_at, channel, success)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (alert_id, level, subscriber_id, ts, channel, int(success)),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as exc:
        logger.exception("log_escalation failed: %s", exc)
        return -1
    finally:
        conn.close()
