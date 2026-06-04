# -*- coding: utf-8 -*-
"""
core/sensor.py — Real client CSV data playback.

Reads 9 CSV files of real machine cooling data from backend/data/.
Replays them row by row at 1 reading/second (normal mode) or
at an accelerated speed for demonstrations (demo mode).

CSV format: timestamp, temperature, reference_value
  Column 1: original timestamp  (ignored — we use current time)
  Column 2: temperature value   (used)
  Column 3: reference value     (ignored)

Fallback: if no CSV files are found a synthetic cooling curve is
generated so the system still works during initial setup.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from config import MODULE_STATUS
from utils.time import now_iso

# ─── Data directory ───────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"

# Playback order for all client CSV files
_CSV_FILE_ORDER = [
    "01.04.2026_Run1.csv",
    "01.04.2026_Run2.csv",
    "01.04.2026_Run3.csv",
    "02.04.2026_Run1.csv",
    "02.04.2026_Run2.csv",
    "02.04.2026_Run3.csv",
    "06.04.2026_Run1.csv",
    "08.04.2026_Run1.csv",
    "08.04.2026_Run2.csv",
]


# ─── CSV Sensor Player ────────────────────────────────────────────────────────

class CSVSensorPlayer:
    """
    Plays back real client CSV data row by row.

    Normal mode : 1 reading per second (real-time, ~2.5 hrs per full cycle).
    Demo mode   : accelerated playback (e.g. 30x → ~5 minutes per cycle).
    """

    def __init__(self) -> None:
        self.readings:   list[float] = []
        self.index:      int         = 0
        self.demo_mode:  bool        = False
        self.demo_speed: int         = 30
        self._load_all_files()

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load_all_files(self) -> None:
        """Load all CSV files in playback order."""
        for filename in _CSV_FILE_ORDER:
            filepath = DATA_DIR / filename
            if filepath.exists():
                self._load_file(filepath)

        if not self.readings:
            # Fallback: synthetic cooling curve if no CSV files present
            print("Sensor: no CSV files found -- using synthetic cooling curve")
            temp = 88.0
            for _ in range(9000):
                self.readings.append(round(temp, 1))
                temp -= 0.005 + (0.002 * (temp / 90.0))
                temp = max(35.0, temp)
        else:
            print(f"Sensor: loaded {len(self.readings)} readings from CSV")

    def _load_file(self, filepath: Path) -> None:
        """Parse a single CSV file and append valid temperature values."""
        loaded = 0
        try:
            with open(filepath, encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(",")
                    if len(parts) < 2:
                        continue
                    try:
                        temp = float(parts[1].strip())
                        # Accept realistic machine temperatures only
                        if 20.0 <= temp <= 100.0:
                            self.readings.append(round(temp, 1))
                            loaded += 1
                    except ValueError:
                        continue  # skip header row or bad data
        except Exception as exc:
            print(f"Sensor: warning - could not load {filepath.name}: {exc}")
        else:
            if loaded:
                print(f"Sensor: {filepath.name} -> {loaded} readings")

    # ── Reading ───────────────────────────────────────────────────────────────

    def get_reading(self) -> dict:
        """Return the next temperature reading and advance the index."""
        if not self.readings:
            return {"temperature": 65.0, "timestamp": now_iso()}

        temp = self.readings[self.index]
        self.index = (self.index + 1) % len(self.readings)

        return {"temperature": temp, "timestamp": now_iso()}

    # ── Controls ──────────────────────────────────────────────────────────────

    def activate_demo(self, speed: int = 30) -> None:
        """Switch to accelerated demo playback and rewind to the beginning."""
        self.demo_mode  = True
        self.demo_speed = max(1, speed)
        self.index      = 0
        total_secs      = len(self.readings) / self.demo_speed
        print(
            f"Sensor: demo mode ON — {speed}x speed, "
            f"~{total_secs / 60:.1f} min for full cycle"
        )

    def reset(self) -> None:
        """Stop demo mode and rewind to the start of the data."""
        self.demo_mode = False
        self.index     = 0
        print("Sensor: reset to normal playback from beginning")


# ─── Singleton instance ───────────────────────────────────────────────────────
player = CSVSensorPlayer()


# ─── Breach override (for /api/simulate/breach) ───────────────────────────────
_breach_override_remaining: int   = 0
_breach_override_value:     float = 92.0   # above 90.0 HIGH threshold


def set_breach_override(ticks: int = 10, value: float = 92.0) -> None:
    """Force temperature to `value` for the next `ticks` readings."""
    global _breach_override_remaining, _breach_override_value
    _breach_override_remaining = ticks
    _breach_override_value     = value


# ─── Public API ───────────────────────────────────────────────────────────────

def get_reading() -> dict:
    """
    Return one sensor reading.

    Priority:
      1. Breach override (forced value for N ticks — for testing)
      2. Normal CSV playback (or demo-speed CSV playback)
    """
    global _breach_override_remaining
    if _breach_override_remaining > 0:
        _breach_override_remaining -= 1
        return {"temperature": _breach_override_value, "timestamp": now_iso()}

    return player.get_reading()


def activate_demo(speed: int = 30) -> dict:
    """Activate demo mode at the given speed multiplier."""
    player.activate_demo(speed)
    total_readings = len(player.readings)
    duration_secs  = total_readings / speed
    return {
        "status":                     "demo_started",
        "speed":                      speed,
        "total_readings":             total_readings,
        "estimated_duration_minutes": round(duration_secs / 60, 1),
    }


def reset_sensor() -> dict:
    """Stop demo mode and rewind playback to the start."""
    player.reset()
    return {"status": "reset", "message": "Sensor reset to beginning of data"}


async def stream_readings():
    """Async generator — yields one reading per tick indefinitely."""
    MODULE_STATUS["sensor"] = "ok"
    while True:
        yield get_reading()
        # Normal: 1 second per reading (real machine speed)
        # Demo:   1/speed seconds per reading (compressed)
        delay = 1.0 / player.demo_speed if player.demo_mode else 1.0
        await asyncio.sleep(delay)
