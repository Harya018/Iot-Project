"""
backend/foundation/03_utils/errors.py
SentinelEdge — Error formatting and reporting helpers.
Standalone copy for foundation testing.
"""

import logging
import traceback

logger = logging.getLogger("sentineledge.utils.errors")


def log_exception(context: str, exc: Exception) -> None:
    """Log an exception with full traceback at ERROR level."""
    logger.error("%s: %s\n%s", context, exc, traceback.format_exc())


def safe_call(fn, *args, default=None, context: str = ""):
    """
    Call fn(*args) and return its result.
    On any exception, log and return `default`.
    """
    try:
        return fn(*args)
    except Exception as exc:
        label = context or fn.__name__
        log_exception(label, exc)
        return default


def format_error(exc: Exception) -> dict:
    """Return a JSON-serialisable error dict for API responses."""
    return {
        "error": type(exc).__name__,
        "detail": str(exc),
    }
