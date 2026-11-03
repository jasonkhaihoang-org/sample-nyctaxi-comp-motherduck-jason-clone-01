# Plan: The v2 surcharge split and tip rate, on the full MotherDuck model-answer Domain

**Goal:** Add congestion-surcharge and airport-fee revenue with their trip counts beside `surcharge_revenue` in `mart_daily_zone_revenue`, and the measurable tip rate with its count and share to `mart_monthly_service_summary`, with the trip Ossie document moving with them.

**Requirement:** `docs/requirement/2026-11-03-the-v2-surcharge-split-and-tip-rate-on-the-full-motherduck-model-answer-domain-03d745f1.md`

**Constraints:**
- Additive only: no existing column changes; grains unchanged.
- dbt through the runtime wrapper on target `dev`, with the path selection and defer `motherduck/dbt.md` § Defer grants, one run per target; dbt's own output must name `VD_EPHM_MOTHERDUCK_DATABASE`.
- Nothing is written to `sa_prd`.

## Scope and impact

| Artifact | Kind | Action | Requirements | Design record | Gate |
| --- | --- | --- | --- | --- | --- |
| `mart_daily_zone_revenue` | model | modify | `R-01`–`R-04`, `R-06`, `R-08` | `docs/design/models/finance/mart_daily_zone_revenue.md` | `dbt build --select "mart_daily_zone_revenue state:modified+,+mart_daily_zone_revenue" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` |
| `mart_monthly_service_summary` | model | modify | `R-05`, `R-06`, `R-08` | `docs/design/models/finance/mart_monthly_service_summary.md` | `dbt build --select "mart_monthly_service_summary state:modified+,+mart_monthly_service_summary" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` |
| `logical-model/nyc_taxi_analytics.ossie.yaml` + generated semantic tests | logical-model | modify | `R-07` | D-05, D-03 | the semantic-model chain |
| `ontology/` | ontology | none (gates re-run) | `R-07` | — | `validate`, `refs`, `glossary` |

**Change impact:** both marts are leaves; their consumers in this repo are the Ossie document's two logical sources.

## Tasks

### Task 1: `mart_daily_zone_revenue`

**Requirements:** `R-01`–`R-04`, `R-06`, `R-08` · **Design:** its record D-02–D-05 · **Skill:** generating-dbt-model · **Depends on:** none

- [x] Add the four columns to the SQL, their YAML entries and tests, and a unit test of missing fees and the counts
- [x] Run `dbt build --select "mart_daily_zone_revenue state:modified+,+mart_daily_zone_revenue" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev`; the acceptance conditions of `R-01`–`R-04`, `R-06`

### Task 2: `mart_monthly_service_summary`

**Requirements:** `R-05`, `R-06`, `R-08` · **Design:** its record D-02, D-03 · **Skill:** generating-dbt-model · **Depends on:** none

- [x] Add the three columns to the SQL, their YAML entries and tests, and a unit test of the mean over measurable trips
- [x] Run `dbt build --select "mart_monthly_service_summary state:modified+,+mart_monthly_service_summary" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev`; the acceptance conditions of `R-05`, `R-06`

### Task 3: the semantic layer

**Requirements:** `R-07` · **Design:** D-05, D-03 · **Skill:** semantic-model, validating-semantic-model, ontology · **Depends on:** 1, 2

- [x] Add the three `trips` fields, the seven metrics and the bindings on `LTS1_detail`, `LTS7_daily_zone_revenue` and `LTS8_monthly_service_summary`; `ossie.py generate-tests`
- [x] Run the semantic-model chain, the semantic tests and the ontology gates; expect exit 0
- [x] Commit and push Tasks 1 to 3 together

## Execution evidence
- Task 1: path selection builds `mart_daily_zone_revenue` only (21 ancestors deferred) — exit 0, PASS=12 WARN=1, both unit tests and the column tests; `run_results.json` names `"vd_eval_20261103194016_02ed7f0a991f_eph"."finance"."mart_daily_zone_revenue"`.
- Task 2: path selection builds `mart_monthly_service_summary` only (22 deferred) — exit 0, PASS=11 WARN=1; the relation is in the same Ephemeral database.
- Tasks 1 and 2: acceptance (in the Verification) — 20,770 zone-days and 30 summary rows matched; 0 mismatches on existing columns, the four new daily columns and the tip rate, count and share; the rate null on all 21 rows with no measurable trip.
- Task 3: the three `trips` fields, seven metrics and three bindings; `generate-tests`; the chain (34 of 34 named) and the ontology gates — exit 0 each; the semantic tests with defer — PASS=2 WARN=1 (the existing levels finding), `assert_semantic_content_holds` PASS.
- Tasks 1 to 3: committed together in e498b56.
