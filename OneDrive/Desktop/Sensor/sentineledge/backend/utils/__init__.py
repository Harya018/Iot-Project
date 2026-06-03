"""
utils/__init__.py — SentinelEdge utils package.

Re-exports the most commonly used helpers for convenient access.

Usage:
    from utils import get_logger, now_iso, sanitise_log_data
"""

from utils.logger import get_logger, sanitise_log_data
from utils.time import now_iso, now_plus_seconds, parse_iso, seconds_since, format_duration, seconds_until_midnight, today_date_str
from utils.errors import (
    SentinelEdgeError, DatabaseError, SensorError,
    ThresholdConfigError, ValidationError, ConfigurationError,
    ModuleDeliveryError, EmailDeliveryError, SMSDeliveryError,
    AuthenticationError, RateLimitError, NotFoundError,
)

__all__ = [
    "get_logger", "sanitise_log_data",
    "now_iso", "now_plus_seconds", "parse_iso",
    "seconds_since", "format_duration",
    "seconds_until_midnight", "today_date_str",
    "SentinelEdgeError", "DatabaseError", "SensorError",
    "ThresholdConfigError", "ValidationError", "ConfigurationError",
    "ModuleDeliveryError", "EmailDeliveryError", "SMSDeliveryError",
    "AuthenticationError", "RateLimitError", "NotFoundError",
]
