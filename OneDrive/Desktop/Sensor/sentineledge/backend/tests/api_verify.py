"""Part 5 — API endpoint verification against live server."""
import requests
import warnings
import time
from datetime import date

warnings.filterwarnings("ignore")

h    = {"X-Admin-Password": "admin123"}
base = "https://localhost:5000"
errors = []

def check(name, condition, msg=""):
    if condition:
        print(f"  PASS -- {name}")
    else:
        print(f"  FAIL -- {name}" + (f": {msg}" if msg else ""))
        errors.append(name)

print("API ENDPOINT TESTS")
print("==================")

# Health
r = requests.get(f"{base}/api/health", verify=False)
check("Health returns 200", r.status_code == 200)
check("Health has version", "version" in r.json())
check("Health version is 1.0.0", r.json().get("version") == "1.0.0")

# Readings
r = requests.get(f"{base}/api/readings/recent", verify=False)
check("Readings returns 200", r.status_code == 200)
check("Readings is array", isinstance(r.json(), list))
check("Readings has data", len(r.json()) > 0)
check("Reading has temperature", "temperature" in (r.json()[0] if r.json() else {}))

# Thresholds
r = requests.get(f"{base}/api/config/thresholds", verify=False)
check("Thresholds returns 200", r.status_code == 200)
thr = r.json()
check("High threshold is 90.0", thr.get("temperature", {}).get("high") == 90.0)
check("Low threshold is 38.0",  thr.get("temperature", {}).get("low")  == 38.0)

# Subscribers
r = requests.get(f"{base}/api/subscribers", headers=h, verify=False)
check("Subscribers returns 200", r.status_code == 200)
subs  = r.json()
names = [s["name"] for s in subs]
check("Has subscribers", len(subs) >= 1)
print(f"  INFO -- Subscribers: {names}")
check("Harya exists", "Harya" in names)

# Alerts
r = requests.get(f"{base}/api/alerts", verify=False)
check("Alerts returns 200", r.status_code == 200)

# Simulate breach
r = requests.post(f"{base}/api/simulate/breach", headers=h, verify=False)
check("Simulate breach 200", r.status_code == 200)

print("  INFO -- Waiting 4 seconds for breach to process...")
time.sleep(4)

r = requests.get(f"{base}/api/alerts", verify=False)
alerts = r.json()
check("Alert created after breach", len(alerts) > 0)

# Events
r = requests.get(f"{base}/api/events", headers=h, verify=False)
check("Events returns 200", r.status_code == 200)

# Receipts
r = requests.get(f"{base}/api/receipts", headers=h, verify=False)
check("Receipts returns 200", r.status_code == 200)

# Reports
r = requests.get(f"{base}/api/reports/daily", headers=h, verify=False)
check("Reports returns 200", r.status_code == 200)

# History stats
today = date.today().isoformat()
r = requests.get(f"{base}/api/history/stats?date={today}", headers=h, verify=False)
check("History stats 200", r.status_code == 200)

# Demo endpoint
r = requests.post(f"{base}/api/simulate/demo", json={"speed": 30}, headers=h, verify=False)
check("Demo endpoint 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()
    print(f"  INFO -- Demo: {d.get('total_readings')} readings @ {d.get('speed')}x, ~{d.get('estimated_duration_minutes')} min")

# Reset
r = requests.post(f"{base}/api/simulate/reset", headers=h, verify=False)
check("Reset endpoint 200", r.status_code == 200)

# Auth rejects empty PIN
r = requests.post(f"{base}/api/auth/login", json={"name": "Harya", "pin": ""}, verify=False)
check("Auth rejects empty PIN", r.status_code == 422)

# Admin verify-password
r = requests.post(f"{base}/api/admin/verify-password", json={"password": "admin123"}, verify=False)
check("Admin verify-password 200", r.status_code == 200)

# Require-admin blocks wrong password
r = requests.post(f"{base}/api/simulate/breach", headers={"X-Admin-Password": "wrong"}, verify=False)
check("Admin blocks wrong password", r.status_code == 401)

print()
print(f"Results: {len(errors)} failure(s)")
if errors:
    print("FAILED:", errors)
else:
    print("ALL API TESTS PASSED")
