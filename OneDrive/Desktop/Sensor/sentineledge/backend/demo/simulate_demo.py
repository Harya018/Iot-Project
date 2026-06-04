"""
backend/demo/simulate_demo.py

!!! DELETE BEFORE PRODUCTION DEPLOYMENT !!!

Simulates a complete 2-hour cooling cycle compressed into ~30 seconds
for client demonstration purposes.

Normal behaviour:
  Machine cools 88°C → 38°C over ~2 hours (real operation).

Demo behaviour (via POST /api/demo/cooling-run):
  Temperature starts at 87°C.
  Drops by 4°C per tick (1 tick = 1 second).
  Reaches 40°C (LOW threshold) in ~12 ticks → alert fires.
  Reaches 35°C in ~13 ticks → resets to 87°C.
  Runs 3 complete cycles then stops (~39 seconds total).

This is called by routers/simulate.py — no other module imports this.
"""

# ── Module state ──────────────────────────────────────────────────────────────

_demo_active:  bool = False
_demo_cycles:  int  = 0     # cycles completed
_cycles_total: int  = 3     # total cycles to run
_tick_count:   int  = 0     # ticks in current cycle


def get_demo_state() -> dict:
    """Return the current demo state for the /api/demo/status endpoint."""
    return {
        "active":         _demo_active,
        "cycles_done":    _demo_cycles,
        "cycles_total":   _cycles_total,
        "ticks_in_cycle": _tick_count,
    }


def is_demo_active() -> bool:
    return _demo_active


def start_demo(cycles: int = 3) -> dict:
    """
    Activate fast-demo cooling mode.

    Returns metadata about the demo run.
    Called by POST /api/demo/cooling-run.
    """
    global _demo_active, _demo_cycles, _cycles_total, _tick_count
    _demo_active   = True
    _demo_cycles   = 0
    _cycles_total  = cycles
    _tick_count    = 0

    # Delegate actual sensor control to core/sensor.py
    import core.sensor as sensor
    sensor.activate_demo_cooling(cycles=cycles)

    ticks_per_cycle = 13   # 87°C / 4°C per tick ≈ 13 ticks
    total_ticks     = cycles * ticks_per_cycle

    return {
        "status":            "demo_started",
        "start_temp":        87.0,
        "drop_per_tick":     4.0,
        "ticks_per_cycle":   ticks_per_cycle,
        "total_ticks":       total_ticks,
        "duration_seconds":  total_ticks,
        "cycles":            cycles,
        "alert_fires_at":    "~12 seconds per cycle (when temp crosses 40°C)",
        "warning":           "DELETE THIS ENDPOINT BEFORE PRODUCTION DEPLOYMENT",
    }


def reset_demo() -> dict:
    """
    Reset sensor to normal operation mode.
    Called by POST /api/demo/reset.
    """
    global _demo_active, _demo_cycles, _tick_count
    _demo_active  = False
    _demo_cycles  = 0
    _tick_count   = 0

    import core.sensor as sensor
    sensor.reset_to_normal()

    return {"status": "reset", "message": "Sensor returned to normal operation"}
