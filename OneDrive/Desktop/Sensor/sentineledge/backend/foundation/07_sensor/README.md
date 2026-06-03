# 07_sensor — Simulated Sensor Stream

**What it does:** Simulates a hardware temperature/humidity sensor. Normal mode drifts randomly; demo mode ramps deterministically from 22°C to 42°C and back; `set_breach_override()` forces a breach for testing.

**Dependencies:** `01_config` (for DEMO_MODE flag).

**How to test:**
```
cd backend/foundation/07_sensor
python test_sensor.py
```

**Pass condition:**
```
sensor module — ALL TESTS PASSED. Safe to proceed.
```
