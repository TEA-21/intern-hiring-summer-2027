"""
Round 3 - Resampling (Optimized Version)
Resample Round 1 output to one row every 10 seconds per vehicle.
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("Loading Round 1 merged data...")
df = pd.read_csv('round1/data/merged_data.csv', low_memory=False)
print(f"Original rows: {len(df):,}")

# Convert timestamp and numeric columns
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
numeric_cols = ['speed_mph', 'engine_rpm', 'acceleration_long_g', 'acceleration_lat_g',
                'fuel_level_pct', 'oil_life_pct', 'odometer_mi']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with invalid timestamps
original_count = len(df)
df = df.dropna(subset=['timestamp'])
print(f"Rows after dropping invalid timestamps: {len(df):,} (dropped {original_count - len(df):,})")

# Sort by vehicle and timestamp
df = df.sort_values(['vehicle_id', 'timestamp']).reset_index(drop=True)

# Floor timestamps to 10-second boundaries
df['tick_time'] = df['timestamp'].dt.floor('10s')

print("\nResampling per vehicle...")

# Process each vehicle
results = []
for vehicle_id, group in df.groupby('vehicle_id'):
    if len(group) == 0:
        continue

    # Group by tick_time and get last valid value per column
    resampled = group.groupby('tick_time').agg(
        make=('make', 'last'),
        model=('model', 'last'),
        model_year=('model_year', 'last'),
        speed_mph=('speed_mph', 'last'),
        engine_rpm=('engine_rpm', 'last'),
        gear_position=('gear_position', 'last'),
        ignition_status=('ignition_status', 'last'),
        acceleration_long_g=('acceleration_long_g', 'last'),
        acceleration_lat_g=('acceleration_lat_g', 'last'),
        fuel_level_pct=('fuel_level_pct', 'last'),
        oil_life_pct=('oil_life_pct', 'last'),
        odometer_mi=('odometer_mi', 'last'),
        num_readings=('timestamp', 'count')
    ).reset_index()

    resampled['vehicle_id'] = vehicle_id
    results.append(resampled)

resampled_df = pd.concat(results, ignore_index=True)
print(f"Resampled rows: {len(resampled_df):,}")

# Compression ratio
compression_ratio = len(df) / len(resampled_df) if len(resampled_df) > 0 else 0
print(f"Compression ratio: {compression_ratio:.2f}x")

# Reorder columns
col_order = ['vehicle_id', 'tick_time', 'make', 'model', 'model_year',
             'speed_mph', 'engine_rpm', 'gear_position', 'ignition_status',
             'acceleration_long_g', 'acceleration_lat_g',
             'fuel_level_pct', 'oil_life_pct', 'odometer_mi', 'num_readings']
resampled_df = resampled_df[col_order]

# Save
output_path = Path('round3/resampled_data.csv')
resampled_df.to_csv(output_path, index=False)
print(f"\nSaved to {output_path}")

# Analysis
print("\n" + "="*60)
print("RESAMPLING ANALYSIS")
print("="*60)

print(f"\n--- Row Counts ---")
print(f"Original rows: {len(df):,}")
print(f"Resampled rows: {len(resampled_df):,}")
print(f"Compression ratio: {compression_ratio:.2f}")

# Per-parameter non-null
print(f"\n--- Per-Parameter Non-Null Percentage ---")
param_cols = ['make', 'model', 'model_year', 'speed_mph', 'engine_rpm',
              'gear_position', 'ignition_status', 'acceleration_long_g',
              'acceleration_lat_g', 'fuel_level_pct', 'oil_life_pct', 'odometer_mi']
for col in param_cols:
    non_null = resampled_df[col].notna().sum()
    pct = (non_null / len(resampled_df)) * 100
    print(f"  {col}: {pct:.1f}%")

# Per-vehicle tick counts
print(f"\n--- Per-Vehicle Tick Count Distribution ---")
tick_counts = resampled_df.groupby('vehicle_id').size()
print(f"  Vehicles: {len(tick_counts)}")
print(f"  Min ticks: {tick_counts.min():,}")
print(f"  Max ticks: {tick_counts.max():,}")
print(f"  Mean ticks: {tick_counts.mean():.1f}")
print(f"  Median ticks: {tick_counts.median():.0f}")

# Outlier detection
median_ticks = tick_counts.median()
q1 = tick_counts.quantile(0.25)
q3 = tick_counts.quantile(0.75)
iqr = q3 - q1
lower_out = q1 - 1.5 * iqr
upper_out = q3 + 1.5 * iqr
outliers = tick_counts[(tick_counts < lower_out) | (tick_counts > upper_out)]
print(f"  Outlier threshold: < {lower_out:.0f} or > {upper_out:.0f}")
print(f"  Outlier vehicles: {len(outliers)}")

# Ticks dropped (windows with no data for any vehicle)
print(f"\n--- Ticks Dropped ---")
# Count total expected ticks vs actual
time_range = df['tick_time'].nunique()
total_expected = time_range * len(tick_counts)
ticks_with_data = len(resampled_df)
ticks_dropped = total_expected - ticks_with_data
print(f"  Total 10-second windows across all vehicles: {total_expected:,}")
print(f"  Windows with data: {ticks_with_data:,}")
print(f"  Windows dropped (no data): {ticks_dropped:,}")

# Save analysis
import json
analysis = {
    'original_rows': int(len(df)),
    'resampled_rows': int(len(resampled_df)),
    'compression_ratio': round(float(compression_ratio), 2),
    'per_parameter_null_pct': {col: round(float((resampled_df[col].notna().sum() / len(resampled_df)) * 100), 2) for col in param_cols},
    'per_vehicle_ticks': {
        'min': int(tick_counts.min()),
        'max': int(tick_counts.max()),
        'mean': round(float(tick_counts.mean()), 1),
        'median': float(tick_counts.median()),
        'outlier_count': int(len(outliers))
    },
    'ticks_dropped': int(ticks_dropped),
    'ticks_total': int(total_expected)
}

with open('round3/analysis_summary.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print(f"\nSaved analysis to round3/analysis_summary.json")