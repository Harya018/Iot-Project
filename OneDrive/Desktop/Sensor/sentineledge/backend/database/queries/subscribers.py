"""
database/queries/subscribers.py — Subscriber CRUD queries.

Uses execute_write / execute_read so the shared connection is never closed.
"""

import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from database.connection import execute_write, execute_read
from utils.logger import get_logger

logger = get_logger(__name__)


def _hash_pin(pin: str) -> str:
    """Return the SHA-256 hex digest of a PIN string."""
    return hashlib.sha256(pin.encode()).hexdigest()


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


def get_subscriber_by_name_and_pin(name: str, pin: str) -> Optional[dict]:
    """
    Find an active subscriber whose name matches (case-insensitive) and whose
    stored PIN hash matches the SHA-256 hash of the supplied PIN.

    Returns the subscriber dict on success, or None if not found / bad PIN.
    """
    try:
        hashed = _hash_pin(pin)
        rows = execute_read(
            """
            SELECT * FROM subscribers
            WHERE LOWER(name) = LOWER(?)
              AND pin = ?
              AND active = 1
            """,
            (name, hashed),
        )
        return rows[0] if rows else None
    except Exception as exc:
        logger.error("get_subscriber_by_name_and_pin failed: %s", exc)
        return None


def add_subscriber(
    name: str, phone: str, email: str, escalation_order: int,
    pin: Optional[str] = None,
) -> int:
    """Insert a new subscriber and return its row id.

    If *pin* is provided it is stored as a SHA-256 hash.
    """
    try:
        ts = datetime.now(timezone.utc).isoformat()
        hashed_pin = _hash_pin(pin) if pin else None
        cur = execute_write(
            """
            INSERT INTO subscribers
                (name, phone, email, pin, escalation_order, active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (name, phone, email, hashed_pin, escalation_order, ts),
        )
        return cur.lastrowid
    except sqlite3.IntegrityError as exc:
        logger.error("add_subscriber UNIQUE conflict: %s", exc)
        return -1
    except Exception as exc:
        logger.error("add_subscriber failed: %s", exc)
        return -1


def set_subscriber_pin(subscriber_id: int, pin: str) -> bool:
    """Hash and store a PIN for an existing subscriber. Returns True on success."""
    try:
        hashed = _hash_pin(pin)
        execute_write(
            "UPDATE subscribers SET pin = ? WHERE id = ?",
            (hashed, subscriber_id),
        )
        return True
    except Exception as exc:
        logger.error("set_subscriber_pin failed: %s", exc)
        return False


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
