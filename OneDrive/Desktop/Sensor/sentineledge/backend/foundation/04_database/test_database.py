"""
backend/foundation/04_database/test_database.py
Production-level tests for database/connection.py and queries.
Uses a temp SQLite file — does not touch the real sentineledge.db.
Run: python test_database.py
"""
import sys, os, sqlite3, tempfile
from pathlib import Path

# ── Add backend to path FIRST ─────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_BACKEND))
os.environ.setdefault("APP_ENV", "development")

# ── Patch DB_PATH to a temp file BEFORE importing anything that touches it ────
import database.connection as _conn
_TMP_DB = tempfile.mktemp(suffix=".db")
_conn.DB_PATH = _TMP_DB
_conn._connection = None   # force fresh connection

from database.connection import init_db, get_connection, execute_write, execute_read
import database   # top-level __init__ re-exports all query functions

passed = failed = 0


def ok(name, detail=""):
    global passed; passed += 1
    print(f"PASS -- {name}" + (f" -- {detail}" if detail else ""))


def fail(name, reason):
    global failed; failed += 1
    print(f"FAIL -- {name} -- {reason}")


# ── Schema ────────────────────────────────────────────────────────────────────
try:
    init_db()
    ok("test_01", "init_db() completed without error")
except Exception as e: fail("test_01", str(e))

try:
    tables = execute_read(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    names = {r["name"] for r in tables}
    expected = {"alerts", "config_changes", "delivery_receipts",
                "escalation_log", "readings", "subscribers"}
    missing = expected - names
    assert not missing, f"missing tables: {missing}"
    ok("test_02", f"All 6 tables exist: {sorted(names)}")
except Exception as e: fail("test_02", str(e))

try:
    conn = get_connection()
    row = conn.execute("PRAGMA journal_mode").fetchone()
    assert row[0].lower() == "wal", f"expected wal, got {row[0]}"
    ok("test_03", "WAL mode is enabled")
except Exception as e: fail("test_03", str(e))

try:
    indexes = execute_read(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
    )
    idx_names = {r["name"] for r in indexes}
    expected_idx = {
        "idx_alerts_timestamp", "idx_alerts_acknowledged",
        "idx_readings_timestamp", "idx_subscribers_order",
    }
    missing_idx = expected_idx - idx_names
    assert not missing_idx, f"missing indexes: {missing_idx}"
    ok("test_04", "All 4 performance indexes exist")
except Exception as e: fail("test_04", str(e))

# ── Readings ──────────────────────────────────────────────────────────────────
try:
    database.insert_reading(25.0, 60.0, "2026-06-02T10:00:00+00:00", is_valid=True)
    database.insert_reading(26.0, 62.0, "2026-06-02T10:00:01+00:00", is_valid=True)
    rows = database.get_recent_readings(limit=10)
    assert len(rows) == 2, f"expected 2, got {len(rows)}"
    ok("test_05", f"insert_reading + get_recent_readings: {len(rows)} rows")
except Exception as e: fail("test_05", str(e))

try:
    rows = database.get_recent_readings(limit=1)
    assert rows[0]["temperature"] in (25.0, 26.0)
    ok("test_06", "get_recent_readings limit=1 works")
except Exception as e: fail("test_06", str(e))

# ── Alerts ────────────────────────────────────────────────────────────────────
try:
    from utils.time import now_iso, now_plus_seconds
    alert_id = database.insert_alert(
        parameter="temperature",
        value=39.2,
        threshold=38.0,
        direction="high",
        severity="WARNING",
        cooldown_until=now_plus_seconds(120),
    )
    assert isinstance(alert_id, int) and alert_id > 0
    ok("test_07", f"insert_alert returned id={alert_id}")
except Exception as e: fail("test_07", str(e))

try:
    rows = database.get_recent_alerts(limit=10)
    assert len(rows) >= 1
    assert rows[0]["parameter"] == "temperature"
    ok("test_08", "get_recent_alerts returns correct data")
except Exception as e: fail("test_08", str(e))

# ── Acknowledge ───────────────────────────────────────────────────────────────
try:
    rows_before = database.get_recent_alerts(limit=10)
    target_id = rows_before[0]["id"]
    ok_ack = database.acknowledge_alert(target_id, "TestUser")
    assert ok_ack is True
    rows_after = database.get_recent_alerts(limit=10)
    target = next((r for r in rows_after if r["id"] == target_id), None)
    assert target and bool(target["acknowledged"])
    assert target["acknowledged_by"] == "TestUser"
    ok("test_09", f"acknowledge_alert updated correctly for id={target_id}")
except Exception as e: fail("test_09", str(e))

# ── Subscribers ───────────────────────────────────────────────────────────────
try:
    sub_id = database.add_subscriber(
        "Alice", "+919876543210", "alice@example.com", 1
    )
    assert sub_id > 0
    ok("test_10", f"add_subscriber returned id={sub_id}")
except Exception as e: fail("test_10", str(e))

try:
    rows = database.get_subscribers_ordered()
    assert len(rows) >= 1
    assert rows[0]["name"] == "Alice"
    ok("test_11", "get_subscribers_ordered returns correct data")
except Exception as e: fail("test_11", str(e))

try:
    sub = database.get_subscriber_by_order(1)
    assert sub is not None and sub["email"] == "alice@example.com"
    ok("test_12", "get_subscriber_by_order returns correct subscriber")
except Exception as e: fail("test_12", str(e))

# ── Cleanup ────────────────────────────────────────────────────────────────────
try:
    _conn._connection = None
    os.unlink(_TMP_DB)
    for ext in ("-wal", "-shm"):
        if os.path.exists(_TMP_DB + ext):
            os.unlink(_TMP_DB + ext)
except Exception:
    pass

print(f"\n{passed}/{passed+failed} tests passed")
if failed == 0: print("database module -- ALL TESTS PASSED. Safe to proceed.")
else: print("database module -- TESTS FAILED. Fix before proceeding.")
