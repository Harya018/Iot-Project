# 05_thresholds — Threshold Defaults & Severity

**What it does:** Defines `DEFAULT_THRESHOLDS` (read-only snapshot of factory values) and `get_severity()` (computes WARNING/CRITICAL/EMERGENCY from how far a value exceeds a threshold). No I/O or external dependencies.

**Dependencies:** None (standalone).

**How to test:**
```
cd backend/foundation/05_thresholds
python test_thresholds.py
```

**Pass condition:**
```
thresholds module — ALL TESTS PASSED. Safe to proceed.
```
