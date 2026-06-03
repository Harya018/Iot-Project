"""
utils/errors.py — SentinelEdge custom exception hierarchy.

Every module catches raw exceptions and re-raises as these.
The global FastAPI error handler in main.py converts them to
structured JSON responses automatically.

Usage:
    from utils.errors import DatabaseError
    raise DatabaseError("Insert failed", details=str(exc))
"""


class SentinelEdgeError(Exception):
    """Base class for all SentinelEdge application errors."""

    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class DatabaseError(SentinelEdgeError):
    """Raised when a database operation fails unrecoverably."""


class SensorError(SentinelEdgeError):
    """Raised when the sensor cannot produce a valid reading."""


class ThresholdConfigError(SentinelEdgeError):
    """Raised when threshold configuration is invalid or inconsistent."""


class ValidationError(SentinelEdgeError):
    """Raised when a sensor reading fails validation checks."""


class ConfigurationError(SentinelEdgeError):
    """Raised when required configuration is missing or invalid."""


class ModuleDeliveryError(SentinelEdgeError):
    """Base class for notification channel delivery failures."""

    def __init__(self, module: str, message: str, details: str = None):
        super().__init__(message, details)
        self.module = module

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["module"] = self.module
        return d


class EmailDeliveryError(ModuleDeliveryError):
    """Raised when the email channel fails to deliver."""

    def __init__(self, message: str, details: str = None):
        super().__init__("email", message, details)


class SMSDeliveryError(ModuleDeliveryError):
    """Raised when the SMS channel fails to deliver."""

    def __init__(self, message: str, details: str = None):
        super().__init__("sms", message, details)


class AuthenticationError(SentinelEdgeError):
    """Raised when admin authentication fails."""


class RateLimitError(SentinelEdgeError):
    """Raised when a client exceeds the allowed request rate."""


class NotFoundError(SentinelEdgeError):
    """Raised when a requested resource does not exist."""
