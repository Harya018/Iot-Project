# 02_models — Pydantic Data Models

**What it does:** Defines all Pydantic v2 request/response models used by the API: `BreachEvent`, `ReadingOut`, `AlertOut`, `SubscriberIn/Out`, `ThresholdConfigIn/Out`, `AcknowledgeIn`, `DeliveryReceiptOut`, `ConfigChangeOut`.

**Dependencies:** `pydantic>=2.0`.

**How to test:**
```
cd backend/foundation/02_models
python test_models.py
```

**Pass condition:**
```
models module — ALL TESTS PASSED. Safe to proceed.
```
