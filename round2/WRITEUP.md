# Round 2 - Hard-Driving Events Analysis

## Threshold Choices and Justification

**Thresholds Used:**
- **Hard Acceleration:** > 0.3g (positive longitudinal)
- **Hard Braking:** < -0.3g (negative longitudinal)
- **Hard Cornering:** |lateral| > 0.3g (absolute value)

**Justification:**

1. **Data Distribution Analysis:**
   - 99th percentile for longitudinal acceleration: ~0.24g
   - 99.9th percentile: ~1.04g
   - 0.3g threshold is above the 99th percentile, capturing only truly aggressive driving

2. **Industry Context:**
   - Typical passenger vehicles achieve 0.3g to 0.4g in normal driving
   - Sustained >0.3g indicates aggressive acceleration/braking
   - 0.3g is commonly used in telematics industry for harsh event detection

3. **Time Gap Threshold:** 5 seconds
   - If readings gap >5 seconds, considered separate events
   - Prevents linking unrelated driving segments

---

## Event Summary

**Total Events Detected:** 54,022

### Events by Type:
| Event Type | Count | Percentage |
|------------|-------|------------|
| Hard Corner | 28,311 | 52.4% |
| Hard Brake | 13,030 | 24.1% |
| Hard Accel | 12,681 | 23.5% |

### Events by Vehicle:
- **Unique vehicles with events:** 68
- **Events per vehicle:** mean 794.4, median 632

---

## Duration Distribution

| Statistic | Value (seconds) |
|-----------|-----------------|
| Minimum | 0.00 |
| Maximum | 59.89 |
| Mean | 1.32 |
| Median | 0.00 |
| 75th percentile | 1.00 |
| 90th percentile | 2.15 |
| 95th percentile | 8.00 |
| 99th percentile | 19.79 |

### Unusually Long Events
- Events >120 seconds: **0**
- Events >60 seconds: 0 (max duration is ~60 seconds)

**Interpretation:** Most hard-driving events are brief (<3 seconds), indicating brief moments of aggressive driving rather than sustained behavior. The median of 0.0 seconds suggests many events are single readings at the threshold boundary.

---

## Speed and Distance Resolvability

| Metric | Resolvable | Percentage |
|--------|------------|------------|
| Start/End G at boundaries | 54,022 / 54,022 | 100.0% |
| Start speed available | 6,664 / 54,022 | 12.3% |
| End speed available | 6,584 / 54,022 | 12.2% |
| Distance traveled | 0 / 54,022 | 0.0% |

**Why speed data is limited:**
- Speed data comes from `driving_dynamics.jsonl` which has ~1.26 million records out of 11.2 million total
- Speed is only available when a driving_dynamics reading coincides with an event
- Speed values are null when no driving_dynamics data exists at that timestamp

**Why no distance data:**
- The vehicle_health data (odometer readings) only overlaps with ~17% of records
- Health data is sampled at different time intervals than acceleration data
- Cannot reliably calculate distance traveled during events

---

## Unusual Observations

1. **Timestamp Corruption:** Some acceleration records have "##CORRUPTED##" as timestamp values - these were filtered out during processing.

2. **Data Quality:** Small percentage (~1.7%) of acceleration readings have non-numeric values ("ERROR") that were excluded from analysis.

3. **Vehicle Count Mismatch:** Metadata has 67 vehicles but acceleration data has 72 unique vehicle IDs - 5 vehicles have no metadata.

4. **Lateral Dominance:** Hard cornering events dominate (52.4%) compared to longitudinal events - suggests many vehicles operate in conditions with frequent turning (urban driving, parking lots).

5. **High G Spikes:** Maximum recorded values reach 23.92g - likely sensor errors or anomalies as these exceed physical vehicle limits.

6. **Missing driving_dynamics initially:** The `driving_dynamics.jsonl` file was stored in Git LFS but not initially available - required LFS pull to access speed data.

---

## Output Files

- `events.csv` - Full events table (54,022 events, 12 columns)
- `analysis_summary.json` - Summary statistics
- `detect_events.py` - Event detection script