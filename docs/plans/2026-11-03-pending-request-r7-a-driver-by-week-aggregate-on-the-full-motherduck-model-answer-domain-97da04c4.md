# Plan: Pending request R7: a driver-by-week aggregate, on the full MotherDuck model-answer Domain

**Goal:** Publish `agg.agg_driver_weekly`, one row per active driver-week built from `agg_driver_daily` and `dim_date`, with the cut-short week marked, and declare it in the fleet Ossie document.

**Requirement:** `docs/requirement/2026-11-03-pending-request-r7-a-driver-by-week-aggregate-on-the-full-motherduck-model-answer-domain-97da04c4.md`

**Constraints:**
- The week is `dim_date.week_start_date` (ADR 0014); rates are ratios of sums through `safe_divide` (ADR 0016).
- dbt runs through the runtime wrapper on target `dev` (`workarounds`), with the path selection and defer `motherduck/dbt.md` § Defer grants; dbt's own output must name `VD_EPHM_MOTHERDUCK_DATABASE` before evidence is recorded.
- Nothing existing changes; nothing is written to `sa_prd`.

## Scope and impact

| Artifact | Kind | Action | Requirements | Design record | Gate |
| --- | --- | --- | --- | --- | --- |
| `agg_driver_weekly` | model | create | `R-01`–`R-05`, `R-07` | `docs/design/models/agg/agg_driver_weekly.md` | `dbt build --select "agg_driver_weekly state:modified+,+agg_driver_weekly" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` |
| `logical-model/nyc_taxi_fleet.ossie.yaml` + generated semantic tests | logical-model | modify | `R-06` | `docs/design/models/agg/agg_driver_weekly.md` D-09 | `ossie.py validate / coverage / suppliers / notes / generate-tests --check` |
| `ontology/` | ontology | none (gates re-run) | `R-06` | `docs/design/models/agg/agg_driver_weekly.md` | `ossie.py validate ontology/`, `refs` |

**Change impact:** a new leaf model; its ancestors (`agg_driver_daily`, `dim_date` and theirs) are unchanged, so the path selection builds only `agg_driver_weekly` and defers the rest. No existing model's SQL changes.

## Tasks

### Task 1: `agg_driver_weekly`

**Requirements:** `R-01`–`R-05`, `R-07` · **Design:** `docs/design/models/agg/agg_driver_weekly.md` · **Skill:** generating-dbt-model · **Depends on:** none

- [x] Author `transformation/models/marts/agg/agg_driver_weekly.sql`, its `_agg.yml` entry (not_null keys, relationships to `dim_driver` and `dim_garage`), unit tests of the incomplete-week flag and the rate rebuild, the singular grain test `assert_agg_driver_weekly_one_row_per_driver_week.sql` and its `test-map.json` row
- [x] List the built and deferred nodes with `dbt ls`, then run `dbt build --select "agg_driver_weekly state:modified+,+agg_driver_weekly" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev`; expect PASS and dbt's output naming the Ephemeral database
- [x] Run the acceptance conditions of `R-01`–`R-05`: grain unique, weeks equal `week_start_date`, the cut-short week marked on every row and no full week marked, shifts, online hours and gross revenue reconciling to `agg_driver_daily` per week, each rate its row's ratio; expect all hold
- [x] Commit with Task 2 (the Ossie change ships with the model)

### Task 2: the semantic layer

**Requirements:** `R-06` · **Design:** `docs/design/models/agg/agg_driver_weekly.md` D-09 · **Skill:** semantic-model (repo `workarounds`), validating-semantic-model, ontology · **Depends on:** 1

- [x] Author the `LTS_driver_week` source on `shift` in `logical-model/nyc_taxi_fleet.ossie.yaml` and its physical table and join, then `ossie.py generate-tests`
- [x] Run the semantic-model gate chain and the regenerated semantic tests on target `dev`; expect exit 0 and PASS
- [x] Run `ossie.py validate ontology/` and `refs`; expect exit 0
- [x] Commit and push Tasks 1 and 2

## Execution evidence
- Task 1: `dbt ls --resource-type model --select "agg_driver_weekly state:modified+,+agg_driver_weekly" --state /data/cache/prod-selection --target dev` — builds `agg_driver_weekly` only; its 22 ancestors are deferred to `/data/cache/prod-target`, and none is a changed ancestor.
- Task 1: `dbt build --select "agg_driver_weekly state:modified+,+agg_driver_weekly" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` — exit 0, PASS=10 (the model, two unit tests, the grain test, four not_null, two relationships); `run_results.json` names `"vd_eval_20261103112118_64f4c013a034_eph"."agg"."agg_driver_weekly"`, which is `VD_EPHM_MOTHERDUCK_DATABASE`. The first run failed in the unit tests' fixtures (`driver_key` is `BIGINT`, the fixtures used strings) and was fixed in the fixtures.
- Task 1: acceptance query (`dbt show --inline`, `/tmp/acc.sql` in the Verification) — 14 weeks; rows equal drivers in every week; shifts, online hours and gross revenue reconcile to `agg_driver_daily` with zero difference; 0 rows with a rate that is not its own ratio; the week of 2023-12-25 marked on all 115 rows, no full week marked.
- Task 2: `ossie.py validate logical-model/`, `coverage logical-model/ transformation/models/marts/` (35 of 35 named), `suppliers`, `notes`, `generate-tests --check`; `validate ontology/`, `refs ontology/ logical-model/`, `glossary ontology/ CONTEXT.md` — exit 0 each. `dbt test --select assert_semantic_content_holds assert_semantic_level_keys_hold assert_semantic_levels_hold --defer --state /data/cache/prod-target --target dev` — PASS=2 WARN=1 (the existing `trips.LTS5_weather…` `unresolved` finding its note records).
- Tasks 1 and 2: committed together in 9d29b9f, as the repository's `workarounds` rule asks that a mart change carries its Ossie update.
