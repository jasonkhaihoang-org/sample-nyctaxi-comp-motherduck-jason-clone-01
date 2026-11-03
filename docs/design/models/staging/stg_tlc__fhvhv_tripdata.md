---
artifacts: [stg_tlc__fhvhv_tripdata]
---

# stg_tlc__fhvhv_tripdata

High-volume for-hire (HVFHV) trips as loaded, renamed and typed.

## Grain

One row per row of `bronze.fhvhv_tripdata`.

## Schema

- `stg_tlc__fhvhv_tripdata`: `staging` (default). Source: user answer (schemas).

## Decisions

- `D-01` Rename and type only, one-to-one with the bronze table, as the yellow and green staging models are. Every bronze column is carried, plus `_dlt_load_id`; `_dlt_id` is dropped, as the other TLC staging models drop it. Source: docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md R-02, [ADR 0005](../../../adr/0005-all-raw-sources-are-loaded-by-dlt.md).
- `D-02` `PULocationID` and `DOLocationID` become `pickup_location_id` and `dropoff_location_id`, the names the TLC staging models use, so the aggregate keys like `agg_trip_zone_daily`. Source: docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md R-04.
- `D-03` Each UTC-tagged timestamp is brought back to a plain timestamp with `timezone('UTC', ...)`, as `stg_tlc__yellow_tripdata` `D-02` does, so every date derived from it does not depend on the session's time zone. Source: [ADR 0005](../../../adr/0005-all-raw-sources-are-loaded-by-dlt.md), [ADR 0006](../../../adr/0006-silver-is-built-in-dbt.md).
- `D-04` A view, as every staging model is (`dbt_project.yml` `staging: +materialized: view`). An internal relation, so it has no Ossie entry. Source: `.agents/skills/dbt-models/SKILL.md`.

## Rejected

- Unioning HVFHV into `int_trips_conformed`: an HVFHV trip is not a taxi trip ([ADR 0006](../../../adr/0006-silver-is-built-in-dbt.md); proposal 0001 is still proposed).

## Consumers

Depended on by: `agg_hvfhv_trip_zone_daily`.

## History

- 2026-11-03 — new-intent-d0d80c5b — design record written; terms: added HVFHV trip — D-01 to D-04
