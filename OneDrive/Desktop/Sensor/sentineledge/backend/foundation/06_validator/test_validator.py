"""
backend/foundation/06_validator/test_validator.py
Production-level tests for core/validator.py.
Run: python test_validator.py
"""
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_BACKEND))

from core.validator import validate_reading, ReadingValidator

passed = failed = 0
TS = "2026-06-02T10:00:00+00:00"


def ok(name, detail=""):
    global passed; passed += 1
    print(f"PASS -- {name}" + (f" -- {detail}" if detail else ""))


def fail(name, reason):
    global failed; failed += 1
    print(f"FAIL -- {name} -- {reason}")


try:
    is_valid, reason = validate_reading(
        {"temperature": 25.0, "humidity": 55.0, "timestamp": TS}
    )
    assert is_valid, f"expected valid, got: {reason}"
    ok("test_01", "Valid reading passes validation")
except Exception as e: fail("test_01", str(e))

try:
    is_valid, reason = validate_reading(
        {"temperature": 999.0, "humidity": 55.0, "timestamp": TS}
    )
    assert not is_valid
    assert "temperature" in reason.lower()
    ok("test_02", f"Temperature out of range rejected: {reason}")
except Exception as e: fail("test_02", str(e))

try:
    is_valid, reason = validate_reading(
        {"temperature": -100.0, "humidity": 55.0, "timestamp": TS}
    )
    assert not is_valid
    ok("test_03", f"Temperature below minimum rejected: {reason}")
except Exception as e: fail("test_03", str(e))

try:
    is_valid, reason = validate_reading(
        {"temperature": 25.0, "humidity": 110.0, "timestamp": TS}
    )
    assert not is_valid
    assert "humidity" in reason.lower()
    ok("test_04", f"Humidity out of range rejected: {reason}")
except Exception as e: fail("test_04", str(e))

try:
    is_valid, reason = validate_reading(
        {"humidity": 55.0, "timestamp": TS}
    )
    assert not is_valid
    ok("test_05", f"Missing temperature field rejected: {reason}")
except Exception as e: fail("test_05", str(e))

try:
    is_valid, reason = validate_reading(
        {"temperature": None, "humidity": 55.0, "timestamp": TS}
    )
    assert not is_valid
    ok("test_06", f"Null temperature rejected: {reason}")
except Exception as e: fail("test_06", str(e))

try:
    is_valid, reason = validate_reading(
        {"temperature": 25.0, "humidity": 55.0, "timestamp": "not-a-date"}
    )
    assert not is_valid
    ok("test_07", f"Invalid timestamp rejected: {reason}")
except Exception as e: fail("test_07", str(e))

try:
    # Spike detection: 15°C jump in one reading
    v = ReadingValidator()
    r1 = {"temperature": 25.0, "humidity": 55.0, "timestamp": TS}
    r2 = {"temperature": 40.0, "humidity": 55.0, "timestamp": TS}
    v.validate(r1)
    is_valid, reason = v.validate(r2)
    assert not is_valid and "spike" in reason.lower()
    ok("test_08", f"Temperature spike of 15°C rejected: {reason}")
except Exception as e: fail("test_08", str(e))

try:
    # Humidity spike detection: 30% jump
    v = ReadingValidator()
    r1 = {"temperature": 25.0, "humidity": 50.0, "timestamp": TS}
    r2 = {"temperature": 25.0, "humidity": 85.0, "timestamp": TS}
    v.validate(r1)
    is_valid, reason = v.validate(r2)
    assert not is_valid and "spike" in reason.lower()
    ok("test_09", f"Humidity spike of 35% rejected: {reason}")
except Exception as e: fail("test_09", str(e))

try:
    # Gradual drift should NOT be flagged as spike
    v = ReadingValidator()
    for temp in range(25, 32):
        r = {"temperature": float(temp), "humidity": 55.0, "timestamp": TS}
        is_valid, reason = v.validate(r)
        assert is_valid, f"gradual reading {temp}°C wrongly rejected: {reason}"
    ok("test_10", "Gradual 1°C/s drift is not flagged as spike")
except Exception as e: fail("test_10", str(e))

print(f"\n{passed}/{passed+failed} tests passed")
if failed == 0: print("validator module -- ALL TESTS PASSED. Safe to proceed.")
else: print("validator module -- TESTS FAILED. Fix before proceeding.")
