---
artifacts: [tlc]
---

# tlc

Loads the NYC TLC yellow and green trip files, the high-volume for-hire (HVFHV) trip file and the zone lookup into `bronze`.

## Grain

Four resources: one row per row of each source file (`yellow_tripdata`, `green_tripdata`, `fhvhv_tripdata`) and one per zone (`taxi_zone_lookup`).

## Schema

- `tlc` source: `bronze` (default). Source: user answer (schemas).

## Decisions

- `D-01` Fetch the files from the public TLC site for 2024-01 to 2024-03; nothing is downloaded or staged by hand ([ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md)). Source: docs/requirement/2026-10-14-load-every-raw-source-with-dlt-and-build-silver-in-dbt.md R-01, R-04, [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md).
- `D-02` Load the source verbatim: no casts, filters or sampling. Column names are kept (`naming = "direct"`), and every row carries `_dlt_load_id` and `_dlt_id`. Source: docs/requirement/2026-10-14-load-every-raw-source-with-dlt-and-build-silver-in-dbt.md R-01.
- `D-03` `yellow_tripdata`: write disposition `replace` (each run reloads the whole fixed window); no incremental cursor; contract `columns: freeze`, `tables: evolve`, `data_type: freeze`; duplicate keys: none removed, because bronze is not deduplicated (`int_trips_conformed` does that). Source: docs/requirement/2026-10-14-load-every-raw-source-with-dlt-and-build-silver-in-dbt.md R-01, [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md).
- `D-04` `green_tripdata`: write disposition `replace` (each run reloads the whole fixed window); no incremental cursor; contract `columns: freeze`, `tables: evolve`, `data_type: freeze`; duplicate keys: none removed, as for yellow. Source: docs/requirement/2026-10-14-load-every-raw-source-with-dlt-and-build-silver-in-dbt.md R-01, [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md).
- `D-05` `taxi_zone_lookup`: write disposition `replace` (each run reloads the whole fixed window); no incremental cursor; contract `columns: freeze`, `tables: evolve`, `data_type: freeze`; duplicate keys: none expected: one row per zone. Source: docs/requirement/2026-10-14-load-every-raw-source-with-dlt-and-build-silver-in-dbt.md R-01, [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md).
- `D-06` `tables` stays `evolve`: the database is rebuilt from empty on every run, so freezing it would forbid creating the tables. Source: docs/requirement/2026-10-14-load-every-raw-source-with-dlt-and-build-silver-in-dbt.md R-01.
- `D-07` The pipeline imports `setup_environment` and `finalize` from `vibedata.dlt.duckdb`. Outside Studio it needs `VD_DOMAIN_DATA_PLATFORM=duckdb_local`, `VD_DOMAIN_SECRET_STORE_KIND=local_toml` and `VD_EPHM_DUCKDB_LOCAL_PATH`; `orchestration/run_ingest.py` sets them. Source: docs/requirement/2026-10-14-load-every-raw-source-with-dlt-and-build-silver-in-dbt.md R-01, [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md).
- `D-08` `fhvhv_tripdata` loads January 2024 only, its own window, while the other resources keep the window of `D-01`. The user chose January only after the conflict with [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md)'s three-month window was named, so February and March show taxi volume with no HVFHV beside it. Source: docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md R-01, user answer (load window).
- `D-09` `fhvhv_tripdata`: write disposition `replace` (each run reloads the whole fixed window); no incremental cursor; contract `columns: freeze`, `tables: evolve`, `data_type: freeze`, as `D-06` keeps `tables`; duplicate keys: none removed, because bronze is not deduplicated and the file carries no identifier. Source: docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md R-01, [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md).
- `D-10` `fhvhv_tripdata` streams its file to a temporary file and yields one Parquet row group at a time, so memory holds one row group, never the whole month; the HVFHV file is many times larger than a taxi file (sizes in the Verification's Discovery). Source: docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md R-01, `.agents/skills/dlt/SKILL.md` ("yields pyarrow tables per parquet row group").
- `D-11` HVFHV is a resource on this source, not a new source, and the `tlc_pipeline` Flight loads it with no change to its program: `flight.py` runs every resource the source returns. Source: `.agents/skills/dlt/SKILL.md` ("Another table from a source that is already loaded … is a resource on that source, not a new source"), [ADR 0005](../../adr/0005-all-raw-sources-are-loaded-by-dlt.md).

## Rejected

- Sampling the trips: a row filter has no place in bronze, and three months already limits volume.
- A download script that stages files before the load.
- A separate HVFHV source or pipeline: the repository's dlt skill makes another TLC file a resource on `tlc`.
- Loading HVFHV for the full three-month window: the user asked for January 2024 only.

## Consumers

Depended on by: `stg_tlc__yellow_tripdata`, `stg_tlc__green_tripdata`, `stg_tlc__fhvhv_tripdata`; and by the `ops` and `mdm` pipelines, which reuse its source code (the yellow trips and the zone lookup).

## History

- - 2026-10-14 — setup-dlt-ingestion — design record written when TLC loading moved from scripts to dlt — D-01 to D-07
- 2026-11-03 — new-intent-1b61894a — HVFHV added as a January-only resource, read row group by row group; terms: added HVFHV trip — D-08 to D-11
