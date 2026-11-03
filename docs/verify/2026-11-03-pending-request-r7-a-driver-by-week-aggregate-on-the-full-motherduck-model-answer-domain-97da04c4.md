# Verification: Pending request R7: a driver-by-week aggregate, on the full MotherDuck model-answer Domain

## Verification

`verdict: verified` at `c6608b3`: `agg.agg_driver_weekly` is built in the Intent's Ephemeral MotherDuck database (`vd_eval_20261103112118_64f4c013a034_eph`) on target `dev`, with only its own node built and its ancestors deferred to the production manifest. Its 14 weeks reconcile exactly to `agg_driver_daily` for rows, drivers, shifts, online hours and gross revenue; every rate is its row's ratio of sums; the week the window cuts short (2023-12-25) is marked on all its rows and no full week is. The fleet Ossie document declares it, and every semantic and ontology gate passes. No golden baseline is configured: an independent recomputation from `agg_driver_daily` and `dim_date` stands in for one. Limits: `assert_semantic_levels_hold` warns once, on the existing `trips.LTS5_weather…` `unresolved` finding; this repo publishes no data contracts, so no contract gate applies.

## Coverage

| Item | Evidence | Result | At |
| --- | --- | --- | --- |
| `R-01` one row per active driver-week | the reconciliation query below (`rows_` against `count(distinct driver_key)` per week, `shift_count < 1` rows) and `assert_agg_driver_weekly_one_row_per_driver_week` | rows = drivers in all 14 weeks; 0 rows without a shift; grain test PASS | `c6608b3` |
| `R-02` the week is `dim_date.week_start_date` | the model SQL (joins `dim_date` on `date_key`, no `date_trunc`); the reconciliation groups `agg_driver_daily` by `dim_date.week_start_date` independently | every week matches, 2023-12-25 to 2024-03-25 | `c6608b3` |
| `R-03` the cut-short week marked, by the window | `min(week_days_covered)`, `max(week_days_covered)` and `sum(case when is_complete_week then 0 else 1 end)` per week; unit test `driver_weekly_marks_the_week_the_window_cuts_short` | 2023-12-25: 1 day covered, 115 of 115 rows marked; every other week 7 days, 0 marked; unit test PASS (a driver with one day in a full week is complete) | `c6608b3` |
| `R-04` measures summed, rates as ratios of sums, reconciling to the daily table | per-week `sum(shift_count)`, `sum(online_hours)`, `sum(gross_revenue)` of both tables, and rows whose `revenue_per_online_hour` or `occupancy_rate` is not their own ratio; unit test `driver_weekly_rebuilds_rates_from_the_weeks_sums` | shifts equal; hours and revenue differences 0.0 in every week; 0 rate mismatches; unit test PASS (0.875 and 40.0, null on zero online hours) | `c6608b3` |
| `R-05` additive | `git diff --name-only 7fcde94 HEAD`; `dbt ls -s state:modified+ --resource-type model --state /data/cache/prod-selection --target dev` | one new `.sql`; the only modified model is `agg_driver_weekly` | `c6608b3` |
| `R-06` semantic layer | Gate results below | exit 0 each; `LTS4_driver_week` bound and held by `assert_semantic_content_holds` (PASS) | `c6608b3` |
| `R-07` nothing written to `sa_prd` | `target/run_results.json` of the gate; every dbt command on `--target dev` | the model's relation is `"vd_eval_20261103112118_64f4c013a034_eph"."agg"."agg_driver_weekly"` = `VD_EPHM_MOTHERDUCK_DATABASE`; no Flight was run | `c6608b3` |
| `agg_driver_weekly` | `dbt build --select agg_driver_weekly+ --exclude test_type:unit --defer --state /data/cache/prod-target --target dev`; `dbt test --select agg_driver_weekly+,test_type:unit …` | PASS=9 WARN=1; PASS=2 | `c6608b3` |
| `logical-model/nyc_taxi_fleet.ossie.yaml` | the semantic-model gate chain; the design record's `## Logical Model` read against the document | exit 0 each; `shift.LTS4_driver_week` present on `shift` | `c6608b3` |
| `ontology/` | `validate`, `refs`, `glossary` | exit 0 each; no concept or mapping changed | `c6608b3` |

Reconciliation query (`dbt show --inline … --defer --state /data/cache/prod-target --target dev`):

```sql
with expected as (
    select d.week_start_date, count(*) as driver_days, count(distinct a.driver_key) as drivers,
           sum(a.shift_count) as shifts, sum(a.online_hours) as hours, sum(a.gross_revenue) as revenue
    from {{ ref('agg_driver_daily') }} a join {{ ref('dim_date') }} d on a.date_key = d.date_key
    group by 1
), got as (
    select week_start_date, count(*) as rows_, count(distinct driver_key) as drivers,
           sum(shift_count) as shifts, sum(online_hours) as hours, sum(gross_revenue) as revenue,
           min(week_days_covered) as min_cov, max(week_days_covered) as max_cov,
           sum(case when is_complete_week then 0 else 1 end) as marked,
           sum(case when abs(coalesce(revenue_per_online_hour, -1) - coalesce(gross_revenue / nullif(online_hours, 0), -1)) > 1e-9 then 1 else 0 end) as bad_rpoh,
           sum(case when abs(coalesce(occupancy_rate, -1) - coalesce(on_trip_hours / nullif(online_hours, 0), -1)) > 1e-9 then 1 else 0 end) as bad_occ,
           sum(case when shift_count < 1 then 1 else 0 end) as empty_rows
    from {{ ref('agg_driver_weekly') }} group by 1
)
select e.week_start_date::date as week, g.rows_, e.drivers, g.drivers as got_drivers, e.shifts, g.shifts as got_shifts,
       round(e.hours - g.hours, 6) as hours_diff, round(e.revenue - g.revenue, 4) as revenue_diff,
       g.min_cov, g.max_cov, g.marked, g.bad_rpoh, g.bad_occ, g.empty_rows
from expected e full join got g using (week_start_date) order by 1
```

## Gate results

| Gate | Command | Exit | Outcome |
| --- | --- | --- | --- |
| Nodes built and deferred | `dbt ls --resource-type model --select "agg_driver_weekly state:modified+,+agg_driver_weekly" --state /data/cache/prod-selection --target dev`, and the same with `--select "+agg_driver_weekly" --exclude …` | 0, 0 | builds `agg_driver_weekly`; defers 22 ancestors; no changed ancestor |
| Model gate | `dbt build --select "agg_driver_weekly state:modified+,+agg_driver_weekly" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` | 0 | PASS=10, on `vd_eval_20261103112118_64f4c013a034_eph` |
| dbt data tests | `dbt build --select agg_driver_weekly+ --exclude test_type:unit --defer --state /data/cache/prod-target --target dev` | 0 | PASS=9 WARN=1 (`assert_semantic_levels_hold`: the existing `trips.LTS5_weather…` `unresolved` finding) |
| dbt unit tests | `dbt test --select agg_driver_weekly+,test_type:unit --defer --state /data/cache/prod-target --target dev` | 0 | PASS=2 |
| Semantic tests | `dbt test --select assert_semantic_content_holds assert_semantic_level_keys_hold assert_semantic_levels_hold --defer --state /data/cache/prod-target --target dev` | 0 | PASS=2 WARN=1 (the same finding) |
| Project audit | `dbt build --select package:dbt_project_evaluator --vars '{dbt_project_evaluator_enabled: true}' --warn-error-options '{"error":["NoNodesForSelectionCriteria"]}' --target dev` | 0 | PASS=66 WARN=12 ERROR=0; `agg_driver_weekly` appears only in `fct_missing_primary_key_tests`, as `agg_driver_daily` and `agg_driver_monthly` do (their grains are held by singular tests) |
| Ossie validate | `python3 .agents/skills/semantic-model/scripts/ossie.py validate logical-model/` | 0 | 3 warnings, the same three as on `main` |
| Ossie coverage | `python3 .agents/skills/semantic-model/scripts/ossie.py coverage logical-model/ transformation/models/marts/` | 0 | 35 of 35 named. The layers declare no `role` and the map no `gold_layers`, so the skill's `models/marts/` fallback is the root |
| Ossie suppliers | `python3 .agents/skills/semantic-model/scripts/ossie.py suppliers logical-model/` | 0 | 0 unsupplied |
| Ossie notes | `python3 .agents/skills/semantic-model/scripts/ossie.py notes logical-model/ transformation/tests/ docs/adr/` | 0 | 0 dangling |
| Ossie tests current | `python3 .agents/skills/semantic-model/scripts/ossie.py generate-tests logical-model/ transformation/tests/ --check` | 0 | 0 stale |
| validating-semantic-model | the chain above and the content review | — | verdict pass: the weekly source binds only the six shift metrics' columns, its content levels are the week level and the driver, its filter states both inner joins, and its rate columns are refused (ADR 0016); no finding, no escalation |
| Ontology | `python3 .agents/skills/semantic-model/scripts/ossie.py validate ontology/`, `python3 .agents/skills/semantic-model/scripts/ossie.py refs ontology/ logical-model/`, `python3 .agents/skills/semantic-model/scripts/ossie.py glossary ontology/ CONTEXT.md` | 0, 0, 0 | pass; no concept added: an aggregate mart gets none |
| Logical Model contract | the design record's block read against the document | — | `shift` changed by `LTS4_driver_week`, as listed |
| Weakening | `git diff --numstat 7fcde94 HEAD` | — | no test or rule removed; the deletions are the two regenerated semantic tests |
| Words against data | the design record, `CONTEXT.md` and the YAML descriptions read against the built table | — | grain, columns, the week source, the incomplete-week rule and the table materialisation agree |
| Dev-artifact scan | `git diff 7fcde94 HEAD -- transformation` for `dev_mode`, `.add_limit(`, a target pin | — | none |
| Baseline cross-check | `dbt ls -s state:modified+ --resource-type model --state /data/cache/prod-selection --target dev` | 0 | `agg_driver_weekly` only = the Plan's one target; `manifest-source.json` `build_sha` `7fcde94` = the branch's base |
| Ship currency | `python3 <plugin>/scripts/ship_currency.py --rows .agents_tmp/ship-currency-rows.json` | 0 | fresh |
| Contract promotion | `access: protected` on `agg_driver_weekly`; no touched model sets `contract: {enforced: true}` or `access: public`, so the manifest diff is not applicable | — | not applicable; no model in the repo set `access:` before (reported, not changed) |
| Contract build | `dbt build --select "agg_driver_weekly state:modified+,+agg_driver_weekly" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` | 0 | PASS=11 WARN=1, no contract violation |
| Domain sweep | `CONTEXT.md` and `docs/adr/` against the Requirement and design record | — | domain sweep: nothing new (driver-week and incomplete week added at the requirement; ADR 0014 and 0016 already rule the week and the rates) |
| Publication | `gh pr create --head intent/new-intent-97da04c4 ...`, `gh pr view 1 --json number,url,state,headRefName,baseRefName` | 0, 0 | https://github.example.invalid/domain/repo/pull/1, OPEN, base `main` |

## Discovery

- `agg_driver_daily` covers 2023-12-31 (a Sunday) to 2024-03-31 (a Sunday): 32,153 driver-days for 760 drivers — `select min(shift_date) as first_day, max(shift_date) as last_day, count(*) as driver_days, count(distinct driver_key) as drivers, dayname(min(shift_date)) as first_dow, dayname(max(shift_date)) as last_dow from {{ ref('agg_driver_daily') }}` (`dbt show --inline … --target dev`, the Ephemeral clone)
- `dim_date.week_start_date` puts 2023-12-31 in the week of 2023-12-25, whose other six days precede the window, and 2024-03-31 in the week of 2024-03-25, which the window covers in full — `select calendar_date, week_start_date, date_key from {{ ref('dim_date') }} where calendar_date in (date '2023-12-25', date '2023-12-31', date '2024-01-01', date '2024-03-31') order by 1`
- `dim_driver` is type 1 (one row per `driver_key`), so a driver's `garage_key` and `engagement_type` hold across a week — `logical-model/nyc_taxi_fleet.ossie.yaml`, dataset `driver`, `scd: {type: 1}`
