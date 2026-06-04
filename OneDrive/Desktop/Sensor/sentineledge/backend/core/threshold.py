"""
core/threshold.py — SentinelEdge threshold checker (temperature only).

check_threshold() inspects a sensor reading against RUNTIME_THRESHOLDS
and returns a list of BreachEvent objects for any exceeded thresholds,
respecting per-direction cooldown windows.

BREACH BOUNDARY (strict):
  temperature > HIGH  → high breach   (exactly HIGH is NOT a breach)
  temperature < LOW   → low breach    (exactly LOW  is NOT a breach)

Severity levels:
  WARNING   — value within 0-10% beyond threshold
  CRITICAL  — value within 10-25% beyond threshold
  EMERGENCY — value more than 25% beyond threshold

Cooldown is tracked per direction (high / low) independently.

DIRECTION TRACKING (cooling-cycle logic):
  For a machine that cools from HIGH → LOW, we only want to fire the
  LOW alert once per cooling run:

  - When temperature rises back above RESET_TEMP (60°C), the LOW
    direction is "reset" so the next cooling cycle will fire again.
  - This prevents multiple LOW alerts during the same cool-down run
    while the temperature hovers just around the LOW threshold.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from config import RUNTIME_THRESHOLDS, ALERT_COOLDOWN_SECONDS, MODULE_STATUS
from models import BreachEvent

# ─── Severity bands ───────────────────────────────────────────────────────────
_WARNING_PCT: float  = 0.05
_CRITICAL_PCT: float = 0.10
_EMERGENCY_PCT: float= 0.25

# Temperature above which the LOW-direction alert is "reset" for the next run.
# When machine heats back above this after a cooling cycle,
# we know a new run has started.
_LOW_DIRECTION_RESET_TEMP: float = 60.0


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


# ─── Cooldown tracker: keyed by direction ────────────────────────────────────
cooldown_tracker: dict[str, datetime | None] = {
    "temperature_high": None,
    "temperature_low":  None,
}

# ─── Direction tracker: prevents duplicate LOW alerts per cooling run ─────────
# Tracks whether the LOW direction has already fired in the current run.
# Reset when temperature rises back above _LOW_DIRECTION_RESET_TEMP.
last_breach_direction: dict[str, str | None] = {
    "temperature": None,   # last direction that fired: "high" | "low" | None
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

    temp  = reading["temperature"]
    t_high = RUNTIME_THRESHOLDS["temp_high"]
    t_low  = RUNTIME_THRESHOLDS["temp_low"]

    # ── Reset LOW direction when machine heats back up ────────────────────────
    # This means a new cooling run is starting; the next crossing of LOW
    # should fire a fresh alert.
    if temp > _LOW_DIRECTION_RESET_TEMP:
        last_breach_direction["temperature"] = None

    checks = [
        ("temperature", temp, t_high, "high"),
        ("temperature", temp, t_low,  "low"),
    ]

    for parameter, value, threshold, direction in checks:
        # STRICT boundary: exactly at threshold is NOT a breach
        if direction == "high" and value <= threshold:
            continue
        if direction == "low"  and value >= threshold:
            continue

        # ── Cooling-run duplicate suppression for LOW direction ───────────────
        # If we already fired a LOW alert in this cooling run, skip.
        # The run resets when temperature climbs back above _LOW_DIRECTION_RESET_TEMP.
        if direction == "low" and last_breach_direction.get(parameter) == "low":
            continue

        # Unique key per direction
        key = f"{parameter}_{direction}"
        last_trigger = cooldown_tracker.get(key)

        if last_trigger is not None and (now - last_trigger) < cooldown_delta:
            # Still within cooldown window — skip
            continue

        # Compute severity
        severity = _get_severity(value, threshold, direction)

        # Record this trigger
        cooldown_tracker[key] = now
        last_breach_direction[parameter] = direction

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
