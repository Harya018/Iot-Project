"""
tests/test_sensor.py — Unit tests for core.sensor module.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from core.sensor import get_reading, set_breach_override


def test_get_reading_keys():
    reading = get_reading()
    assert "temperature" in reading
    assert "humidity" in reading
    assert "timestamp" in reading


def test_get_reading_types():
    reading = get_reading()
    assert isinstance(reading["temperature"], float)
    assert isinstance(reading["humidity"], float)
    assert isinstance(reading["timestamp"], str)


def test_temperature_range():
    for _ in range(20):
        reading = get_reading()
        assert 15.0 <= reading["temperature"] <= 50.0


def test_humidity_range():
    for _ in range(20):
        reading = get_reading()
        assert 20.0 <= reading["humidity"] <= 95.0


def test_breach_override():
    set_breach_override(3)
    for _ in range(3):
        reading = get_reading()
        assert reading["temperature"] == 42.0
    # After 3 ticks, override should be exhausted
    reading = get_reading()
    assert reading["temperature"] != 42.0
