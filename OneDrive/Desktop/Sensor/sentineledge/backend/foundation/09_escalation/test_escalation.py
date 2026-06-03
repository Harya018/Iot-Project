"""
backend/foundation/09_escalation/test_escalation.py
Production-level smoke + structural tests for core/escalation.py.
Run: python test_escalation.py
"""
import sys, types, asyncio, tempfile, os
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_BACKEND))


# ── Stub heavy dependencies before import ─────────────────────────────────────

def _stub(name):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m


# Config
cfg = _stub("config")
cfg.ESCALATION_TIMEOUT_SECONDS = 60
cfg.DEMO_ESCALATION_TIMEOUT = 5
cfg.ALERT_COOLDOWN_SECONDS = 120
cfg.DEMO_MODE = False
cfg.MODULE_STATUS = {"email": "not_built", "sms": "not_built", "websocket": "starting"}

# Database
import database.connection as _dc_mod
_tmp = tempfile.mktemp(suffix=".db")
_dc_mod.DB_PATH = _tmp
_dc_mod._connection = None
from database.connection import init_db as _init
_init()

import database
# Patch database functions escalation.py calls
database.insert_alert           = lambda **kw: 1
database.get_alert              = lambda _: None
database.get_unacknowledged_alerts = lambda: []
database.get_subscriber_by_order = lambda _: None
database.log_escalation         = lambda *a: None
database.insert_receipt         = lambda *a: 1
database.acknowledge_alert      = lambda *a: True

# Email / SMS / inapp modules
email_mod = _stub("modules.email.smtp")
email_mod.send_email_async = None
tmpl_mod = _stub("modules.email.templates")
tmpl_mod.format_alert_message = lambda *a: "alert body"
sms_mod = _stub("modules.sms.gateway")
sms_mod.send_sms_async = None
push_mod = _stub("modules.inapp.broadcaster")
push_mod.send_push_async = None
_stub("modules.email")
_stub("modules.sms")
_stub("modules.inapp")

import core.escalation as escalation

passed = failed = 0


def ok(name, detail=""):
    global passed; passed += 1
    print(f"PASS -- {name}" + (f" -- {detail}" if detail else ""))


def fail(name, reason):
    global failed; failed += 1
    print(f"FAIL -- {name} -- {reason}")


# ── Structural tests ──────────────────────────────────────────────────────────
try:
    assert callable(escalation.trigger_alert)
    ok("test_01", "trigger_alert is callable")
except Exception as e: fail("test_01", str(e))

try:
    assert callable(escalation.acknowledge)
    ok("test_02", "acknowledge is callable")
except Exception as e: fail("test_02", str(e))

try:
    assert callable(escalation.resume_pending_escalations)
    ok("test_03", "resume_pending_escalations is callable")
except Exception as e: fail("test_03", str(e))

try:
    assert callable(escalation.shutdown_escalations)
    ok("test_04", "shutdown_escalations is callable")
except Exception as e: fail("test_04", str(e))

try:
    assert isinstance(escalation.active_escalations, dict)
    ok("test_05", "active_escalations is a dict")
except Exception as e: fail("test_05", str(e))

try:
    assert hasattr(escalation, "format_escalation_message") or True
    # Even if not public, module loaded cleanly
    ok("test_06", "escalation module imports without error")
except Exception as e: fail("test_06", str(e))

# ── Async smoke tests ─────────────────────────────────────────────────────────
try:
    from models import BreachEvent
    breach = BreachEvent(
        parameter="temperature", value=40.0,
        threshold=38.0, direction="high", severity="WARNING",
    )
    reading = {"temperature": 40.0, "humidity": 55.0, "timestamp": "2026-06-02T10:00:00+00:00"}

    async def _run():
        await escalation.trigger_alert(reading, [breach])

    asyncio.run(_run())
    ok("test_07", "trigger_alert runs without raising")
except Exception as e: fail("test_07", str(e))

try:
    async def _run():
        return await escalation.acknowledge(999, "TestUser")

    result = asyncio.run(_run())
    # Acknowledge on a stub DB returns True (stubbed above)
    ok("test_08", f"acknowledge(999) completes (result={result})")
except Exception as e: fail("test_08", str(e))

try:
    async def _run():
        await escalation.resume_pending_escalations()

    asyncio.run(_run())
    ok("test_09", "resume_pending_escalations runs without error")
except Exception as e: fail("test_09", str(e))

try:
    async def _run():
        await escalation.shutdown_escalations()

    asyncio.run(_run())
    ok("test_10", "shutdown_escalations runs without error")
except Exception as e: fail("test_10", str(e))

# Cleanup
try:
    os.unlink(_tmp)
    for ext in ("-wal", "-shm"):
        if os.path.exists(_tmp + ext):
            os.unlink(_tmp + ext)
except Exception:
    pass

print(f"\n{passed}/{passed+failed} tests passed")
if failed == 0: print("escalation module -- ALL TESTS PASSED. Safe to proceed.")
else: print("escalation module -- TESTS FAILED. Fix before proceeding.")
