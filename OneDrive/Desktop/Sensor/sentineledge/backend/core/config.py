"""
core/config.py — Production config re-export.

Imports everything from the canonical config.py at backend root so that
production code can use:
    from core.config import APP_ENV, RUNTIME_THRESHOLDS, ...

This keeps core/ as the single import source for all modules.
"""

from config import (  # noqa: F401
    APP_ENV,
    APP_VERSION,
    TEMP_THRESHOLD_HIGH,
    TEMP_THRESHOLD_LOW,
    ALERT_COOLDOWN_SECONDS,
    ESCALATION_TIMEOUT_SECONDS,
    DEMO_ESCALATION_TIMEOUT,
    SERVER_HOST,
    SERVER_PORT,
    DEMO_MODE,
    ADMIN_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMS_GATEWAY_URL,
    SMS_GATEWAY_USER,
    SMS_GATEWAY_PASS,
    RUNTIME_THRESHOLDS,
    RUNTIME_SOURCE,
    MODULE_STATUS,
    CONNECTED_CLIENTS,
    SERVER_START_TIME,
)
