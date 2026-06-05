"""
routers/admin.py — Admin-only endpoints.

Tags: Admin
All endpoints require X-Admin-Password header.

Endpoints:
    GET  /api/admin/config-changes    — config audit log
    GET  /api/admin/backups           — list database backups
    POST /api/admin/backup            — trigger immediate backup
    GET  /api/admin/database/stats    — database size and row counts
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import database
from config import ADMIN_PASSWORD, SMTP_USER
from middleware.auth import require_admin
from models import ConfigChangeOut
from database.backup import create_backup, get_backup_list
from database.retention import get_database_stats
from modules.email.smtp import send_alert_email
from utils.logger import get_logger
from utils.time import now_iso

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["Admin"])


class _VerifyIn(BaseModel):
    password: str


@router.post(
    "/admin/verify-password",
    summary="Verify admin password",
    description="Checks whether the supplied password matches ADMIN_PASSWORD. "
                "No auth header required. Returns {valid: bool}.",
)
async def verify_password(body: _VerifyIn):
    """Used by the frontend admin modal to verify the password on first entry."""
    return {"valid": body.password == ADMIN_PASSWORD}



@router.get(
    "/admin/config-changes",
    response_model=list[ConfigChangeOut],
    summary="Get config change audit log",
    description="Returns the last 50 configuration changes. Requires admin auth.",
    dependencies=[Depends(require_admin)],
)
async def get_config_changes():
    rows = database.get_recent_config_changes(limit=50)
    return [
        ConfigChangeOut(
            id=r["id"],
            changed_by=r["changed_by"],
            field_name=r["field_name"],
            old_value=r["old_value"],
            new_value=r["new_value"],
            changed_at=r["changed_at"],
        )
        for r in rows
    ]


@router.get(
    "/admin/backups",
    summary="List database backups",
    description="Returns metadata for all available database backup files.",
    dependencies=[Depends(require_admin)],
)
async def list_backups():
    """Return a list of available database backup files."""
    try:
        backups = get_backup_list()
        return {
            "count":   len(backups),
            "backups": backups,
        }
    except Exception as exc:
        logger.error("list_backups failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to list backups", "detail": str(exc)},
        )


@router.post(
    "/admin/backup",
    summary="Trigger immediate backup",
    description="Creates a timestamped database backup right now.",
    dependencies=[Depends(require_admin)],
)
async def trigger_backup():
    """Create a database backup immediately."""
    try:
        path = create_backup()
        if path is None:
            return JSONResponse(
                status_code=500,
                content={"error": "Backup failed", "detail": "See server logs."},
            )
        backups = get_backup_list()
        latest = backups[0] if backups else {}
        return {
            "status":    "success",
            "filename":  latest.get("filename", "backup.db"),
            "size_mb":   latest.get("size_mb", 0),
            "timestamp": now_iso(),
        }
    except Exception as exc:
        logger.error("trigger_backup failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Backup failed", "detail": str(exc)},
        )


@router.get(
    "/admin/database/stats",
    summary="Database statistics",
    description=(
        "Returns row counts, database file size, oldest reading, "
        "and number of available backups."
    ),
    dependencies=[Depends(require_admin)],
)
async def database_stats():
    """Return database size and content statistics."""
    try:
        return get_database_stats()
    except Exception as exc:
        logger.error("database_stats failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get stats", "detail": str(exc)},
        )


class _ImportCsvIn(BaseModel):
    filename: str  # absolute or relative path to the CSV file


@router.post(
    "/admin/import-csv",
    summary="Import historical readings from CSV",
    description=(
        "Reads a CSV file with columns: timestamp, temperature, reference_value. "
        "Inserts each valid row into the readings table. "
        "Skips rows with bad data gracefully. "
        "Requires admin auth. "
        "Body: {filename: 'path/to/file.csv'}"
    ),
    dependencies=[Depends(require_admin)],
)
async def import_csv(body: _ImportCsvIn):
    """Import historical readings from a CSV file on the server."""
    try:
        from utils.import_csv import import_csv_file
        count = import_csv_file(body.filename)
        logger.info("CSV import: %d readings from %s", count, body.filename)
        return {
            "status":   "success",
            "imported": count,
            "filename": body.filename,
        }
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": "File not found", "detail": str(exc)},
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": "Invalid CSV format", "detail": str(exc)},
        )
    except Exception as exc:
        logger.error("import_csv failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Import failed", "detail": str(exc)},
        )

class _TestEmailIn(BaseModel):
    email: str


@router.post(
    "/admin/test-email",
    summary="Send a test HTML alert email",
    description=(
        "Immediately sends a test HTML email to the given address using dummy "
        "data. Use this to verify the email template without triggering a breach. "
        "Requires admin auth."
    ),
    dependencies=[Depends(require_admin)],
)
async def test_email(body: _TestEmailIn):
    """Send a test HTML email to verify the Module 2 template."""
    import asyncio
    try:
        ok = await asyncio.get_event_loop().run_in_executor(
            None,
            send_alert_email,
            body.email,          # recipient_email
            "Test Operator",     # recipient_name
            37.5,                # temperature
            38.0,                # threshold
            "low",               # direction
            "WARNING",           # severity
            1,                   # escalation_level
            now_iso(),           # timestamp_utc
        )
        if ok:
            logger.info("Test email sent to %s", body.email)
            return {"status": "sent", "email": body.email}
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": "SMTP send returned False — check server logs"},
        )
    except Exception as exc:
        logger.error("test_email failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": str(exc)},
        )


# ─── Test SMS ─────────────────────────────────────────────────────────────────

class _TestSmsIn(BaseModel):
    phone: str


@router.post(
    "/admin/test-sms",
    summary="Send a test SMS alert",
    description=(
        "Immediately sends a test SMS to the given phone number using dummy "
        "low-temperature data (37.5°C below 38.0°C threshold). "
        "Routes through the configured SMS_METHOD (adb / gammu / gateway). "
        "Requires admin auth. Body: {\"phone\": \"6385936224\"}"
    ),
    dependencies=[Depends(require_admin)],
)
async def test_sms(body: _TestSmsIn):
    """Send a test SMS to verify Module 3 (ADB/Gammu/Gateway transport)."""
    from config import SMS_METHOD
    from modules.sms.sender import build_sms_message, send_sms
    try:
        ts = now_iso()
        message = build_sms_message(
            value=37.5,
            threshold=38.0,
            direction="low",
            timestamp_utc=ts,
        )
        ok = send_sms(body.phone, message)
        if ok:
            logger.info("Test SMS sent to %s via %s", body.phone, SMS_METHOD)
            return {
                "status":  "sent",
                "phone":   body.phone,
                "method":  SMS_METHOD,
                "message": message,
                "chars":   len(message),
            }
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "phone":  body.phone,
                "method": SMS_METHOD,
                "error":  "SMS transport returned False — check server logs for details",
            },
        )
    except Exception as exc:
        logger.error("test_sms failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"status": "failed", "error": str(exc)},
        )
