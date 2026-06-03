"""
modules/sms/sender.py — High-level SMS send helper.

Thin wrapper around gateway.send_sms_async that adds retry logic
and structured logging. Delegates all transport to gateway.py.
"""

from __future__ import annotations

import logging

from modules.sms.gateway import send_sms_async

logger = logging.getLogger("sentineledge.sms.sender")


async def send_alert_sms(phone_number: str, message: str, retries: int = 1) -> bool:
    """
    Send an alert SMS with optional single retry on failure.

    Parameters
    ----------
    phone_number : str
        E.164 destination number.
    message : str
        Alert message body.
    retries : int
        Number of retry attempts after initial failure (default 1).

    Returns
    -------
    bool
        True if at least one attempt succeeded.
    """
    for attempt in range(1 + retries):
        ok = await send_sms_async(phone_number, message)
        if ok:
            return True
        if attempt < retries:
            logger.warning(
                "SMS to %s failed on attempt %d — retrying...", phone_number, attempt + 1
            )
    logger.error("SMS to %s failed after %d attempt(s).", phone_number, 1 + retries)
    return False
