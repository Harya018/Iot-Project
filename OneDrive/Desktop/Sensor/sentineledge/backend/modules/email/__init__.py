"""backend/modules/email — Email notification channel."""

from modules.email.smtp import send_email, send_email_async
from modules.email.templates import format_alert_message

__all__ = ["send_email", "send_email_async", "format_alert_message"]
