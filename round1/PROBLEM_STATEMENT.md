# Data Reconstruction Challenge

## What you're working with

You've been given real (anonymized) telemetry data from a small fleet of vehicles over a one-week period. No location data, no VIN — just vehicle behavior: speed, acceleration, fuel level, oil life, odometer, engine RPM, gear position, and ignition status.

The data was not handed to you as one clean table. It's spread across a handful of files in `data/raw/`. Different sensors on a vehicle report at different rates, and the files reflect that — some are dense, some are sparse. They're also not all in the same format.

There's also one file with vehicle metadata (make/model/year) so you can tie a vehicle ID back to something recognizable.

Real-world telemetry is never perfectly clean. Expect some of what you find in here to be genuine sensor noise or logging artifacts, and some of it to be more clearly wrong than that.

## What we want from you

1. Figure out what each file is and how to read it.
2. Combine everything into a single, consistent table — one row per vehicle per timestamp, with every parameter aligned.
3. Look critically at what you've combined. Some of it won't hold up. Decide what's usable, what's noise, and what should be dropped or corrected — and be able to explain your reasoning for each call you make.
4. Get to a clean, combined dataset you'd be comfortable handing to someone else to build on.

## Deliverable

- Your cleaned, combined dataset (whatever format is convenient for you — CSV, Parquet, whatever)
- A short write-up: how you approached combining the files, what data quality issues you found, and how you handled each one
- Whatever code/notebook you used to get there

We're not looking for a specific "correct" pipeline. We're evaluating how you investigate unfamiliar data, the judgment calls you make, and whether you can justify them. Take the time you need, do your own research, and come back to us with what you found.
