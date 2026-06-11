"""backend/modules/email — Email notification channel."""

from modules.email.smtp import (
    send_email,
    send_email_async,
    send_alert_email,
    send_alert_email_async,
    send_alert_email_to_all,
)
from modules.email.templates import format_alert_message

__all__ = [
    "send_email",
    "send_email_async",
    "send_alert_email",
    "send_alert_email_async",
    "send_alert_email_to_all",
    "format_alert_message",
]
