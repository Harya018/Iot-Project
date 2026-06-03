"""
tests/test_threshold.py — Unit tests for core.threshold module.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Patch RUNTIME_THRESHOLDS for deterministic tests
import config
config.RUNTIME_THRESHOLDS = {
    "temp_high": 38.0,
    "temp_low": 22.0,
    "humidity_high": 80.0,
    "humidity_low": 35.0,
}
config.ALERT_COOLDOWN_SECONDS = 0  # disable cooldown for tests

from core.threshold import check_threshold, cooldown_tracker


def _clear_cooldown():
    cooldown_tracker.clear()


def test_no_breach_within_range():
    _clear_cooldown()
    reading = {"temperature": 25.0, "humidity": 55.0}
    result = check_threshold(reading)
    assert result == []


def test_temp_high_breach():
    _clear_cooldown()
    reading = {"temperature": 40.0, "humidity": 55.0}
    result = check_threshold(reading)
    assert any(b.parameter == "temperature" and b.direction == "high" for b in result)


def test_temp_low_breach():
    _clear_cooldown()
    reading = {"temperature": 18.0, "humidity": 55.0}
    result = check_threshold(reading)
    assert any(b.parameter == "temperature" and b.direction == "low" for b in result)


def test_humidity_high_breach():
    _clear_cooldown()
    reading = {"temperature": 25.0, "humidity": 90.0}
    result = check_threshold(reading)
    assert any(b.parameter == "humidity" and b.direction == "high" for b in result)


def test_humidity_low_breach():
    _clear_cooldown()
    reading = {"temperature": 25.0, "humidity": 20.0}
    result = check_threshold(reading)
    assert any(b.parameter == "humidity" and b.direction == "low" for b in result)
