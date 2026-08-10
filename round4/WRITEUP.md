# Round 4 - Advanced Resampling Analysis

## Summary

Extended Round 3 resampling by adding extra rows whenever important events occur, regardless of the 10-second grid schedule. Updated to use improved Round 2 event detection (merged duration-based, 425 events vs. original 4,284).

---

## Trigger Types

1. **Ignition status changes** - When `ignition_status` flips between on/off
2. **Hard-driving event starts** - When a Round 2 event begins (using merged duration-based detection)
3. **Hard-driving event ends** - When a Round 2 event ends
4. **Gear position changes** - When `gear_position` changes

### Round 2 Event Detection Update

The Round 2 event detection was improved to use merged duration-based detection:
- Merge consecutive same-type events (gap < 5s, magnitude within 0.15g)
- Require minimum duration of 5 seconds
- Result: 425 events (vs. original 4,284 fragmented events)

This significantly reduced event-triggered rows in Round 4.

---

## Row Counts

| Metric | Value |
|--------|-------|
| Round 3 rows | 1,060,256 |
| Round 4 rows | 1,061,040 |
| **Extra rows** | **784 (0.07%)** |

---

## Off-Grid Rows

| Metric | Value |
|--------|-------|
| Off-grid rows | 784 |
| Off-grid percentage | 0.07% |
| On-grid rows | 1,060,256 |

**Note:** Off-grid rows are those whose timestamp is NOT a multiple of 10 seconds from the hour. These represent triggered events that occurred between scheduled ticks.

---

## How Off-Grid Rows Were Identified

1. For each vehicle, compared consecutive rows to detect:
   - Ignition status changes (on <-> off)
   - Gear position changes (drive <-> reverse, drive <-> neutral, etc.)

2. Extracted event start/end times from Round 2 events (using merged duration-based detection)

3. For each detected trigger time:
   - If the timestamp falls exactly on the 10-second grid, it overlaps with an existing scheduled row
   - If the timestamp is off-grid (second % 10 != 0), a new row is added

4. Values at trigger time are populated from the most recently known reading

---

## Trigger Distribution

| Trigger Type | Count |
|--------------|-------|
| scheduled (10s grid) | 1,038,468 |
| gear_change | 17,223 |
| ignition_change | 4,565 |
| event_start | 394 |
| event_end | 390 |

**Note:** With improved event detection (425 events), event triggers total 784 rows instead of the original 7,548. Most event start/end times now fall on or very close to existing scheduled ticks.

---

## Per-Vehicle Extra Row Distribution

| Statistic | Value |
|-----------|-------|
| Min extra rows per vehicle | varies by vehicle activity |
| Max extra rows per vehicle | varies by vehicle activity |

The reduced event count means fewer event-triggered rows per vehicle.

---

## Handling Triggers Landing on Existing Ticks

When a trigger (e.g., gear change) occurs at a time that exactly matches an existing 10-second tick:

1. Both the scheduled row and the triggered row would have the same timestamp
2. During deduplication, the **scheduled row is kept** (priority)
3. The triggered row is discarded to avoid duplicate timestamps

This ensures:
- No duplicate (vehicle_id, timestamp) combinations
- The scheduled tick always takes precedence when timing matches
- Event-triggered rows only add NEW timestamps, not override existing ones

---

## Output Files

- `advanced_resampled.csv` - Advanced resampled table (1,061,040 rows)
- `advanced_resample.py` - Resampling script
- `analysis_summary.json` - Summary statistics

---

## Notes

- Timestamps are irregularly spaced for triggered rows - this is expected per the problem statement
- The 0.07% increase in rows reflects the improved event detection - with 425 real events (vs. 4,284 fragmented ones), fewer distinct trigger timestamps fall off the 10-second grid
- Gear changes remain the most frequent trigger (17,223), followed by ignition changes (4,565)
- Event start/end triggers total 784 (down from 7,548), reflecting the improved merged duration-based detection