# 06_validator — Sensor Reading Validator

**What it does:** `ReadingValidator` checks every incoming sensor reading for required fields, null values, physical range violations (temp: -50..150, humidity: 0..100), invalid timestamps, and per-second spikes. Invalid readings are flagged and excluded from threshold processing.

**Dependencies:** None (standalone, stdlib only).

**How to test:**
```
cd backend/foundation/06_validator
python test_validator.py
```

**Pass condition:**
```
validator module — ALL TESTS PASSED. Safe to proceed.
```
