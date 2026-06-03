"""
database/queries/escalation_log.py — Escalation log insert query.

Uses execute_write so the shared connection is never closed.
"""

from datetime import datetime, timezone

from database.connection import execute_write
from utils.logger import get_logger

logger = get_logger(__name__)


def log_escalation(
    alert_id: int,
    level: int,
    subscriber_id: int,
    channel: str,
    success: bool,
) -> int:
    """Insert an escalation log entry. Returns its row id."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = execute_write(
            """
            INSERT INTO escalation_log
                (alert_id, escalation_level, subscriber_id, sent_at, channel, success)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (alert_id, level, subscriber_id, ts, channel, int(success)),
        )
        return cur.lastrowid
    except Exception as exc:
        logger.error("log_escalation failed: %s", exc)
        return -1
