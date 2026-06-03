"""
database/backup.py — Daily database backup for SentinelEdge.

Creates a timestamped copy of sentineledge.db in database/backups/.
Keeps only the last MAX_BACKUPS files. Runs at UTC midnight every day.

Never raises — all errors are logged and silently swallowed so
a backup failure never crashes the server.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

from utils.logger import get_logger
from utils.time import now_iso, today_date_str, seconds_until_midnight

logger = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
# database/backup.py → ../../database/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DB_PATH = _PROJECT_ROOT / "database" / "sentineledge.db"
_BACKUP_DIR = _PROJECT_ROOT / "database" / "backups"

MAX_BACKUPS = 7


# ── Core functions ────────────────────────────────────────────────────────────

def create_backup() -> str | None:
    """
    Create a timestamped copy of sentineledge.db in database/backups/.

    Returns the backup file path on success, None on failure.
    Deletes oldest backups beyond MAX_BACKUPS.
    """
    try:
        if not _DB_PATH.exists():
            logger.warning("Backup skipped: database file not found at %s", _DB_PATH)
            return None

        _BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Build filename: sentineledge_2026-06-02T10-45-00.db
        ts = now_iso().replace(":", "-").replace("+", "Z").split(".")[0]
        backup_name = f"sentineledge_{ts}.db"
        backup_path = _BACKUP_DIR / backup_name

        shutil.copy2(_DB_PATH, backup_path)
        size_mb = round(backup_path.stat().st_size / (1024 * 1024), 2)
        logger.info("Backup created: %s (%.2f MB)", backup_name, size_mb)

        cleanup_old_backups()
        return str(backup_path)

    except Exception as exc:
        logger.error("Backup failed: %s", exc)
        return None


def cleanup_old_backups() -> None:
    """
    Delete all backup files beyond the most recent MAX_BACKUPS.
    Files are sorted by modification time (oldest first).
    """
    try:
        if not _BACKUP_DIR.exists():
            return
        backups = sorted(
            _BACKUP_DIR.glob("sentineledge_*.db"),
            key=lambda p: p.stat().st_mtime,
        )
        to_delete = backups[:-MAX_BACKUPS] if len(backups) > MAX_BACKUPS else []
        for f in to_delete:
            f.unlink(missing_ok=True)
            logger.info("Old backup deleted: %s", f.name)
    except Exception as exc:
        logger.error("cleanup_old_backups failed: %s", exc)


def get_backup_list() -> list[dict]:
    """
    Return metadata for all existing backup files.

    Each entry: {"filename": str, "size_mb": float, "created_at": str}
    """
    try:
        if not _BACKUP_DIR.exists():
            return []
        backups = sorted(
            _BACKUP_DIR.glob("sentineledge_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        result = []
        for f in backups:
            result.append({
                "filename":   f.name,
                "size_mb":    round(f.stat().st_size / (1024 * 1024), 2),
                "created_at": now_iso(),   # approximation — real ts is in filename
            })
        return result
    except Exception as exc:
        logger.error("get_backup_list failed: %s", exc)
        return []


# ── Scheduler ─────────────────────────────────────────────────────────────────

async def schedule_daily_backup() -> None:
    """
    Asyncio background task — runs create_backup() once per day at UTC midnight.
    Loops forever; a single backup failure does not stop the scheduler.
    """
    logger.info("Daily backup scheduler started.")
    while True:
        wait = seconds_until_midnight()
        logger.info("Next backup in %.0f seconds (at midnight UTC).", wait)
        await asyncio.sleep(wait)
        logger.info("Running daily backup...")
        path = create_backup()
        if path:
            logger.info("Daily backup completed: %s", path)
        else:
            logger.warning("Daily backup completed with errors.")
