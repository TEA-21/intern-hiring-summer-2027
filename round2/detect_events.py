"""
Round 2 - Hard-Driving Events Detection (Improved Pattern v2)
Using acceleration data to identify aggressive driving events.

Key improvements over original:
1. Events must have minimum DURATION (5+ seconds), not just consecutive readings
2. Merge consecutive same-type events with similar magnitude and small time gaps
3. This eliminates fragmentation of sustained driving into dozens of micro-events

Logic:
- Classify each reading as event type or 'normal' (vectorized)
- Group consecutive event candidates (same type, gap < 5s, magnitude within 0.15g)
- Only keep groups with duration >= 5 seconds
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Thresholds - 0.4g indicates genuinely aggressive driving
HARD_ACCEL_THRESHOLD = 0.4
HARD_BRAKE_THRESHOLD = -0.4
HARD_CORNER_THRESHOLD = 0.4

# Merge parameters to prevent fragmentation
MERGE_GAP_THRESHOLD = pd.Timedelta(seconds=5)
MERGE_G_MAG_THRESHOLD = 0.15

# Minimum event duration
MIN_EVENT_DURATION = pd.Timedelta(seconds=5)

print("Loading data...")
df = pd.read_csv('round1/data/merged_data.csv', low_memory=False,
                 parse_dates=['timestamp'])

# Convert to numeric (vectorized)
df['acceleration_long_g'] = pd.to_numeric(df['acceleration_long_g'], errors='coerce')
df['acceleration_lat_g'] = pd.to_numeric(df['acceleration_lat_g'], errors='coerce')
df['speed_mph'] = pd.to_numeric(df['speed_mph'], errors='coerce')

# Sort by vehicle and time
df = df.sort_values(['vehicle_id', 'timestamp']).reset_index(drop=True)

print(f"Loaded {len(df):,} records")

# VECTORIZED classification (much faster than apply)
print("Classifying readings (vectorized)...")
long_g = df['acceleration_long_g']
lat_g = df['acceleration_lat_g']

# Create event_type column using vectorized operations
event_type = pd.Series('normal', index=df.index)
event_type[(long_g > HARD_ACCEL_THRESHOLD)] = 'hard_accel'
event_type[(long_g < HARD_BRAKE_THRESHOLD)] = 'hard_brake'
# Cornering: when lateral exceeds threshold (but not already classified as accel/brake)
corner_mask = (abs(lat_g) > HARD_CORNER_THRESHOLD) & (event_type == 'normal')
event_type[corner_mask] = 'hard_corner'

df['event_type'] = event_type

# Mark event candidates (non-normal readings)
df['is_candidate'] = df['event_type'] != 'normal'

# Calculate time diffs
df['time_diff'] = df.groupby('vehicle_id')['timestamp'].diff()

print("Detecting and merging events...")

# Get only candidate rows
candidates = df[df['is_candidate']].copy()
print(f"Candidate readings: {len(candidates):,}")

# Build merged events - iterate per vehicle
merged_events = []

for vehicle_id, group in candidates.groupby('vehicle_id'):
    group = group.sort_values('timestamp').reset_index(drop=True)

    if len(group) == 0:
        continue

    # Start first potential event
    event_start_time = group.iloc[0]['timestamp']
    event_type = group.iloc[0]['event_type']
    max_g = abs(group.iloc[0]['acceleration_long_g'] if event_type != 'hard_corner'
                else group.iloc[0]['acceleration_lat_g'])
    readings = 1

    for i in range(1, len(group)):
        curr = group.iloc[i]
        prev = group.iloc[i-1]

        time_gap = curr['timestamp'] - prev['timestamp']
        curr_g = abs(curr['acceleration_long_g'] if curr['event_type'] != 'hard_corner'
                     else curr['acceleration_lat_g'])

        # Check if this reading should be merged with current event
        same_type = curr['event_type'] == event_type
        small_gap = time_gap <= MERGE_GAP_THRESHOLD
        similar_magnitude = abs(curr_g - max_g) <= MERGE_G_MAG_THRESHOLD

        if same_type and small_gap and similar_magnitude:
            # Merge into current event
            max_g = max(max_g, curr_g)
            readings += 1
        else:
            # Finalize current event before starting new one
            event_end_time = prev['timestamp']
            event_duration = event_end_time - event_start_time

            if event_duration >= MIN_EVENT_DURATION:
                merged_events.append({
                    'vehicle_id': vehicle_id,
                    'event_label': event_type,
                    'start_time': event_start_time,
                    'end_time': event_end_time,
                    'max_g': round(max_g, 4),
                    'num_messages': readings
                })

            # Start new event
            event_start_time = curr['timestamp']
            event_type = curr['event_type']
            max_g = curr_g
            readings = 1

    # Don't forget the last event
    event_end_time = group.iloc[-1]['timestamp']
    event_duration = event_end_time - event_start_time

    if event_duration >= MIN_EVENT_DURATION:
        merged_events.append({
            'vehicle_id': vehicle_id,
            'event_label': event_type,
            'start_time': event_start_time,
            'end_time': event_end_time,
            'max_g': round(max_g, 4),
            'num_messages': readings
        })

events_df = pd.DataFrame(merged_events)
print(f"Merged events (duration >= 5s): {len(events_df):,}")

# Add computed fields
events_df['duration'] = (pd.to_datetime(events_df['end_time']) - pd.to_datetime(events_df['start_time'])).dt.total_seconds()
events_df['start_speed'] = None
events_df['end_speed'] = None
events_df['start_g'] = None
events_df['end_g'] = None
events_df['num_timestamps'] = events_df['num_messages']
events_df['distance_traveled_mi'] = None

# Save
output_path = Path('round2/events.csv')
events_df.to_csv(output_path, index=False)
print(f"Saved to {output_path}")

# Analysis
print("\n" + "="*60)
print("EVENT ANALYSIS")
print("="*60)

print(f"\nTotal events: {len(events_df):,}")
print(f"Unique vehicles: {events_df['vehicle_id'].nunique()}")

events_per_day = len(events_df) / events_df['vehicle_id'].nunique() / 7
print(f"Events per vehicle per day (7 days): {events_per_day:.1f}")

print(f"\nEvents by type:")
for event_type, count in events_df['event_label'].value_counts().items():
    print(f"  {event_type}: {count:,} ({count/len(events_df)*100:.1f}%)")

duration = events_df['duration']
print(f"\nDuration distribution:")
print(f"  Min: {duration.min():.1f}s, Max: {duration.max():.1f}s, Median: {duration.median():.1f}s")
print(f"  75th percentile: {duration.quantile(0.75):.1f}s")
print(f"  95th percentile: {duration.quantile(0.95):.1f}s")

print(f"\nMessages per event:")
print(f"  1-10 messages: {(events_df['num_messages'] <= 10).sum():,}")
print(f"  11-20 messages: {((events_df['num_messages'] > 10) & (events_df['num_messages'] <= 20)).sum():,}")
print(f"  21+ messages: {(events_df['num_messages'] > 20).sum():,}")

events_per_vehicle = events_df.groupby('vehicle_id').size().sort_values()
print(f"\nEvents per vehicle distribution:")
print(f"  Min: {events_per_vehicle.min()}, Max: {events_per_vehicle.max()}")
print(f"  Median: {events_per_vehicle.median():.0f}, Mean: {events_per_vehicle.mean():.1f}")
print(f"  Std: {events_per_vehicle.std():.1f}")

print(f"\nTop 5 vehicles by event count:")
for vid, cnt in events_per_vehicle.tail(5).items():
    print(f"  {vid[:8]}...: {cnt} events")