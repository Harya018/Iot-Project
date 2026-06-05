"""
modules/sms/gammu_sender.py — Send SMS via USB GSM modem using Gammu.

Requires the `python-gammu` package (Windows) or `gammu` package (Linux/macOS).
The modem must be connected via USB and the COM port configured in .env.

Requirements:
    pip install python-gammu          # Windows
    pip install gammu                 # Linux/macOS

    Windows driver: install Gammu from https://wammu.eu/download/gammu/
    Linux: apt install python3-gammu  (or pip install gammu)

Configure in .env:
    SMS_GAMMU_PORT=COM3               # Windows: COM3, COM4 etc.
                                      # Linux:   /dev/ttyUSB0, /dev/ttyACM0
    SMS_GAMMU_BAUD=9600               # 9600 is standard for most modems

If gammu is not installed, all calls log a clear install instruction and return False.
Never raises exceptions — always returns bool.
"""

from __future__ import annotations

from config import SMS_GAMMU_PORT, SMS_GAMMU_BAUD, MODULE_STATUS
from utils.logger import get_logger

logger = get_logger("sms.gammu_sender")


def send_sms_gammu(phone_number: str, message: str) -> bool:
    """
    Send an SMS via USB GSM modem using the Gammu state machine.

    Flow:
      1. Import gammu (fail fast with install instructions if missing)
      2. Configure state machine with port + baud from config
      3. Init (connect to modem)
      4. Send message
      5. Terminate (always, even on error)
      6. Update MODULE_STATUS on success

    Parameters
    ----------
    phone_number : str
        Destination number. Use E.164 format (+91...) for best reliability.
    message : str
        Plain-text SMS body. Must be under 160 chars.

    Returns
    -------
    bool
        True on success, False on any failure.
    """
    # ── Step 1: Import gammu ──────────────────────────────────────────────────
    try:
        import gammu  # type: ignore
    except ImportError:
        logger.error(
            "gammu package not installed. Install with: "
            "pip install python-gammu  (Windows) or  pip install gammu  (Linux/macOS). "
            "Then restart the server."
        )
        MODULE_STATUS["sms"] = "error: gammu not installed"
        return False

    sm = None
    try:
        # ── Step 2: Configure state machine ──────────────────────────────────
        sm = gammu.StateMachine()
        sm.SetConfig(0, {
            "Device":     SMS_GAMMU_PORT,
            "Connection": "at",
            "BaudRate":   str(SMS_GAMMU_BAUD),
        })
        logger.debug(
            "Gammu configured: port=%s baud=%d", SMS_GAMMU_PORT, SMS_GAMMU_BAUD
        )

        # ── Step 3: Connect to modem ──────────────────────────────────────────
        try:
            sm.Init()
            logger.debug("Gammu modem connected on %s", SMS_GAMMU_PORT)
        except Exception as exc:
            logger.error(
                "Cannot connect to GSM modem on port %s. "
                "Check: modem is plugged in, correct port in SMS_GAMMU_PORT, "
                "driver installed. Error: %s",
                SMS_GAMMU_PORT, exc,
            )
            MODULE_STATUS["sms"] = f"error: no modem on {SMS_GAMMU_PORT}"
            return False

        # ── Step 4: Send SMS ──────────────────────────────────────────────────
        sms_payload = {
            "Text":   message,
            "SMSC":   {"Location": 1},
            "Number": phone_number,
        }
        try:
            sm.SendSMS(sms_payload)
            logger.info(
                "SMS sent via Gammu to %s (port=%s)", phone_number, SMS_GAMMU_PORT
            )
            MODULE_STATUS["sms"] = "ok -- gammu"
            return True

        except gammu.GSMError as exc:  # type: ignore[attr-defined]
            logger.error(
                "GSM modem error sending to %s: %s", phone_number, exc
            )
            MODULE_STATUS["sms"] = "error: gsm send failed"
            return False

    except Exception as exc:
        logger.error("send_sms_gammu unexpected error: %s", exc)
        MODULE_STATUS["sms"] = f"error: {str(exc)[:50]}"
        return False

    finally:
        # ── Step 5: Always disconnect ─────────────────────────────────────────
        if sm is not None:
            try:
                sm.Terminate()
                logger.debug("Gammu modem disconnected.")
            except Exception:
                pass  # Never let cleanup raise
