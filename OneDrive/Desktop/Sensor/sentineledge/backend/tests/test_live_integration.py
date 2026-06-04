"""
backend/tests/test_live_integration.py
SentinelEdge Live Integration Test Suite -- 15 tests.

Assumes the server is ALREADY running on https://localhost:5000
with a self-signed TLS certificate (ssl/cert.pem + ssl/key.pem).

Start with:
    $env:PYTHONPATH="$PWD;$PWD\backend"
    uvicorn backend.main:app --host 0.0.0.0 --port 5000 \
        --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem

Run with:
    python backend/tests/test_live_integration.py

Dependencies:
    pip install requests websockets
"""

from __future__ import annotations

import asyncio
import json
import queue as _queue
import ssl
import sys
import threading
import time
import warnings

# Force UTF-8 stdout so any extended chars print cleanly on Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
import websockets

# Suppress SSL warnings for self-signed certificate
try:
    from urllib3.exceptions import InsecureRequestWarning
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
except ImportError:
    pass

# SSL context for WebSocket connections -- accepts self-signed certificates
WS_SSL_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
WS_SSL_CONTEXT.check_hostname = False
WS_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL  = "https://localhost:5000"
WS_URL    = "wss://localhost:5000/ws"
ADMIN_HDR = {"X-Admin-Password": "admin123"}
REQ_OPTS  = {"timeout": 10, "verify": False}   # verify=False for self-signed cert

# ── Result store ──────────────────────────────────────────────────────────────
_results: list[tuple[int, bool, str]] = []


def _pass(num: int, label: str) -> None:
    _results.append((num, True, label))
    print(f"  PASS -- TEST {num:02d}: {label}")


def _fail(num: int, label: str, reason: str) -> None:
    _results.append((num, False, label))
    print(f"  FAIL -- TEST {num:02d}: {label}")
    print(f"           |- {reason}")


# ── Shared state ──────────────────────────────────────────────────────────────
_alert_id: int | None = None
_ws_msg_queue: _queue.Queue = _queue.Queue()
_keepalive_connected = threading.Event()


# -----------------------------------------------------------------------------
# Background WSS keepalive
# Holds a persistent WSS connection open so sensor readings are stored and
# threshold checks fire continuously throughout the test run.
# Every received message is enqueued into _ws_msg_queue for test 13.
# -----------------------------------------------------------------------------
def _start_ws_keepalive() -> None:
    """Start a daemon thread that holds a WSS connection open."""

    def _run() -> None:
        async def _loop() -> None:
            while True:
                try:
                    async with websockets.connect(
                        WS_URL, ssl=WS_SSL_CONTEXT, open_timeout=10
                    ) as ws:
                        _keepalive_connected.set()
                        while True:
                            try:
                                raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
                                try:
                                    _ws_msg_queue.put_nowait(json.loads(raw))
                                except Exception:
                                    pass
                            except asyncio.TimeoutError:
                                continue
                            except Exception:
                                break
                except Exception:
                    _keepalive_connected.clear()
                    await asyncio.sleep(2)   # reconnect after any error

        asyncio.run(_loop())

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    connected = _keepalive_connected.wait(timeout=12)
    if connected:
        time.sleep(3)   # let a few readings accumulate before tests start
    else:
        print("  WARN -- keepalive did not connect within 12s; some tests may fail")


# -----------------------------------------------------------------------------
# TEST 01 -- Server alive
# -----------------------------------------------------------------------------
def test_01_server_alive() -> None:
    try:
        r = requests.get(f"{BASE_URL}/api/health", **REQ_OPTS)
        d = r.json()
        assert r.status_code == 200,                               f"HTTP {r.status_code}"
        assert d.get("status") in ("ok", "degraded"),              f"status={d.get('status')!r}"
        assert d.get("version") == "1.0.0",                        f"version={d.get('version')!r}"
        assert d.get("modules", {}).get("database") == "ok",       f"database={d.get('modules',{}).get('database')!r}"
        assert d.get("environment") == "development",              f"environment={d.get('environment')!r}"
        _pass(1, f"Server alive v{d['version']}")
    except Exception as exc:
        _fail(1, "Server alive", str(exc))


# -----------------------------------------------------------------------------
# TEST 02 -- Sensor streaming via WSS
# -----------------------------------------------------------------------------
def test_02_sensor_streaming() -> None:
    readings: list[dict] = []

    async def _collect() -> None:
        async with websockets.connect(
            WS_URL, ssl=WS_SSL_CONTEXT, open_timeout=10
        ) as ws:
            deadline = time.monotonic() + 10.0
            while len(readings) < 5 and time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    msg = json.loads(raw)
                    if "temperature" in msg and "timestamp" in msg:
                        readings.append(msg)
                except asyncio.TimeoutError:
                    break

    try:
        asyncio.run(_collect())
        assert len(readings) >= 5, f"only {len(readings)} readings received within 10s"
        for rd in readings:
            t = rd["temperature"]
            assert 20.0 <= t <= 100.0, f"temperature {t} out of 20-100 range"
        _pass(2, f"Sensor streaming ({len(readings)} readings, last={readings[-1]['temperature']}C)")
    except Exception as exc:
        _fail(2, "Sensor streaming (5 readings)", str(exc))


# -----------------------------------------------------------------------------
# TEST 03 -- Thresholds correct (90.0 / 38.0 from .env.development)
# -----------------------------------------------------------------------------
def test_03_thresholds_correct() -> None:
    try:
        r = requests.get(f"{BASE_URL}/api/config/thresholds", **REQ_OPTS)
        d = r.json()
        assert r.status_code == 200,             f"HTTP {r.status_code}"
        temp = d.get("temperature", {})
        assert temp.get("high") == 90.0,         f"temp.high={temp.get('high')} (expected 90.0)"
        assert temp.get("low")  == 38.0,         f"temp.low={temp.get('low')} (expected 38.0)"
        assert d.get("source")  == "default",    f"source={d.get('source')!r}"
        _pass(3, "Thresholds correct (90.0/38.0)")
    except Exception as exc:
        _fail(3, "Thresholds correct (90.0/38.0)", str(exc))


# -----------------------------------------------------------------------------
# TEST 04 -- Subscribers exist
# -----------------------------------------------------------------------------
def test_04_subscribers_exist() -> None:
    try:
        r = requests.get(f"{BASE_URL}/api/subscribers", **REQ_OPTS)
        subs = r.json()
        assert r.status_code == 200,   f"HTTP {r.status_code}"
        assert isinstance(subs, list), "response is not a list"
        assert len(subs) >= 1,         f"no subscribers registered -- need at least 1"
        orders = {s.get("escalation_order") for s in subs}
        assert 1 in orders,            "no subscriber with escalation_order=1"
        _pass(4, f"{len(subs)} subscriber(s) registered")
    except Exception as exc:
        _fail(4, "Subscribers exist", str(exc))


# -----------------------------------------------------------------------------
# TEST 13 -- WebSocket breach detection
# Fires FIRST among breach tests (no alert cooldown active yet).
# Reads from the shared keepalive message queue.
# -----------------------------------------------------------------------------
def test_13_websocket_breach_detected() -> None:
    try:
        # Drain any stale messages
        while not _ws_msg_queue.empty():
            try:
                _ws_msg_queue.get_nowait()
            except _queue.Empty:
                break

        # Fire the breach simulation
        r = requests.post(
            f"{BASE_URL}/api/simulate/breach",
            headers=ADMIN_HDR, **REQ_OPTS,
        )
        assert r.status_code == 200, f"simulate/breach HTTP {r.status_code}: {r.text}"
        assert r.json().get("status") == "activated", \
            f"status={r.json().get('status')!r}"

        # Wait up to 15s for a WSS message with non-empty breaches
        deadline = time.monotonic() + 15.0
        breach_msg: dict | None = None
        while time.monotonic() < deadline:
            try:
                msg = _ws_msg_queue.get(timeout=1.0)
                if msg.get("breaches") and len(msg["breaches"]) > 0:
                    breach_msg = msg
                    break
            except _queue.Empty:
                continue

        assert breach_msg is not None, \
            "no WSS breach message received within 15s after simulate/breach"
        b0 = breach_msg["breaches"][0]
        assert b0.get("parameter") == "temperature", \
            f"unexpected parameter: {b0.get('parameter')!r}"
        _pass(13, f"WSS breach detected ({b0.get('value')}C {b0.get('direction')})")
    except Exception as exc:
        _fail(13, "WebSocket breach detected", str(exc))


# -----------------------------------------------------------------------------
# TEST 05 -- Simulate breach + alert created
# Reuses the alert created by test 13 if still within cooldown window.
# -----------------------------------------------------------------------------
def test_05_simulate_breach() -> None:
    global _alert_id
    try:
        # Check if an alert already exists from test 13's breach
        alerts_r = requests.get(f"{BASE_URL}/api/alerts", **REQ_OPTS)
        assert alerts_r.status_code == 200
        existing = alerts_r.json()

        breach = next(
            (a for a in existing
             if a.get("parameter") == "temperature" and a.get("direction") == "high"),
            None,
        ) if isinstance(existing, list) else None

        if breach is None:
            # No existing alert -- fire a fresh one and wait
            r = requests.post(
                f"{BASE_URL}/api/simulate/breach",
                headers=ADMIN_HDR, **REQ_OPTS,
            )
            assert r.status_code == 200, f"simulate/breach HTTP {r.status_code}: {r.text}"
            time.sleep(8)

            alerts_r = requests.get(f"{BASE_URL}/api/alerts", **REQ_OPTS)
            assert alerts_r.status_code == 200
            alerts = alerts_r.json()
            breach = next(
                (a for a in alerts
                 if a.get("parameter") == "temperature" and a.get("direction") == "high"),
                None,
            ) if isinstance(alerts, list) else None

        assert breach is not None, (
            "no temperature/high breach alert found -- "
            "restart the server to reset the in-memory cooldown tracker, then re-run"
        )
        assert "threshold" in breach,  "threshold field missing"
        assert "severity"  in breach,  "severity field missing"
        val = breach.get("value", 0.0)
        assert val > 90.0, f"breach value {val} not > 90.0 threshold"

        _alert_id = breach["id"]
        _pass(5, f"Breach alert created (id={_alert_id}, {val}C, {breach['severity']})")
    except Exception as exc:
        _fail(5, "Breach alert created", str(exc))


# -----------------------------------------------------------------------------
# TEST 06 -- Alert has delivery receipts
# -----------------------------------------------------------------------------
def test_06_delivery_receipts() -> None:
    try:
        assert _alert_id is not None, "no alert_id from test 05 -- test 05 must pass"
        r = requests.get(f"{BASE_URL}/api/alerts", **REQ_OPTS)
        alerts = r.json()
        alert = next((a for a in alerts if a.get("id") == _alert_id), None)
        assert alert is not None, f"alert {_alert_id} not found"
        assert "delivery_status" in alert, \
            f"delivery_status field missing -- keys: {list(alert.keys())}"
        _pass(6, f"Delivery receipts present (status={alert['delivery_status']!r})")
    except Exception as exc:
        _fail(6, "Delivery receipts present", str(exc))


# -----------------------------------------------------------------------------
# TEST 07 -- Acknowledge works
# -----------------------------------------------------------------------------
def test_07_acknowledge() -> None:
    try:
        assert _alert_id is not None, "no alert_id from test 05 -- test 05 must pass"
        ack_r = requests.post(
            f"{BASE_URL}/api/alerts/{_alert_id}/acknowledge",
            headers=ADMIN_HDR,
            json={"acknowledged_by": "Integration Test"},
            **REQ_OPTS,
        )
        assert ack_r.status_code == 200, f"HTTP {ack_r.status_code}: {ack_r.text}"
        assert ack_r.json().get("status") == "acknowledged", \
            f"status={ack_r.json().get('status')!r}"

        alerts_r = requests.get(f"{BASE_URL}/api/alerts", **REQ_OPTS)
        alert = next((a for a in alerts_r.json() if a.get("id") == _alert_id), None)
        assert alert is not None,                                  "alert not found after ack"
        assert alert.get("acknowledged") is True,                  f"acknowledged={alert.get('acknowledged')}"
        assert alert.get("acknowledged_by") == "Integration Test", f"acknowledged_by={alert.get('acknowledged_by')!r}"
        _pass(7, "Acknowledge works")
    except Exception as exc:
        _fail(7, "Acknowledge works", str(exc))


# -----------------------------------------------------------------------------
# TEST 08 -- Threshold update works
# -----------------------------------------------------------------------------
def test_08_threshold_update() -> None:
    try:
        r = requests.post(
            f"{BASE_URL}/api/config/thresholds",
            headers=ADMIN_HDR,
            json={"temp_high": 92.0, "temp_low": 36.0},
            **REQ_OPTS,
        )
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        updated = r.json()
        assert updated.get("temp_high") == 92.0, f"temp_high={updated.get('temp_high')}"
        assert updated.get("temp_low")  == 36.0, f"temp_low={updated.get('temp_low')}"

        get_r = requests.get(f"{BASE_URL}/api/config/thresholds", **REQ_OPTS)
        gd = get_r.json()
        assert gd.get("source")          == "runtime_override", f"source={gd.get('source')!r}"
        assert gd["temperature"]["high"] == 92.0,               f"GET high={gd['temperature']['high']}"
        assert gd["temperature"]["low"]  == 36.0,               f"GET low={gd['temperature']['low']}"
        _pass(8, "Threshold update works (92.0/36.0)")
    except Exception as exc:
        _fail(8, "Threshold update works", str(exc))


# -----------------------------------------------------------------------------
# TEST 09 -- Threshold reset works
# -----------------------------------------------------------------------------
def test_09_threshold_reset() -> None:
    try:
        r = requests.post(
            f"{BASE_URL}/api/config/thresholds/reset",
            headers=ADMIN_HDR, **REQ_OPTS,
        )
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        assert r.json().get("source") == "default", f"reset source={r.json().get('source')!r}"

        get_r = requests.get(f"{BASE_URL}/api/config/thresholds", **REQ_OPTS)
        gd = get_r.json()
        assert gd["temperature"]["high"] == 90.0,    f"high after reset={gd['temperature']['high']}"
        assert gd["temperature"]["low"]  == 38.0,    f"low after reset={gd['temperature']['low']}"
        assert gd.get("source")          == "default", f"source after reset={gd.get('source')!r}"
        _pass(9, "Threshold reset works (back to 90.0/38.0)")
    except Exception as exc:
        _fail(9, "Threshold reset works", str(exc))


# -----------------------------------------------------------------------------
# TEST 10 -- Invalid input rejected (422)
# -----------------------------------------------------------------------------
def test_10_invalid_input_rejected() -> None:
    try:
        r = requests.post(
            f"{BASE_URL}/api/subscribers",
            headers=ADMIN_HDR,
            json={"name": "X", "phone": "notaphone",
                  "email": "bademail", "escalation_order": 9},
            **REQ_OPTS,
        )
        assert r.status_code == 422, f"expected 422, got {r.status_code}: {r.text[:200]}"
        d = r.json()
        assert "detail" in d or "error" in d, \
            f"no detail/error in 422 body -- keys: {list(d.keys())}"
        _pass(10, "Invalid input rejected (422 Unprocessable Entity)")
    except Exception as exc:
        _fail(10, "Invalid input rejected", str(exc))


# -----------------------------------------------------------------------------
# TEST 11 -- Admin auth enforced (401)
# -----------------------------------------------------------------------------
def test_11_auth_enforced() -> None:
    try:
        r = requests.post(f"{BASE_URL}/api/simulate/breach", **REQ_OPTS)
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"
        _pass(11, "Auth enforced (401 without X-Admin-Password)")
    except Exception as exc:
        _fail(11, "Auth enforced", str(exc))


# -----------------------------------------------------------------------------
# TEST 12 -- Rate limiting (429)
# Waits 62s for the 60s rate-limit window to reset, then fires 6 rapid calls.
# -----------------------------------------------------------------------------
def test_12_rate_limiting() -> None:
    try:
        print("  INFO -- Waiting 62s for rate-limit window to reset...")
        time.sleep(62)

        statuses: list[int] = []
        for _ in range(6):
            r = requests.post(
                f"{BASE_URL}/api/simulate/breach",
                headers=ADMIN_HDR, **REQ_OPTS,
            )
            statuses.append(r.status_code)

        assert 429 in statuses, f"no 429 received -- statuses: {statuses}"
        assert 200 in statuses, f"no 200 received -- statuses: {statuses}"
        _pass(12, f"Rate limiting active ({statuses.count(429)}/6 requests throttled)")
    except Exception as exc:
        _fail(12, "Rate limiting active", str(exc))


# -----------------------------------------------------------------------------
# TEST 14 -- Database stats
# By this point the background keepalive has been running for ~90s, storing
# readings every second via the WSS handler.
# -----------------------------------------------------------------------------
def test_14_database_stats() -> None:
    try:
        r = requests.get(
            f"{BASE_URL}/api/admin/database/stats",
            headers=ADMIN_HDR, **REQ_OPTS,
        )
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        d = r.json()
        assert "readings_count" in d,    "readings_count field missing"
        assert "database_size_mb" in d,  "database_size_mb field missing"
        assert d["readings_count"] > 0, (
            f"readings_count={d['readings_count']} -- "
            "readings are only stored while a WSS client is connected; "
            "the background keepalive should have populated this by now"
        )
        assert d["database_size_mb"] >= 0, f"database_size_mb={d['database_size_mb']} negative"
        _pass(14, f"Database stats available ({d['readings_count']} readings, {d['database_size_mb']} MB)")
    except Exception as exc:
        _fail(14, "Database stats available", str(exc))


# -----------------------------------------------------------------------------
# TEST 15 -- Backup
# -----------------------------------------------------------------------------
def test_15_backup() -> None:
    try:
        r = requests.post(
            f"{BASE_URL}/api/admin/backup",
            headers=ADMIN_HDR,
            timeout=20, verify=False,
        )
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        d = r.json()
        assert d.get("status") == "success", f"status={d.get('status')!r}"
        fname = d.get("filename", "")
        assert fname.endswith(".db"),         f"filename={fname!r} does not end with .db"
        size = d.get("size_mb", -1)
        assert size >= 0,                     f"size_mb={size} is negative"
        _pass(15, f"Backup created ({fname}, {size} MB)")
    except Exception as exc:
        _fail(15, "Backup created", str(exc))


# -----------------------------------------------------------------------------
# Main runner
# -----------------------------------------------------------------------------
def main() -> None:
    BAR = "=" * 42
    SEP = "-" * 42

    print()
    print(f"  {BAR}")
    print("  SENTINELEDGE LIVE INTEGRATION TESTS")
    print(f"  {BAR}")
    print(f"  Server : {BASE_URL}")
    print(f"  WS     : {WS_URL}")
    print(f"  TLS    : verify=False (self-signed cert accepted)")
    print()

    # Start background WSS keepalive.
    # Critical: readings are ONLY stored and threshold checks ONLY fire
    # when at least one WSS client is actively connected.
    print("  Starting background WSS keepalive...")
    _start_ws_keepalive()
    if _keepalive_connected.is_set():
        print("  Keepalive connected (WSS). Running tests...")
    else:
        print("  WARN -- Keepalive not connected. Tests may fail.")
    print()

    # Execution order:
    #   test_13 fires FIRST among breach tests (no cooldown active).
    #   test_05 reuses the alert created by test_13.
    #   test_06/07 depend on test_05's _alert_id.
    #   test_12 (rate limit) runs with a 62s delay to reset the window.
    tests = [
        test_01_server_alive,
        test_02_sensor_streaming,
        test_03_thresholds_correct,
        test_04_subscribers_exist,
        test_13_websocket_breach_detected,  # fires breach first, no cooldown
        test_05_simulate_breach,            # reuses alert from test_13
        test_06_delivery_receipts,
        test_07_acknowledge,
        test_08_threshold_update,
        test_09_threshold_reset,
        test_10_invalid_input_rejected,
        test_11_auth_enforced,
        test_12_rate_limiting,              # waits 62s for rate-limit window
        test_14_database_stats,
        test_15_backup,
    ]

    for fn in tests:
        try:
            fn()
        except Exception as exc:
            num_str = fn.__name__.split("_")[1]
            try:
                num = int(num_str)
            except ValueError:
                num = 0
            _fail(num, fn.__name__, f"Unexpected crash: {exc}")

    _results.sort(key=lambda x: x[0])

    total  = len(_results)
    passed = sum(1 for _, ok, _ in _results if ok)
    failed = total - passed

    print()
    print(f"  {SEP}")
    print(f"  TOTAL: {passed}/{total} passed")
    print()

    if failed == 0:
        print("  ALL LIVE INTEGRATION TESTS PASSED.")
        print("  Foundation verified end-to-end (HTTPS + WSS).")
        print("  Safe to build Module 1.")
    else:
        print(f"  {failed} TEST(S) FAILED.")
        print("  Fix failures before building Module 1.")
        print()
        print("  Failed tests:")
        for num, ok, label in _results:
            if not ok:
                print(f"    x TEST {num:02d}: {label}")

    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
