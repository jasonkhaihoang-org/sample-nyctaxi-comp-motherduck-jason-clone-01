# Plan: Migrate, not add: one zone-day roll-up shared by mart_daily_zone_revenue and agg_trip_zone_daily, nothing a consumer reads changed, on the full MotherDuck model-answer Domain

**Goal:** Move the zone-day roll-up of `fct_trip` into one gold model, `agg_trip_zone_daily_base`, and build `mart_daily_zone_revenue` and `agg_trip_zone_daily` on it, with nothing their readers see changed.

**Requirement:** `docs/requirement/2026-11-04-migrate-not-add-one-zone-day-roll-up-shared-by-mart-daily-zone-revenue-and-agg-trip-zone-daily-nothing-a-consumer-reads-changed-on-the-full-motherduck-model-answer-domain-3e385ecb.md`

**Constraints:**
- Restructuring: both published relations stay identical (names, columns, order, types, rows); proven equivalent at verify.
- dbt on target `dev`, with the path selection and defer `motherduck/dbt.md` § Defer grants, one run per target; dbt's own output must name `VD_EPHM_MOTHERDUCK_DATABASE`.
- Nothing is written to `sa_prd`.

## Scope and impact

| Artifact | Kind | Action | Requirements | Design record | Gate |
| --- | --- | --- | --- | --- | --- |
| `agg_trip_zone_daily_base` | model | create | `R-01`, `R-04`, `R-06` | `docs/design/models/agg/agg_trip_zone_daily_base.md` | built inside both gates below; its unit test |
| `mart_daily_zone_revenue` | model | modify | `R-01`, `R-02`, `R-06` | `docs/design/models/finance/mart_daily_zone_revenue.md` | `dbt build --select "mart_daily_zone_revenue state:modified+,+mart_daily_zone_revenue" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` |
| `agg_trip_zone_daily` | model | modify | `R-01`, `R-03`, `R-06` | `docs/design/models/agg/agg_trip_zone_daily.md` | `dbt build --select "agg_trip_zone_daily state:modified+,+agg_trip_zone_daily" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` |
| `logical-model/nyc_taxi_analytics.ossie.yaml` | logical-model | modify (registration note only) | `R-05` | each record's `## Logical Model` | `ossie.py validate`, `coverage`, `suppliers`, `notes`, `generate-tests --check`; `tools/ossie_lint.py` |

**Change impact:** `state:modified+` against `/data/cache/prod-selection` is exactly the three models. Consumers: the Ossie document's `LTS2_zone_day_agg` and `LTS7_daily_zone_revenue`, which bind unchanged columns; the generated semantic tests read both.

## Tasks

### Task 1: the shared roll-up and both models on it

**Requirements:** `R-01`–`R-04`, `R-06` · **Design:** the three records · **Skill:** generating-dbt-model · **Depends on:** none

- [x] Add `agg_trip_zone_daily_base` with its `_agg.yml` entry, a grain test and a unit test of the billable split and the distinct driver count; rebuild both models on it; re-point `agg_trip_zone_daily`'s unit test at its new input
- [x] Run `dbt build --select "mart_daily_zone_revenue state:modified+,+mart_daily_zone_revenue" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` and `dbt build --select "agg_trip_zone_daily state:modified+,+agg_trip_zone_daily" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev`; the acceptance conditions of `R-02`–`R-04`

### Task 2: the semantic layer

**Requirements:** `R-05` · **Design:** each record's `## Logical Model` · **Skill:** semantic-model, validating-semantic-model · **Depends on:** 1

- [x] Register `agg_trip_zone_daily_base` in `physical_tables` with a note saying why it is not mapped
- [x] Run the semantic-model chain and `tools/ossie_lint.py`; expect exit 0
- [x] Commit and push Tasks 1 and 2 together

## Execution evidence
- Task 1: the `mart_daily_zone_revenue` gate builds `agg_trip_zone_daily_base` and the mart (ancestors deferred) — exit 0, PASS=18 WARN=1 (`assert_semantic_levels_hold`, the finding `main` has); the `agg_trip_zone_daily` gate builds the base and the agg — exit 0, PASS=18 WARN=1, both unit tests PASS (the new `trip_zone_daily_base_keeps_both_populations` and the re-pointed `trip_zone_daily_ranks_revenue_at_the_cent`); `run_results.json` names `vd_eval_20261104072731_aab43ba9f5c0_eph` for all three relations, at `3202b9c`.
- Task 1, a check on the check: the mart built once with `where trip_count > 0` over every trip gave 20,771 rows against the Domain's 20,770 and was caught by the equivalence comparison; restored and rebuilt before the commit.
- Task 2: `ossie.py validate`, `coverage`, `suppliers`, `notes`, `generate-tests --check` and `tools/ossie_lint.py` — exit 0 each at `3202b9c`; before the registration, coverage reported `coverage/unmapped` for `agg_trip_zone_daily_base`.
- Tasks 1 and 2: committed together in 3202b9c.
