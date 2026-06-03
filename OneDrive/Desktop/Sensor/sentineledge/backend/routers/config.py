"""
routers/config.py — /api/config endpoints.

Additions:
  - Addition 6:  POST /api/config/thresholds logs audit trail
  - Addition 10: POST endpoints protected by require_admin
  - Addition 11: GET /api/config/thresholds returns detailed source info
                 POST /api/config/thresholds/reset resets to defaults
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

import database
from config import (
    RUNTIME_THRESHOLDS,
    DEFAULT_THRESHOLDS,
    VAPID_PUBLIC_KEY,
)
import config as _config
from middleware.auth import require_admin
from models import ThresholdConfigIn, ThresholdConfigOut, ThresholdConfigDetailOut

router = APIRouter(prefix="/api")
logger = logging.getLogger("sentineledge.routers.config")


@router.get("/config/thresholds")
async def get_thresholds():
    """
    Return current thresholds with source info (Addition 11).
    """
    return {
        "temperature": {
            "high": RUNTIME_THRESHOLDS["temp_high"],
            "low":  RUNTIME_THRESHOLDS["temp_low"],
            "unit": "°C",
            "name": "Temperature",
        },
        "source": _config.RUNTIME_SOURCE,
        "last_changed": _config.RUNTIME_LAST_CHANGED,
    }


@router.post(
    "/config/thresholds",
    response_model=ThresholdConfigOut,
    dependencies=[Depends(require_admin)],
)
async def update_thresholds(body: ThresholdConfigIn):
    """Update runtime thresholds and log changes (Additions 6 + 10)."""
    fields = {
        "temp_high": body.temp_high,
        "temp_low":  body.temp_low,
    }
    for field, new_val in fields.items():
        old_val = RUNTIME_THRESHOLDS[field]
        if old_val != new_val:
            database.log_config_change(
                changed_by="admin",
                field_name=field,
                old_value=str(old_val),
                new_value=str(new_val),
            )
            RUNTIME_THRESHOLDS[field] = new_val

    _config.RUNTIME_SOURCE = "runtime_override"
    _config.RUNTIME_LAST_CHANGED = datetime.now(timezone.utc).isoformat()
    logger.info("Thresholds updated at runtime: %s", RUNTIME_THRESHOLDS)
    return ThresholdConfigOut(**RUNTIME_THRESHOLDS)


@router.post(
    "/config/thresholds/reset",
    dependencies=[Depends(require_admin)],
)
async def reset_thresholds():
    """
    Reset RUNTIME_THRESHOLDS back to the values from .env (Addition 11).
    Logs each changed field.
    """
    for field, default_val in DEFAULT_THRESHOLDS.items():
        old_val = RUNTIME_THRESHOLDS[field]
        if old_val != default_val:
            database.log_config_change(
                changed_by="admin",
                field_name=field,
                old_value=str(old_val),
                new_value=str(default_val),
            )
            RUNTIME_THRESHOLDS[field] = default_val

    _config.RUNTIME_SOURCE = "default"
    _config.RUNTIME_LAST_CHANGED = datetime.now(timezone.utc).isoformat()
    logger.info("Thresholds reset to defaults: %s", RUNTIME_THRESHOLDS)
    return {
        "status": "reset",
        "thresholds": {
            "temperature": {
                "high": RUNTIME_THRESHOLDS["temp_high"],
                "low":  RUNTIME_THRESHOLDS["temp_low"],
            },
        },
        "source": _config.RUNTIME_SOURCE,
    }


@router.get("/config/vapid-public-key")
async def get_vapid_public_key():
    return {"vapid_public_key": VAPID_PUBLIC_KEY}
