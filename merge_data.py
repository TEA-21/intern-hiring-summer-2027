"""
Round 1 - Data Merging (Updated with driving_dynamics.jsonl)
Merge all datasets using outer join on vehicle_id and timestamp.
"""

import pandas as pd
import base64
import gzip
from pathlib import Path
from io import BytesIO

# Paths
base_path = Path("round1/data/raw")

print("Loading datasets...")

# 1. Load vehicle_metadata.csv
metadata = pd.read_csv(base_path / "vehicle_metadata.csv")
print(f"vehicle_metadata: {metadata.shape[0]} rows, columns: {metadata.columns.tolist()}")

# 2. Load acceleration_data.parquet
acceleration = pd.read_parquet(base_path / "acceleration_data.parquet")
print(f"acceleration_data: {acceleration.shape[0]} rows, columns: {acceleration.columns.tolist()}")

# 3. Load driving_dynamics.jsonl
dynamics = pd.read_json(base_path / "driving_dynamics.jsonl", lines=True)
print(f"driving_dynamics: {dynamics.shape[0]} rows, columns: {dynamics.columns.tolist()}")

# 4. Decode vehicle_health.b64 (base64 -> gzip -> JSON lines)
print("\nDecoding vehicle_health.b64...")
with open(base_path / "vehicle_health.b64", "rb") as f:
    raw = f.read()

# Decode base64 once (gives gzip data)
decoded = base64.b64decode(raw)
# Decompress gzip
data = gzip.decompress(decoded)
# Load as JSON lines format
health = pd.read_json(BytesIO(data), lines=True)
print(f"vehicle_health: {health.shape[0]} rows, columns: {health.columns.tolist()}")

# Convert timestamp columns to datetime for proper merging
print("\nConverting timestamps...")
acceleration['timestamp'] = pd.to_datetime(acceleration['timestamp'], errors='coerce')
dynamics['timestamp'] = pd.to_datetime(dynamics['timestamp'], errors='coerce')
health['timestamp'] = pd.to_datetime(health['timestamp'], errors='coerce')

# 5. Outer join all dataframes on vehicle_id AND timestamp
print("\nMerging datasets with outer join on [vehicle_id, timestamp]...")

# Merge acceleration with dynamics (both have timestamps)
merged = acceleration.merge(dynamics, on=["vehicle_id", "timestamp"], how="outer")
print(f"After merging acceleration + dynamics: {merged.shape}")

# Merge with health data
merged = merged.merge(health, on=["vehicle_id", "timestamp"], how="outer")
print(f"After merging with vehicle_health: {merged.shape}")

# Now merge with metadata (only on vehicle_id, as metadata doesn't have timestamp)
merged = merged.merge(metadata, on=["vehicle_id"], how="left")
print(f"After merging with vehicle_metadata: {merged.shape}")

# Reorder columns for clarity
col_order = ['vehicle_id', 'timestamp',
             'make', 'model', 'model_year',
             'speed_mph', 'engine_rpm', 'gear_position', 'ignition_status',
             'acceleration_long_g', 'acceleration_lat_g',
             'fuel_level_pct', 'oil_life_pct', 'odometer_mi']
merged = merged[[c for c in col_order if c in merged.columns]]

# Save the merged dataset
output_path = base_path.parent / "merged_data.csv"
merged.to_csv(output_path, index=False)
print(f"\nSaved to: {output_path}")
print(f"Total rows: {merged.shape[0]}, Total columns: {merged.shape[1]}")

print("\nColumn summary:")
for col in merged.columns:
    non_null = merged[col].notna().sum()
    pct = (non_null / len(merged)) * 100
    print(f"  {col}: {non_null}/{len(merged)} ({pct:.1f}%) non-null")

print(f"\nSample of merged data:")
print(merged.head(10))