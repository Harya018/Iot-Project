"""
database/connection.py — SQLite connection factory and schema initialiser.

The database file lives at ../../database/sentineledge.db relative to this
file (i.e. the project root's database/ directory).
"""

import os
import sqlite3
import logging

from config import MODULE_STATUS

logger = logging.getLogger("sentineledge.database")

# Resolve path: backend/database/connection.py -> ../../database/sentineledge.db
_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "database", "sentineledge.db")
)


def get_connection() -> sqlite3.Connection:
    """Return a new thread-safe SQLite connection with row factory."""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """Create all tables if they do not already exist."""
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = get_connection()
    try:
        conn.cursor().executescript(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL    NOT NULL,
                humidity    REAL    NOT NULL,
                timestamp   TEXT    NOT NULL,
                is_valid    INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter        TEXT    NOT NULL,
                value            REAL    NOT NULL,
                threshold        REAL    NOT NULL,
                direction        TEXT    NOT NULL,
                severity         TEXT    NOT NULL DEFAULT 'WARNING',
                timestamp        TEXT    NOT NULL,
                acknowledged     INTEGER DEFAULT 0,
                acknowledged_by  TEXT,
                acknowledged_at  TEXT,
                escalation_level INTEGER DEFAULT 1,
                max_escalated    INTEGER DEFAULT 0,
                cooldown_until   TEXT
            );

            CREATE TABLE IF NOT EXISTS subscribers (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                name             TEXT    NOT NULL,
                phone            TEXT    NOT NULL,
                email            TEXT    NOT NULL,
                push_subscription TEXT,
                escalation_order INTEGER NOT NULL UNIQUE,
                active           INTEGER DEFAULT 1,
                created_at       TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS escalation_log (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id         INTEGER NOT NULL,
                escalation_level INTEGER NOT NULL,
                subscriber_id    INTEGER NOT NULL,
                sent_at          TEXT    NOT NULL,
                channel          TEXT    NOT NULL,
                success          INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS delivery_receipts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id         INTEGER NOT NULL,
                channel          TEXT    NOT NULL,
                subscriber_id    INTEGER NOT NULL,
                escalation_level INTEGER NOT NULL,
                sent_at          TEXT    NOT NULL,
                success          INTEGER NOT NULL,
                error_message    TEXT
            );

            CREATE TABLE IF NOT EXISTS config_changes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                changed_by  TEXT NOT NULL,
                field_name  TEXT NOT NULL,
                old_value   TEXT NOT NULL,
                new_value   TEXT NOT NULL,
                changed_at  TEXT NOT NULL
            );
            """
        )
        conn.commit()
        logger.info("Database initialised at %s", _DB_PATH)
        MODULE_STATUS["database"] = "ok"
    except Exception as exc:
        logger.exception("Failed to initialise database: %s", exc)
        MODULE_STATUS["database"] = f"error: {exc}"
        raise
    finally:
        conn.close()
