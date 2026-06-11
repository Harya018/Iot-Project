r"""
database/backup.py — Daily database backup for SentinelEdge (PostgreSQL).

Creates a pg_dump .sql file in database/backups/ at UTC midnight.
Keeps only the last MAX_BACKUPS files. Runs at UTC midnight every day.

pg_dump is available on PATH after the PostgreSQL Windows installer runs
(default install adds C:\Program Files\PostgreSQL\<version>\bin to PATH).

Never raises — all errors are logged and silently swallowed so a backup
failure never crashes the server.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import urllib.parse
from pathlib import Path

from utils.logger import get_logger
from utils.time import now_iso, seconds_until_midnight

logger = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKUP_DIR   = _PROJECT_ROOT / "database" / "backups"

MAX_BACKUPS = 7

# ── Parse DATABASE_URL for pg_dump ────────────────────────────────────────────

def _parse_db_url() -> dict:
    """
    Parse DATABASE_URL environment variable into components for pg_dump.
    Returns dict with keys: host, port, dbname, user, password.
    """
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://sentineledge:sentineledge123@localhost:5432/sentineledge",
    )
    parsed = urllib.parse.urlparse(url)
    return {
        "host":     parsed.hostname or "localhost",
        "port":     str(parsed.port or 5432),
        "dbname":   parsed.path.lstrip("/") or "sentineledge",
        "user":     parsed.username or "sentineledge",
        "password": parsed.password or "",
    }


# ── Core functions ────────────────────────────────────────────────────────────

def create_backup() -> str | None:
    """
    Create a pg_dump .sql backup of the PostgreSQL database.

    Returns the backup file path on success, None on failure.
    Deletes oldest backups beyond MAX_BACKUPS.
    """
    try:
        _BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Build filename: sentineledge_2026-06-02T10-45-00.sql
        ts = now_iso().replace(":", "-").replace("+", "Z").split(".")[0]
        backup_name = f"sentineledge_{ts}.sql"
        backup_path = _BACKUP_DIR / backup_name

        db = _parse_db_url()

        env = os.environ.copy()
        env["PGPASSWORD"] = db["password"]

        cmd = [
            "pg_dump",
            "-h", db["host"],
            "-p", db["port"],
            "-U", db["user"],
            "-d", db["dbname"],
            "-F", "p",          # plain SQL format
            "-f", str(backup_path),
        ]

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            logger.error(
                "pg_dump failed (exit %d): %s",
                result.returncode,
                result.stderr[:500],
            )
            return None

        size_mb = round(backup_path.stat().st_size / (1024 * 1024), 3)
        logger.info("Backup created: %s (%.3f MB)", backup_name, size_mb)

        cleanup_old_backups()
        return str(backup_path)

    except FileNotFoundError:
        logger.error(
            "Backup failed: pg_dump not found on PATH. "
            "Ensure PostgreSQL bin directory is in the system PATH."
        )
        return None
    except subprocess.TimeoutExpired:
        logger.error("Backup failed: pg_dump timed out after 120 seconds")
        return None
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
            list(_BACKUP_DIR.glob("sentineledge_*.sql"))
            + list(_BACKUP_DIR.glob("sentineledge_*.db")),  # legacy .db files
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
            list(_BACKUP_DIR.glob("sentineledge_*.sql"))
            + list(_BACKUP_DIR.glob("sentineledge_*.db")),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        result = []
        for f in backups:
            result.append({
                "filename":   f.name,
                "size_mb":    round(f.stat().st_size / (1024 * 1024), 3),
                "created_at": now_iso(),
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
    logger.info("Daily backup scheduler started (pg_dump mode).")
    while True:
        wait = seconds_until_midnight()
        logger.info("Next backup in %.0f seconds (at midnight UTC).", wait)
        await asyncio.sleep(wait)
        logger.info("Running daily pg_dump backup ...")
        path = create_backup()
        if path:
            logger.info("Daily backup completed: %s", path)
        else:
            logger.warning("Daily backup completed with errors — check logs.")
