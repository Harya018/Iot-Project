"""
database/queries/readings.py — Sensor reading queries.
Addition 3: insert_reading accepts is_valid flag.
"""

import logging
from database.connection import get_connection

logger = logging.getLogger("sentineledge.database")


def insert_reading(
    temperature: float,
    humidity: float,
    timestamp: str,
    is_valid: bool = True,
) -> int:
    """Insert a sensor reading and return its row id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO readings (temperature, humidity, timestamp, is_valid) VALUES (?, ?, ?, ?)",
            (temperature, humidity, timestamp, int(is_valid)),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as exc:
        logger.exception("insert_reading failed: %s", exc)
        return -1
    finally:
        conn.close()


def get_recent_readings(limit: int = 60) -> list:
    """Return the most recent `limit` readings, newest last."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM readings ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
    except Exception as exc:
        logger.exception("get_recent_readings failed: %s", exc)
        return []
    finally:
        conn.close()
