"""
routers/simulate.py — /api/simulate endpoints.

Tags: Testing
Rate limiting: POST /simulate/breach → 5 requests/minute per IP
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

import core.sensor as sensor
from middleware.auth import require_admin
from middleware.rate_limiter import rate_limiter, make_rate_limit_response

router = APIRouter(prefix="/api", tags=["Testing"])


@router.post(
    "/simulate/breach",
    summary="Simulate a threshold breach",
    description=(
        "Forces the sensor to emit 10 readings above the high threshold. "
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
    sensor.set_breach_override(10)
    return {
        "status": "activated",
        "message": "Breach simulation active for next 10 readings",
        "ticks": 10,
    }
