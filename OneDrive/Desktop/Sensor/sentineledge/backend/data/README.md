# SentinelEdge — Client CSV Data Directory

Place the client CSV files here.
Files are loaded in order by `CSVSensorPlayer` (backend/core/sensor.py).

---

## File Format

```
timestamp, temperature, reference_value
04-01-2026 7.52.00,89.63000488,-54.61333466
04-01-2026 7.52.01,89.51000214,-54.61333466
...
```

| Column | Used? | Description |
|--------|-------|-------------|
| 1 — `timestamp`       | ❌ ignored | Original recording time (replaced by current time) |
| 2 — `temperature`     | ✅ **used** | Machine temperature in °C |
| 3 — `reference_value` | ❌ ignored | Reference sensor reading |

Valid temperature range accepted: **20.0 °C — 100.0 °C**
Rows outside this range or with bad data are skipped automatically.

---

## Playback Order

Files are loaded and concatenated in this exact order:

```
01_04_2026_Run1.csv   ← loaded first
01_04_2026_Run2.csv
01_04_2026_Run3.csv
02_04_2026_Run1.csv
02_04_2026_Run2.csv
02_04_2026_Run3.csv
06_04_2026_Run1.csv
08_04_2026_Run1.csv
08_04_2026_Run2.csv   ← loaded last
```

After the last row of the last file the player loops back to the beginning.

---

## Playback Modes

| Mode | Speed | Duration (full cycle) |
|------|-------|----------------------|
| Normal | 1 reading/sec | ~2.5 hours |
| Demo 10x | 10x faster | ~15 minutes |
| Demo 30x | 30x faster | ~5 minutes |
| Demo 50x | 50x faster | ~3 minutes |

---

## Missing Files

If a file in the list above is not present it is silently skipped.
If **no files at all** are found, the system falls back to a synthetic
cooling curve (88°C → 35°C) so the server still runs.

---

## Startup Log

On server start you will see:
```
Sensor: 01_04_2026_Run1.csv → 9128 readings
Sensor: 01_04_2026_Run2.csv → 8954 readings
...
Sensor: loaded 78432 readings from CSV
```
