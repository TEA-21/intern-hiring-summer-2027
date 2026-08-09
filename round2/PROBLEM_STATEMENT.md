# Round 2 — Hard-Driving Events

Using the cleaned dataset you built in Round 1, find moments where a vehicle was driving aggressively — hard acceleration, hard braking, or hard cornering.

You decide what counts as a hard-driving event. State your reasoning clearly and be ready to justify your choices.

## Deliverable

An events table, one row per detected event, with:

- vehicle_id
- event_label (what kind of event)
- start_time, end_time
- start_speed, end_speed
- start_g, end_g
- number of messages, number of distinct timestamps
- estimated distance travelled during the event

Plus a short write-up:
- The threshold you chose and why
- Total events found, broken down by event type and by vehicle
- Event duration distribution — at minimum the median and upper percentiles, plus how many (if any) are unusually long and what you think that means
- What fraction of events had a resolvable speed and distance at both boundaries
- Anything unusual you noticed in the data
