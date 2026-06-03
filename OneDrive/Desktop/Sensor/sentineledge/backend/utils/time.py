"""
utils/time.py — UTC timestamp helpers for SentinelEdge.

Rules:
- All times stored as UTC ISO 8601 strings in the database.
- All times returned as UTC ISO 8601 strings by the API.
- Display conversion to local timezone (IST = UTC+5:30) 
  happens in the frontend only, never in the backend.
"""

from datetime import datetime, timezone, timedelta
from typing import Union


# IST is UTC + 5 hours 30 minutes (for reference only — never used in backend)
_IST_OFFSET = timedelta(hours=5, minutes=30)


def now_iso() -> str:
    """
    Return current UTC datetime as ISO 8601 string.

    Example: "2026-06-02T10:45:00.123456+00:00"
    """
    return datetime.now(timezone.utc).isoformat()


def now_plus_seconds(seconds: int) -> str:
    """
    Return UTC now + N seconds as ISO 8601 string.

    Used for cooldown_until calculation.
    """
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def parse_iso(iso_string: str) -> datetime:
    """
    Parse an ISO 8601 string to a timezone-aware datetime object.

    Handles both timezone-aware ("2026-06-02T10:00:00+00:00")
    and naive ("2026-06-02T10:00:00") inputs.
    Naive strings are assumed to be UTC.
    """
    if iso_string is None:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(iso_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def seconds_since(iso_string: str) -> float:
    """
    Return how many seconds have passed since the given ISO timestamp.

    Returns 0.0 if the timestamp is in the future.
    """
    try:
        then = parse_iso(iso_string)
        delta = (datetime.now(timezone.utc) - then).total_seconds()
        return max(0.0, delta)
    except Exception:
        return 0.0


def format_duration(seconds: int) -> str:
    """
    Return a human-readable duration string.

    Examples:
        45    → "45s"
        90    → "1m 30s"
        3720  → "1h 2m"
        86400 → "24h 0m"
    """
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {secs}s"


def seconds_until_midnight() -> float:
    """
    Return seconds until the next UTC midnight.

    Used by the daily report and backup schedulers.
    """
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return (tomorrow - now).total_seconds()


def today_date_str() -> str:
    """
    Return today's date as "YYYY-MM-DD" string (UTC).

    Used for daily stats database queries.
    """
    return datetime.now(timezone.utc).date().isoformat()
