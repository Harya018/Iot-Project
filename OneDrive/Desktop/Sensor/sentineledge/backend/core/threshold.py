"""
core/threshold.py — SentinelEdge threshold checker (temperature only).

check_threshold() inspects a sensor reading against RUNTIME_THRESHOLDS
and returns a list of BreachEvent objects for any exceeded thresholds,
respecting per-direction cooldown windows.

BREACH BOUNDARY (strict):
  temperature > 40.0  → high breach  (exactly 40.0 is NOT a breach)
  temperature < 35.0  → low breach   (exactly 35.0 is NOT a breach)

Severity levels:
  WARNING   — value within 0-10% beyond threshold
  CRITICAL  — value within 10-25% beyond threshold
  EMERGENCY — value more than 25% beyond threshold

Cooldown is tracked per direction (high / low) independently.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from config import RUNTIME_THRESHOLDS, ALERT_COOLDOWN_SECONDS, MODULE_STATUS
from models import BreachEvent

# ─── Severity bands ───────────────────────────────────────────────────────────
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


# ─── Cooldown tracker: keyed by direction ─────────────────────────────────────
cooldown_tracker: dict[str, datetime | None] = {
    "temperature_high": None,
    "temperature_low":  None,
}


def check_threshold(reading: dict) -> list[BreachEvent]:
    """
    Compare a reading against current RUNTIME_THRESHOLDS (temperature only).

    Parameters
    ----------
    reading : dict
        Must contain 'temperature' (float).

    Returns
    -------
    list[BreachEvent]
        One entry per threshold currently breached and not in cooldown.
        Returns an empty list when no threshold is breached.
    """
    now = datetime.now(timezone.utc)
    cooldown_delta = timedelta(seconds=ALERT_COOLDOWN_SECONDS)
    breaches: list[BreachEvent] = []

    checks = [
        ("temperature", reading["temperature"], RUNTIME_THRESHOLDS["temp_high"], "high"),
        ("temperature", reading["temperature"], RUNTIME_THRESHOLDS["temp_low"],  "low"),
    ]

    for parameter, value, threshold, direction in checks:
        # STRICT boundary: exactly at threshold is NOT a breach
        if direction == "high" and value <= threshold:   # need value > threshold
            continue
        if direction == "low"  and value >= threshold:   # need value < threshold
            continue

        # Unique key per direction
        key = f"{parameter}_{direction}"
        last_trigger = cooldown_tracker.get(key)

        if last_trigger is not None and (now - last_trigger) < cooldown_delta:
            # Still within cooldown window — skip without creating an alert
            continue

        # Compute severity
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
