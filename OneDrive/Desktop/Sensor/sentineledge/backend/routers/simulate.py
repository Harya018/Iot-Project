"""
routers/simulate.py — /api/simulate/* endpoints.

POST /api/simulate/breach  — force a HIGH threshold breach for N ticks (testing)
POST /api/simulate/demo    — start accelerated CSV playback (demo)
POST /api/simulate/reset   — stop demo mode, rewind to start of data
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import core.sensor as sensor
from middleware.auth import require_admin
from middleware.rate_limiter import rate_limiter, make_rate_limit_response

router = APIRouter(prefix="/api", tags=["Testing"])


# ─── Breach simulation ────────────────────────────────────────────────────────

@router.post(
    "/simulate/breach",
    summary="Simulate a threshold breach",
    description=(
        "Forces the sensor to emit 10 readings at 92.0°C (above the 90.0°C HIGH "
        "threshold), triggering the alert pipeline for testing. "
        "Requires admin auth. Rate limited to 5/min."
    ),
    dependencies=[Depends(require_admin)],
)
async def simulate_breach(request: Request):
    if not rate_limiter.is_allowed(request.client.host, limit=5, window_seconds=60):
        return JSONResponse(
            status_code=429,
            content=make_rate_limit_response(60),
            headers={"Retry-After": "60"},
        )
    sensor.set_breach_override(ticks=10, value=92.0)
    return {
        "status":  "activated",
        "message": "Breach simulation active for next 10 readings (92.0°C)",
        "ticks":   10,
        "value":   92.0,
    }


# ─── Demo playback ────────────────────────────────────────────────────────────

class _DemoIn(BaseModel):
    speed: int = Field(
        default=30,
        ge=1,
        le=100,
        description=(
            "Playback speed multiplier. "
            "1 = real time (~2.5 hrs), "
            "30 = ~5 min, "
            "50 = ~3 min."
        ),
    )


@router.post(
    "/simulate/demo",
    summary="Start accelerated demo playback",
    description=(
        "Rewinds to the first CSV reading and plays back at the requested speed. "
        "The LOW threshold alert fires when temperature drops below 38.0°C. "
        "speed=30 → ~5 minutes, speed=50 → ~3 minutes. "
        "Requires admin auth."
    ),
    dependencies=[Depends(require_admin)],
)
async def simulate_demo(body: _DemoIn, request: Request):
    if not rate_limiter.is_allowed(request.client.host, limit=10, window_seconds=60):
        return JSONResponse(
            status_code=429,
            content=make_rate_limit_response(60),
            headers={"Retry-After": "60"},
        )
    result = sensor.activate_demo(speed=body.speed)
    return result


# ─── Reset ───────────────────────────────────────────────────────────────────

@router.post(
    "/simulate/reset",
    summary="Reset sensor to beginning of data",
    description=(
        "Stops demo mode and rewinds CSV playback to the very first reading. "
        "Normal 1-reading/second speed is restored. "
        "Requires admin auth."
    ),
    dependencies=[Depends(require_admin)],
)
async def simulate_reset():
    return sensor.reset_sensor()
