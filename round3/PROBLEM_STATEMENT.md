# Round 3 — Resampling

We only need this data every 10 seconds, not at whatever rate it happens to arrive.

Resample your Round 1 output to one row every 10 wall-clock seconds, per vehicle. At each tick, take the most recent value of each parameter observed since the previous tick. If a parameter had no reading at all in that window, leave it null — don't carry forward from further back than the immediately preceding window. If literally nothing arrived for a vehicle in a given 10-second window, don't emit a row for it at all.

## Deliverable

Your resampled table, same parameter columns as before, one row per (vehicle, tick).

Plus a short write-up:
- Original vs. resampled row count, and the resulting compression ratio
- Per-parameter non-null percentage after resampling (all 9 parameters)
- Per-vehicle tick count distribution — median, min, max, and whether any vehicle looks like an outlier
- How many ticks you dropped entirely because nothing arrived in that window
