# SentinelEdge

**Production-ready local IoT threshold alert and escalation system.**

Zero cloud. Zero cost. Runs entirely on your LAN.

---

## What It Does

SentinelEdge monitors temperature and humidity every second and:

1. **Streams** live data to connected dashboards via WebSocket
2. **Alerts** when a threshold is breached:
   - 🔔 In-app visual + audio alarm on the web dashboard
   - 📱 Push notification to all registered phones (via pywebpush)
   - 📧 Email to all registered subscribers (via Gmail SMTP)
   - 📟 SMS via your Android phone acting as a GSM gateway
3. **Escalates** if unacknowledged:
   - Level 1 → Level 2 after 60 s → Level 3 after another 60 s
   - Stops the moment anyone acknowledges
4. **Logs** every alert, escalation, and acknowledgement to SQLite

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| Backend | Python 3.11+ |
| Web frontend | Node.js 18+ |
| Mobile | Expo Go app on Android or iOS |
| SMS | Android phone with [android-sms-gateway](https://github.com/capcom6/android-sms-gateway) |
| Email | Gmail account with App Password enabled |

---

## Quick Start

### 1. Clone and configure

```bash
# Copy the template and fill in your values
cp .env.example .env
nano .env
```

**Minimum required values:**
```
SMTP_USER=youremail@gmail.com
SMTP_PASSWORD=your_16_char_app_password
SMS_GATEWAY_URL=http://192.168.1.x:8080   # IP of Android phone
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_CLAIM_EMAIL=youremail@gmail.com
```

### 2. Generate VAPID keys (Web Push)

```bash
python3 -c "
from py_vapid import Vapid
v = Vapid()
v.generate_keys()
import base64, json
print('VAPID_PUBLIC_KEY=' + v.public_key.public_bytes_raw().hex())
print('VAPID_PRIVATE_KEY=' + v.private_key.private_bytes_raw().hex())
"
```

Or use the pywebpush CLI: `vapid --gen`

### 3. Backend setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 4. Web frontend

```bash
cd frontend-web
npm install
npm run build
cd ..

# Copy build output for FastAPI to serve
cp -r frontend-web/dist backend/static
```

### 5. Start the server

```bash
# Linux/macOS:
chmod +x start.sh stop.sh
./start.sh

# Windows (PowerShell):
$env:PYTHONPATH = "backend"
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 6. Open the web dashboard

```
http://YOUR_LAPTOP_IP:8000
```

### 7. Mobile app

```bash
cd frontend-mobile
npm install
npx expo start
```

Scan the QR code with **Expo Go** (available on App Store and Google Play).

In the app: **Settings → Enter your laptop's IP address → Save**

---

## Android SMS Gateway Setup

1. Install the [android-sms-gateway](https://github.com/capcom6/android-sms-gateway) app on an Android phone
2. Keep that phone on the same Wi-Fi network as your server
3. Note the IP address and port shown in the app (usually `http://192.168.x.x:8080`)
4. Set `SMS_GATEWAY_URL=http://192.168.x.x:8080` in your `.env`
5. The app will use that phone's cellular connection to send real SMS messages

---

## Gmail App Password

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to **App Passwords** → Generate one for "Mail"
4. Paste the 16-character password as `SMTP_PASSWORD` in `.env`

---

## Folder Structure

```
sentineledge/
├── backend/         Python FastAPI server + SQLite
├── frontend-web/    React admin dashboard (Vite + Tailwind)
├── frontend-mobile/ React Native Expo mobile app
├── database/        SQLite database (auto-created)
├── logs/            Server logs
├── .env             Your configuration (never commit this)
├── .env.example     Template for .env
├── start.sh         One-command startup (Linux/macOS)
└── stop.sh          Graceful shutdown
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws` | Live sensor stream |
| GET | `/api/readings/recent` | Last 60 readings |
| GET | `/api/alerts` | Last 50 alerts |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge alert |
| GET | `/api/subscribers` | All subscribers |
| POST | `/api/subscribers` | Add subscriber |
| DELETE | `/api/subscribers/{id}` | Remove subscriber |
| POST | `/api/subscribers/{id}/push` | Register push subscription |
| GET | `/api/config/thresholds` | Current thresholds |
| POST | `/api/config/thresholds` | Update thresholds (live, no restart) |
| GET | `/api/config/vapid-public-key` | VAPID public key |
| POST | `/api/simulate/breach` | Force a threshold breach (demo) |
| GET | `/api/health` | Health check |

---

## Architecture

```
Android/iOS App ──WebSocket──┐
Web Browser ──WebSocket──────┤
                             ▼
                    FastAPI + SQLite
                    sensor.py (1 Hz drift)
                    threshold.py (breach check)
                    escalation.py (L1→L2→L3)
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Email        SMS       Push
         (smtplib)  (Android    (pywebpush
                     Gateway)    VAPID)
```

All communication stays on your LAN. No data ever leaves your network.

---

## Security Notes

- `.env` is never committed (add to `.gitignore`)
- The SQLite database stores all sensor readings and alert history
- VAPID keys authenticate push notifications end-to-end
- The web dashboard has no authentication by default — secure your LAN

---

## License

MIT — Use freely, modify freely, zero warranty.
