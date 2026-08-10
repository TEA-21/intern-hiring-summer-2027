"""
Round 2 - Hard-Driving Events Detection
Using acceleration data to identify aggressive driving events.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Thresholds chosen based on data analysis:
# - 99th percentile for longitudinal acceleration is ~0.24g
# - 99.9th percentile is ~1.04g (extreme values)
# - Using 0.3g as threshold: clearly aggressive but captures meaningful events

HARD_ACCEL_THRESHOLD = 0.3  # g (positive = acceleration)
HARD_BRAKE_THRESHOLD = -0.3  # g (negative = deceleration)
HARD_CORNER_THRESHOLD = 0.3  # g (absolute lateral acceleration)

# Time gap threshold: if gap > 5 seconds, start a new event
TIME_GAP_THRESHOLD = pd.Timedelta(seconds=5)

print("Loading data...")
df = pd.read_csv('round1/data/merged_data.csv', low_memory=False,
                 parse_dates=['timestamp'])

# Convert acceleration, odometer, and speed to numeric
df['acceleration_long_g'] = pd.to_numeric(df['acceleration_long_g'], errors='coerce')
df['acceleration_lat_g'] = pd.to_numeric(df['acceleration_lat_g'], errors='coerce')
df['odometer_mi'] = pd.to_numeric(df['odometer_mi'], errors='coerce')
df['speed_mph'] = pd.to_numeric(df['speed_mph'], errors='coerce')

# Sort by vehicle and time
df = df.sort_values(['vehicle_id', 'timestamp']).reset_index(drop=True)

print(f"Loaded {len(df):,} records")
print(f"Speed data available: {df['speed_mph'].notna().sum():,} records")

# Classify each reading
def classify_reading(row):
    """Classify a single reading as one of: 'hard_accel', 'hard_brake', 'hard_corner', 'normal'"""
    if pd.isna(row['acceleration_long_g']) or pd.isna(row['acceleration_lat_g']):
        return 'normal'

    long_g = row['acceleration_long_g']
    lat_g = row['acceleration_lat_g']

    # Check for hard events (prioritize longitudinal over lateral)
    if long_g > HARD_ACCEL_THRESHOLD:
        return 'hard_accel'
    elif long_g < HARD_BRAKE_THRESHOLD:
        return 'hard_brake'
    elif abs(lat_g) > HARD_CORNER_THRESHOLD:
        return 'hard_corner'
    else:
        return 'normal'

print("Classifying readings...")
df['event_type'] = df.apply(classify_reading, axis=1)

# Detect event sequences
print("Detecting event sequences...")

# Identify gaps in time that break an event
df['time_diff'] = df.groupby('vehicle_id')['timestamp'].diff()
df['new_event'] = (df['time_diff'] > TIME_GAP_THRESHOLD) | (df['event_type'] != df['event_type'].shift(1))

# Event number for each vehicle
df['event_num'] = df.groupby('vehicle_id')['new_event'].cumsum()

events = []

for (vehicle_id, event_num), group in df.groupby(['vehicle_id', 'event_num']):
    if len(group) == 0:
        continue

    # Get valid readings (not 'normal')
    active = group[group['event_type'] != 'normal']

    if len(active) == 0:
        continue

    # Determine dominant event type
    type_counts = active['event_type'].value_counts()
    dominant_type = type_counts.index[0]

    # Event boundaries
    start_time = active['timestamp'].min()
    end_time = active['timestamp'].max()

    # Start and end G values (first/last active reading)
    start_row = active.iloc[0]
    end_row = active.iloc[-1]

    start_g_long = start_row['acceleration_long_g']
    end_g_long = end_row['acceleration_long_g']
    start_g_lat = start_row['acceleration_lat_g']
    end_g_lat = end_row['acceleration_lat_g']

    # Get speed from the first and last active readings
    start_speed = start_row['speed_mph'] if pd.notna(start_row['speed_mph']) else None
    end_speed = end_row['speed_mph'] if pd.notna(end_row['speed_mph']) else None

    # Calculate distance from odometer if available
    odometer_col = pd.to_numeric(active['odometer_mi'], errors='coerce').dropna()
    if len(odometer_col) > 0:
        odometer_start = odometer_col.iloc[0]
        odometer_end = odometer_col.iloc[-1]
        if not pd.isna(odometer_start) and not pd.isna(odometer_end):
            distance_traveled = float(odometer_end) - float(odometer_start)
        else:
            distance_traveled = None
    else:
        distance_traveled = None

    # Event statistics
    num_messages = len(active)
    num_timestamps = active['timestamp'].nunique()
    duration = (end_time - start_time).total_seconds()

    events.append({
        'vehicle_id': vehicle_id,
        'event_label': dominant_type,
        'start_time': start_time,
        'end_time': end_time,
        'start_speed': round(start_speed, 2) if start_speed is not None else None,
        'end_speed': round(end_speed, 2) if end_speed is not None else None,
        'start_g': round(start_g_long, 4) if not pd.isna(start_g_long) else None,
        'end_g': round(end_g_long, 4) if not pd.isna(end_g_long) else None,
        'num_messages': num_messages,
        'num_timestamps': num_timestamps,
        'distance_traveled_mi': round(distance_traveled, 2) if distance_traveled else None,
        'max_g': round(active['acceleration_long_g'].abs().max(), 4) if len(active) > 0 else None
    })

events_df = pd.DataFrame(events)
print(f"\nDetected {len(events_df):,} events")

# Save events
output_path = Path('round2/events.csv')
events_df.to_csv(output_path, index=False)
print(f"Saved events to {output_path}")

# Analysis
print("\n" + "="*60)
print("EVENT ANALYSIS")
print("="*60)

print(f"\nTotal events: {len(events_df):,}")
print(f"\nEvents by type:")
type_counts = events_df['event_label'].value_counts()
for event_type, count in type_counts.items():
    pct = (count / len(events_df)) * 100
    print(f"  {event_type}: {count:,} ({pct:.1f}%)")

print(f"\nEvents by vehicle:")
vehicle_counts = events_df['vehicle_id'].value_counts()
print(f"  Unique vehicles with events: {len(vehicle_counts)}")
print(f"  Events per vehicle - mean: {vehicle_counts.mean():.1f}, median: {vehicle_counts.median():.0f}")

# Calculate duration from start/end times for analysis
events_df['duration_seconds'] = (pd.to_datetime(events_df['end_time']) - pd.to_datetime(events_df['start_time'])).dt.total_seconds()

print(f"\nDuration distribution (seconds):")
duration = events_df['duration_seconds']
print(f"  Min: {duration.min():.2f}")
print(f"  Max: {duration.max():.2f}")
print(f"  Mean: {duration.mean():.2f}")
print(f"  Median: {duration.median():.2f}")
print(f"  75th percentile: {duration.quantile(0.75):.2f}")
print(f"  90th percentile: {duration.quantile(0.90):.2f}")
print(f"  95th percentile: {duration.quantile(0.95):.2f}")
print(f"  99th percentile: {duration.quantile(0.99):.2f}")

# Unusually long events (> 2 minutes)
long_events = events_df[events_df['duration_seconds'] > 120]
print(f"\nUnusually long events (>120s): {len(long_events)}")

# Speed/distance resolvable
start_speed_resolvable = events_df['start_speed'].notna()
end_speed_resolvable = events_df['end_speed'].notna()
both_speed_resolvable = start_speed_resolvable & end_speed_resolvable
resolvable_distance = events_df['distance_traveled_mi'].notna()
print(f"\nEvents with resolvable start_speed: {start_speed_resolvable.sum():,} ({start_speed_resolvable.mean()*100:.1f}%)")
print(f"Events with resolvable end_speed: {end_speed_resolvable.sum():,} ({end_speed_resolvable.mean()*100:.1f}%)")
print(f"Events with resolvable distance: {resolvable_distance.sum():,} ({resolvable_distance.mean()*100:.1f}%)")

# Save summary
summary = {
    'threshold_accel': HARD_ACCEL_THRESHOLD,
    'threshold_brake': HARD_BRAKE_THRESHOLD,
    'threshold_corner': HARD_CORNER_THRESHOLD,
    'total_events': int(len(events_df)),
    'hard_accel_count': int((events_df['event_label'] == 'hard_accel').sum()),
    'hard_brake_count': int((events_df['event_label'] == 'hard_brake').sum()),
    'hard_corner_count': int((events_df['event_label'] == 'hard_corner').sum()),
    'median_duration': float(duration.median()),
    'p95_duration': float(duration.quantile(0.95)),
    'start_speed_available_pct': float(start_speed_resolvable.mean() * 100),
    'end_speed_available_pct': float(end_speed_resolvable.mean() * 100),
    'distance_available_pct': float(resolvable_distance.mean() * 100)
}

import json
with open('round2/analysis_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\nSaved summary to round2/analysis_summary.json")