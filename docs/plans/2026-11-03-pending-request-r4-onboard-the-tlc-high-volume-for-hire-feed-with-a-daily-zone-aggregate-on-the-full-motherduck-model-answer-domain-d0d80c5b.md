# Plan: Pending request R4: onboard the TLC high-volume for-hire feed with a daily zone aggregate, on the full MotherDuck model-answer Domain

**Goal:** Land January 2024 HVFHV trips in bronze as a resource on `tlc`, loaded on the `tlc_pipeline` Flight into the Intent's Ephemeral database, stage them, and publish a daily pickup-zone trip count beside `agg_trip_zone_daily`, with the semantic layer moving with it.

**Requirement:** `docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md`

**Constraints:**
- `fhvhv_tripdata` loads `HVFHV_MONTHS = ["2024-01"]` only; the other `tlc` resources keep their window (`tlc.md` D-08).
- Every load runs on the `tlc_pipeline` Flight (`motherduck/dlt.md` § Sandbox run): the git secret rewritten first, `update_flight` with the committed `flight.py`, `requirements.txt` and `config.json`, then `run_flight` overriding `DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE` with `VD_EPHM_MOTHERDUCK_DATABASE` and `GIT_REF` with the Intent branch; each run's own `get_flight_logs` read goes to `assert_destination.py --resolved-from-log`.
- A safety run (`DLT_INGEST_LIMIT=1`, `DEV_MODE=true`), then one full load after the pipeline and docs are final.
- dbt through the runtime wrapper on target `dev` with the path selection and defer, one run per target.
- Nothing is written to `sa_prd`.

## Scope and impact

| Artifact | Kind | Action | Requirements | Design record | Gate |
| --- | --- | --- | --- | --- | --- |
| `tlc` (`ingestion/sources/tlc.py`, `ingestion/docs/tlc.yml`, `tests/ingestion/test_tlc.py`), loaded by `ingestion/tlc_pipeline.Flight` | pipeline | modify | `R-01`, `R-07` | `docs/design/pipelines/tlc.md` | `pytest tests/ingestion`, `assert_destination.py --resolved-from-log` |
| `stg_tlc__fhvhv_tripdata` | model | create | `R-02` | `docs/design/models/staging/stg_tlc__fhvhv_tripdata.md` | `dbt build --select "stg_tlc__fhvhv_tripdata state:modified+,+stg_tlc__fhvhv_tripdata" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` |
| `agg_hvfhv_trip_zone_daily` | model | create | `R-03`–`R-05` | `docs/design/models/agg/agg_hvfhv_trip_zone_daily.md` | `dbt build --select "agg_hvfhv_trip_zone_daily state:modified+,+agg_hvfhv_trip_zone_daily" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` |
| `logical-model/nyc_taxi_analytics.ossie.yaml` + generated semantic tests | logical-model | modify | `R-06` | agg record D-06 | the semantic-model chain |
| `ontology/` | ontology | none (gates re-run) | `R-06` | agg record D-07 | `validate`, `refs`, `glossary` |

**Change impact:** no existing model's SQL changes; the two new models have no consumers in this repo.

## Tasks

### Task 1: `fhvhv_tripdata` on `tlc`

**Requirements:** `R-01`, `R-07` · **Design:** `docs/design/pipelines/tlc.md` · **Skill:** generating-dlt-pipeline · **Depends on:** none

- [x] Author `ingestion/sources/tlc.py` (the resource, `HVFHV_MONTHS`, the row-group reader), `ingestion/docs/tlc.yml`, `tests/ingestion/test_tlc.py`; `pytest tests/ingestion`; commit and push
- [x] Safety run on the Flight; `assert_destination.py --resolved-from-log` on its log
- [x] Load: full, once, on the Flight; `assert_destination.py --resolved-from-log`; the acceptance condition of `R-01`

### Task 2: `stg_tlc__fhvhv_tripdata`

**Requirements:** `R-02` · **Design:** its record · **Skill:** generating-dbt-model · **Depends on:** 1

- [x] Author the source entry, the SQL and its `_staging.yml` entry; run its gate; the acceptance condition of `R-02`

### Task 3: `agg_hvfhv_trip_zone_daily`

**Requirements:** `R-03`–`R-05` · **Design:** its record · **Skill:** generating-dbt-model · **Depends on:** 2

- [x] Author the SQL, its `_agg.yml` entry, unit tests, the singular grain test and its `test-map.json` row; run its gate; the acceptance conditions of `R-03`–`R-05`

### Task 4: the semantic layer

**Requirements:** `R-06` · **Design:** agg record D-06, D-07 · **Skill:** semantic-model, validating-semantic-model, ontology · **Depends on:** 3

- [x] Author the `hvfhv_zone_day` star; `ossie.py generate-tests`; the chain, the semantic tests and the ontology gates
- [x] Commit and push Tasks 2 to 4

## Execution evidence
- Task 1: `pytest tests/ingestion -q` — 27 passed; `ruff check` — pass — e2083db. Git secret rewritten with `resolve_creds_and_run.py` and `{{BROKER:github}}` before each run; `validate-flight.py ingestion/tlc_pipeline.Flight --repo-root .` — exit 0; `create_flight` `tlc_pipeline` (`8c8e1438-83ae-490a-bfdb-367a08cc9d12`, version 1) with the committed program, requirements and config.
- Task 1: safety run (`run_flight` run 1: database `vd_eval_20261103195103_f31892c8ad9e_eph`, `GIT_REF` `intent/new-intent-d0d80c5b`, `DLT_INGEST_LIMIT=1`, `DEV_MODE=true`) — SUCCEEDED, exit_code 0, checked out the Intent branch at e2083db, dataset `bronze_20261103075644`, `fhvhv_tripdata` one row group (1,048,576 rows); `assert_destination.py --pipeline tlc --resolved-from-log .agents_tmp/tlc-safety-run.log` — `DESTINATION_OK`; Tier-1 on the dev dataset — PASS × 4 + audit; the dev dataset dropped.
- Task 1: full load (run 2, database and ref overridden only) — SUCCEEDED, exit_code 0, 8.5 minutes; `assert_destination.py --pipeline tlc --resolved-from-log .agents_tmp/tlc-full-load.log` — `DESTINATION_OK`; Tier-1 on `bronze` — PASS × 4 + audit; `bronze.fhvhv_tripdata` 19,663,930 rows, 0 outside January, 1 load; `audit_runs.total_rows_extracted` 29,386,558.
- Tasks 2 and 3: the path selection per target — `stg_tlc__fhvhv_tripdata` PASS=3; `agg_hvfhv_trip_zone_daily` PASS=11 (the run rebuilt the changed staging view on its path); both relations in `vd_eval_20261103195103_f31892c8ad9e_eph`. Acceptance: staged = bronze = aggregated = 19,663,930; 8,006 unique zone-days; 765 unknown-zone trips; keys `BIGINT`/`DATE` as `agg_trip_zone_daily`.
- Task 4: the `hvfhv_zone_day` star; `generate-tests`; the chain (35 of 35 named) and the ontology gates — exit 0 each; the semantic tests — PASS=2 WARN=1 (the existing levels finding). Committed in 3cb463a.
