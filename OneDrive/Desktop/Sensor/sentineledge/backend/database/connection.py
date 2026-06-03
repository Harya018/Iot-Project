"""
database/connection.py — SQLite connection pool and schema initialiser.

Uses a single shared connection with a threading.Lock() for write safety.
WAL (Write-Ahead Logging) mode prevents "database is locked" errors under
concurrent reads during WebSocket streaming.

Public API:
    get_connection()    → shared sqlite3.Connection
    execute_write()     → thread-safe INSERT/UPDATE/DELETE
    execute_read()      → thread-safe SELECT, returns list[dict]
    init_db()           → create schema + indexes on startup
"""

import os
import sqlite3
import threading

from utils.logger import get_logger
from config import MODULE_STATUS

logger = get_logger(__name__)

# ── Database path ─────────────────────────────────────────────────────────────
# backend/database/connection.py → ../../database/sentineledge.db
DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "database", "sentineledge.db")
)

# ── Shared connection pool ────────────────────────────────────────────────────
_connection: sqlite3.Connection = None
_lock = threading.Lock()


def get_connection() -> sqlite3.Connection:
    """
    Return the shared SQLite connection, creating it on first call.

    The connection is configured with:
    - row_factory = sqlite3.Row  (dict-like row access)
    - journal_mode = WAL         (concurrent reads without locking)
    - foreign_keys = ON
    - check_same_thread = False  (safe because writes go through _lock)
    """
    global _connection
    if _connection is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _connection = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,
            timeout=10,
        )
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL;")
        _connection.execute("PRAGMA foreign_keys=ON;")
        _connection.execute("PRAGMA synchronous=NORMAL;")
        logger.debug("SQLite connection created: %s", DB_PATH)
    return _connection


def execute_write(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """
    Execute an INSERT, UPDATE, or DELETE inside the write lock.

    Returns the cursor so callers can read lastrowid if needed.
    """
    with _lock:
        conn = get_connection()
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor


def execute_read(sql: str, params: tuple = ()) -> list[dict]:
    """
    Execute a SELECT and return all rows as a list of plain dicts.
    """
    conn = get_connection()
    cursor = conn.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]


# ── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL    NOT NULL,
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

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
    ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged
    ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp
    ON readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_subscribers_order
    ON subscribers(escalation_order);
"""


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Apply schema migrations for columns added/removed after initial deployment."""
    try:
        # ── readings table ────────────────────────────────────────────────────
        cursor = conn.execute("PRAGMA table_info(readings)")
        reading_cols = {row[1] for row in cursor.fetchall()}

        # Migration 1: add is_valid if missing
        if "is_valid" not in reading_cols:
            conn.execute("ALTER TABLE readings ADD COLUMN is_valid INTEGER DEFAULT 1")
            conn.commit()
            logger.info("Migration: added is_valid column to readings table")

        # Migration 2: remove humidity column (temperature-only system).
        # SQLite doesn't support DROP COLUMN until v3.35; use rename-create-copy-drop.
        if "humidity" in reading_cols:
            logger.info("Migration: removing humidity column from readings table")
            conn.executescript("""
                PRAGMA foreign_keys=OFF;
                BEGIN;
                CREATE TABLE readings_new (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperature REAL    NOT NULL,
                    timestamp   TEXT    NOT NULL,
                    is_valid    INTEGER DEFAULT 1
                );
                INSERT INTO readings_new (id, temperature, timestamp, is_valid)
                    SELECT id, temperature, timestamp,
                           COALESCE(is_valid, 1)
                    FROM readings;
                DROP TABLE readings;
                ALTER TABLE readings_new RENAME TO readings;
                CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp);
                COMMIT;
                PRAGMA foreign_keys=ON;
            """)
            logger.info("Migration: humidity column removed from readings table")

        # ── alerts table ──────────────────────────────────────────────────────
        cursor = conn.execute("PRAGMA table_info(alerts)")
        alert_cols = {row[1] for row in cursor.fetchall()}

        # Migration 3: add severity column if missing
        if "severity" not in alert_cols:
            conn.execute(
                "ALTER TABLE alerts ADD COLUMN severity TEXT NOT NULL DEFAULT 'WARNING'"
            )
            conn.commit()
            logger.info("Migration: added severity column to alerts table")

        # Migration 4: add max_escalated column if missing
        if "max_escalated" not in alert_cols:
            conn.execute(
                "ALTER TABLE alerts ADD COLUMN max_escalated INTEGER DEFAULT 0"
            )
            conn.commit()
            logger.info("Migration: added max_escalated column to alerts table")

        # Migration 5: add cooldown_until column if missing
        if "cooldown_until" not in alert_cols:
            conn.execute("ALTER TABLE alerts ADD COLUMN cooldown_until TEXT")
            conn.commit()
            logger.info("Migration: added cooldown_until column to alerts table")

        # ── subscribers table ─────────────────────────────────────────────────
        cursor = conn.execute("PRAGMA table_info(subscribers)")
        subscriber_cols = {row[1] for row in cursor.fetchall()}

        # Migration 6: remove push_subscription column.
        # SQLite doesn't support DROP COLUMN until v3.35; use rename-create-copy-drop.
        if "push_subscription" in subscriber_cols:
            logger.info("Migration: removing push_subscription column from subscribers table")
            conn.executescript("""
                PRAGMA foreign_keys=OFF;
                BEGIN;
                CREATE TABLE subscribers_new (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    name             TEXT    NOT NULL,
                    phone            TEXT    NOT NULL,
                    email            TEXT    NOT NULL,
                    escalation_order INTEGER NOT NULL UNIQUE,
                    active           INTEGER DEFAULT 1,
                    created_at       TEXT    NOT NULL
                );
                INSERT INTO subscribers_new
                        (id, name, phone, email, escalation_order, active, created_at)
                    SELECT id, name, phone, email, escalation_order, active, created_at
                    FROM subscribers;
                DROP TABLE subscribers;
                ALTER TABLE subscribers_new RENAME TO subscribers;
                CREATE INDEX IF NOT EXISTS idx_subscribers_order
                    ON subscribers(escalation_order);
                COMMIT;
                PRAGMA foreign_keys=ON;
            """)
            logger.info("Migration: push_subscription column removed from subscribers table")

    except Exception as exc:
        logger.warning("Migration warning: %s", exc)


def init_db() -> None:
    """Create all tables and indexes if they do not already exist."""
    try:
        conn = get_connection()
        with _lock:
            conn.executescript(_SCHEMA_SQL)
            conn.commit()
        _run_migrations(conn)
        logger.info("Database initialised at %s", DB_PATH)
        MODULE_STATUS["database"] = "ok"
    except Exception as exc:
        logger.exception("Failed to initialise database: %s", exc)
        MODULE_STATUS["database"] = f"error: {exc}"
        raise

