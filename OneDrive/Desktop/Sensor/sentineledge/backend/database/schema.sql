-- schema.sql — SentinelEdge database schema (PostgreSQL reference copy)
-- The actual schema is applied via database/connection.py:init_db()
-- This file is kept in sync for documentation and migration planning.
-- System monitors temperature only. Humidity removed.

CREATE TABLE IF NOT EXISTS readings (
    id          SERIAL           PRIMARY KEY,
    temperature DOUBLE PRECISION NOT NULL,
    timestamp   TEXT             NOT NULL,
    is_valid    INTEGER          DEFAULT 1
);

CREATE TABLE IF NOT EXISTS alerts (
    id               SERIAL           PRIMARY KEY,
    parameter        TEXT             NOT NULL,
    value            DOUBLE PRECISION NOT NULL,
    threshold        DOUBLE PRECISION NOT NULL,
    direction        TEXT             NOT NULL,
    severity         TEXT             NOT NULL DEFAULT 'WARNING',
    timestamp        TEXT             NOT NULL,
    acknowledged     INTEGER          DEFAULT 0,
    acknowledged_by  TEXT,
    acknowledged_at  TEXT,
    escalation_level INTEGER          DEFAULT 1,
    max_escalated    INTEGER          DEFAULT 0,
    cooldown_until   TEXT
);

CREATE TABLE IF NOT EXISTS subscribers (
    id               SERIAL  PRIMARY KEY,
    name             TEXT    NOT NULL,
    phone            TEXT    NOT NULL,
    email            TEXT    NOT NULL,
    pin              TEXT    DEFAULT NULL,
    escalation_order INTEGER NOT NULL UNIQUE,
    active           INTEGER DEFAULT 1,
    is_active        INTEGER DEFAULT 1,
    created_at       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS escalation_log (
    id               SERIAL  PRIMARY KEY,
    alert_id         INTEGER NOT NULL,
    escalation_level INTEGER NOT NULL,
    subscriber_id    INTEGER NOT NULL,
    sent_at          TEXT    NOT NULL,
    channel          TEXT    NOT NULL,
    success          INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS delivery_receipts (
    id               SERIAL  PRIMARY KEY,
    alert_id         INTEGER NOT NULL,
    channel          TEXT    NOT NULL,
    subscriber_id    INTEGER NOT NULL,
    escalation_level INTEGER NOT NULL,
    sent_at          TEXT    NOT NULL,
    success          INTEGER NOT NULL,
    error_message    TEXT
);

CREATE TABLE IF NOT EXISTS config_changes (
    id          SERIAL PRIMARY KEY,
    changed_by  TEXT   NOT NULL,
    field_name  TEXT   NOT NULL,
    old_value   TEXT   NOT NULL,
    new_value   TEXT   NOT NULL,
    changed_at  TEXT   NOT NULL
);

CREATE TABLE IF NOT EXISTS admins (
    id            SERIAL PRIMARY KEY,
    name          TEXT   NOT NULL UNIQUE,
    password_hash TEXT   NOT NULL,
    role          TEXT   NOT NULL DEFAULT 'sub',
    created_at    TEXT   NOT NULL
);

-- Persistent admin sessions (survives server restarts)
CREATE TABLE IF NOT EXISTS admin_sessions (
    id           SERIAL      PRIMARY KEY,
    token        TEXT        NOT NULL UNIQUE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    expires_at   TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ DEFAULT NOW()
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
CREATE INDEX IF NOT EXISTS idx_admin_sessions_token
    ON admin_sessions(token);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires
    ON admin_sessions(expires_at);
