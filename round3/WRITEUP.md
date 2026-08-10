# Round 3 - Resampling Analysis

## Summary

Resampled the Round 1 output to one row every 10 wall-clock seconds per vehicle, taking the most recent value of each parameter observed since the previous tick.

---

## Row Counts and Compression

| Metric | Value |
|--------|-------|
| Original rows | 11,220,689 |
| Resampled rows | 1,060,295 |
| **Compression ratio** | **10.58x** |
| Rows dropped | 10,160,394 (90.5%) |

The ~10.6x compression ratio indicates the original data was sampled at approximately 1 reading per second on average.

---

## Per-Parameter Non-Null Percentage (All 9 parameters)

| Parameter | Non-Null % |
|-----------|------------|
| make | 100.0% |
| model | 100.0% |
| model_year | 100.0% |
| speed_mph | 99.5% |
| engine_rpm | 99.5% |
| gear_position | 98.7% |
| ignition_status | 94.6% |
| acceleration_long_g | 99.7% |
| acceleration_lat_g | 99.7% |

**Note:** fuel_level_pct, oil_life_pct, and odometer_mi have ~16.9% coverage due to different sampling rates in the source data.

---

## Per-Vehicle Tick Count Distribution

| Statistic | Value |
|-----------|-------|
| Vehicles | 72 |
| Min ticks | 33 |
| Max ticks | 35,215 |
| Mean ticks | 14,726.3 |
| Median ticks | 13,128 |

**Outlier analysis:** Using IQR method (Q1 - 1.5*IQR to Q3 + 1.5*IQR), the threshold is < -9,913 or > 36,786. No vehicles fall outside these bounds.

**Interpretation:** The large range (33 to 35,215) reflects different vehicles having different activity periods. Some vehicles may have been inactive for portions of the data collection period, while others were continuously transmitting.

---

## Ticks Dropped Entirely

| Metric | Value |
|--------|-------|
| Total 10-second windows (all vehicles) | 4,356,864 |
| Windows with data | 1,060,295 |
| **Windows dropped (no data)** | **3,296,569** |

75.7% of expected tick windows had no data for any vehicle. This reflects:
- Vehicles not operating during certain time windows
- Data gaps in the collection period
- Vehicles entering/exiting the fleet at different times

---

## Output Files

- `resampled_data.csv` - Resampled table with 1,060,295 rows
- `resample.py` - Resampling script
- `analysis_summary.json` - Summary statistics

---

## Notes

- 43 rows were dropped during processing due to invalid (non-parseable) timestamps
- No carry-forward was applied; parameters are null if no reading exists in the current 10-second window
- The resampling uses floor(timestamp, 10s) to align all readings to 10-second boundaries
- All 14 columns from Round 1 are preserved in the resampled output