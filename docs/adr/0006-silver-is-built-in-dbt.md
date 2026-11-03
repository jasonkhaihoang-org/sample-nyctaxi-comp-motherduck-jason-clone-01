---
status: decided
date: 2026-10-14
---

# The conformed trip grain is built in dbt, not in a script

Yellow and green trips are conformed onto one grain by `int_trips_conformed`, built by dbt from two staging models that are each one-to-one with a bronze table. One row per distinct trip, shared column names, a `service_type` discriminator, derived duration, speed and calendar keys, and no filtering. Columns that exist on only one fleet are dropped here rather than carried as a column that is null for a whole fleet: a column that is structurally null for most rows invites averages that are silently wrong, so a consumer who needs one reads staging or `int_trips_enriched` on purpose. There is no `silver` schema.

This supersedes ADR 0001. Its reasoning for conforming still holds; what changed is where it is built. ADR 0001 placed the grain in `silver.trips`, built by a script outside dbt.

## Considered options

- **Keep the script** — rejected: the grain would sit outside the project that owns every consumer, with no tests and no lineage.
- **A `silver` schema built by dbt models** — rejected: it keeps a layer that the dbt layering (staging, intermediate, gold) already covers.
- **Staging plus one intermediate model** — chosen.

## Consequences

- The model has the same row count and the same set of trip keys as the script it replaced.
- `int_trips_enriched` rejoins the fleet-specific columns from the extras models.
- A unit test covers the deduplication and the key.

## Affected designs

- [`models/intermediate/int_trips_conformed.md`](../design/models/intermediate/int_trips_conformed.md)
- [`models/staging/stg_tlc__yellow_tripdata.md`](../design/models/staging/stg_tlc__yellow_tripdata.md)
- [`models/staging/stg_tlc__green_tripdata.md`](../design/models/staging/stg_tlc__green_tripdata.md)
- [`models/intermediate/int_trips_enriched.md`](../design/models/intermediate/int_trips_enriched.md)
- [`models/staging/stg_tlc__fhvhv_tripdata.md`](../design/models/staging/stg_tlc__fhvhv_tripdata.md)
- [`models/agg/agg_hvfhv_trip_zone_daily.md`](../design/models/agg/agg_hvfhv_trip_zone_daily.md)
