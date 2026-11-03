# Plan: Pending request R1: a vehicle scorecard per medallion and month, on the full MotherDuck model-answer Domain

**Goal:** Publish `ops.mart_vehicle_scorecard`, one row per vehicle per month on `agg_vehicle_monthly`, ranked on revenue per online hour fleet-wide and within garage, with the 40-hour floor flagged, the cut-short month marked, and its source in the fleet Ossie document.

**Requirement:** `docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md`

**Constraints:**
- Read `agg_vehicle_monthly` only (ADR 0016); rank on revenue per online hour (ADR 0010) with `rank()`; floor 40 online hours, flagged, never dropped.
- dbt through the runtime wrapper on target `dev`, with the path selection and defer `motherduck/dbt.md` § Defer grants; dbt's own output must name `VD_EPHM_MOTHERDUCK_DATABASE`.
- Nothing existing changes; nothing is written to `sa_prd`.

## Scope and impact

| Artifact | Kind | Action | Requirements | Design record | Gate |
| --- | --- | --- | --- | --- | --- |
| `mart_vehicle_scorecard` | model | create | `R-01`–`R-06` | `docs/design/models/ops/mart_vehicle_scorecard.md` | `dbt build --select "mart_vehicle_scorecard state:modified+,+mart_vehicle_scorecard" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` |
| `logical-model/nyc_taxi_fleet.ossie.yaml` + generated semantic tests | logical-model | modify | `R-07` | D-09 | the semantic-model chain |
| `ontology/` | ontology | none (gates re-run) | `R-07` | D-09 | `validate`, `refs`, `glossary` |

**Change impact:** a new leaf mart on `agg_vehicle_monthly`; nothing existing changes.

## Tasks

### Task 1: `mart_vehicle_scorecard`

**Requirements:** `R-01`–`R-06` · **Design:** `docs/design/models/ops/mart_vehicle_scorecard.md` · **Skill:** generating-dbt-model · **Depends on:** none

- [x] Author the SQL, its `_ops.yml` entry (not_null keys and flags, relationships to `dim_vehicle` and `dim_garage`), unit tests of the ranking and its tie-break and of the incomplete-month mark, the singular grain test and its `test-map.json` row
- [x] List the built and deferred nodes, then run `dbt build --select "mart_vehicle_scorecard state:modified+,+mart_vehicle_scorecard" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev`; expect PASS and the Ephemeral database in `run_results.json`
- [x] Run the acceptance conditions of `R-01`–`R-06`
- [x] Commit with Task 2

### Task 2: the semantic layer

**Requirements:** `R-07` · **Design:** D-09 · **Skill:** semantic-model, validating-semantic-model, ontology · **Depends on:** 1

- [x] Author `LTS9_vehicle_scorecard` on `shift`, its physical table and joins; `ossie.py generate-tests`
- [x] Run the semantic-model chain, the semantic tests on `dev` with defer, and the ontology gates; expect exit 0
- [x] Commit and push Tasks 1 and 2

## Execution evidence
- Task 1: `dbt ls` builds `mart_vehicle_scorecard` only and defers 25 ancestors; the gate — PASS=12 (the model, two unit tests, the grain test, the not_null and relationships tests); `run_results.json` names `"vd_eval_20261103192916_83f4d5f25477_eph"."ops"."mart_vehicle_scorecard"`.
- Task 1: acceptance (in the Verification) — 1,376 rows, every key matched; 0 value, rank, rate or flag mismatches; 115 flagged, all ranked; only 2023-12 marked incomplete.
- Task 2: `LTS9_vehicle_scorecard` on `shift`; `generate-tests`; the semantic-model chain (35 of 35 named) and the ontology gates — exit 0 each; the semantic tests with defer — PASS=2 WARN=1 (the existing `assert_semantic_levels_hold` warning). Committed together in 1a738df.
