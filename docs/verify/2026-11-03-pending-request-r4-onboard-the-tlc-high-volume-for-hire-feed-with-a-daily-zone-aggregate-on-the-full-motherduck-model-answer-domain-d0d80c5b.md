# Verification: Pending request R4: onboard the TLC high-volume for-hire feed with a daily zone aggregate, on the full MotherDuck model-answer Domain

## Verification

`verdict: verified` at `55b1c23`: January 2024 HVFHV trips are in the Ephemeral database's `bronze` as one full load on the `tlc_pipeline` Flight, which checked out the Intent branch and reconciles with the source file. `stg_tlc__fhvhv_tripdata` and `agg_hvfhv_trip_zone_daily` are built on target `dev` with the path selection and defer, and their tests pass. The `hvfhv_zone_day` star passes every semantic and ontology gate. Nothing landed in `sa_prd`. No golden baseline is configured: independent recomputation from bronze, staging and the file's footer stands in. Limits: the bronze preview renders every schema of the Ephemeral database (70 blocks), so the audit's preview rule cannot pass here (plugin defect, VD-7707); MotherDuck reported the plan's daily compute limit reached after the full load; this repo publishes no data contracts.

## Coverage

| Item | Evidence | Result | At |
| --- | --- | --- | --- |
| `R-01` January 2024 HVFHV in bronze as one full load | `query` on `vd_eval_20261103195103_f31892c8ad9e_eph`: `select count(*) as row_count, count(*) filter (where timezone('UTC', pickup_datetime) < TIMESTAMP '2024-01-01' or timezone('UTC', pickup_datetime) >= TIMESTAMP '2024-02-01') as outside_january, count(distinct _dlt_load_id) as loads, (select total_rows_extracted from bronze.audit_runs order by started_at desc limit 1) as extracted, (select count(*) from bronze.yellow_tripdata) as yellow, (select count(*) from bronze.green_tripdata) as green, (select count(*) from bronze.taxi_zone_lookup) as zones from bronze.fhvhv_tripdata` | 19,663,930 rows = the file's 19,663,930; 0 outside January; 1 load; extracted 29,386,558 = 19,663,930 + 9,554,778 yellow + 167,585 green + 265 zones | `55b1c23` |
| `R-02` staging one row per bronze row | the acceptance query below (`staged`, `bronze`) | 19,663,930 = 19,663,930 | `55b1c23` |
| `R-03` one row per zone per date, every trip, unknown zones kept | the same (`aggregated`, `staged_in_window`, `zone_days`, `distinct_keys`, `unknown_zone_trips`) | 19,663,930 = 19,663,930; 8,006 rows, 8,006 keys; 765 = the file's 765 in zones 264 and 265 | `55b1c23` |
| `R-04` keyed like `agg_trip_zone_daily` | the same (`key_types`) | both `pickup_location_id BIGINT`, `pickup_date DATE` | `55b1c23` |
| `R-05` existing models unchanged | `git diff --name-only 7fcde94 HEAD`; `dbt ls -s state:modified+ --resource-type model --state /data/cache/prod-selection --target dev` | only the two new `.sql` files; the modified set is exactly the two new models | `55b1c23` |
| `R-06` semantic layer | Gate results below | exit 0 each | `55b1c23` |
| `R-07` every load on the Flight, nothing in `sa_prd` | each run's config and log; `assert_destination.py --pipeline tlc --resolved-from-log`; each dbt gate's `run_results.json` | runs 1 and 2 with `DESTINATION__MOTHERDUCK__CREDENTIALS__DATABASE=vd_eval_20261103195103_f31892c8ad9e_eph` and `GIT_REF=intent/new-intent-d0d80c5b`; `DESTINATION_OK … vd_eval_20261103195103_f31892c8ad9e_eph` for both; both dbt relations in `vd_eval_20261103195103_f31892c8ad9e_eph` | `55b1c23` |

Acceptance query (`query` on `vd_eval_20261103195103_f31892c8ad9e_eph`):

```sql
select (select count(*) from vd_eval_20261103195103_f31892c8ad9e_eph.staging.stg_tlc__fhvhv_tripdata) as staged, (select count(*) from vd_eval_20261103195103_f31892c8ad9e_eph.bronze.fhvhv_tripdata) as bronze, (select sum(hvfhv_trip_count) from vd_eval_20261103195103_f31892c8ad9e_eph.agg.agg_hvfhv_trip_zone_daily) as aggregated, (select count(*) from vd_eval_20261103195103_f31892c8ad9e_eph.staging.stg_tlc__fhvhv_tripdata where pickup_datetime >= timestamp '2024-01-01' and pickup_datetime < timestamp '2024-04-01') as staged_in_window, (select count(*) from vd_eval_20261103195103_f31892c8ad9e_eph.agg.agg_hvfhv_trip_zone_daily) as zone_days, (select count(distinct (pickup_location_id, pickup_date)) from vd_eval_20261103195103_f31892c8ad9e_eph.agg.agg_hvfhv_trip_zone_daily) as distinct_keys, (select sum(hvfhv_trip_count) from vd_eval_20261103195103_f31892c8ad9e_eph.agg.agg_hvfhv_trip_zone_daily where pickup_location_id in (264, 265)) as unknown_zone_trips, (select string_agg(table_name || '.' || column_name || '=' || data_type, ', ' order by table_name, column_name) from information_schema.columns where table_catalog = 'vd_eval_20261103195103_f31892c8ad9e_eph' and table_schema = 'agg' and table_name in ('agg_hvfhv_trip_zone_daily', 'agg_trip_zone_daily') and column_name in ('pickup_location_id', 'pickup_date')) as key_types
```

## Gate results

| Gate | Command | Exit | Outcome |
| --- | --- | --- | --- |
| Flight item | `python3 <plugin>/scripts/platforms/motherduck/validate-flight.py ingestion/tlc_pipeline.Flight --repo-root .` | 0 | pass |
| Apply | `create_flight` `tlc_pipeline` with the committed `flight.py`, `requirements.txt` and `config.json` (`flight_secret_names` as its own argument) | — | `8c8e1438-83ae-490a-bfdb-367a08cc9d12`, version 1 |
| Safety run | `run_flight` run 1 (`DLT_INGEST_LIMIT=1`, `DEV_MODE=true`), `get_flight_logs` saved to `.agents_tmp/tlc-safety-run.log` | 0 | SUCCEEDED, exit_code 0, `destination-identity` `vd_eval_20261103195103_f31892c8ad9e_eph` |
| Full load | `run_flight` run 2, saved to `.agents_tmp/tlc-full-load.log` | 0 | SUCCEEDED, exit_code 0, `destination-identity` `vd_eval_20261103195103_f31892c8ad9e_eph` |
| Destination identity | `python3 <plugin>/scripts/assert_destination.py --pipeline tlc --resolved-from-log <run log>` | 0, 0 | `DESTINATION_OK` for both runs |
| Tier-1 landing | `python3 <plugin>/scripts/run_bronze_tier1_tests.py --dataset bronze --audit` | 0 | PASS × 4 tables + audit |
| Source tests | `python3 -m pytest -q tests/ingestion` | 0 | 27 passed |
| Pipeline audit | the `generating-dlt-pipeline` rules; `check_dlt_dataset_literal.py` and `validate_schema_contract.py` on `flight.py` | 0, 0 | dataset name logical, `SCHEMA_CONTRACT_OK`; `preview-emitted-correctly` fails: the preview rendered all 70 tables of the Ephemeral database (VD-7707), the bronze blocks present |
| Model gates | `dbt build --select "<model> state:modified+,+<model>" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev`, per model | 0, 0 | PASS=3; PASS=11 |
| dbt data tests | `dbt build --select stg_tlc__fhvhv_tripdata+ --exclude test_type:unit --defer --state /data/cache/prod-target --target dev` | 0 | PASS=9 |
| dbt unit tests | `dbt test --select stg_tlc__fhvhv_tripdata+,test_type:unit --defer --state /data/cache/prod-target --target dev` | 0 | PASS=2 |
| Semantic tests | `dbt test --select assert_semantic_content_holds assert_semantic_level_keys_hold assert_semantic_levels_hold --defer --state /data/cache/prod-target --target dev` | 0 | PASS=2 WARN=1 (the existing levels finding) |
| Project audit | `dbt build --select package:dbt_project_evaluator --vars '{dbt_project_evaluator_enabled: true}' --warn-error-options '{"error":["NoNodesForSelectionCriteria"]}' --target dev` | 0 | PASS=66 WARN=12 ERROR=0 |
| Ossie chain | `ossie.py validate`, `coverage logical-model/ transformation/models/marts/`, `suppliers`, `notes`, `generate-tests --check` | 0 each | the two new `to-column-not-a-key` warnings join the zone and day levels by their level keys, as `zone_poi_to_zone` does; 35 of 35 named |
| validating-semantic-model | the review | — | verdict pass: the star's detail is the aggregate, its grain held by the singular test, one `SUM` metric, no binding on the trip star |
| Ontology | `ossie.py validate ontology/`, `refs`, `glossary` | 0, 0, 0 | pass; no concept (an aggregate gets none) |
| Baseline cross-check | `dbt ls -s state:modified+ …` against the Plan's targets | 0 | the two new models = the Plan's two targets; `manifest-source.json` `build_sha` `7fcde94` |
| Ship currency | `python3 <plugin>/scripts/ship_currency.py --rows .agents_tmp/ship-currency-rows.json` | 0 | fresh |
| Contract promotion | `access: protected` on both new models, which set no enforced contract | — | manifest diff not applicable |
| Contract build | `dbt build --select "agg_hvfhv_trip_zone_daily state:modified+,+agg_hvfhv_trip_zone_daily" … --target dev` | 0 | pass |
| Source registration | `bronze.fhvhv_tripdata` in `_sources.yml`, read by the staging build | 0 | the staging gate selected and built from it |
| Domain sweep | `CONTEXT.md`, `docs/adr/` | — | domain sweep: nothing new (HVFHV trip added at the requirement) |
| Publication | `gh pr create --head intent/new-intent-d0d80c5b ...`, then `gh pr view 1 --json state,headRefName,baseRefName` | 0, 0 | https://github.example.invalid/domain/repo/pull/1, OPEN, base `main` |

## Discovery

- The HVFHV January 2024 file is 472,757,547 bytes, in 19 Parquet row groups of at most 1,048,576 rows, with 24 columns — `select count(distinct row_group_id) as row_groups, max(row_group_num_rows) as largest_row_group from parquet_metadata('https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2024-01.parquet')` (DuckDB 1.5.6, httpfs, in the sandbox)
- It holds 19,663,930 rows; pickups run from 2024-01-01 00:00:00 to 2024-01-31 23:59:59, with 0 outside January; 0 rows have a null `PULocationID` and 765 pick up in zones 264 or 265; 2 distinct `hvfhs_license_num` — `select count(*) as row_count, min(pickup_datetime) as first_pickup, max(pickup_datetime) as last_pickup, count(*) filter (where pickup_datetime < TIMESTAMP '2024-01-01' or pickup_datetime >= TIMESTAMP '2024-02-01') as outside_january, count(*) filter (where PULocationID is null) as null_pickup_zone, count(*) filter (where PULocationID in (264, 265)) as unknown_pickup_zone, count(distinct hvfhs_license_num) as licensees from read_parquet('https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2024-01.parquet')`
- For scale, the yellow January 2024 file holds 2,964,624 rows, so the HVFHV file is about 6.6 times larger — `select count(*) as row_count from read_parquet('https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet')`
- The unresolved zones are 264 (borough `Unknown`) and 265 (`N/A`) — `select zone_natural_key, borough_name from core.dim_zone where is_unresolved_zone order by 1` (Domain, read through the Ephemeral clone)
- `agg_trip_zone_daily` publishes `pickup_date` as `DATE` and `pickup_location_id` as `BIGINT`; the HVFHV file carries `PULocationID` as `INT32` — `select column_name, data_type from information_schema.columns where table_schema = 'agg' and table_name = 'agg_trip_zone_daily' and column_name in ('pickup_location_id', 'pickup_date') order by 1` (Domain, read through the Ephemeral clone), and the file's `parquet_schema`
