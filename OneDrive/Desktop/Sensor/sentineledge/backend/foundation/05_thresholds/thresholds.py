"""
backend/foundation/05_thresholds/thresholds.py
SentinelEdge — Threshold defaults and severity calculation.
Standalone module — no external dependencies.
"""

# ── Default threshold values ──────────────────────────────────────────────────
TEMP_THRESHOLD_HIGH: float     = 38.0
TEMP_THRESHOLD_LOW: float      = 22.0
HUMIDITY_THRESHOLD_HIGH: float = 80.0
HUMIDITY_THRESHOLD_LOW: float  = 35.0

# Read-only default snapshot
DEFAULT_THRESHOLDS: dict = {
    "temperature": {
        "high": TEMP_THRESHOLD_HIGH,
        "low":  TEMP_THRESHOLD_LOW,
        "unit": "C",
        "name": "Temperature",
        "description": "Ambient air temperature in degrees Celsius",
    },
    "humidity": {
        "high": HUMIDITY_THRESHOLD_HIGH,
        "low":  HUMIDITY_THRESHOLD_LOW,
        "unit": "%",
        "name": "Humidity",
        "description": "Relative humidity as a percentage",
    },
}

# ── Severity band percentages ─────────────────────────────────────────────────
WARNING_PCT:   float = 0.05
CRITICAL_PCT:  float = 0.10
EMERGENCY_PCT: float = 0.25


def get_severity(value: float, threshold: float, direction: str) -> str:
    """
    Compute breach severity based on how far the value exceeds the threshold.

    Returns "WARNING", "CRITICAL", or "EMERGENCY".
    """
    if threshold == 0:
        return "WARNING"
    pct = (
        (value - threshold) / abs(threshold)
        if direction == "high"
        else (threshold - value) / abs(threshold)
    )
    if pct >= EMERGENCY_PCT:
        return "EMERGENCY"
    elif pct >= CRITICAL_PCT:
        return "CRITICAL"
    return "WARNING"
