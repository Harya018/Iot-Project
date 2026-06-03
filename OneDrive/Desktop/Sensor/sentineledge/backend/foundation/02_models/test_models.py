"""
backend/foundation/02_models/test_models.py
Standalone tests for models.py.
Run: python test_models.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from models import (
    BreachEvent, ReadingOut, AlertOut, SubscriberIn, SubscriberOut,
    ThresholdConfigIn, ThresholdConfigOut, AcknowledgeIn,
)

passed = failed = 0

def ok(name, detail=""): 
    global passed; passed += 1
    print(f"PASS -- {name}" + (f" -- {detail}" if detail else ""))

def fail(name, reason):
    global failed; failed += 1
    print(f"FAIL -- {name} -- {reason}")

try:
    b = BreachEvent(parameter="temperature", value=40.0, threshold=38.0, direction="high")
    assert b.severity == "WARNING"
    ok("test_1", "BreachEvent default severity is WARNING")
except Exception as e: fail("test_1", str(e))

try:
    b = BreachEvent(parameter="humidity", value=90.0, threshold=80.0, direction="high", severity="CRITICAL")
    assert b.severity == "CRITICAL"
    ok("test_2", "BreachEvent accepts explicit severity")
except Exception as e: fail("test_2", str(e))

try:
    r = ReadingOut(temperature=25.0, humidity=55.0, timestamp="2026-01-01T00:00:00+00:00")
    assert r.is_valid is True
    assert r.breaches == []
    ok("test_3", "ReadingOut defaults correct")
except Exception as e: fail("test_3", str(e))

try:
    a = AlertOut(
        id=1, parameter="temperature", value=40.0, threshold=38.0,
        direction="high", timestamp="2026-01-01T00:00:00+00:00",
        acknowledged=False, escalation_level=1, max_escalated=False,
    )
    assert a.severity == "WARNING"
    assert a.delivery_status is None
    ok("test_4", "AlertOut defaults correct")
except Exception as e: fail("test_4", str(e))

try:
    s = SubscriberIn(name="Alice", phone="+1555", email="alice@x.com", escalation_order=1)
    assert s.escalation_order == 1
    ok("test_5", "SubscriberIn parses correctly")
except Exception as e: fail("test_5", str(e))

try:
    cfg = ThresholdConfigIn(temp_high=38.0, temp_low=22.0, humidity_high=80.0, humidity_low=35.0)
    out = ThresholdConfigOut(**cfg.model_dump())
    assert out.temp_high == 38.0
    ok("test_6", "ThresholdConfigIn/Out round-trip")
except Exception as e: fail("test_6", str(e))

try:
    ack = AcknowledgeIn(acknowledged_by="Bob")
    assert ack.acknowledged_by == "Bob"
    ok("test_7", "AcknowledgeIn parses correctly")
except Exception as e: fail("test_7", str(e))

print(f"\n{passed}/{passed+failed} tests passed")
if failed == 0: print("models module -- ALL TESTS PASSED. Safe to proceed.")
else: print("models module -- TESTS FAILED. Fix before proceeding.")
