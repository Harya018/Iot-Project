"""
modules/email/smtp.py — SMTP email sender.

Extracted from the original notifier.py (send_email / send_email_async).
Uses smtplib with STARTTLS — no external libraries required.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.text import MIMEText

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

logger = logging.getLogger("sentineledge.email.smtp")


def send_email(to_address: str, subject: str, body: str) -> bool:
    """
    Send a plain-text email using smtplib with STARTTLS.

    Returns True on success, False on any failure (logs the error).
    Never raises.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — email skipped.")
        return False

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_address

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [to_address], msg.as_string())

        logger.info("Email sent to %s — subject: %s", to_address, subject)
        return True
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("SMTP authentication failed: %s", exc)
        return False
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending to %s: %s", to_address, exc)
        return False
    except Exception as exc:
        logger.exception("Unexpected error sending email to %s: %s", to_address, exc)
        return False


async def send_email_async(to_address: str, subject: str, body: str) -> bool:
    """Async wrapper around send_email() using a thread-pool executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, send_email, to_address, subject, body)
