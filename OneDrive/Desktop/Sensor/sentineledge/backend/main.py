"""
main.py — SentinelEdge FastAPI application entry point.

Production upgrades in this version:
  - Structured error handlers (SentinelEdgeError, 404, 500)
  - Full OpenAPI documentation with descriptions, tags, and version
  - Startup tasks: DB backup + data retention schedulers
  - All timestamps UTC ISO 8601
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

import database
import core.sensor as sensor
import core.threshold as threshold
import core.escalation as escalation
from core.validator import validate_reading
from core.daily_report import schedule_daily_report
from config import (
    APP_ENV, DEMO_MODE, SERVER_PORT, MODULE_STATUS,
    SMTP_USER, SMTP_PASSWORD, SMS_GATEWAY_URL, ADMIN_PASSWORD,
    APP_VERSION,
)
from models import ReadingOut
from utils.errors import SentinelEdgeError
from utils.logger import get_logger
from utils.time import now_iso

from middleware.cors import configure_cors
from middleware.logger import log_requests

from modules.inapp.manager import (
    add_connection, remove_connection, broadcast, active_connections,
)

from routers.alerts import router as alerts_router
from routers.subscribers import router as subscribers_router
from routers.config import router as config_router
from routers.simulate import router as simulate_router
from routers.health import router as health_router
from routers.admin import router as admin_router

from database.backup import schedule_daily_backup
from database.retention import schedule_retention_cleanup

logger = get_logger(__name__)


# ─── Startup / shutdown ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    database.init_db()
    await escalation.resume_pending_escalations()

    # Background tasks
    asyncio.create_task(schedule_daily_report(),      name="daily-report-scheduler")
    asyncio.create_task(schedule_daily_backup(),      name="daily-backup-scheduler")
    asyncio.create_task(schedule_retention_cleanup(), name="retention-cleanup-scheduler")

    try:
        lan_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        lan_ip = "127.0.0.1"
    logger.info(
        "SentinelEdge v%s started -- https://%s:%d  (DEMO_MODE=%s, ENV=%s)",
        APP_VERSION, lan_ip, SERVER_PORT, DEMO_MODE, APP_ENV,
    )

    # ── Startup validation ────────────────────────────────────────────────────
    if APP_ENV == "production":
        if not SMTP_USER:
            logger.warning("SMTP_USER not set — email alerts will fail")
        if not SMTP_PASSWORD:
            logger.warning("SMTP_PASSWORD not set — email alerts will fail")
        if not SMS_GATEWAY_URL:
            logger.warning("SMS_GATEWAY_URL not set — SMS alerts will fail")
        if ADMIN_PASSWORD == "admin123":
            logger.warning("ADMIN_PASSWORD is default — change before deployment")
    else:
        logger.info("Running in DEVELOPMENT mode — using test configuration")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("SentinelEdge shutting down...")

    shutdown_msg = json.dumps({"type": "server_shutdown"})
    dead = set()
    for ws in list(active_connections):
        try:
            await ws.send_text(shutdown_msg)
            await ws.close()
        except Exception:
            dead.add(ws)
    active_connections.difference_update(dead)
    active_connections.clear()

    await escalation.shutdown_escalations()
    logger.info("Shutdown complete.")


# ─── Application ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="SentinelEdge",
    description="""
## SentinelEdge Monitoring System

Real-time IoT sensor monitoring with multi-channel threshold alerts.

### Alert Channels
- **In-App** — WebSocket real-time dashboard
- **Email** — Gmail SMTP delivery
- **SMS** — Android Gateway cellular delivery

### Authentication
Admin endpoints require header:
`X-Admin-Password: your_password`

### Severity Levels
- **WARNING** — 5% over threshold
- **CRITICAL** — 10% over threshold
- **EMERGENCY** — 25% over threshold
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

configure_cors(app)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)


# ─── Global error handlers ────────────────────────────────────────────────────

@app.exception_handler(SentinelEdgeError)
async def sentinel_error_handler(request: Request, exc: SentinelEdgeError):
    """Convert SentinelEdge domain errors to structured JSON 400 responses."""
    return JSONResponse(
        status_code=400,
        content={
            "error":     exc.__class__.__name__,
            "message":   exc.message,
            "details":   exc.details,
            "timestamp": now_iso(),
            "path":      str(request.url),
        },
    )


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions — never expose stack traces to clients."""
    logger.error("Unhandled error on %s: %s", request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error":     "InternalServerError",
            "message":   "An unexpected error occurred",
            "timestamp": now_iso(),
            "path":      str(request.url),
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error":     "NotFound",
            "message":   f"Path {request.url.path} not found",
            "timestamp": now_iso(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception("Internal server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ─── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    add_connection(ws)
    MODULE_STATUS["websocket"] = "ok"

    try:
        async for reading in sensor.stream_readings():

            is_valid, reason = validate_reading(reading)

            database.insert_reading(
                reading["temperature"],
                reading["timestamp"],
                is_valid=is_valid,
            )

            if not is_valid:
                logger.warning("Invalid reading skipped: %s", reason)
                payload = {
                    "temperature":      reading["temperature"],
                    "timestamp":        reading["timestamp"],
                    "breaches":         [],
                    "is_valid":         False,
                    "validation_error": reason,
                }
                await broadcast(payload)
                continue

            breaches = threshold.check_threshold(reading)

            if breaches:
                asyncio.create_task(escalation.trigger_alert(reading, breaches))

            import routers.health as _health_mod
            _health_mod.last_reading = {
                "temperature": reading["temperature"],
                "timestamp":   reading["timestamp"],
            }

            payload = {
                "temperature": reading["temperature"],
                "timestamp":   reading["timestamp"],
                "breaches":    [b.model_dump() for b in breaches],
                "is_valid":    True,
            }
            await broadcast(payload)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
        MODULE_STATUS["websocket"] = f"error: {exc}"
    finally:
        remove_connection(ws)


# ─── Readings endpoint ────────────────────────────────────────────────────────

_readings_router = APIRouter(prefix="/api", tags=["Readings"])


@_readings_router.get(
    "/readings/recent",
    response_model=list[ReadingOut],
    summary="Get recent readings",
    description="Returns the last 60 sensor readings in reverse-chronological order.",
)
async def get_recent_readings():
    rows = database.get_recent_readings(limit=60)
    return [
        ReadingOut(
            temperature=r["temperature"],
            timestamp=r["timestamp"],
            is_valid=bool(r.get("is_valid", True)),
            breaches=[],
        )
        for r in rows
    ]


# ─── Include all routers ──────────────────────────────────────────────────────

app.include_router(_readings_router)
app.include_router(alerts_router)
app.include_router(subscribers_router)
app.include_router(config_router)
app.include_router(simulate_router)
app.include_router(health_router)
app.include_router(admin_router)

# ─── Static files (built React app) ──────────────────────────────────────────
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
else:
    logger.warning(
        "Static dir '%s' not found. Run 'npm run build' in frontend-web/ first.",
        _static_dir,
    )
