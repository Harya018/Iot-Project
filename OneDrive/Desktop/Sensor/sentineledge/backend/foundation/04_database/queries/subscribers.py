"""
database/queries/subscribers.py — Subscriber CRUD queries.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from database.connection import get_connection

logger = logging.getLogger("sentineledge.database")


def get_subscribers_ordered() -> list:
    """Return all active subscribers ordered by escalation_order ASC."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM subscribers WHERE active = 1 ORDER BY escalation_order ASC"
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.exception("get_subscribers_ordered failed: %s", exc)
        return []
    finally:
        conn.close()


def get_subscriber_by_order(order: int) -> Optional[dict]:
    """Return the active subscriber at a specific escalation_order, or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM subscribers WHERE escalation_order = ? AND active = 1",
            (order,),
        ).fetchone()
        return dict(row) if row else None
    except Exception as exc:
        logger.exception("get_subscriber_by_order failed: %s", exc)
        return None
    finally:
        conn.close()


def add_subscriber(
    name: str, phone: str, email: str, escalation_order: int
) -> int:
    """Insert a new subscriber and return its row id."""
    conn = get_connection()
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            INSERT INTO subscribers
                (name, phone, email, escalation_order, active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (name, phone, email, escalation_order, ts),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as exc:
        logger.error("add_subscriber UNIQUE conflict: %s", exc)
        return -1
    except Exception as exc:
        logger.exception("add_subscriber failed: %s", exc)
        return -1
    finally:
        conn.close()


def update_push_subscription(subscriber_id: int, push_subscription_json: str) -> bool:
    """Save or update the Web Push subscription JSON for a subscriber."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE subscribers SET push_subscription = ? WHERE id = ?",
            (push_subscription_json, subscriber_id),
        )
        conn.commit()
        return True
    except Exception as exc:
        logger.exception("update_push_subscription failed: %s", exc)
        return False
    finally:
        conn.close()


def delete_subscriber(subscriber_id: int) -> bool:
    """Hard-delete a subscriber by id. Returns True on success."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM subscribers WHERE id = ?", (subscriber_id,))
        conn.commit()
        return True
    except Exception as exc:
        logger.exception("delete_subscriber failed: %s", exc)
        return False
    finally:
        conn.close()
