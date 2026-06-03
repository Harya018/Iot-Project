"""
backend/foundation/03_utils/test_utils.py
Standalone production-level tests for the utils package.
Tests: logger, sanitise_log_data, time helpers, formatter functions.
Run: python test_utils.py
"""
import sys, datetime
from pathlib import Path

# Add utils package to path
_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import os
os.environ.setdefault("APP_ENV", "development")

from utils.logger import get_logger, sanitise_log_data
from utils.time import (
    now_iso, now_plus_seconds, parse_iso,
    seconds_since, format_duration, seconds_until_midnight, today_date_str,
)
from utils.formatter import (
    format_alert_message, format_escalation_message,
    format_email_subject, format_sms_message, format_daily_report,
)

logger = get_logger("test_utils")
passed = failed = 0


def ok(name, detail=""):
    global passed; passed += 1
    print(f"PASS -- {name}" + (f" -- {detail}" if detail else ""))


def fail(name, reason):
    global failed; failed += 1
    print(f"FAIL -- {name} -- {reason}")


# ── Logger ────────────────────────────────────────────────────────────────────
try:
    logger.info("Test log message")
    ok("test_01", "get_logger returns working logger")
except Exception as e: fail("test_01", str(e))

try:
    log_dir = _BACKEND.parent / "logs"
    assert log_dir.exists(), f"logs/ dir not found at {log_dir}"
    ok("test_02", f"logs/ directory exists at {log_dir}")
except Exception as e: fail("test_02", str(e))

try:
    d = sanitise_log_data({"username": "alice", "password": "secret123"})
    assert d["password"] == "***REDACTED***"
    assert d["username"] == "alice"
    ok("test_03", "sanitise_log_data redacts password")
except Exception as e: fail("test_03", str(e))

try:
    d = sanitise_log_data({"smtp_password": "x", "token": "abc", "host": "smtp.gmail.com"})
    assert d["smtp_password"] == "***REDACTED***"
    assert d["token"] == "***REDACTED***"
    assert d["host"] == "smtp.gmail.com"
    ok("test_04", "sanitise_log_data redacts smtp_password and token, keeps host")
except Exception as e: fail("test_04", str(e))

# ── Time ──────────────────────────────────────────────────────────────────────
try:
    iso = now_iso()
    assert "T" in iso and "+" in iso
    ok("test_05", f"now_iso returns UTC ISO string: {iso[:22]}")
except Exception as e: fail("test_05", str(e))

try:
    iso = now_plus_seconds(120)
    dt = parse_iso(iso)
    diff = (dt - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    assert 110 < diff < 130
    ok("test_06", f"now_plus_seconds(120) is ~120s in future")
except Exception as e: fail("test_06", str(e))

try:
    past = now_plus_seconds(-30)
    secs = seconds_since(past)
    assert 25 < secs < 40, f"expected ~30, got {secs}"
    ok("test_07", f"seconds_since past timestamp: {secs:.1f}s")
except Exception as e: fail("test_07", str(e))

try:
    future = now_plus_seconds(30)
    secs = seconds_since(future)
    assert secs == 0.0, f"expected 0, got {secs}"
    ok("test_08", "seconds_since future timestamp returns 0")
except Exception as e: fail("test_08", str(e))

try:
    assert format_duration(45) == "45s"
    assert format_duration(90) == "1m 30s"
    assert format_duration(3720) == "1h 2m"
    ok("test_09", "format_duration: 45s, 1m 30s, 1h 2m")
except Exception as e: fail("test_09", str(e))

try:
    wait = seconds_until_midnight()
    assert 0 < wait <= 86400
    ok("test_10", f"seconds_until_midnight: {wait:.0f}s")
except Exception as e: fail("test_10", str(e))

try:
    d = today_date_str()
    assert len(d) == 10 and "-" in d
    ok("test_11", f"today_date_str: {d}")
except Exception as e: fail("test_11", str(e))

# ── Formatter ─────────────────────────────────────────────────────────────────
try:
    msg = format_alert_message("temperature", 39.2, 38.0, "high", "WARNING", "\u00b0C")
    assert "[WARNING]" in msg and "39.2" in msg and "exceeds high" in msg
    ok("test_12", f"format_alert_message high: {msg[:60]}")
except Exception as e: fail("test_12", str(e))

try:
    msg = format_alert_message("temperature", 20.0, 22.0, "low", "WARNING", "\u00b0C")
    assert "below low" in msg
    ok("test_13", f"format_alert_message low: {msg[:60]}")
except Exception as e: fail("test_13", str(e))

try:
    msg = format_alert_message("humidity", 85.0, 80.0, "high", "CRITICAL", "%")
    assert "[CRITICAL]" in msg and "exceeds high" in msg
    ok("test_14", "format_alert_message humidity high")
except Exception as e: fail("test_14", str(e))

try:
    msg = format_alert_message("humidity", 30.0, 35.0, "low", "EMERGENCY", "%")
    assert "[EMERGENCY]" in msg and "below low" in msg
    ok("test_15", "format_alert_message humidity low")
except Exception as e: fail("test_15", str(e))

try:
    msg = format_escalation_message(
        "temperature", 42.0, 38.0, "high", "CRITICAL", "\u00b0C",
        level=2, prev_name="Alice", timeout=60
    )
    assert "Level 2" in msg and "Alice" in msg and "60s" in msg
    ok("test_16", f"format_escalation_message level 2: {msg[:80]}")
except Exception as e: fail("test_16", str(e))

try:
    msg = format_escalation_message(
        "temperature", 42.0, 38.0, "high", "EMERGENCY", "\u00b0C",
        level=3, timeout=60
    )
    assert "Level 3" in msg and "120s" in msg
    ok("test_17", f"format_escalation_message level 3: {msg[:80]}")
except Exception as e: fail("test_17", str(e))

try:
    msg = format_sms_message(
        "temperature", 42.0, 38.0, "high", "CRITICAL", "\u00b0C", 2
    )
    assert len(msg) <= 160, f"SMS too long: {len(msg)} chars"
    assert "SENTINEL" in msg and "42.0" in msg
    ok("test_18", "format_sms_message is under 160 chars (" + str(len(msg)) + " chars)")
except Exception as e: fail("test_18", str(e))

try:
    subj = format_email_subject("temperature", "high", "CRITICAL", 2)
    assert "[CRITICAL]" in subj and "Level 2" in subj
    ok("test_19", f"format_email_subject: {subj}")
except Exception as e: fail("test_19", str(e))

try:
    report = format_daily_report({
        "date": "2026-06-02", "generated_at": now_iso(),
        "total_readings": 86400, "valid_readings": 86300, "invalid_readings": 100,
        "total_alerts": 5, "alerts_by_parameter": {"temperature_high": 3, "humidity_high": 2},
        "avg_temperature": 27.5, "avg_humidity": 60.0,
        "peak_temperature": 39.2, "peak_temperature_time": "14:30",
        "peak_humidity": 85.0, "peak_humidity_time": "10:15",
        "escalations_count": 2,
        "email_sent": 4, "email_failed": 1,
        "sms_sent": 3, "sms_failed": 0,
    })
    assert "SentinelEdge" in report and "86400" in report
    ok("test_20", f"format_daily_report produces valid report ({len(report)} chars)")
except Exception as e: fail("test_20", str(e))

print(f"\n{passed}/{passed+failed} tests passed")
if failed == 0: print("utils module -- ALL TESTS PASSED. Safe to proceed.")
else: print("utils module -- TESTS FAILED. Fix before proceeding.")
