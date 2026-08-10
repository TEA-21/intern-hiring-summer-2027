"""
Round 2 - Hard-Driving Events Detection (Fixed)
Using acceleration data to identify aggressive driving events.
Only counts events with MULTIPLE CONSECUTIVE readings above threshold.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Higher thresholds - using 0.4g for meaningful aggressive driving
# 0.3g is too sensitive - normal driving frequently exceeds this
HARD_ACCEL_THRESHOLD = 0.4   # g (positive = acceleration)
HARD_BRAKE_THRESHOLD = -0.4  # g (negative = deceleration)
HARD_CORNER_THRESHOLD = 0.4  # g (absolute lateral acceleration)

# Minimum consecutive readings to count as an event
MIN_CONSECUTIVE_READINGS = 2

# Time gap threshold: if gap > 2 seconds, break the event
TIME_GAP_THRESHOLD = pd.Timedelta(seconds=2)

print("Loading data...")
df = pd.read_csv('round1/data/merged_data.csv', low_memory=False,
                 parse_dates=['timestamp'])

# Convert to numeric
df['acceleration_long_g'] = pd.to_numeric(df['acceleration_long_g'], errors='coerce')
df['acceleration_lat_g'] = pd.to_numeric(df['acceleration_lat_g'], errors='coerce')
df['speed_mph'] = pd.to_numeric(df['speed_mph'], errors='coerce')
df['odometer_mi'] = pd.to_numeric(df['odometer_mi'], errors='coerce')

# Sort by vehicle and time
df = df.sort_values(['vehicle_id', 'timestamp']).reset_index(drop=True)

print(f"Loaded {len(df):,} records")

# Classify each reading
def classify_reading(row):
    """Classify a single reading as event type or 'normal'"""
    if pd.isna(row['acceleration_long_g']) or pd.isna(row['acceleration_lat_g']):
        return 'normal'

    long_g = row['acceleration_long_g']
    lat_g = row['acceleration_lat_g']

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

# Mark event candidates (non-normal readings)
df['is_candidate'] = df['event_type'] != 'normal'

# Calculate time diffs
df['time_diff'] = df.groupby('vehicle_id')['timestamp'].diff()

# Break events if:
# 1. Gap > TIME_GAP_THRESHOLD
# 2. Reading is normal (gap in hard driving)
df['event_break'] = (df['time_diff'] > TIME_GAP_THRESHOLD) | (df['is_candidate'] != df['is_candidate'].shift(1))

# Assign event IDs
df['event_id'] = df['event_break'].cumsum()

# Filter to only event candidates
events_raw = df[df['is_candidate']].copy()

# Count consecutive readings per event
event_counts = events_raw.groupby(['vehicle_id', 'event_id']).size().reset_index(name='count')

# Only keep events with MIN_CONSECUTIVE_READINGS or more
valid_events = event_counts[event_counts['count'] >= MIN_CONSECUTIVE_READINGS]
print(f"Events with >= {MIN_CONSECUTIVE_READINGS} consecutive readings: {len(valid_events):,}")

# Now build the final events from only valid events
events = []

for idx, row in valid_events.iterrows():
    vehicle_id = row['vehicle_id']
    event_id = row['event_id']

    group = events_raw[(events_raw['vehicle_id'] == vehicle_id) & (events_raw['event_id'] == event_id)]

    if len(group) == 0:
        continue

    # Dominant event type
    type_counts = group['event_type'].value_counts()
    dominant_type = type_counts.index[0]

    # Event boundaries
    start_time = group['timestamp'].min()
    end_time = group['timestamp'].max()

    # Get start/end rows
    start_row = group.iloc[0]
    end_row = group.iloc[-1]

    events.append({
        'vehicle_id': vehicle_id,
        'event_label': dominant_type,
        'start_time': start_time,
        'end_time': end_time,
        'start_speed': round(start_row['speed_mph'], 2) if pd.notna(start_row['speed_mph']) else None,
        'end_speed': round(end_row['speed_mph'], 2) if pd.notna(end_row['speed_mph']) else None,
        'start_g': round(start_row['acceleration_long_g'], 4),
        'end_g': round(end_row['acceleration_long_g'], 4),
        'num_messages': len(group),
        'num_timestamps': group['timestamp'].nunique(),
        'distance_traveled_mi': None,  # Can't reliably calculate
        'max_g': round(group['acceleration_long_g'].abs().max(), 4) if dominant_type != 'hard_corner'
                 else round(group['acceleration_lat_g'].abs().max(), 4)
    })

events_df = pd.DataFrame(events)
print(f"\nFinal events: {len(events_df):,}")

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
print(f"Events per vehicle per day (7 days): {len(events_df) / events_df['vehicle_id'].nunique() / 7:.1f}")

print(f"\nEvents by type:")
for event_type, count in events_df['event_label'].value_counts().items():
    print(f"  {event_type}: {count:,} ({count/len(events_df)*100:.1f}%)")

print(f"\nDuration distribution:")
events_df['duration'] = (pd.to_datetime(events_df['end_time']) - pd.to_datetime(events_df['start_time'])).dt.total_seconds()
duration = events_df['duration']
print(f"  Min: {duration.min():.2f}s, Max: {duration.max():.2f}s, Median: {duration.median():.1f}s")
print(f"  75th percentile: {duration.quantile(0.75):.1f}s")
print(f"  95th percentile: {duration.quantile(0.95):.1f}s")

print(f"\nMessages per event:")
print(f"  2 messages: {(events_df['num_messages'] == 2).sum():,}")
print(f"  3-5 messages: {((events_df['num_messages'] >= 3) & (events_df['num_messages'] <= 5)).sum():,}")
print(f"  6+ messages: {(events_df['num_messages'] >= 6).sum():,}")

print(f"\nSpeed availability: {events_df['start_speed'].notna().mean()*100:.1f}%")