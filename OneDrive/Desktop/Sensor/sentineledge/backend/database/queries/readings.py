"""
database/queries/readings.py — Sensor reading queries (temperature only).

Uses execute_write / execute_read from connection.py so the shared
connection is never closed and no connection-per-call overhead occurs.
"""

from database.connection import execute_write, execute_read
from utils.logger import get_logger

logger = get_logger(__name__)


def insert_reading(
    temperature: float,
    timestamp: str,
    is_valid: bool = True,
) -> int:
    """Insert a sensor reading. Returns the new row id, or -1 on failure."""
    try:
        cur = execute_write(
            "INSERT INTO readings (temperature, timestamp, is_valid) "
            "VALUES (?, ?, ?)",
            (temperature, timestamp, int(is_valid)),
        )
        return cur.lastrowid
    except Exception as exc:
        logger.error("insert_reading failed: %s", exc)
        return -1


def get_recent_readings(limit: int = 60) -> list:
    """Return the most recent `limit` readings, oldest first."""
    try:
        rows = execute_read(
            "SELECT * FROM readings ORDER BY id DESC LIMIT ?", (limit,)
        )
        return list(reversed(rows))
    except Exception as exc:
        logger.error("get_recent_readings failed: %s", exc)
        return []
