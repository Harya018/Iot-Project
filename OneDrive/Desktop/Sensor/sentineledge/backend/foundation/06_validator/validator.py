"""
core/validator.py — Sensor reading validator (Addition 3).

Validates every reading from the sensor before it is processed.
Checks for:
  1. Required fields present
  2. No null / None values
  3. Temperature within physically valid range
  4. Humidity within physically valid range
  5. Timestamp is a valid ISO-8601 string
  6. Temperature spike vs previous reading
  7. Humidity spike vs previous reading
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("sentineledge.validator")

# ─── Physical valid ranges ────────────────────────────────────────────────────
VALID_RANGES = {
    "temperature": (-50.0, 150.0),
    "humidity": (0.0, 100.0),
}

# ─── Maximum allowed change per second ───────────────────────────────────────
MAX_SPIKE_PER_SECOND = {
    "temperature": 10.0,
    "humidity": 20.0,
}


class ReadingValidator:
    """Stateful validator that tracks the previous reading for spike detection."""

    def __init__(self) -> None:
        self.prev_reading: Optional[dict] = None

    def validate(self, reading: dict) -> tuple[bool, str]:
        """
        Validate a sensor reading.

        Parameters
        ----------
        reading : dict
            Must contain 'temperature', 'humidity', 'timestamp'.

        Returns
        -------
        tuple[bool, str]
            (True, "") if valid.
            (False, "reason string") if invalid.
        """
        # Check 1: required fields present
        for field in ("temperature", "humidity", "timestamp"):
            if field not in reading:
                self._update_prev(reading)
                return False, f"missing field: {field}"

        # Check 2: no null values
        for field in ("temperature", "humidity", "timestamp"):
            if reading[field] is None:
                self._update_prev(reading)
                return False, f"null value for field: {field}"

        temp = reading["temperature"]
        hum = reading["humidity"]

        # Check 3: temperature in valid range
        t_min, t_max = VALID_RANGES["temperature"]
        if not (t_min <= temp <= t_max):
            self._update_prev(reading)
            return False, f"temperature {temp} out of range [{t_min}, {t_max}]"

        # Check 4: humidity in valid range
        h_min, h_max = VALID_RANGES["humidity"]
        if not (h_min <= hum <= h_max):
            self._update_prev(reading)
            return False, f"humidity {hum} out of range [{h_min}, {h_max}]"

        # Check 5: timestamp is a valid ISO string
        try:
            datetime.fromisoformat(reading["timestamp"])
        except (ValueError, TypeError) as exc:
            self._update_prev(reading)
            return False, f"invalid timestamp: {reading['timestamp']!r}"

        # Spike checks (only when we have a previous reading)
        if self.prev_reading is not None:
            prev_temp = self.prev_reading.get("temperature")
            prev_hum = self.prev_reading.get("humidity")

            # Check 6: temperature spike
            if prev_temp is not None:
                if abs(temp - prev_temp) > MAX_SPIKE_PER_SECOND["temperature"]:
                    self._update_prev(reading)
                    return (
                        False,
                        f"temperature spike: {prev_temp} -> {temp} "
                        f"(max {MAX_SPIKE_PER_SECOND['temperature']}/s)",
                    )

            # Check 7: humidity spike
            if prev_hum is not None:
                if abs(hum - prev_hum) > MAX_SPIKE_PER_SECOND["humidity"]:
                    self._update_prev(reading)
                    return (
                        False,
                        f"humidity spike: {prev_hum} -> {hum} "
                        f"(max {MAX_SPIKE_PER_SECOND['humidity']}/s)",
                    )

        self._update_prev(reading)
        return True, ""

    def _update_prev(self, reading: dict) -> None:
        """Store current reading as previous for next spike check."""
        self.prev_reading = reading


# ─── Module-level singleton ───────────────────────────────────────────────────
validator = ReadingValidator()


def validate_reading(reading: dict) -> tuple[bool, str]:
    """Validate a sensor reading using the module singleton."""
    return validator.validate(reading)
