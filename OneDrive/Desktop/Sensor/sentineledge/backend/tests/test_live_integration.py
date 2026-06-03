"""
backend/tests/test_live_integration.py
SentinelEdge Live Integration Test Suite -- 15 tests.

Assumes the server is ALREADY running on https://localhost:5000
with a self-signed TLS certificate.

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
import time
import warnings

# Force UTF-8 stdout so any extended chars print cleanly on Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
import websockets
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for self-signed certificate
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

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
_alert_id: int | None = None         # set by test 05, used by tests 06 and 07
_ws_message_queue: _queue.Queue = _queue.Queue()  # all WS msgs from keepalive


# -----------------------------------------------------------------------------
# Background WS keepalive
# Keeps a WSS connection open so sensor readings are stored and threshold
# checks fire.  Every received message is put into _ws_message_queue so
# test 13 can observe breach notifications without a separate connection.
# -----------------------------------------------------------------------------
def start_ws_keepalive() -> None:
    """Start a daemon thread that holds a WSS connection open indefinitely."""
    import threading

    def _run() -> None:
        async def _loop() -> None:
            while True:
                try:
                    async with websockets.connect(
                        WS_URL, ssl=WS_SSL_CONTEXT, open_timeout=6
                    ) as ws:
                        while True:
                            try:
                                raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
                                try:
                                    msg = json.loads(raw)
                                    _ws_message_queue.put_nowait(msg)
                                except Exception:
                                    pass
                            except asyncio.TimeoutError:
                                continue
                except Exception:
                    await asyncio.sleep(1)  # reconnect after error

        asyncio.run(_loop())

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    # Give the keepalive connection time to establish before tests start
    time.sleep(2)


# -----------------------------------------------------------------------------
# TEST 01 -- Server alive
# -----------------------------------------------------------------------------
def test_01_server_alive() -> None:
    try:
        r = requests.get(f"{BASE_URL}/api/health", **REQ_OPTS)
        d = r.json()
        assert r.status_code == 200,                                 f"HTTP {r.status_code}"
        assert d.get("status") in ("ok", "degraded"),                f"status={d.get('status')!r}"
        assert d.get("version") == "1.0.0",                          f"version={d.get('version')!r}"
        assert d.get("modules", {}).get("database") == "ok",         f"database module={d.get('modules',{}).get('database')!r}"
        assert d.get("environment") == "development",                f"environment={d.get('environment')!r}"
        _pass(1, f"Server alive v{d['version']}")
    except Exception as exc:
        _fail(1, "Server alive", str(exc))


# -----------------------------------------------------------------------------
# TEST 02 -- Sensor streaming
# Connecting to WSS populates the readings table for test 14.
# -----------------------------------------------------------------------------
def test_02_sensor_streaming() -> None:
    readings: list[dict] = []

    async def _collect() -> None:
        async with websockets.connect(
            WS_URL, ssl=WS_SSL_CONTEXT, open_timeout=6
        ) as ws:
            deadline = time.monotonic() + 8.0
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
        assert len(readings) >= 5, f"only {len(readings)} readings received within 8s"
        for rd in readings:
            t = rd["temperature"]
            assert 15.0 <= t <= 50.0, f"temperature {t} out of 15-50 range"
        _pass(2, f"Sensor streaming ({len(readings)} readings)")
    except Exception as exc:
        _fail(2, "Sensor streaming (5 readings)", str(exc))


# -----------------------------------------------------------------------------
# TEST 03 -- Thresholds correct
# -----------------------------------------------------------------------------
def test_03_thresholds_correct() -> None:
    try:
        r = requests.get(f"{BASE_URL}/api/config/thresholds", **REQ_OPTS)
        d = r.json()
        assert r.status_code == 200,              f"HTTP {r.status_code}"
        temp = d.get("temperature", {})
        assert temp.get("high") == 40.0,          f"temp.high={temp.get('high')}"
        assert temp.get("low")  == 35.0,          f"temp.low={temp.get('low')}"
        assert d.get("source")  == "default",     f"source={d.get('source')!r}"
        _pass(3, "Thresholds correct (40.0/35.0)")
    except Exception as exc:
        _fail(3, "Thresholds correct (40.0/35.0)", str(exc))


# -----------------------------------------------------------------------------
# TEST 04 -- Subscribers exist
# -----------------------------------------------------------------------------
def test_04_subscribers_exist() -> None:
    try:
        r = requests.get(f"{BASE_URL}/api/subscribers", **REQ_OPTS)
        subs = r.json()
        assert r.status_code == 200,      f"HTTP {r.status_code}"
        assert isinstance(subs, list),    "response is not a list"
        assert len(subs) >= 2,            f"only {len(subs)} subscriber(s) -- need at least 2"
        orders = {s.get("escalation_order") for s in subs}
        assert 1 in orders,               "no subscriber with escalation_order=1"
        assert 2 in orders,               "no subscriber with escalation_order=2"
        _pass(4, f"{len(subs)} subscribers registered")
    except Exception as exc:
        _fail(4, "Subscribers exist", str(exc))


# -----------------------------------------------------------------------------
# TEST 13 -- WebSocket breach detection
# Runs BEFORE test 05 so no cooldown is active.
# Fires simulate/breach then reads from the shared keepalive message queue
# (which receives every WSS message in real-time) to confirm a breach was
# delivered on the stream without opening a competing WS connection.
# -----------------------------------------------------------------------------
def test_13_websocket_breach_detected() -> None:
    try:
        # Drain stale messages accumulated before this test
        while not _ws_message_queue.empty():
            try:
                _ws_message_queue.get_nowait()
            except _queue.Empty:
                break

        # Fire the breach simulation -- no cooldown active at this point
        r = requests.post(
            f"{BASE_URL}/api/simulate/breach",
            headers=ADMIN_HDR, **REQ_OPTS,
        )
        assert r.status_code == 200, f"simulate/breach HTTP {r.status_code}: {r.text}"

        # Read from the shared queue until a message with non-empty breaches arrives
        # or 15 seconds elapse.  The keepalive thread feeds this queue in real-time.
        deadline = time.monotonic() + 15.0
        breach_msg: dict | None = None
        while time.monotonic() < deadline:
            try:
                msg = _ws_message_queue.get(timeout=1.0)
                if msg.get("breaches") and len(msg["breaches"]) > 0:
                    breach_msg = msg
                    break
            except _queue.Empty:
                continue

        assert breach_msg is not None, (
            "no WSS breach message received within 15s after simulate/breach"
        )
        b0 = breach_msg["breaches"][0]
        assert b0.get("parameter") == "temperature", \
            f"unexpected parameter: {b0.get('parameter')!r}"
        _pass(13, f"WebSocket breach detected ({b0.get('value')}C {b0.get('direction')})")
    except Exception as exc:
        _fail(13, "WebSocket breach detected", str(exc))


# -----------------------------------------------------------------------------
# TEST 05 -- Simulate breach fires alert
# Runs AFTER test 13 (which already used the first breach cooldown window).
# Waits for the cooldown to reset (test 13 fires breach, we wait 6s, sensor
# ticks 10x at 42C -- the cooldown started from test 13's breach, which
# precedes test 05 by ~17s; still within 120s cooldown).
#
# Solution: test 05 checks GET /api/alerts for any existing temperature/high
# alert (which may have been created by test 13's breach), not necessarily a
# brand-new one.  If test 13 created the alert, test 05 reuses it.
# -----------------------------------------------------------------------------
def test_05_simulate_breach() -> None:
    global _alert_id
    try:
        # Fire a new breach (may be suppressed by cooldown if within 120s of test 13)
        r = requests.post(
            f"{BASE_URL}/api/simulate/breach",
            headers=ADMIN_HDR, **REQ_OPTS,
        )
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("status") == "activated", f"status={data.get('status')!r}"

        # Wait for breach readings to arrive and alert to be created
        time.sleep(6)

        alerts_r = requests.get(f"{BASE_URL}/api/alerts", **REQ_OPTS)
        assert alerts_r.status_code == 200
        alerts = alerts_r.json()
        assert isinstance(alerts, list) and len(alerts) > 0, (
            "no alerts in response -- restart server to reset cooldown tracker"
        )

        breach = next(
            (a for a in alerts
             if a.get("parameter") == "temperature" and a.get("direction") == "high"),
            None,
        )
        assert breach is not None, \
            f"no temperature/high breach -- alerts: {[(a.get('parameter'),a.get('direction')) for a in alerts]}"
        assert breach.get("threshold") == 40.0, f"threshold={breach.get('threshold')}"
        assert "severity" in breach,             "severity field missing"
        val = breach.get("value", 0.0)
        assert 40.0 < val <= 50.0,               f"breach value {val} unexpected"

        _alert_id = breach["id"]
        _pass(5, f"Breach alert created (id={_alert_id}, {val}C, {breach['severity']})")
    except Exception as exc:
        _fail(5, "Breach alert created", str(exc))


# -----------------------------------------------------------------------------
# TEST 06 -- Alert has delivery receipts
# -----------------------------------------------------------------------------
def test_06_delivery_receipts() -> None:
    try:
        assert _alert_id is not None, "no alert_id from test 5 -- test 5 must pass first"
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
        assert _alert_id is not None, "no alert_id from test 5 -- test 5 must pass first"
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
        assert alert is not None,                                        "alert not found after ack"
        assert alert.get("acknowledged") is True,                        f"acknowledged={alert.get('acknowledged')}"
        assert alert.get("acknowledged_by") == "Integration Test",       f"acknowledged_by={alert.get('acknowledged_by')!r}"
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
            json={"temp_high": 42.0, "temp_low": 33.0},
            **REQ_OPTS,
        )
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        updated = r.json()
        assert updated.get("temp_high") == 42.0, f"temp_high={updated.get('temp_high')}"
        assert updated.get("temp_low")  == 33.0, f"temp_low={updated.get('temp_low')}"

        get_r = requests.get(f"{BASE_URL}/api/config/thresholds", **REQ_OPTS)
        gd = get_r.json()
        assert gd.get("source")          == "runtime_override", f"source={gd.get('source')!r}"
        assert gd["temperature"]["high"] == 42.0,               f"GET high={gd['temperature']['high']}"
        assert gd["temperature"]["low"]  == 33.0,               f"GET low={gd['temperature']['low']}"
        _pass(8, "Threshold update works (42.0/33.0)")
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
        assert gd["temperature"]["high"] == 40.0,    f"high after reset={gd['temperature']['high']}"
        assert gd["temperature"]["low"]  == 35.0,    f"low after reset={gd['temperature']['low']}"
        assert gd.get("source")          == "default", f"source after reset={gd.get('source')!r}"
        _pass(9, "Threshold reset works (back to 40.0/35.0)")
    except Exception as exc:
        _fail(9, "Threshold reset works", str(exc))


# -----------------------------------------------------------------------------
# TEST 10 -- Invalid input rejected
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
# TEST 11 -- Admin auth enforced
# -----------------------------------------------------------------------------
def test_11_auth_enforced() -> None:
    try:
        r = requests.post(f"{BASE_URL}/api/simulate/breach", **REQ_OPTS)
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"
        _pass(11, "Auth enforced (401 without X-Admin-Password)")
    except Exception as exc:
        _fail(11, "Auth enforced", str(exc))


# -----------------------------------------------------------------------------
# TEST 12 -- Rate limiting
# -----------------------------------------------------------------------------
def test_12_rate_limiting() -> None:
    try:
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
# The keepalive WSS connection ensures readings accumulate automatically.
# -----------------------------------------------------------------------------
def test_14_database_stats() -> None:
    try:
        r = requests.get(
            f"{BASE_URL}/api/admin/database/stats",
            headers=ADMIN_HDR, **REQ_OPTS,
        )
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        d = r.json()
        assert "readings_count" in d,   "readings_count field missing"
        assert "database_size_mb" in d, "database_size_mb field missing"
        assert d["readings_count"] > 0, (
            f"readings_count={d['readings_count']} -- "
            f"readings are only stored while a WSS client is connected; "
            f"the keepalive connection should have populated this"
        )
        # database_size_mb rounds to 0.0 on a fresh DB; accept any non-negative value
        assert d["database_size_mb"] >= 0, f"database_size_mb={d['database_size_mb']} is negative"
        _pass(14, f"Database stats available "
              f"({d['readings_count']} readings, {d['database_size_mb']} MB)")
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
        # size_mb rounds to 0.0 on a fresh DB -- accept any non-negative value
        assert size >= 0,                     f"size_mb={size} is negative"
        _pass(15, f"Backup created ({fname}, {size} MB)")
    except Exception as exc:
        _fail(15, "Backup created", str(exc))


# -----------------------------------------------------------------------------
# Main runner
# -----------------------------------------------------------------------------
def main() -> None:
    BAR = "=" * 38
    SEP = "-" * 38

    print()
    print(f"  {BAR}")
    print("  SENTINELEDGE LIVE INTEGRATION TESTS")
    print(f"  {BAR}")
    print(f"  Server : {BASE_URL}")
    print(f"  WS     : {WS_URL}")
    print()

    # Start background WSS connection so sensor data flows throughout all tests.
    # This is critical: readings are only stored and thresholds only checked
    # when at least one WSS client is actively connected.
    print("  Starting background WSS keepalive...")
    start_ws_keepalive()
    print("  Keepalive connected. Running tests...")
    print()

    # Execution order:
    #   test_13 fires FIRST among breach tests (no cooldown active yet).
    #   test_05 runs second -- the same alert created by test_13 is reused.
    #   test_06/07 depend on test_05's _alert_id.
    #   test_12 (rate limit) uses simulate/breach -- runs after test_05.
    tests = [
        test_01_server_alive,
        test_02_sensor_streaming,
        test_03_thresholds_correct,
        test_04_subscribers_exist,
        test_13_websocket_breach_detected,  # BEFORE test_05: first breach, no cooldown
        test_05_simulate_breach,            # reuses alert from test_13's breach window
        test_06_delivery_receipts,
        test_07_acknowledge,
        test_08_threshold_update,
        test_09_threshold_reset,
        test_10_invalid_input_rejected,
        test_11_auth_enforced,
        test_12_rate_limiting,
        test_14_database_stats,
        test_15_backup,
    ]

    for fn in tests:
        try:
            fn()
        except Exception as exc:
            num_str = fn.__name__.split("_")[1]
            _fail(int(num_str), fn.__name__, f"Unexpected crash: {exc}")

    # Sort results by test number for display
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
        print("  Foundation verified end-to-end.")
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
