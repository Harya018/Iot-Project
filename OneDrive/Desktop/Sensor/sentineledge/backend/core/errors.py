"""
core/errors.py — SentinelEdge custom exception hierarchy.

All application-specific exceptions inherit from SentinelEdgeError so
callers can catch them with a single except clause.
"""


class SentinelEdgeError(Exception):
    """Base class for all SentinelEdge application errors."""


class ConfigError(SentinelEdgeError):
    """Raised when configuration is missing or invalid."""


class DatabaseError(SentinelEdgeError):
    """Raised when a database operation fails unrecoverably."""


class ValidationError(SentinelEdgeError):
    """Raised when a sensor reading fails validation."""


class ThresholdError(SentinelEdgeError):
    """Raised when threshold configuration is invalid."""


class NotificationError(SentinelEdgeError):
    """Raised when all notification channels fail for an alert."""


class EscalationError(SentinelEdgeError):
    """Raised when the escalation engine encounters an unrecoverable state."""
