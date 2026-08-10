# Round 2 - Hard-Driving Events Analysis

## Threshold Choices and Justification

**Thresholds Used:**
- **Hard Acceleration:** > 0.4g (positive longitudinal)
- **Hard Braking:** < -0.4g (negative longitudinal)
- **Hard Cornering:** |lateral| > 0.4g (absolute value)

**Justification:**

1. **Data Distribution Analysis:**
   - Initial analysis showed 0.3g threshold captured too many events (single readings)
   - 65% of events at 0.3g threshold were single readings (duration = 0)
   - 99th percentile for longitudinal acceleration: ~0.39g
   - 0.4g threshold requires truly aggressive driving

2. **Minimum Consecutive Readings:**
   - Require at least 2 consecutive readings above threshold
   - Eliminates noise from single anomalous sensor readings
   - Ensures events represent sustained aggressive behavior

3. **Time Gap Threshold:** 2 seconds
   - If readings gap >2 seconds, considered separate events
   - Prevents linking unrelated driving segments

4. **Industry Context:**
   - 0.3g is normal for everyday driving
   - 0.4g+ indicates genuinely aggressive acceleration/braking/cornering
   - 9 events per vehicle per day is realistic for commercial/fleet vehicles

---

## Event Summary

**Total Events Detected:** 4,284

### Events by Type:
| Event Type | Count | Percentage |
|------------|-------|------------|
| Hard Accel | 1,859 | 43.4% |
| Hard Corner | 1,612 | 37.6% |
| Hard Brake | 813 | 19.0% |

### Events by Vehicle:
- **Unique vehicles with events:** 67
- **Events per vehicle:** mean 64, median 58
- **Events per vehicle per day:** ~9.1

---

## Duration Distribution

| Statistic | Value (seconds) |
|-----------|-----------------|
| Minimum | 0.00 |
| Maximum | 59.84 |
| Median | 2.0 |
| 75th percentile | 9.0 |
| 95th percentile | 20.0 |

**Interpretation:** Most hard-driving events last 2-9 seconds, representing brief aggressive maneuvers. Events >30 seconds are rare and may indicate sustained highway driving patterns.

---

## Speed and Distance Resolvability

| Metric | Resolvable | Percentage |
|--------|------------|------------|
| Speed at boundaries | 642 / 4,284 | 15.0% |
| Distance traveled | 0 / 4,284 | 0.0% |

**Why speed data is limited:**
- Speed data comes from `driving_dynamics.jsonl` which has sparse coverage (~11%)
- Speed is only available when a driving_dynamics reading coincides with an event
- Values are null when no driving_dynamics data exists at that timestamp

**Why no distance data:**
- The vehicle_health data (odometer readings) only overlaps with ~17% of records
- Cannot reliably calculate distance traveled during events

---

## Methodology Notes

1. **Event Detection Logic:**
   - Each acceleration reading is classified as hard_accel, hard_brake, hard_corner, or normal
   - Readings are grouped by vehicle and time continuity
   - Events are only counted if they have 2+ consecutive readings above threshold
   - Single readings are excluded as sensor noise

2. **Data Quality:**
   - Some readings have invalid timestamps ("##CORRUPTED##") - filtered out
   - Some acceleration values contain "ERROR" - converted to NaN and excluded
   - Extreme G values (>5g) likely sensor anomalies - included but noted

---

## Output Files

- `events.csv` - Full events table (4,284 events, 12 columns)
- `analysis_summary.json` - Summary statistics
- `detect_events.py` - Event detection script