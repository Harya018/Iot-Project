# 01_config — Configuration Loader

**What it does:** Loads environment variables from `.env.<APP_ENV>` using pathlib, exposes all system constants as module-level variables, and initialises `RUNTIME_THRESHOLDS` and `MODULE_STATUS` dicts.

**Dependencies:** None (stdlib + python-dotenv only).

**How to test:**
```
cd backend/foundation/01_config
python test_config.py
```

**Pass condition:**
```
10/10 tests passed
config module — ALL TESTS PASSED. Safe to proceed.
```
