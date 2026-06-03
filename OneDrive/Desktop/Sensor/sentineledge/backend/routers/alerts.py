"""
routers/alerts.py — /api/alerts endpoints.

Tags: Alerts
Rate limiting: POST /acknowledge → 10 requests/minute per IP
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

import database
import core.escalation as escalation
from middleware.rate_limiter import rate_limiter, make_rate_limit_response
from models import AcknowledgeIn, AlertOut

router = APIRouter(prefix="/api", tags=["Alerts"])


def _build_delivery_status(alert_id: int) -> dict:
    receipts = database.get_receipts_for_alert(alert_id)
    status: dict = {}
    for r in receipts:
        channel = r["channel"]
        if r["success"]:
            status[channel] = "delivered"
        else:
            if status.get(channel) != "delivered":
                status[channel] = "failed"
    return status


@router.get(
    "/alerts",
    response_model=list[AlertOut],
    summary="Get recent alerts",
    description="Returns the last 50 alerts with delivery status and escalation level.",
)
async def get_alerts():
    rows = database.get_recent_alerts(limit=50)
    result = []
    for r in rows:
        delivery_status = _build_delivery_status(r["id"])
        result.append(
            AlertOut(
                id=r["id"],
                parameter=r["parameter"],
                value=r["value"],
                threshold=r["threshold"],
                direction=r["direction"],
                severity=r.get("severity", "WARNING"),
                timestamp=r["timestamp"],
                acknowledged=bool(r["acknowledged"]),
                acknowledged_by=r.get("acknowledged_by"),
                acknowledged_at=r.get("acknowledged_at"),
                escalation_level=r["escalation_level"],
                max_escalated=bool(r["max_escalated"]),
                cooldown_until=r.get("cooldown_until"),
                delivery_status=delivery_status if delivery_status else None,
            )
        )
    return result


@router.post(
    "/alerts/{alert_id}/acknowledge",
    summary="Acknowledge an alert",
    description="Marks the alert as acknowledged and stops further escalation.",
)
async def acknowledge_alert(alert_id: int, body: AcknowledgeIn, request: Request):
    # Rate limit: 10 per minute
    if not rate_limiter.is_allowed(request.client.host, limit=10, window_seconds=60):
        return JSONResponse(
            status_code=429,
            content=make_rate_limit_response(60),
            headers={"Retry-After": "60"},
        )

    ok = await escalation.acknowledge(alert_id, body.acknowledged_by)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"Alert {alert_id} not found or already acknowledged",
        )
    return {"status": "acknowledged", "alert_id": alert_id}
