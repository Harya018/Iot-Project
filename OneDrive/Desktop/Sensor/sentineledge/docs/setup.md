# SentinelEdge Setup Guide

## Alert Modules

SentinelEdge uses exactly **3 alert channels**:

| Module | Transport | Requirement |
|--------|-----------|-------------|
| **In-app** | WebSocket broadcast | None — always active |
| **Email** | smtplib / Gmail SMTP | Gmail App Password |
| **SMS** | Android SMS Gateway (LAN) | Android phone on same Wi-Fi |

## Prerequisites

| Component | Requirement |
|-----------|-------------|
| Python | 3.11 or later |
| Node.js | 18 or later (frontend only) |
| npm | 9 or later (frontend only) |
| Android phone | For SMS (optional) |

## Step 1 — Clone & Configure

```bash
cd sentineledge
cp .env.example .env.development
# Edit .env.development with your values
```

## Step 2 — Backend

```bash
# Windows:
python -m venv venv
venv\Scripts\activate
pip install -r backend\requirements.txt
```

## Step 3 — VAPID Keys (Web Push)

```bash
pip install py-vapid
vapid --gen
# Copy generated keys into .env.development
```

## Step 4 — Gmail App Password

1. Enable 2-Step Verification at myaccount.google.com
2. Go to Security -> App Passwords
3. Generate a password for "Mail"
4. Set `SMTP_PASSWORD=<16-char-password>` in `.env.development`

## Step 5 — Android SMS Gateway

1. Install **android-sms-gateway** from GitHub on an Android device
2. Connect device to the same Wi-Fi as your server
3. Note the IP shown in the app (e.g. `192.168.1.50:8080`)
4. Set `SMS_GATEWAY_URL=http://192.168.1.50:8080` in `.env.development`

## Step 6 — Web Frontend

```bash
cd frontend-web
npm install
npm run build
# Windows:
xcopy /E /I dist ..\backend\static
```

## Step 7 — Start the Server

```batch
# Development:
start.bat

# Production:
start_production.bat
```

Or manually:
```powershell
$env:PYTHONPATH = "backend"
$env:APP_ENV = "development"
.\venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 5000
```

## Step 8 — Mobile App

```bash
cd frontend-mobile
npm install
npx expo start
```

Scan the QR with **Expo Go** on your phone.
In the app: **Settings -> Enter server IP -> Save**.

## Step 9 — Verify

1. Open `http://localhost:5000` — dashboard should load
2. Check `http://localhost:5000/api/health` -> `{"status": "ok", ...}`
3. Click **Simulate Breach** on the dashboard — watch the chart spike and alert log update

## .env Reference

```env
TEMP_THRESHOLD_HIGH=38.0
TEMP_THRESHOLD_LOW=22.0
HUMIDITY_THRESHOLD_HIGH=80.0
HUMIDITY_THRESHOLD_LOW=35.0

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@gmail.com
SMTP_PASSWORD=your_16_char_app_password

SMS_GATEWAY_URL=http://192.168.1.x:8080
SMS_GATEWAY_USER=admin
SMS_GATEWAY_PASS=password

ESCALATION_TIMEOUT_SECONDS=60
ALERT_COOLDOWN_SECONDS=120

VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIM_EMAIL=youremail@gmail.com

SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DEMO_MODE=false

ADMIN_PASSWORD=your_admin_password
```
