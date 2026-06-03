
"""Part 1 — Suites 01-05"""
import sys, os, types, tempfile, asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("APP_ENV", "development")

results = {}

def run_test(name, fn):
    try:
        fn()
        print(f"  PASS — {name}")
        return True
    except Exception as e:
        print(f"  FAIL — {name} — {e}")
        return False

def run_suite(key, label, tests):
    print(f"\n{'='*50}")
    print(f"  TESTING {key} — {label}")
    print(f"{'='*50}")
    p = sum(run_test(n, f) for n, f in tests)
    t = len(tests)
    print(f"  Result: {p}/{t} passed")
    results[f"{key}_{label}"] = (p, t)

# ── SUITE 01 — CONFIG ─────────────────────────────────────────────────────────
try:
    import config as cfg
    def s01():
        run_suite("01", "CONFIG", [
            ("APP_ENV is valid string",
             lambda: (assert_true(cfg.APP_ENV in ("development","production","test")))),
            ("TEMP_THRESHOLD_HIGH > TEMP_THRESHOLD_LOW",
             lambda: assert_true(cfg.TEMP_THRESHOLD_HIGH > cfg.TEMP_THRESHOLD_LOW)),
            ("TEMP_THRESHOLD_HIGH is float",
             lambda: assert_true(isinstance(cfg.TEMP_THRESHOLD_HIGH, float))),
            ("HUMIDITY_THRESHOLD_HIGH > HUMIDITY_THRESHOLD_LOW",
             lambda: assert_true(cfg.HUMIDITY_THRESHOLD_HIGH > cfg.HUMIDITY_THRESHOLD_LOW)),
            ("HUMIDITY_THRESHOLD_HIGH is float",
             lambda: assert_true(isinstance(cfg.HUMIDITY_THRESHOLD_HIGH, float))),
            ("ALERT_COOLDOWN_SECONDS > 0",
             lambda: assert_true(cfg.ALERT_COOLDOWN_SECONDS > 0)),
            ("ESCALATION_TIMEOUT_SECONDS > 0",
             lambda: assert_true(cfg.ESCALATION_TIMEOUT_SECONDS > 0)),
            ("SERVER_PORT 1000-65535",
             lambda: assert_true(1000 <= cfg.SERVER_PORT <= 65535)),
            ("RUNTIME_THRESHOLDS has flat keys",
             lambda: assert_true(all(k in cfg.RUNTIME_THRESHOLDS for k in
                 ["temp_high","temp_low","humidity_high","humidity_low"]))),
            ("MODULE_STATUS has 5 keys",
             lambda: assert_true(all(k in cfg.MODULE_STATUS for k in
                 ["sensor","database","email","sms","websocket"]))),
            ("SERVER_START_TIME is datetime",
             lambda: assert_true(hasattr(cfg.SERVER_START_TIME, 'year'))),
            ("CONNECTED_CLIENTS >= 0",
             lambda: assert_true(cfg.CONNECTED_CLIENTS >= 0)),
        ])
    s01()
except Exception as e:
    results["01_CONFIG"] = (0, 12)
    print(f"  SUITE 01 IMPORT ERROR: {e}")

# ── SUITE 02 — MODELS ─────────────────────────────────────────────────────────
try:
    from models import BreachEvent, ReadingOut, AlertOut, SubscriberIn, ThresholdConfigIn, AcknowledgeIn
    from pydantic import ValidationError

    def s02():
        def t02_01():
            b = BreachEvent(parameter="temperature", value=40.0, threshold=38.0, direction="high")
            assert b.severity == "WARNING"
        def t02_02():
            try:
                BreachEvent(value=40.0, threshold=38.0, direction="high")
                raise AssertionError("should fail")
            except (ValidationError, TypeError): pass
        def t02_03():
            r = ReadingOut(temperature=25.0, humidity=55.0, timestamp="2026-01-01T00:00:00+00:00")
            assert r.breaches == []
        def t02_04():
            a = AlertOut(id=1, parameter="temperature", value=40.0, threshold=38.0,
                direction="high", timestamp="2026-01-01T00:00:00+00:00",
                acknowledged=False, escalation_level=1, max_escalated=False)
            assert a.severity == "WARNING"
        def t02_05():
            try:
                SubscriberIn(name="Alice", phone="abc123", email="a@b.com", escalation_order=1)
                raise AssertionError("should fail")
            except ValidationError: pass
        def t02_06():
            try:
                SubscriberIn(name="Alice", phone="+919876543210", email="a@b.com", escalation_order=5)
                raise AssertionError("should fail")
            except ValidationError: pass
        def t02_07():
            try:
                ThresholdConfigIn(temp_high=20.0, temp_low=30.0, humidity_high=80.0, humidity_low=35.0)
                raise AssertionError("should fail")
            except ValidationError: pass
        def t02_08():
            try:
                AcknowledgeIn(acknowledged_by=" ")
                raise AssertionError("should fail")
            except ValidationError: pass
        def t02_09():
            s = SubscriberIn(name="Bob", phone="+919876543210", email="b@c.com", escalation_order=2)
            assert s.escalation_order == 2
        def t02_10():
            cfg_in = ThresholdConfigIn(temp_high=38.0, temp_low=22.0, humidity_high=80.0, humidity_low=35.0)
            assert cfg_in.temp_high == 38.0

        run_suite("02", "MODELS", [
            ("BreachEvent created with defaults", t02_01),
            ("BreachEvent rejects missing parameter", t02_02),
            ("ReadingOut defaults breaches=[]", t02_03),
            ("AlertOut has all required fields", t02_04),
            ("SubscriberIn rejects letters in phone", t02_05),
            ("SubscriberIn rejects escalation_order=5", t02_06),
            ("ThresholdConfigIn rejects high < low", t02_07),
            ("AcknowledgeIn rejects whitespace-only", t02_08),
            ("SubscriberIn accepts valid data", t02_09),
            ("ThresholdConfigIn accepts valid data", t02_10),
        ])
    s02()
except Exception as e:
    results["02_MODELS"] = (0, 10)
    print(f"  SUITE 02 IMPORT ERROR: {e}")

# ── SUITE 03 — UTILS ──────────────────────────────────────────────────────────
try:
    from utils.logger import get_logger, sanitise_log_data
    from utils.time import now_iso, now_plus_seconds, seconds_since, format_duration
    from utils.formatter import format_alert_message, format_escalation_message, format_sms_message
    import logging

    def s03():
        run_suite("03", "UTILS", [
            ("get_logger returns Logger",
             lambda: assert_true(isinstance(get_logger("test"), logging.Logger))),
            ("log file exists",
             lambda: assert_true((ROOT / "logs" / "sentineledge.log").exists())),
            ("sanitise redacts password",
             lambda: assert_true(sanitise_log_data({"password":"x"})["password"] == "***REDACTED***")),
            ("sanitise redacts smtp_password",
             lambda: assert_true(sanitise_log_data({"smtp_password":"x"})["smtp_password"] == "***REDACTED***")),
            ("sanitise keeps non-sensitive",
             lambda: assert_true(sanitise_log_data({"host":"smtp.gmail.com"})["host"] == "smtp.gmail.com")),
            ("now_iso contains T",
             lambda: assert_true("T" in now_iso())),
            ("seconds_since returns float >= 0",
             lambda: assert_true(seconds_since(now_plus_seconds(-10)) >= 0)),
            ("now_plus_seconds(60) is ahead",
             lambda: assert_true(now_plus_seconds(60) > now_iso())),
            ("format_duration(90) = 1m 30s",
             lambda: assert_true(format_duration(90) == "1m 30s")),
            ("format_duration(3600) = 1h 0m",
             lambda: assert_true(format_duration(3600) == "1h 0m")),
            ("format_alert_message temp high has exceeds",
             lambda: assert_true("exceeds" in format_alert_message("temperature",39.0,38.0,"high","WARNING","\u00b0C"))),
            ("format_alert_message humidity low has below",
             lambda: assert_true("below" in format_alert_message("humidity",30.0,35.0,"low","WARNING","%"))),
            ("format_sms_message <= 160 chars",
             lambda: assert_true(len(format_sms_message("temperature",42.0,38.0,"high","CRITICAL","\u00b0C",2)) <= 160)),
            ("format_escalation_message level 2",
             lambda: assert_true("ESCALATION" in format_escalation_message("temperature",42.0,38.0,"high","CRITICAL","\u00b0C",2))),
            ("format_escalation_message level 3",
             lambda: assert_true("Level 3" in format_escalation_message("temperature",42.0,38.0,"high","EMERGENCY","\u00b0C",3))),
        ])
    s03()
except Exception as e:
    results["03_UTILS"] = (0, 15)
    print(f"  SUITE 03 IMPORT ERROR: {e}")

# ── SUITE 04 — DATABASE ───────────────────────────────────────────────────────
_tmp_db = None
try:
    import database.connection as _dc
    _tmp_db = tempfile.mktemp(suffix="_test.db")
    _real_db = _dc.DB_PATH
    _dc.DB_PATH = _tmp_db
    _dc._connection = None

    from database.connection import init_db, execute_read, execute_write, get_connection
    import database

    def s04():
        init_db()
        from utils.time import now_plus_seconds

        def t04_01(): init_db()
        def t04_02():
            tables = {r["name"] for r in execute_read(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            assert {"readings","alerts","subscribers","escalation_log",
                    "delivery_receipts","config_changes"}.issubset(tables)
        def t04_03():
            row = get_connection().execute("PRAGMA journal_mode").fetchone()
            assert row[0].lower() == "wal"
        def t04_04():
            rid = database.insert_reading(25.0, 60.0, now_iso(), True)
            assert isinstance(rid, int) and rid > 0
        def t04_05():
            database.insert_reading(26.0, 61.0, now_iso(), True)
            rows = database.get_recent_readings(limit=10)
            assert len(rows) >= 1
        def t04_06():
            aid = database.insert_alert("temperature", 40.0, 38.0, "high", now_plus_seconds(120), "WARNING")
            assert isinstance(aid, int) and aid > 0
        def t04_07():
            rows = database.get_recent_alerts(limit=10)
            assert len(rows) >= 1
        def t04_08():
            sid = database.add_subscriber("Alice", "+919876543210", "a@b.com", 1)
            assert isinstance(sid, int) and sid > 0
        def t04_09():
            rows = database.get_subscribers_ordered()
            assert len(rows) >= 1
        def t04_10():
            rows = database.get_recent_alerts(limit=10)
            aid = rows[0]["id"]
            ok = database.acknowledge_alert(aid, "Tester")
            assert ok is True
            rows2 = database.get_recent_alerts(limit=10)
            target = next(r for r in rows2 if r["id"] == aid)
            assert bool(target["acknowledged"])
        def t04_11():
            rows = database.get_recent_alerts(limit=10)
            aid = rows[0]["id"]
            ok = database.update_escalation_level(aid, 2)
            assert ok is True
        def t04_12():
            idxs = {r["name"] for r in execute_read(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")}
            assert "idx_alerts_timestamp" in idxs
            assert "idx_readings_timestamp" in idxs
            assert "idx_subscribers_order" in idxs

        run_suite("04", "DATABASE", [
            ("init_db() runs without error", t04_01),
            ("All 6 tables exist", t04_02),
            ("WAL mode enabled", t04_03),
            ("insert_reading returns int ID", t04_04),
            ("get_recent_readings returns rows", t04_05),
            ("insert_alert returns int ID", t04_06),
            ("get_recent_alerts returns rows", t04_07),
            ("add_subscriber returns int ID", t04_08),
            ("get_subscribers_ordered returns rows", t04_09),
            ("acknowledge_alert updates DB", t04_10),
            ("update_escalation_level updates DB", t04_11),
            ("Performance indexes exist", t04_12),
        ])
    s04()
except Exception as e:
    results["04_DATABASE"] = (0, 12)
    print(f"  SUITE 04 IMPORT ERROR: {e}")
finally:
    try:
        import database.connection as _dc2
        _dc2._connection = None
        if _tmp_db and os.path.exists(_tmp_db):
            os.unlink(_tmp_db)
        for ext in ("-wal", "-shm"):
            if _tmp_db and os.path.exists(_tmp_db + ext):
                os.unlink(_tmp_db + ext)
    except Exception:
        pass

# ── SUITE 05 — THRESHOLDS ────────────────────────────────────────────────────
try:
    from core.thresholds import THRESHOLDS, get_all_thresholds

    def s05():
        run_suite("05", "THRESHOLDS", [
            ("temperature.high == 38.0",
             lambda: assert_true(THRESHOLDS.temperature.high == 38.0)),
            ("temperature.low == 22.0",
             lambda: assert_true(THRESHOLDS.temperature.low == 22.0)),
            ("humidity.high == 80.0",
             lambda: assert_true(THRESHOLDS.humidity.high == 80.0)),
            ("humidity.low == 35.0",
             lambda: assert_true(THRESHOLDS.humidity.low == 35.0)),
            ("get_severity 3% over = WARNING",
             lambda: assert_true(THRESHOLDS.temperature.get_severity(38.0*1.03,"high") == "WARNING")),
            ("get_severity 12% over = CRITICAL",
             lambda: assert_true(THRESHOLDS.temperature.get_severity(38.0*1.12,"high") == "CRITICAL")),
            ("get_severity 30% over = EMERGENCY",
             lambda: assert_true(THRESHOLDS.temperature.get_severity(38.0*1.30,"high") == "EMERGENCY")),
            ("get_severity low direction works",
             lambda: assert_true(THRESHOLDS.temperature.get_severity(22.0*0.85,"low") in ("CRITICAL","EMERGENCY"))),
            ("get_all_thresholds has temp+humidity",
             lambda: assert_true("temperature" in get_all_thresholds() and "humidity" in get_all_thresholds())),
            ("to_dict has required fields",
             lambda: assert_true(all(k in THRESHOLDS.temperature.to_dict()
                 for k in ("high","low","unit","name","severity_levels")))),
        ])
    s05()
except Exception as e:
    results["05_THRESHOLDS"] = (0, 10)
    print(f"  SUITE 05 IMPORT ERROR: {e}")

def assert_true(val):
    if not val:
        raise AssertionError(f"assertion failed: {val!r}")

def now_iso():
    from utils.time import now_iso as _n
    return _n()

# Save partial results for part2
import json
_out = ROOT / "backend" / "foundation" / "_part1_results.json"
with open(_out, "w") as f:
    json.dump(results, f)
print("\nPart 1 complete. Run run_all_tests_part2.py next.")
