"""
core/thresholds.py — Single source of truth for threshold configuration.

═══════════════════════════════════════════════════════════
WHEN THE CLIENT SENDS A REAL DATASET:
  Edit ONLY the numbers inside THRESHOLDS below.
  Do not change any other file.
  Restart the server after saving. Done.
═══════════════════════════════════════════════════════════

The threshold engine (core/threshold.py) reads from THRESHOLDS at runtime.
The config API (routers/config.py) can also update RUNTIME_THRESHOLDS in
config.py for live changes without restart.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParameterThreshold:
    """
    Configuration for a single sensor parameter (e.g. temperature).

    Severity bands are expressed as percentage over/under the threshold:
        warning:   0-10%  beyond threshold
        critical:  10-25% beyond threshold
        emergency: >25%   beyond threshold
    """

    high: float
    low: float
    unit: str
    name: str
    warning_pct: float = 0.05
    critical_pct: float = 0.10
    emergency_pct: float = 0.25

    def get_severity(self, value: float, direction: str) -> str:
        """
        Compute breach severity based on how far value exceeds the threshold.

        Returns "WARNING", "CRITICAL", or "EMERGENCY".
        """
        if direction == "high":
            ref = self.high
            if ref == 0:
                return "WARNING"
            pct = (value - ref) / abs(ref)
        else:
            ref = self.low
            if ref == 0:
                return "WARNING"
            pct = (ref - value) / abs(ref)

        if pct >= self.emergency_pct:
            return "EMERGENCY"
        elif pct >= self.critical_pct:
            return "CRITICAL"
        return "WARNING"

    def to_dict(self) -> dict:
        return {
            "high": self.high,
            "low": self.low,
            "unit": self.unit,
            "name": self.name,
            "severity_levels": {
                "warning":   f"{self.warning_pct * 100:.0f}% over threshold",
                "critical":  f"{self.critical_pct * 100:.0f}% over threshold",
                "emergency": f"{self.emergency_pct * 100:.0f}% over threshold",
            },
        }


@dataclass
class ThresholdConfig:
    """Container for all monitored parameters."""

    temperature: ParameterThreshold = field(
        default_factory=lambda: ParameterThreshold(
            high=40.0,
            low=35.0,
            unit="\u00b0C",
            name="Temperature",
        )
    )


# ═══════════════════════════════════════════════════════════
# EDIT ONLY THESE NUMBERS WHEN CLIENT SENDS REAL DATASET:
# ═══════════════════════════════════════════════════════════
THRESHOLDS = ThresholdConfig(
    temperature=ParameterThreshold(
        high=40.0,
        low=35.0,
        unit="\u00b0C",
        name="Temperature",
    )
)


def get_all_thresholds() -> dict:
    """Return all threshold configurations as a plain dict."""
    return {"temperature": THRESHOLDS.temperature.to_dict()}