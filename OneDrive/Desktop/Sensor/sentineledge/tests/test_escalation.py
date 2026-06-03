"""
tests/test_escalation.py — Integration-level tests for core.escalation module.
Uses an in-memory SQLite database to avoid touching the real database.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import asyncio
import pytest

import config
config.ESCALATION_TIMEOUT_SECONDS = 0  # instant escalation for tests
config.ALERT_COOLDOWN_SECONDS = 0

import database
import core.escalation as escalation
from models import BreachEvent


def test_format_escalation_message_level1():
    msg = escalation.format_escalation_message(
        "temperature", 40.0, 38.0, "high", 1, "Alice"
    )
    assert "ALERT" in msg
    assert "acknowledge" in msg.lower()


def test_format_escalation_message_level2():
    msg = escalation.format_escalation_message(
        "temperature", 40.0, 38.0, "high", 2, "Bob", prev_name="Alice"
    )
    assert "ESCALATION" in msg
    assert "Alice" in msg


def test_format_escalation_message_level3():
    msg = escalation.format_escalation_message(
        "humidity", 90.0, 80.0, "high", 3, "Charlie", prev_name="Bob"
    )
    assert "CRITICAL" in msg
