"""
database/queries/config_log.py — Config audit log queries.

Uses execute_write / execute_read so the shared connection is never closed.
"""

from datetime import datetime, timezone

from database.connection import execute_write, execute_read
from utils.logger import get_logger

logger = get_logger(__name__)


def log_config_change(
    changed_by: str,
    field_name: str,
    old_value: str,
    new_value: str,
) -> int:
    """Insert a config change log entry. Returns its row id."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = execute_write(
            """
            INSERT INTO config_changes
                (changed_by, field_name, old_value, new_value, changed_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (changed_by, field_name, old_value, new_value, ts),
        )
        return cur.lastrowid
    except Exception as exc:
        logger.error("log_config_change failed: %s", exc)
        return -1


def get_recent_config_changes(limit: int = 50) -> list[dict]:
    """Return the most recent `limit` config changes, newest first."""
    try:
        return execute_read(
            "SELECT * FROM config_changes ORDER BY id DESC LIMIT ?", (limit,)
        )
    except Exception as exc:
        logger.error("get_recent_config_changes failed: %s", exc)
        return []
