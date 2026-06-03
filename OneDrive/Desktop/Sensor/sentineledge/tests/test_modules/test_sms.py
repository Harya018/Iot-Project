"""
tests/test_modules/test_sms.py — Unit tests for modules.sms.gateway.
Tests use monkeypatching so no real SMS gateway is required.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from unittest.mock import patch, MagicMock
from modules.sms.gateway import send_sms


def test_send_sms_success():
    mock_response = MagicMock()
    mock_response.status_code = 202
    with patch("modules.sms.gateway.requests.post", return_value=mock_response):
        result = send_sms("+15551234567", "Test message")
    assert result is True


def test_send_sms_failure_status():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server error"
    with patch("modules.sms.gateway.requests.post", return_value=mock_response):
        result = send_sms("+15551234567", "Test message")
    assert result is False


def test_send_sms_connection_error():
    import requests
    with patch(
        "modules.sms.gateway.requests.post",
        side_effect=requests.exceptions.ConnectionError("unreachable"),
    ):
        result = send_sms("+15551234567", "Test message")
    assert result is False
