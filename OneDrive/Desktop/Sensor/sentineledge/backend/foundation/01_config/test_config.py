"""
backend/foundation/01_config/test_config.py
Production-level tests for 01_config/config.py.
Run: python test_config.py
"""
import sys, os
from pathlib import Path

# Add this folder to path for standalone run
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
# Also add backend so utils can load
_BACKEND = _HERE.parent.parent
sys.path.insert(0, str(_BACKEND))
os.environ.setdefault("APP_ENV", "development")

import config

passed = failed = 0


def ok(name, detail=""):
    global passed; passed += 1
    print(f"PASS -- {name}" + (f" -- {detail}" if detail else ""))


def fail(name, reason):
    global failed; failed += 1
    print(f"FAIL -- {name} -- {reason}")


# ── APP_ENV ───────────────────────────────────────────────────────────────────
try:
    assert hasattr(config, "APP_ENV")
    assert config.APP_ENV in ("development", "production", "test")
    ok("test_01", f"APP_ENV = {config.APP_ENV!r}")
except Exception as e: fail("test_01", str(e))

# ── Threshold values ──────────────────────────────────────────────────────────
try:
    assert hasattr(config, "TEMP_THRESHOLD_HIGH")
    assert isinstance(config.TEMP_THRESHOLD_HIGH, float)
    assert config.TEMP_THRESHOLD_HIGH > 0
    ok("test_02", f"TEMP_THRESHOLD_HIGH = {config.TEMP_THRESHOLD_HIGH}")
except Exception as e: fail("test_02", str(e))

try:
    assert hasattr(config, "TEMP_THRESHOLD_LOW")
    assert isinstance(config.TEMP_THRESHOLD_LOW, float)
    assert config.TEMP_THRESHOLD_HIGH > config.TEMP_THRESHOLD_LOW
    ok("test_03", f"TEMP_THRESHOLD_LOW = {config.TEMP_THRESHOLD_LOW} (below HIGH)")
except Exception as e: fail("test_03", str(e))

try:
    assert hasattr(config, "HUMIDITY_THRESHOLD_HIGH")
    assert isinstance(config.HUMIDITY_THRESHOLD_HIGH, float)
    assert 0 < config.HUMIDITY_THRESHOLD_HIGH <= 100
    ok("test_04", f"HUMIDITY_THRESHOLD_HIGH = {config.HUMIDITY_THRESHOLD_HIGH}")
except Exception as e: fail("test_04", str(e))

try:
    assert hasattr(config, "HUMIDITY_THRESHOLD_LOW")
    assert isinstance(config.HUMIDITY_THRESHOLD_LOW, float)
    assert config.HUMIDITY_THRESHOLD_HIGH > config.HUMIDITY_THRESHOLD_LOW
    ok("test_05", f"HUMIDITY_THRESHOLD_LOW = {config.HUMIDITY_THRESHOLD_LOW}")
except Exception as e: fail("test_05", str(e))

# ── RUNTIME_THRESHOLDS structure ──────────────────────────────────────────────
try:
    rt = config.RUNTIME_THRESHOLDS
    assert isinstance(rt, dict)
    for key in ("temp_high", "temp_low", "humidity_high", "humidity_low"):
        assert key in rt, f"missing key: {key}"
        assert isinstance(rt[key], float), f"{key} must be float"
    ok("test_06", f"RUNTIME_THRESHOLDS has all 4 float keys: {list(rt.keys())}")
except Exception as e: fail("test_06", str(e))

# ── MODULE_STATUS ─────────────────────────────────────────────────────────────
try:
    ms = config.MODULE_STATUS
    assert isinstance(ms, dict)
    expected = {"sensor", "database", "email", "sms", "websocket"}
    missing = expected - set(ms.keys())
    assert not missing, f"missing keys: {missing}"
    ok("test_07", f"MODULE_STATUS has keys: {list(ms.keys())}")
except Exception as e: fail("test_07", str(e))

# ── SERVER_PORT ───────────────────────────────────────────────────────────────
try:
    assert hasattr(config, "SERVER_PORT")
    assert isinstance(config.SERVER_PORT, int)
    assert 1024 <= config.SERVER_PORT <= 65535
    ok("test_08", f"SERVER_PORT = {config.SERVER_PORT} (valid range)")
except Exception as e: fail("test_08", str(e))

# ── SERVER_START_TIME ─────────────────────────────────────────────────────────
try:
    import datetime
    assert hasattr(config, "SERVER_START_TIME")
    assert isinstance(config.SERVER_START_TIME, datetime.datetime)
    ok("test_09", f"SERVER_START_TIME is datetime")
except Exception as e: fail("test_09", str(e))

# ── CONNECTED_CLIENTS ─────────────────────────────────────────────────────────
try:
    assert hasattr(config, "CONNECTED_CLIENTS")
    assert isinstance(config.CONNECTED_CLIENTS, int)
    assert config.CONNECTED_CLIENTS >= 0
    ok("test_10", f"CONNECTED_CLIENTS = {config.CONNECTED_CLIENTS}")
except Exception as e: fail("test_10", str(e))

print(f"\n{passed}/{passed+failed} tests passed")
if failed == 0: print("config module -- ALL TESTS PASSED. Safe to proceed.")
else: print("config module -- TESTS FAILED. Fix before proceeding.")
