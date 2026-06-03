"""
database/queries/subscribers.py — Subscriber CRUD queries.

Uses execute_write / execute_read so the shared connection is never closed.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from database.connection import execute_write, execute_read
from utils.logger import get_logger

logger = get_logger(__name__)


def get_subscribers_ordered() -> list:
    """Return all active subscribers ordered by escalation_order ASC."""
    try:
        return execute_read(
            "SELECT * FROM subscribers WHERE active = 1 ORDER BY escalation_order ASC"
        )
    except Exception as exc:
        logger.error("get_subscribers_ordered failed: %s", exc)
        return []


def get_subscriber_by_order(order: int) -> Optional[dict]:
    """Return the active subscriber at a specific escalation_order, or None."""
    try:
        rows = execute_read(
            "SELECT * FROM subscribers WHERE escalation_order = ? AND active = 1",
            (order,),
        )
        return rows[0] if rows else None
    except Exception as exc:
        logger.error("get_subscriber_by_order failed: %s", exc)
        return None


def add_subscriber(
    name: str, phone: str, email: str, escalation_order: int
) -> int:
    """Insert a new subscriber and return its row id."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        cur = execute_write(
            """
            INSERT INTO subscribers
                (name, phone, email, escalation_order, active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (name, phone, email, escalation_order, ts),
        )
        return cur.lastrowid
    except sqlite3.IntegrityError as exc:
        logger.error("add_subscriber UNIQUE conflict: %s", exc)
        return -1
    except Exception as exc:
        logger.error("add_subscriber failed: %s", exc)
        return -1


def update_push_subscription(subscriber_id: int, push_subscription_json: str) -> bool:
    """Save or update the Web Push subscription JSON for a subscriber."""
    try:
        execute_write(
            "UPDATE subscribers SET push_subscription = ? WHERE id = ?",
            (push_subscription_json, subscriber_id),
        )
        return True
    except Exception as exc:
        logger.error("update_push_subscription failed: %s", exc)
        return False


def delete_subscriber(subscriber_id: int) -> bool:
    """Hard-delete a subscriber by id. Returns True on success."""
    try:
        execute_write("DELETE FROM subscribers WHERE id = ?", (subscriber_id,))
        return True
    except Exception as exc:
        logger.error("delete_subscriber failed: %s", exc)
        return False
