# SentinelEdge Architecture

## System Overview

```
+-------------------------------------------------------------+
|                       Client Layer                          |
|  Web Dashboard (React/Vite)    Mobile App (React Native)    |
+------------------------+------------------------------------+
                         | WebSocket + REST (LAN HTTP)
+------------------------v------------------------------------+
|                    FastAPI Backend                          |
|  main.py ---> core/ (sensor, threshold, escalation)        |
|          ---> database/ (SQLite via connection.py)         |
|          ---> modules/ (email, sms, inapp)                 |
|          ---> routers/ (alerts, subscribers, config, ...)  |
+-------------+-----------------------------------------------+
              |
   +----------+----------+
   |                     |
Email (smtplib)     SMS (Android
                    SMS Gateway)
```

## Three Alert Modules

| # | Module | Transport | Trigger |
|---|--------|-----------|---------|
| 1 | **In-app** | WebSocket broadcast | Every breach |
| 2 | **Email** | smtplib / Gmail SMTP | WARNING, CRITICAL, EMERGENCY |
| 3 | **SMS** | Android SMS Gateway (local) | CRITICAL, EMERGENCY |

## Severity Levels

| Severity | Condition | Channels fired |
|----------|-----------|----------------|
| WARNING | 0-10% beyond threshold | Email |
| CRITICAL | 10-25% beyond threshold | Email + SMS |
| EMERGENCY | >25% beyond threshold | Email + SMS + In-app push (no delay) |

## Data Flow

```
1 Hz sensor tick (core/sensor.py)
         |
         v
  validate_reading (core/validator.py)
         |
    +----+----+
    |invalid? |
    +----+----+
    YES  |  NO
         |
  threshold check (core/threshold.py)
         |
    +----+----+
    | breach? |
    +----+----+
    YES  |  NO --> broadcast reading --> WebSocket clients
         |
   insert_alert (database/queries/alerts.py)
         |
   notify L1 subscriber (core/escalation.py)
         |
   spawn asyncio task: run_escalation(alert_id)
         |
   +---------------------------------------------------------+
   |  wait ESCALATION_TIMEOUT_SECONDS                        |
   |  check acknowledged? --> stop if yes                    |
   |  notify L2 subscriber                                   |
   |  wait ESCALATION_TIMEOUT_SECONDS                        |
   |  check acknowledged? --> stop if yes                    |
   |  notify L3 subscriber + set_max_escalated               |
   +---------------------------------------------------------+
```

## Package Structure

| Package | Responsibility |
|---------|----------------|
| `core/` | Pure business logic: sensor sim, breach detection, escalation engine, validator, daily report |
| `database/` | SQLite schema, connection factory, domain-specific query functions |
| `modules/` | Notification channels: email, SMS, in-app push |
| `routers/` | FastAPI route handlers, one file per API resource |
| `middleware/` | CORS, request logging, admin auth |
| `utils/` | Shared helpers: logging config, time, formatting |

## Key Design Decisions

- **Async-first**: All IO uses `asyncio`; blocking calls (SMTP, SMS) run in a thread-pool executor.
- **Non-blocking escalation**: `trigger_alert()` spawns `asyncio.create_task`, keeping the 1 Hz sensor stream uninterrupted.
- **DB polling**: Escalation tasks re-query the DB at each timeout boundary — server restarts are safe.
- **Decoupled channels**: SMS and email fire via `asyncio.gather(return_exceptions=True)` — one failure never blocks the other.
- **Zero cloud**: All services run on LAN; SMS goes through a local Android phone running the SMS Gateway app.
- **Sensor validation**: Every reading is checked for range validity and spike detection before threshold comparison.
