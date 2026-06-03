# 09_escalation — Alert Escalation Engine

**What it does:** `trigger_alert()` inserts a breach into the database, notifies Level-1 subscribers immediately, and spawns an `asyncio` background task that escalates through Levels 2 and 3 if the alert remains unacknowledged. Channels: Email (all), SMS (CRITICAL+), In-app push (EMERGENCY). Severity EMERGENCY skips the wait and notifies all levels simultaneously.

**Dependencies:** `01_config`, `02_models`, `04_database`, `modules/email`, `modules/sms`, `modules/inapp`.

**How to test:**
```
cd backend/foundation/09_escalation
python test_escalation.py
```

**Pass condition:**
```
escalation module — ALL TESTS PASSED. Safe to proceed.
```
