"""
database/queries/config_log.py — Config audit log queries (Addition 6).
"""

import logging
from datetime import datetime, timezone

from database.connection import get_connection

logger = logging.getLogger("sentineledge.database")


def log_config_change(
    changed_by: str,
    field_name: str,
    old_value: str,
    new_value: str,
) -> int:
    """Insert a config change log entry. Returns its row id."""
    conn = get_connection()
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO config_changes
                (changed_by, field_name, old_value, new_value, changed_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (changed_by, field_name, old_value, new_value, ts),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as exc:
        logger.exception("log_config_change failed: %s", exc)
        return -1
    finally:
        conn.close()


def get_recent_config_changes(limit: int = 50) -> list[dict]:
    """Return the most recent `limit` config changes, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM config_changes ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.exception("get_recent_config_changes failed: %s", exc)
        return []
    finally:
        conn.close()
