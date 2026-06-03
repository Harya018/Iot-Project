"""
backend/foundation/05_thresholds/test_thresholds.py
Production-level tests for core/thresholds.py.
Run: python test_thresholds.py
"""
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_BACKEND))

from core.thresholds import THRESHOLDS, ParameterThreshold, ThresholdConfig, get_all_thresholds

passed = failed = 0


def ok(name, detail=""):
    global passed; passed += 1
    print(f"PASS -- {name}" + (f" -- {detail}" if detail else ""))


def fail(name, reason):
    global failed; failed += 1
    print(f"FAIL -- {name} -- {reason}")


try:
    assert THRESHOLDS.temperature.high == 38.0
    ok("test_01", f"THRESHOLDS.temperature.high == 38.0")
except Exception as e: fail("test_01", str(e))

try:
    assert THRESHOLDS.temperature.low == 22.0
    ok("test_02", f"THRESHOLDS.temperature.low == 22.0")
except Exception as e: fail("test_02", str(e))

try:
    assert THRESHOLDS.humidity.high == 80.0
    ok("test_03", f"THRESHOLDS.humidity.high == 80.0")
except Exception as e: fail("test_03", str(e))

try:
    assert THRESHOLDS.humidity.low == 35.0
    ok("test_04", f"THRESHOLDS.humidity.low == 35.0")
except Exception as e: fail("test_04", str(e))

try:
    # 5% over 38.0 = 39.9 → WARNING
    sev = THRESHOLDS.temperature.get_severity(39.9, "high")
    assert sev == "WARNING", f"expected WARNING got {sev}"
    ok("test_05", f"get_severity 5% over threshold = WARNING (39.9 vs 38.0)")
except Exception as e: fail("test_05", str(e))

try:
    # 12% over 38.0 = 42.56 → CRITICAL
    sev = THRESHOLDS.temperature.get_severity(42.56, "high")
    assert sev == "CRITICAL", f"expected CRITICAL got {sev}"
    ok("test_06", f"get_severity 12% over threshold = CRITICAL (42.56 vs 38.0)")
except Exception as e: fail("test_06", str(e))

try:
    # 30% over 38.0 = 49.4 → EMERGENCY
    sev = THRESHOLDS.temperature.get_severity(49.4, "high")
    assert sev == "EMERGENCY", f"expected EMERGENCY got {sev}"
    ok("test_07", f"get_severity 30% over threshold = EMERGENCY (49.4 vs 38.0)")
except Exception as e: fail("test_07", str(e))

try:
    # 4% below low of 22.0 = 21.12 → WARNING
    sev = THRESHOLDS.temperature.get_severity(21.12, "low")
    assert sev == "WARNING", f"expected WARNING got {sev}"
    ok("test_08", f"get_severity 4% below low = WARNING (21.12 vs 22.0)")
except Exception as e: fail("test_08", str(e))

try:
    # 15% below low of 22.0 = 18.7 → CRITICAL
    sev = THRESHOLDS.temperature.get_severity(18.7, "low")
    assert sev == "CRITICAL", f"expected CRITICAL got {sev}"
    ok("test_09", f"get_severity 15% below low = CRITICAL")
except Exception as e: fail("test_09", str(e))

try:
    result = get_all_thresholds()
    assert "temperature" in result and "humidity" in result
    for param in ("temperature", "humidity"):
        for key in ("high", "low", "unit", "name", "severity_levels"):
            assert key in result[param], f"missing {key} in {param}"
    ok("test_10", "get_all_thresholds returns correct structure")
except Exception as e: fail("test_10", str(e))

try:
    d = THRESHOLDS.temperature.to_dict()
    sev_levels = d["severity_levels"]
    assert "warning" in sev_levels and "critical" in sev_levels and "emergency" in sev_levels
    ok("test_11", "to_dict severity_levels has warning/critical/emergency keys")
except Exception as e: fail("test_11", str(e))

try:
    custom = ParameterThreshold(high=50.0, low=10.0, unit="°C", name="Custom")
    sev = custom.get_severity(52.5, "high")  # 5% over 50 = WARNING
    assert sev == "WARNING"
    ok("test_12", "Custom ParameterThreshold get_severity works")
except Exception as e: fail("test_12", str(e))

print(f"\n{passed}/{passed+failed} tests passed")
if failed == 0: print("thresholds module -- ALL TESTS PASSED. Safe to proceed.")
else: print("thresholds module -- TESTS FAILED. Fix before proceeding.")
