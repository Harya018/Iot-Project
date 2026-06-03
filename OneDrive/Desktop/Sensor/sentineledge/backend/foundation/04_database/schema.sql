-- schema.sql — SentinelEdge database schema (reference copy)
-- The actual schema is applied via connection.py:init_db().

CREATE TABLE IF NOT EXISTS readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL    NOT NULL,
    humidity    REAL    NOT NULL,
    timestamp   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    parameter        TEXT    NOT NULL,
    value            REAL    NOT NULL,
    threshold        REAL    NOT NULL,
    direction        TEXT    NOT NULL,
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
