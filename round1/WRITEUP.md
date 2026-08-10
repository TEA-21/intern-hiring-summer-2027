# Round 1 - Data Merging Analysis

## Approach

The challenge was to combine telemetry data from multiple sources with different:
- Sampling rates (acceleration at ~1Hz, health data at ~0.1Hz)
- File formats (CSV, Parquet, Base64-encoded Gzip-JSON)
- Time alignments

### Data Sources Identified:

1. **vehicle_metadata.csv** - 67 vehicles with make/model/year
   - Format: Plain CSV
   - Columns: vehicle_id, make, model, model_year

2. **acceleration_data.parquet** - High-frequency acceleration readings
   - Format: Apache Parquet (binary columnar format)
   - Columns: vehicle_id, timestamp, acceleration_long_g, acceleration_lat_g
   - ~10.4 million records

3. **driving_dynamics.jsonl** - Vehicle operational data
   - Format: JSON Lines (one JSON object per line)
   - Columns: vehicle_id, timestamp, speed_mph, engine_rpm, gear_position, ignition_status
   - ~2.3 million records

4. **vehicle_health.b64** - Vehicle health metrics (encoded)
   - Format: Base64 → Gzip → JSON Lines
   - Manifest indicated: vehicle_id, timestamp, fuel_level_pct, oil_life_pct, odometer_mi
   - ~179K records

---

## Data Quality Issues Found and Handled

### 1. Timestamp Corruption
- **Issue:** Some records have "##CORRUPTED##" as timestamp values
- **Handling:** Converted to NaT (null) and excluded from merges; excluded from analysis

### 2. Encoding Layers (vehicle_health.b64)
- **Issue:** Data encoded in multiple layers: Base64 → Gzip → JSON Lines
- **Handling:** 
  - Decoded Base64 once to get Gzip-compressed data
  - Decompressed with gzip to get raw JSON
  - Loaded as JSON Lines format (one object per line)
  - Final count: 179,494 records

### 3. Missing driving_dynamics.jsonl
- **Issue:** File stored in Git LFS but not initially available
- **Handling:** Used `git lfs pull` to download the file (~397MB)

### 4. Mixed Data Types
- **Issue:** Some acceleration values contain "ERROR" as string
- **Handling:** Used `pd.to_numeric(errors='coerce')` to convert to NaN

### 5. Different Sampling Rates
- **Issue:** Health data sampled at different intervals than acceleration
- **Handling:** Used outer join to preserve all records; acknowledged that ~17% of records have health data

### 6. Vehicle Count Mismatch
- **Issue:** Metadata has 67 vehicles, acceleration has 72 unique vehicle IDs
- **Handling:** Left-joined metadata to preserve all acceleration records; 5 vehicles have null make/model/year

---

## Merge Strategy

1. **Primary join keys:** vehicle_id AND timestamp
   - Ensures data is aligned to the same moment in time
   - Preserves all records from all sources

2. **Merge order:**
   - acceleration + driving_dynamics (both have timestamp)
   - + vehicle_health (has timestamp)
   - + vehicle_metadata (left join on vehicle_id only, no timestamp)

3. **Result:** 11,220,689 rows with 14 columns

---

## Final Dataset Statistics

| Column | Non-Null Count | Percentage |
|--------|----------------|------------|
| vehicle_id | 11,220,689 | 100.0% |
| timestamp | 11,220,646 | 100.0% |
| make | 10,566,234 | 94.2% |
| model | 10,566,234 | 94.2% |
| model_year | 10,566,234 | 94.2% |
| speed_mph | 1,257,255 | 11.2% |
| engine_rpm | 1,257,255 | 11.2% |
| gear_position | 1,257,255 | 11.2% |
| ignition_status | 1,257,255 | 11.2% |
| acceleration_long_g | 10,388,738 | 92.6% |
| acceleration_lat_g | 10,388,737 | 92.6% |
| fuel_level_pct | 1,793,924 | 16.0% |
| oil_life_pct | 1,793,865 | 16.0% |
| odometer_mi | 1,793,923 | 16.0% |

---

## Output Files

- `data/merged_data.csv` - Final merged dataset (11,220,689 rows, 14 columns)
- `merge_data.py` - Python script used for merging
- `data/raw/` - Original source data files

---

## Usability Assessment

This dataset is suitable for:
- Hard-driving event detection (acceleration data available)
- Vehicle fleet behavior analysis (metadata joined)
- Time-series analysis (timestamps aligned)

Limitations:
- Speed/health data sparse (~11-17% coverage)
- Some vehicles lack metadata
- ~0.04% records have invalid timestamps