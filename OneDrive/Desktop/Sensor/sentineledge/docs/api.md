# SentinelEdge API Reference

Base URL: `http://<server-ip>:5000`

## Three Alert Modules

| Module | Transport | When |
|--------|-----------|------|
| In-app | WebSocket broadcast | Every breach, every severity |
| Email | SMTP (Gmail) | WARNING, CRITICAL, EMERGENCY |
| SMS | Android SMS Gateway (LAN) | CRITICAL, EMERGENCY |

## WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://<ip>:5000/ws` | Live sensor stream — 1 message per second |

### Message format (server -> client)
```json
{
  "temperature": 24.2,
  "humidity": 54.5,
  "timestamp": "2026-06-01T10:00:00+00:00",
  "is_valid": true,
  "breaches": [
    {
      "parameter": "temperature",
      "value": 39.5,
      "threshold": 38.0,
      "direction": "high",
      "severity": "WARNING"
    }
  ]
}
```

When `is_valid` is `false`, `breaches` is empty and a `validation_error` field is included. The frontend shows a `SENSOR ERROR` banner.

## REST Endpoints

### Readings

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/readings/recent` | None | Last 60 readings (oldest first) |

### Alerts

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/alerts` | None | Last 50 alerts with delivery_status |
| POST | `/api/alerts/{id}/acknowledge` | None | Acknowledge an alert |

**POST body:**
```json
{ "acknowledged_by": "Alice" }
```

**Alert object (GET /api/alerts):**
```json
{
  "id": 42,
  "parameter": "temperature",
  "value": 40.2,
  "threshold": 38.0,
  "direction": "high",
  "severity": "CRITICAL",
  "timestamp": "...",
  "acknowledged": false,
  "escalation_level": 1,
  "max_escalated": false,
  "delivery_status": {
    "email": "delivered",
    "sms": "failed"
  }
}
```

### Subscribers

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/subscribers` | None | All active subscribers |
| POST | `/api/subscribers` | Admin | Add a subscriber |
| DELETE | `/api/subscribers/{id}` | Admin | Remove a subscriber |
| POST | `/api/subscribers/{id}/push` | Admin | Save Web Push subscription |

**POST /api/subscribers body:**
```json
{
  "name": "Alice",
  "phone": "+15551234567",
  "email": "alice@example.com",
  "escalation_order": 1
}
```

### Configuration

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/config/thresholds` | None | Current thresholds with source info |
| POST | `/api/config/thresholds` | Admin | Update thresholds (live, no restart) |
| POST | `/api/config/thresholds/reset` | Admin | Reset to .env defaults |
| GET | `/api/config/vapid-public-key` | None | VAPID public key for Web Push |

### Admin

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/admin/config-changes` | Admin | Last 50 config audit entries |

Admin endpoints require header: `X-Admin-Password: <ADMIN_PASSWORD>`

### Simulation & Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/simulate/breach` | Admin | Force a temperature breach for 10 ticks |
| GET | `/api/health` | None | Full system health check |

**GET /api/health response:**
```json
{
  "status": "ok",
  "environment": "development",
  "uptime": "2h 34m",
  "timestamp": "...",
  "modules": {
    "sensor": "ok",
    "database": "ok",
    "email": "not_built",
    "sms": "not_built",
    "websocket": "ok -- 2 client(s) connected"
  },
  "connected_clients": 2,
  "alerts_today": 12,
  "last_reading": {
    "temperature": 32.4,
    "humidity": 61.2,
    "timestamp": "..."
  },
  "delivery_stats_today": {
    "email": {"sent": 10, "failed": 2},
    "sms":   {"sent": 8,  "failed": 4}
  }
}
```
