"""
modules/sms/adb_sender.py — Send SMS via Termux HTTP server running on the phone.

Mechanism:
    A tiny Python HTTP server runs inside Termux on the Android phone (port 8765).
    This sender POSTs {"phone": "...", "message": "..."} to it over LAN.
    Termux receives the request and calls `termux-sms-send` directly.

    This replaces the old file-based ADB approach which broke on newer Android versions.

Requirements:
    - Android phone on the same LAN as the server (WiFi)
    - Termux installed with termux-api add-on
    - Termux HTTP server running on the phone (see setup below)

One-time setup on phone (run inside Termux):
    pkg install python termux-api
    Then start the server:
    python -c "
import http.server, subprocess, json

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(length))
        subprocess.run(['termux-sms-send', '-n', data['phone'], data['message']])
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *a): pass

http.server.HTTPServer(('0.0.0.0', 8765), H).serve_forever()
"

No ADB USB connection required at runtime — phone just needs to be on WiFi.
"""

from __future__ import annotations

import urllib.request
import urllib.error
import json

from config import MODULE_STATUS
from utils.logger import get_logger

logger = get_logger("sms.adb_sender")

# ── Configuration ─────────────────────────────────────────────────────────────
TERMUX_SMS_HOST = "192.168.1.4"   # Phone's LAN IP — update if it changes
TERMUX_SMS_PORT = 8765
TERMUX_SMS_URL  = f"http://{TERMUX_SMS_HOST}:{TERMUX_SMS_PORT}"
REQUEST_TIMEOUT = 15              # seconds


def send_sms_adb(phone_number: str, message: str) -> bool:
    """
    Send an SMS by POSTing to the Termux HTTP server running on the phone.

    Parameters
    ----------
    phone_number : str
        Destination phone number (e.g. "8778124338" or "+918778124338").
    message : str
        Plain-text SMS body. Keep under 160 chars for single SMS.

    Returns
    -------
    bool
        True on success, False on any failure.
    """
    try:
        payload = json.dumps({
            "phone":   phone_number,
            "message": message,
        }).encode("utf-8")

        req = urllib.request.Request(
            TERMUX_SMS_URL,
            data    = payload,
            headers = {"Content-Type": "application/json"},
            method  = "POST",
        )

        logger.info(
            "Sending SMS via Termux HTTP to %s (%d chars)",
            phone_number, len(message),
        )

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read().decode().strip()
            if resp.status == 200 and body == "OK":
                logger.info("SMS sent to %s via Termux HTTP", phone_number)
                MODULE_STATUS["sms"] = "ok -- termux-http"
                return True
            else:
                logger.error(
                    "Termux HTTP server returned unexpected response: status=%d body=%s",
                    resp.status, body,
                )
                MODULE_STATUS["sms"] = f"error: unexpected response {resp.status}"
                return False

    except urllib.error.URLError as exc:
        logger.error(
            "Cannot reach Termux SMS server at %s — is the server running on the phone? Error: %s",
            TERMUX_SMS_URL, exc.reason,
        )
        MODULE_STATUS["sms"] = "error: termux server unreachable"
        return False

    except TimeoutError:
        logger.error(
            "Termux SMS server timed out after %ds (phone: %s)",
            REQUEST_TIMEOUT, TERMUX_SMS_HOST,
        )
        MODULE_STATUS["sms"] = "error: termux timeout"
        return False

    except Exception as exc:
        logger.error("send_sms_adb unexpected error: %s", exc)
        MODULE_STATUS["sms"] = f"error: {str(exc)[:50]}"
        return False