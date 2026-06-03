# 08_threshold_engine — Threshold Breach Detection

**What it does:** `check_threshold()` compares a sensor reading against `RUNTIME_THRESHOLDS`, applies per-direction cooldown windows, computes severity (WARNING/CRITICAL/EMERGENCY), and returns `BreachEvent` objects for every active breach.

**Dependencies:** `01_config`, `02_models`, `05_thresholds`.

**How to test:**
```
cd backend/foundation/08_threshold_engine
python test_threshold_engine.py
```

**Pass condition:**
```
threshold engine module — ALL TESTS PASSED. Safe to proceed.
```
