"""
modules/sms/adb_sender.py — Send SMS via Android phone over ADB (USB).

Uses the Android service call isms method to send real SMS messages
through a USB-connected Android phone with USB debugging enabled.

Falls back to an intent-based method if the service call fails.

Requirements:
    - Android SDK Platform Tools installed and `adb` on PATH
    - Android phone connected via USB with USB debugging enabled
    - Phone shown as "device" in `adb devices`

No pip packages required — uses only stdlib subprocess.
"""

from __future__ import annotations

import subprocess
from typing import Optional

from config import SMS_ADB_SERIAL, MODULE_STATUS
from utils.logger import get_logger

logger = get_logger("sms.adb_sender")

_TIMEOUT = 15  # seconds per ADB command


def _adb_base() -> list[str]:
    """Return base ADB command with optional -s <serial> flag."""
    cmd = ["adb"]
    if SMS_ADB_SERIAL.strip():
        cmd += ["-s", SMS_ADB_SERIAL.strip()]
    return cmd


def _check_adb_available() -> bool:
    """Return True if `adb` is installed and on PATH."""
    try:
        result = subprocess.run(
            ["adb", "version"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            logger.debug("ADB found: %s", result.stdout.splitlines()[0] if result.stdout else "")
            return True
        logger.error("ADB returned non-zero exit code: %d", result.returncode)
        return False
    except FileNotFoundError:
        logger.error(
            "ADB not found in PATH. Install Android SDK Platform Tools and add to PATH. "
            "Download: https://developer.android.com/tools/releases/platform-tools"
        )
        return False
    except subprocess.TimeoutExpired:
        logger.error("ADB version check timed out.")
        return False
    except Exception as exc:
        logger.error("ADB availability check failed: %s", exc)
        return False


def _check_device_connected() -> bool:
    """Return True if at least one Android device is connected and authorised."""
    try:
        result = subprocess.run(
            _adb_base() + ["devices"],
            capture_output=True, text=True, timeout=10,
        )
        lines = result.stdout.strip().splitlines()
        # Lines format: "<serial>\tdevice"  or "<serial>\tunauthorized"
        connected = [
            line for line in lines[1:]  # skip "List of devices attached" header
            if line.strip() and line.strip().endswith("device")
        ]
        if connected:
            logger.debug("ADB device(s) connected: %s", connected)
            return True
        unauthorized = [l for l in lines[1:] if "unauthorized" in l]
        if unauthorized:
            logger.error(
                "ADB device found but UNAUTHORIZED. "
                "Accept the 'Allow USB debugging' dialog on the phone. "
                "Found: %s", unauthorized,
            )
        else:
            logger.error(
                "No ADB device connected. "
                "Plug in Android phone with USB debugging enabled and run: adb devices"
            )
        return False
    except Exception as exc:
        logger.error("ADB device check failed: %s", exc)
        return False


def _send_via_service_call(phone_number: str, message: str) -> bool:
    """
    Send SMS using Android's isms service call (method 7).

    This invokes the SMS service directly — no UI, fully background.
    Works on most Android versions 4.4+ without root.
    """
    # Escape message for shell safety — replace double quotes
    safe_msg = message.replace("'", "\\'").replace("\n", " ")

    shell_cmd = (
        f"service call isms 7 i32 0 s16 com.android.mms "
        f"s16 '{phone_number}' s16 'null' s16 '{safe_msg}' s16 'null' s16 'null'"
    )
    cmd = _adb_base() + ["shell", shell_cmd]
    cmd = _adb_base() + [
        "shell",
        "service", "call", "isms", "7",
        "i32", "0",
        "s16", "com.android.mms",
        "s16", phone_number,
        "s16", "null",
        "s16", safe_msg,
        "s16", "null",
        "s16", "null",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_TIMEOUT,
        )
        if result.returncode == 0:
            logger.info("SMS sent via ADB service call to %s", phone_number)
            return True
        logger.warning(
            "ADB service call returned code %d. stderr: %s",
            result.returncode, result.stderr[:200],
        )
        return False
    except subprocess.TimeoutExpired:
        logger.error("ADB service call timed out after %ds", _TIMEOUT)
        return False
    except Exception as exc:
        logger.error("ADB service call exception: %s", exc)
        return False


def _send_via_intent(phone_number: str, message: str) -> bool:
    """
    Fallback: send SMS using Android Intent (am start SENDTO).

    Opens the SMS app with the message pre-filled and exit_on_sent=true.
    Less reliable than service call but works as a fallback.
    """
    safe_msg = message.replace("'", "\\'").replace("\n", " ")

    shell_cmd = (
        f"am start -a android.intent.action.SENDTO "
        f"-d sms:{phone_number} "
        f"--es sms_body '{safe_msg}' "
        f"--ez exit_on_sent true"
    )
    cmd = _adb_base() + ["shell", shell_cmd]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_TIMEOUT,
        )
        if result.returncode == 0:
            logger.info("SMS sent via ADB intent fallback to %s", phone_number)
            return True
        logger.error(
            "ADB intent fallback failed (code %d). stderr: %s",
            result.returncode, result.stderr[:200],
        )
        return False
    except subprocess.TimeoutExpired:
        logger.error("ADB intent fallback timed out after %ds", _TIMEOUT)
        return False
    except Exception as exc:
        logger.error("ADB intent fallback exception: %s", exc)
        return False


def send_sms_adb(phone_number: str, message: str) -> bool:
    """
    Send an SMS to `phone_number` via USB-connected Android phone.

    Flow:
      1. Check ADB is installed
      2. Check device is connected and authorised
      3. Try service call method (background, silent)
      4. If that fails, try intent fallback
      5. Update MODULE_STATUS on first success

    Parameters
    ----------
    phone_number : str
        Destination phone number (any format — passed directly to Android).
    message : str
        Plain-text SMS body. Must be under 160 chars.

    Returns
    -------
    bool
        True on success, False on any failure.
    """
    try:
        # Step 1: ADB installed?
        if not _check_adb_available():
            MODULE_STATUS["sms"] = "error: adb not found"
            return False

        # Step 2: Device connected?
        if not _check_device_connected():
            MODULE_STATUS["sms"] = "error: no device"
            return False

        # Step 3: Primary method — service call
        if _send_via_service_call(phone_number, message):
            MODULE_STATUS["sms"] = "ok -- adb"
            return True

        # Step 4: Fallback — intent
        logger.warning("Service call failed — trying intent fallback...")
        if _send_via_intent(phone_number, message):
            MODULE_STATUS["sms"] = "ok -- adb"
            return True

        MODULE_STATUS["sms"] = "error: send failed"
        return False

    except Exception as exc:
        logger.error("send_sms_adb unexpected error: %s", exc)
        MODULE_STATUS["sms"] = f"error: {str(exc)[:50]}"
        return False
