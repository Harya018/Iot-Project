"""
backend/foundation/08_threshold_engine/test_threshold_engine.py
Production-level tests for core/threshold.py.
Run: python test_threshold_engine.py
"""
import sys, types, time
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_BACKEND))

# Stub config with test thresholds and fast cooldown
_fake_config = types.ModuleType("config")
_fake_config.RUNTIME_THRESHOLDS = {
    "temp_high":      38.0,
    "temp_low":       22.0,
    "humidity_high":  80.0,
    "humidity_low":   35.0,
}
_fake_config.ALERT_COOLDOWN_SECONDS = 2   # fast cooldown for testing
_fake_config.MODULE_STATUS = {"sensor": "starting"}
sys.modules["config"] = _fake_config

# Stub models with our real models
sys.modules.pop("models", None)
import models as _local_models
sys.modules["models"] = _local_models

import core.threshold as threshold

passed = failed = 0


def ok(name, detail=""):
    global passed; passed += 1
    print(f"PASS -- {name}" + (f" -- {detail}" if detail else ""))


def fail(name, reason):
    global failed; failed += 1
    print(f"FAIL -- {name} -- {reason}")


def reset_cooldowns():
    for k in threshold.cooldown_tracker:
        threshold.cooldown_tracker[k] = None


try:
    reset_cooldowns()
    breaches = threshold.check_threshold({"temperature": 25.0, "humidity": 55.0})
    assert breaches == [], f"expected no breach, got {breaches}"
    ok("test_01", "Normal reading produces no breach")
except Exception as e: fail("test_01", str(e))

try:
    reset_cooldowns()
    breaches = threshold.check_threshold({"temperature": 39.0, "humidity": 55.0})
    assert len(breaches) == 1
    assert breaches[0].parameter == "temperature"
    assert breaches[0].direction == "high"
    ok("test_02", f"Temperature high breach detected, severity={breaches[0].severity}")
except Exception as e: fail("test_02", str(e))

try:
    reset_cooldowns()
    breaches = threshold.check_threshold({"temperature": 20.0, "humidity": 55.0})
    assert any(b.direction == "low" for b in breaches)
    ok("test_03", "Temperature low breach detected")
except Exception as e: fail("test_03", str(e))

try:
    reset_cooldowns()
    breaches = threshold.check_threshold({"temperature": 39.0, "humidity": 85.0})
    assert len(breaches) == 2
    params = {b.parameter for b in breaches}
    assert "temperature" in params and "humidity" in params
    ok("test_04", "Two simultaneous breaches detected (temp high + humidity high)")
except Exception as e: fail("test_04", str(e))

try:
    reset_cooldowns()
    threshold.check_threshold({"temperature": 39.0, "humidity": 55.0})
    # Immediate second call — should be suppressed by cooldown
    breaches2 = threshold.check_threshold({"temperature": 39.0, "humidity": 55.0})
    assert breaches2 == [], f"expected cooldown to suppress, got {breaches2}"
    ok("test_05", "Cooldown suppresses duplicate breach within window")
except Exception as e: fail("test_05", str(e))

try:
    reset_cooldowns()
    # temperature_high and temperature_low have independent cooldowns
    threshold.check_threshold({"temperature": 39.0, "humidity": 55.0})  # trip temp_high
    breaches = threshold.check_threshold({"temperature": 20.0, "humidity": 55.0})  # trip temp_low
    assert any(b.direction == "low" for b in breaches), "temp_low should not be in cooldown"
    ok("test_06", "temperature_high and temperature_low tracked independently")
except Exception as e: fail("test_06", str(e))

try:
    reset_cooldowns()
    # >25% over 38.0 = > 47.5 → EMERGENCY
    breaches = threshold.check_threshold({"temperature": 50.0, "humidity": 55.0})
    assert breaches and breaches[0].severity == "EMERGENCY"
    ok("test_07", f"50°C (>25% over 38°C) triggers EMERGENCY")
except Exception as e: fail("test_07", str(e))

try:
    reset_cooldowns()
    # 10-25% over 38.0 = 41.8-47.5 → CRITICAL
    breaches = threshold.check_threshold({"temperature": 43.0, "humidity": 55.0})
    assert breaches and breaches[0].severity == "CRITICAL"
    ok("test_08", f"43°C (~13% over 38°C) triggers CRITICAL")
except Exception as e: fail("test_08", str(e))

try:
    reset_cooldowns()
    # Cooldown expires — breach should fire again after 2s (fast cooldown for tests)
    threshold.check_threshold({"temperature": 39.0, "humidity": 55.0})
    time.sleep(2.1)
    breaches = threshold.check_threshold({"temperature": 39.0, "humidity": 55.0})
    assert len(breaches) == 1, f"expected breach after cooldown, got {breaches}"
    ok("test_09", "Breach fires again after cooldown expires")
except Exception as e: fail("test_09", str(e))

print(f"\n{passed}/{passed+failed} tests passed")
if failed == 0: print("threshold engine module -- ALL TESTS PASSED. Safe to proceed.")
else: print("threshold engine module -- TESTS FAILED. Fix before proceeding.")
