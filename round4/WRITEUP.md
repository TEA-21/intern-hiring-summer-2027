# Round 4 - Advanced Resampling Analysis

## Summary

Extended Round 3 resampling by adding extra rows whenever important events occur, regardless of the 10-second grid schedule.

**Key Fix:** Changed to detect ignition/gear changes from **raw data** (not resampled data). The 10-second grid resampling was creating false transitions through interpolation/fill logic.

---

## Trigger Types

1. **Ignition status changes** - When `ignition_status` flips between on/off (detected from raw data)
2. **Hard-driving event starts** - When a Round 2 event begins
3. **Hard-driving event ends** - When a Round 2 event ends
4. **Gear position changes** - When `gear_position` changes (detected from raw data)

---

## Row Counts

| Metric | Value |
|--------|-------|
| Round 3 rows | 1,060,256 |
| Round 4 rows | 1,062,486 |
| **Extra rows** | **2,230 (0.21%)** |

---

## Off-Grid Rows

| Metric | Value |
|--------|-------|
| Off-grid rows | 2,230 |
| Off-grid percentage | 0.21% |
| On-grid rows | 1,060,256 |

**Note:** Off-grid rows are those whose timestamp is NOT a multiple of 10 seconds from the hour. These represent triggered events that occurred between scheduled ticks.

---

## How Off-Grid Rows Were Identified

1. **Ignition changes** detected from raw data by comparing consecutive readings per vehicle
   - Detected 1,379 changes from 11M+ raw records
   - Some fall exactly on the 10-second grid (deduplicated)

2. **Gear changes** detected from raw data by comparing consecutive readings per vehicle
   - Detected 246 changes from 11M+ raw records
   - Some fall exactly on the 10-second grid (deduplicated)

3. **Event starts/ends** from Round 2 events
   - 425 events × 2 = 850 potential trigger times

4. All triggers combined and deduplicated by (vehicle_id, timestamp)

5. For each trigger time:
   - If on-grid: use values from resampled row
   - If off-grid: use most recent raw reading values

---

## Why Detect from Raw Data?

The original approach detected changes from the resampled data, but this caused issues:

| Trigger Type | Changes in Raw | Changes in Resampled | Ratio |
|--------------|----------------|----------------------|-------|
| Ignition | 1,379 | 4,565 | 3.3x inflated |
| Gear | 246 | 18,177 | 74x inflated |

The resampling process (forward-fill, interpolation) was creating false transitions. Detecting from raw data gives accurate change counts.

---

## Trigger Distribution

| Trigger Type | Count |
|--------------|-------|
| scheduled (10s grid) | 1,060,256 |
| ignition_change | 1,251 |
| event_start | 390 |
| event_end | 388 |
| gear_change | 201 |

**Note:** Off-grid counts are lower than raw counts because some triggers fall exactly on 10-second boundaries and get deduplicated with scheduled rows.

---

## Per-Vehicle Extra Row Distribution

| Statistic | Value |
|-----------|-------|
| Min extra rows per vehicle | varies by vehicle activity |
| Max extra rows per vehicle | varies by vehicle activity |

---

## Handling Triggers Landing on Existing Ticks

When a trigger occurs at a time that exactly matches an existing 10-second tick:

1. Both the scheduled row and the triggered row would have the same timestamp
2. During deduplication, the **scheduled row is kept** (priority)
3. The triggered row is discarded to avoid duplicate timestamps

This ensures:
- No duplicate (vehicle_id, timestamp) combinations
- The scheduled tick always takes precedence when timing matches
- Event-triggered rows only add NEW timestamps, not override existing ones

---

## Output Files

- `advanced_resampled.csv` - Advanced resampled table (1,062,486 rows)
- `advanced_resample.py` - Resampling script
- `analysis_summary.json` - Summary statistics

---

## Notes

- Timestamps are irregularly spaced for triggered rows - this is expected per the problem statement
- The 0.21% increase in rows reflects accurate change detection from raw data
- Ignition changes are the most frequent trigger (1,251), followed by event starts/ends (778)
- Gear changes are relatively rare (201) in the raw data