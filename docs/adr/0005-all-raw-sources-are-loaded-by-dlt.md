---
status: decided
date: 2026-10-14
---

# Every raw source is loaded by a dlt pipeline that fetches from the source

The TLC trips and zone lookup, the fleet operator's platform (`ops_raw`) and the master-data platform (`mdm_raw`) are each loaded by a dlt pipeline in `ingestion/`. The TLC pipeline downloads its files from the public TLC site; nothing is downloaded or staged by hand first. Each pipeline follows the plugin's DuckDB-local template and imports `vibedata.dlt.duckdb`. The loaded window is three months, reloaded in full on every run (`replace`), with no sampling.

## Considered options

- **Scripts that write into the warehouse** — rejected: no load metadata, no schema contract, and a manual download step before the build.
- **dlt for TLC only** — rejected: the simulated sources are still sources, and leaving them as scripts keeps two ways to land data.
- **dlt for every raw source** — chosen.

## Consequences

- Source column names are kept verbatim (`naming = "direct"`) and every row carries `_dlt_load_id` and `_dlt_id`.
- Bronze timestamps arrive tagged UTC, so staging converts them to plain timestamps.
- A one-off fixed window has no freshness check.
- Changing the dlt normalisation settings against an existing database fails; the database is rebuilt instead.

## Affected designs

- [`pipelines/tlc.md`](../design/pipelines/tlc.md)
- [`pipelines/ops.md`](../design/pipelines/ops.md)
- [`pipelines/mdm.md`](../design/pipelines/mdm.md)
- [`models/staging/stg_tlc__yellow_tripdata.md`](../design/models/staging/stg_tlc__yellow_tripdata.md)
- [`models/staging/stg_tlc__green_tripdata.md`](../design/models/staging/stg_tlc__green_tripdata.md)
- [`orchestration/driver_weekly_refresh.md`](../design/orchestration/driver_weekly_refresh.md)
