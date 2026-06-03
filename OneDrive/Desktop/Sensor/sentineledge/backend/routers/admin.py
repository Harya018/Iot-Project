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

import database
from middleware.auth import require_admin
from models import ConfigChangeOut
from database.backup import create_backup, get_backup_list
from database.retention import get_database_stats
from utils.logger import get_logger
from utils.time import now_iso

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["Admin"])


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
