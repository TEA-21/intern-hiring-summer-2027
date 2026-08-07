# Round 2 — Hard-Driving Events

Using the cleaned dataset you built in Round 1, find moments where a vehicle was driving aggressively — hard acceleration, hard braking, or hard cornering.

A hard-driving event is: a continuous period, sustained for more than 2 seconds, where the absolute g-force exceeds 0.35g, treated as a single event as long as it stays in the same direction (same axis, same sign). A gap of more than 2 seconds between qualifying readings ends the event.

Watch for gaps in cadence between your signals — some parameters report far less often than others, and an event's duration is usually shorter than the gap between readings for some of them.

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
- Total events found, broken down by event type and by vehicle
- Event duration distribution — at minimum, the median and P90/P95/P99, plus how many (if any) are unusually long and what you think that means
- What fraction of events had a resolvable speed/distance at both boundaries
- How you resolved speed/distance when there wasn't an exact reading at the event boundary
- Anything unusual you noticed in the data while doing this
