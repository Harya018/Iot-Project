"""
core/sensor.py — Simulated temperature sensor.

Normal mode : slow random drift within realistic bounds (35–40°C).
Demo mode   : deterministic ramp from 35°C → 42°C → 35°C over 180 ticks
              so a threshold breach is guaranteed for demonstration purposes.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import AsyncGenerator

from config import DEMO_MODE

# ─── Internal state ───────────────────────────────────────────────────────────
_temperature: float = 37.0

# Demo-mode ramp state
_demo_tick: int = 0
_DEMO_CYCLE: int = 180  # ticks per half-cycle (up or down)

# Simulate-breach override: force temperature high for N readings
_breach_override_remaining: int = 0


def set_breach_override(ticks: int = 10) -> None:
    """Force temperature to 42.0 for the next `ticks` readings (demo/test)."""
    global _breach_override_remaining
    _breach_override_remaining = ticks


def get_reading() -> dict:
    """
    Return a sensor reading dict.

    Keys: temperature (float), timestamp (ISO-8601 str).
    """
    global _temperature, _demo_tick, _breach_override_remaining

    if _breach_override_remaining > 0:
        # Hard override for simulate-breach endpoint
        _breach_override_remaining -= 1
        temp = 42.0
    elif DEMO_MODE:
        # Deterministic ramp: 35 → 42 over 180 ticks, then 42 → 35, repeat
        half = _demo_tick % (_DEMO_CYCLE * 2)
        if half < _DEMO_CYCLE:
            # Rising phase
            temp = 35.0 + (7.0 * half / _DEMO_CYCLE)
        else:
            # Falling phase
            temp = 42.0 - (7.0 * (half - _DEMO_CYCLE) / _DEMO_CYCLE)
        temp = round(temp, 1)
        _demo_tick += 1
    else:
        # Normal slow-drift mode
        delta_t = random.uniform(-0.8, 0.8)
        _temperature = max(15.0, min(50.0, _temperature + delta_t))
        temp = round(_temperature, 1)

    return {
        "temperature": temp,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def stream_readings() -> AsyncGenerator[dict, None]:
    """Async generator that yields one reading per second indefinitely."""
    from config import MODULE_STATUS
    MODULE_STATUS["sensor"] = "ok"
    while True:
        yield get_reading()
        await asyncio.sleep(1)
