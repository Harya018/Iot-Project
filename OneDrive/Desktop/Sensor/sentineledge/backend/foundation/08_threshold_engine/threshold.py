"""
core/threshold.py — SentinelEdge threshold checker.

check_threshold() inspects a sensor reading against RUNTIME_THRESHOLDS
and returns a list of BreachEvent objects for any exceeded thresholds,
respecting per-parameter-per-direction cooldown windows (Addition 7).

Addition 2: each breach is tagged with a severity level:
  WARNING   — value within 0-10% beyond threshold
  CRITICAL  — value within 10-25% beyond threshold
  EMERGENCY — value more than 25% beyond threshold

Addition 7: cooldown is tracked per parameter AND per direction
independently, so temperature_high and temperature_low never block
each other.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from config import RUNTIME_THRESHOLDS, ALERT_COOLDOWN_SECONDS, MODULE_STATUS
from models import BreachEvent

# ─── Severity bands (Addition 2) ──────────────────────────────────────────────
_WARNING_PCT: float = 0.05
_CRITICAL_PCT: float = 0.10
_EMERGENCY_PCT: float = 0.25


def _get_severity(value: float, threshold: float, direction: str) -> str:
    """
    Compute breach severity based on how far the value exceeds the threshold.

    Returns "WARNING", "CRITICAL", or "EMERGENCY".
    """
    if threshold == 0:
        return "WARNING"
    if direction == "high":
        pct = (value - threshold) / abs(threshold)
    else:
        pct = (threshold - value) / abs(threshold)

    if pct >= _EMERGENCY_PCT:
        return "EMERGENCY"
    elif pct >= _CRITICAL_PCT:
        return "CRITICAL"
    else:
        return "WARNING"


# ─── Cooldown tracker: keyed by "parameter_direction" (Addition 7) ────────────
# Each parameter+direction combination has its own independent cooldown.
cooldown_tracker: dict[str, datetime | None] = {
    "temperature_high": None,
    "temperature_low": None,
    "humidity_high": None,
    "humidity_low": None,
}


def check_threshold(reading: dict) -> list[BreachEvent]:
    """
    Compare a reading against current RUNTIME_THRESHOLDS.

    Parameters
    ----------
    reading : dict
        Must contain 'temperature' (float) and 'humidity' (float).

    Returns
    -------
    list[BreachEvent]
        One entry per threshold currently breached and not in cooldown.
        Each breach includes a severity field (Addition 2).
        Returns an empty list when no threshold is breached.
    """
    now = datetime.now(timezone.utc)
    cooldown_delta = timedelta(seconds=ALERT_COOLDOWN_SECONDS)
    breaches: list[BreachEvent] = []

    checks = [
        ("temperature", reading["temperature"], RUNTIME_THRESHOLDS["temp_high"], "high"),
        ("temperature", reading["temperature"], RUNTIME_THRESHOLDS["temp_low"], "low"),
        ("humidity", reading["humidity"], RUNTIME_THRESHOLDS["humidity_high"], "high"),
        ("humidity", reading["humidity"], RUNTIME_THRESHOLDS["humidity_low"], "low"),
    ]

    for parameter, value, threshold, direction in checks:
        # Determine if this reading actually breaches the threshold
        if direction == "high" and value <= threshold:
            continue
        if direction == "low" and value >= threshold:
            continue

        # Unique key per parameter+direction combination (Addition 7)
        key = f"{parameter}_{direction}"
        last_trigger = cooldown_tracker.get(key)

        if last_trigger is not None and (now - last_trigger) < cooldown_delta:
            # Still within cooldown window — skip without creating an alert
            continue

        # Compute severity (Addition 2)
        severity = _get_severity(value, threshold, direction)

        # Record this trigger and add a breach event
        cooldown_tracker[key] = now
        breaches.append(
            BreachEvent(
                parameter=parameter,
                value=value,
                threshold=threshold,
                direction=direction,
                severity=severity,
            )
        )

    # Update module status once we've processed at least one reading
    if "sensor" not in MODULE_STATUS or MODULE_STATUS.get("sensor") == "starting":
        MODULE_STATUS["sensor"] = "ok"

    return breaches
