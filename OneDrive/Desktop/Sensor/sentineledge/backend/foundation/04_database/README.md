# 04_database — SQLite Persistence Layer

**What it does:** Provides `connection.py` (schema initialisation, WAL-mode connection factory), `schema.sql` (table definitions), and `queries/` (CRUD functions for readings, alerts, subscribers, escalation_log, receipts, config_log).

**Dependencies:** `01_config` (for DB path), stdlib `sqlite3`.

**How to test:**
```
cd backend/foundation/04_database
python test_database.py
```

**Pass condition:**
```
database module — ALL TESTS PASSED. Safe to proceed.
```
