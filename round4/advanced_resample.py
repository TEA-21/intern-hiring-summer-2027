"""
Round 4 - Advanced Resampling
Detect ignition/gear changes from RAW data (not resampled).
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("Loading data...")

# Load Round 3 resampled data
resampled = pd.read_csv('round3/resampled_data.csv', low_memory=False)
resampled['tick_time'] = pd.to_datetime(resampled['tick_time'])
print(f"Round 3 rows: {len(resampled):,}")

# Load Round 2 events
events = pd.read_csv('round2/events.csv')
events['start_time'] = pd.to_datetime(events['start_time'])
events['end_time'] = pd.to_datetime(events['end_time'])
print(f"Events: {len(events):,}")

# Load raw data
raw = pd.read_csv('round1/data/merged_data.csv', low_memory=False)
raw['timestamp'] = pd.to_datetime(raw['timestamp'], errors='coerce')
numeric_cols = ['speed_mph', 'engine_rpm', 'acceleration_long_g', 'acceleration_lat_g',
                'fuel_level_pct', 'oil_life_pct', 'odometer_mi']
for col in numeric_cols:
    raw[col] = pd.to_numeric(raw[col], errors='coerce')
raw = raw[(raw['timestamp'].dt.year >= 2020) & (raw['timestamp'].dt.year <= 2030)]
raw = raw.sort_values(['vehicle_id', 'timestamp']).reset_index(drop=True)
print(f"Raw data rows: {len(raw):,}")

print("\n--- Identifying Triggers from RAW data ---")

# Function to find changes in a column from raw data
def find_changes_from_raw(df, col):
    df = df.copy()
    df['prev'] = df.groupby('vehicle_id')[col].shift(1)
    changes = df[
        (df[col] != df['prev']) &
        df[col].notna() &
        df['prev'].notna()
    ].copy()
    return changes[['vehicle_id', 'timestamp', col]]

# 1. Ignition changes (from raw data)
print("Detecting ignition changes from raw...")
ignition_changes = find_changes_from_raw(raw, 'ignition_status')
ignition_changes = ignition_changes.rename(columns={'timestamp': 'tick_time', 'ignition_status': 'new_ignition'})
ignition_changes['trigger_type'] = 'ignition_change'
print(f"  Ignition changes in raw: {len(ignition_changes):,}")

# 2. Gear changes (from raw data)
print("Detecting gear changes from raw...")
gear_changes = find_changes_from_raw(raw, 'gear_position')
gear_changes = gear_changes.rename(columns={'timestamp': 'tick_time', 'gear_position': 'new_gear'})
gear_changes['trigger_type'] = 'gear_change'
print(f"  Gear changes in raw: {len(gear_changes):,}")

# 3. Event starts/ends
event_starts = events[['vehicle_id', 'start_time']].copy()
event_starts['trigger_type'] = 'event_start'
event_starts = event_starts.rename(columns={'start_time': 'tick_time'})

event_ends = events[['vehicle_id', 'end_time']].copy()
event_ends['trigger_type'] = 'event_end'
event_ends = event_ends.rename(columns={'end_time': 'tick_time'})

# Combine all triggers (only keep vehicle_id and tick_time for deduplication)
triggers = pd.concat([
    ignition_changes[['vehicle_id', 'tick_time', 'trigger_type']],
    gear_changes[['vehicle_id', 'tick_time', 'trigger_type']],
    event_starts,
    event_ends
], ignore_index=True)

# Drop duplicates - keep first occurrence for each (vehicle_id, tick_time)
triggers = triggers.drop_duplicates(subset=['vehicle_id', 'tick_time'], keep='first')
print(f"\nTotal triggers (after dedup): {len(triggers):,}")

# Identify on/off grid
triggers['second'] = triggers['tick_time'].dt.second
triggers['is_on_grid'] = triggers['second'] % 10 == 0
print(f"On-grid: {triggers['is_on_grid'].sum():,}, Off-grid: {(~triggers['is_on_grid']).sum():,}")

# Process each vehicle
print("\n--- Processing per vehicle ---")

all_triggered_rows = []

# Create lookup for resampled data
resampled_dict = {}
for vehicle_id, group in resampled.groupby('vehicle_id'):
    group = group.sort_values('tick_time').reset_index(drop=True)
    resampled_dict[vehicle_id] = group

# Create lookup for raw data
raw_dict = {}
for vehicle_id, group in raw.groupby('vehicle_id'):
    group = group.sort_values('timestamp').reset_index(drop=True)
    raw_dict[vehicle_id] = group

for vehicle_id, vehicle_triggers in triggers.groupby('vehicle_id'):
    vehicle_triggers = vehicle_triggers.sort_values('tick_time').reset_index(drop=True)
    vehicle_resampled = resampled_dict.get(vehicle_id)
    vehicle_raw = raw_dict.get(vehicle_id)

    if vehicle_raw is None:
        continue

    for _, trigger in vehicle_triggers.iterrows():
        t_time = trigger['tick_time']
        t_type = trigger['trigger_type']
        is_on_grid = trigger['is_on_grid']

        if is_on_grid and vehicle_resampled is not None:
            # Get values from resampled data (exact tick match)
            mask = vehicle_resampled['tick_time'] == t_time
            tick_rows = vehicle_resampled[mask]
            if len(tick_rows) > 0:
                row = tick_rows.iloc[0]
                all_triggered_rows.append({
                    'vehicle_id': vehicle_id,
                    'timestamp': t_time,
                    'trigger_type': t_type,
                    'speed_mph': row['speed_mph'] if pd.notna(row['speed_mph']) else None,
                    'engine_rpm': row['engine_rpm'] if pd.notna(row['engine_rpm']) else None,
                    'gear_position': row['gear_position'] if pd.notna(row['gear_position']) else None,
                    'ignition_status': row['ignition_status'] if pd.notna(row['ignition_status']) else None,
                    'acceleration_long_g': row['acceleration_long_g'] if pd.notna(row['acceleration_long_g']) else None,
                    'acceleration_lat_g': row['acceleration_lat_g'] if pd.notna(row['acceleration_lat_g']) else None,
                    'fuel_level_pct': row['fuel_level_pct'] if pd.notna(row['fuel_level_pct']) else None,
                    'oil_life_pct': row['oil_life_pct'] if pd.notna(row['oil_life_pct']) else None,
                    'odometer_mi': row['odometer_mi'] if pd.notna(row['odometer_mi']) else None,
                })
        else:
            # Get most recent value from raw data
            readings = vehicle_raw[vehicle_raw['timestamp'] <= t_time]
            if len(readings) > 0:
                row = readings.iloc[-1]
                all_triggered_rows.append({
                    'vehicle_id': vehicle_id,
                    'timestamp': t_time,
                    'trigger_type': t_type,
                    'speed_mph': row['speed_mph'] if pd.notna(row['speed_mph']) else None,
                    'engine_rpm': row['engine_rpm'] if pd.notna(row['engine_rpm']) else None,
                    'gear_position': row['gear_position'] if pd.notna(row['gear_position']) else None,
                    'ignition_status': row['ignition_status'] if pd.notna(row['ignition_status']) else None,
                    'acceleration_long_g': row['acceleration_long_g'] if pd.notna(row['acceleration_long_g']) else None,
                    'acceleration_lat_g': row['acceleration_lat_g'] if pd.notna(row['acceleration_lat_g']) else None,
                    'fuel_level_pct': row['fuel_level_pct'] if pd.notna(row['fuel_level_pct']) else None,
                    'oil_life_pct': row['oil_life_pct'] if pd.notna(row['oil_life_pct']) else None,
                    'odometer_mi': row['odometer_mi'] if pd.notna(row['odometer_mi']) else None,
                })

triggered = pd.DataFrame(all_triggered_rows)
print(f"Triggered rows: {len(triggered):,}")

# Combine with Round 3
print("\n--- Combining ---")
round3 = resampled[['vehicle_id', 'tick_time', 'speed_mph', 'engine_rpm', 'gear_position',
                     'ignition_status', 'acceleration_long_g', 'acceleration_lat_g',
                     'fuel_level_pct', 'oil_life_pct', 'odometer_mi']].copy()
round3 = round3.rename(columns={'tick_time': 'timestamp'})
round3['trigger_type'] = 'scheduled'

combined = pd.concat([round3, triggered], ignore_index=True)
combined = combined.sort_values(['vehicle_id', 'timestamp', 'trigger_type'])
combined = combined.drop_duplicates(subset=['vehicle_id', 'timestamp'], keep='first')
combined = combined.sort_values(['vehicle_id', 'timestamp']).reset_index(drop=True)

print(f"Final rows: {len(combined):,}")

# Save
combined.to_csv('round4/advanced_resampled.csv', index=False)
print("Saved!")

# Analysis
print("\n" + "="*60)
round3_count = len(resampled)
extra = len(combined) - round3_count
print(f"Round 3: {round3_count:,}, Round 4: {len(combined):,}, Extra: {extra:,} ({extra/round3_count*100:.2f}%)")

combined['ts_dt'] = pd.to_datetime(combined['timestamp'])
combined['sec_mod'] = combined['ts_dt'].dt.second % 10
true_off = combined[(combined['trigger_type'] != 'scheduled') & (combined['sec_mod'] != 0)]
print(f"Off-grid: {len(true_off):,} ({len(true_off)/len(combined)*100:.2f}%)")
print(f"\n{combined['trigger_type'].value_counts()}")

# Save summary
import json
with open('round4/analysis_summary.json', 'w') as f:
    json.dump({
        'round3_rows': int(round3_count),
        'round4_rows': int(len(combined)),
        'extra_rows': int(extra),
        'off_grid_rows': int(len(true_off)),
        'trigger_dist': combined['trigger_type'].value_counts().to_dict()
    }, f, indent=2)

print("\nDone!")