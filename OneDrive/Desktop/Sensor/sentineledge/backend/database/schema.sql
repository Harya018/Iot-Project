-- schema.sql — SentinelEdge database schema (reference copy)
-- The actual schema is applied via database/connection.py:init_db()
-- This file is kept in sync for documentation and migration planning.
-- System monitors temperature only. Humidity removed.

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

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
    ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged
    ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp
    ON readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_subscribers_order
    ON subscribers(escalation_order);
