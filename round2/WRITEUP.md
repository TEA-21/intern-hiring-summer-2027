# Round 2 - Hard-Driving Events Analysis

## Methodology: Merged Duration-Based Detection

The original approach (2+ consecutive readings) produced 4,284 events with 9+ per vehicle/day and high skew toward certain vehicles. The improved approach uses **merged duration-based detection**:

1. **Merge consecutive same-type events** when:
   - Time gap < 5 seconds (short pauses don't end the event)
   - Max G values within 0.15g (same intensity)

2. **Require minimum duration**: Events must be ≥5 seconds to count

This prevents fragmentation of sustained aggressive driving into dozens of micro-events.

---

## Threshold Choices and Justification

**Thresholds Used:**
- **Hard Acceleration:** > 0.4g (positive longitudinal)
- **Hard Braking:** < -0.4g (negative longitudinal)
- **Hard Cornering:** |lateral| > 0.4g (absolute value)

**Justification:**

1. **Data Distribution Analysis:**
   - 0.4g threshold requires genuinely aggressive driving
   - 99th percentile for longitudinal acceleration: ~0.39g
   - 0.4g+ captures meaningful aggressive maneuvers

2. **Merge Parameters:**
   - Gap threshold: 5 seconds (short breaks between hard acceleration don't reset the event)
   - Magnitude threshold: 0.15g (events with similar intensity are merged)

3. **Minimum Duration:** 5 seconds
   - Eliminates brief spikes that don't represent true hard driving
   - Ensures events represent sustained aggressive behavior

---

## Event Summary

**Total Events Detected:** 425

### Events by Type:
| Event Type | Count | Percentage |
|------------|-------|------------|
| Hard Corner | 177 | 41.6% |
| Hard Accel | 159 | 37.4% |
| Hard Brake | 89 | 20.9% |

### Events by Vehicle:
- **Unique vehicles with events:** 52
- **Events per vehicle:** mean 8.2, median 4
- **Events per vehicle per day:** ~1.2

**Improvement over original:**
| Metric | Original | Improved |
|--------|----------|----------|
| Total events | 4,284 | 425 |
| Per vehicle/day | 9.1 | 1.2 |
| Median events/vehicle | 29 | 4 |
| Max events/vehicle | 820 | 116 |

---

## Duration Distribution

| Statistic | Value (seconds) |
|-----------|-----------------|
| Minimum | 5.0 (enforced) |
| Maximum | 2,615.7 |
| Median | 7.6 |
| 75th percentile | 15.0 |
| 95th percentile | 193.8 |

**Interpretation:** Most hard-driving events last 5-15 seconds, representing brief aggressive maneuvers. Long events (>200s) may indicate sustained aggressive driving patterns or vehicle-specific behavior.

---

## Messages per Event

| Message Count | Events |
|---------------|--------|
| 1-10 messages | 326 (76.7%) |
| 11-20 messages | 32 (7.5%) |
| 21+ messages | 67 (15.8%) |

---

## Events per Vehicle Distribution

| Statistic | Value |
|-----------|-------|
| Minimum | 1 |
| Maximum | 116 |
| Median | 4 |
| Mean | 8.2 |
| Std Dev | 16.6 |

**Note:** Even with improved merging, some vehicles still have higher event counts. This may reflect:
- Different driver behavior patterns
- Vehicle type/duty (commercial vs. personal)
- Sensor calibration differences

---

## Methodology Notes

1. **Event Detection Logic:**
   - Each acceleration reading is classified as hard_accel, hard_brake, hard_corner, or normal
   - Consecutive readings of same type with small gaps and similar magnitude are merged
   - Events are only counted if duration >= 5 seconds

2. **Data Quality:**
   - Some readings have invalid timestamps ("##CORRUPTED##") - filtered out
   - Some acceleration values contain "ERROR" - converted to NaN and excluded
   - Extreme G values (>5g) likely sensor anomalies - noted but included

3. **Performance:**
   - Vectorized classification for speed on 11M+ records
   - Per-vehicle iteration for event merging

---

## Output Files

- `events.csv` - Full events table (425 events, 12 columns)
- `detect_events.py` - Event detection script