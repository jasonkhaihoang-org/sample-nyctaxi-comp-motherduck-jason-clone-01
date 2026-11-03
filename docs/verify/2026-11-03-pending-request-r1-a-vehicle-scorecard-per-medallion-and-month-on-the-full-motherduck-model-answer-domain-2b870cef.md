# Verification: Pending request R1: a vehicle scorecard per medallion and month, on the full MotherDuck model-answer Domain

## Verification

`verdict: verified` at `510dea5`: `ops.mart_vehicle_scorecard` is built in the Intent's Ephemeral MotherDuck database (`vd_eval_20261103192916_83f4d5f25477_eph`) on target `dev`, with only its own node built and its ancestors deferred. It matches `agg_vehicle_monthly` on all 1,376 vehicle-months; both ranks equal a competition rank recomputed from the published rate; the 115 vehicle-months under 40 online hours are flagged and ranked; only December 2023 is marked incomplete. Its source is in the fleet Ossie document and every semantic and ontology gate passes. No golden baseline is configured: an independent recomputation from `agg_vehicle_monthly` stands in. Limits: `assert_semantic_levels_hold` warns once, the existing `trips.LTS5_weather…` finding; this repo publishes no data contracts.

## Coverage

| Item | Evidence | Result | At |
| --- | --- | --- | --- |
| `R-01` one row per vehicle per month with medallion, month and garage | the acceptance query below; `assert_mart_vehicle_scorecard_one_row_per_vehicle_month` | 1,376 = 1,376, every key matched; grain test PASS | `510dea5` |
| `R-02` on `agg_vehicle_monthly`, rates as ratios of sums | `value_mismatches`, `rate_mismatches`; the SQL reads only `ref('agg_vehicle_monthly')` | 0, 0 | `510dea5` |
| `R-03` ranked within month, fleet and garage, ties shared | `rank_mismatches`; unit test `vehicle_scorecard_ranks_within_each_month_and_garage_and_shares_a_tied_rank` | 0; PASS | `510dea5` |
| `R-04` under 40 hours kept, ranked, flagged | `flag_mismatches`, `flagged`, `flagged_unranked` | 0; 115; 0 | `510dea5` |
| `R-05` the cut-short month marked | `incomplete_months`; unit test `vehicle_scorecard_marks_only_a_cut_short_month` | `2023-12` only; PASS | `510dea5` |
| `R-06` additive, nothing in `sa_prd` | `git diff --name-only 7fcde94 HEAD`; `run_results.json` of the gate | one new `.sql`; the relation is in `vd_eval_20261103192916_83f4d5f25477_eph` = `VD_EPHM_MOTHERDUCK_DATABASE`; every command on `--target dev`; no Flight run | `510dea5` |
| `R-07` semantic layer | Gate results below | exit 0 each | `510dea5` |

Acceptance query (`dbt show --inline … --output json --target dev --defer --state /data/cache/prod-target`):

```sql
with src as (
    select month_start_date, vehicle_key, garage_key, online_hours, gross_revenue, trip_count,
           gross_revenue / nullif(online_hours, 0) as rate
    from {{ ref('agg_vehicle_monthly') }}
), ranked as (
    select *, rank() over (partition by month_start_date order by rate desc nulls last) as fleet_rank_expected,
              rank() over (partition by month_start_date, garage_key order by rate desc nulls last) as garage_rank_expected
    from src
)
select
    (select count(*) from {{ ref('mart_vehicle_scorecard') }}) as mart_rows,
    (select count(*) from src) as source_rows,
    count(m.vehicle_key) as matched_keys,
    count(*) filter (where abs(m.online_hours - r.online_hours) > 1e-6 or abs(m.gross_revenue - r.gross_revenue) > 0.005 or m.trip_count <> r.trip_count) as value_mismatches,
    count(*) filter (where m.fleet_rank <> r.fleet_rank_expected or m.garage_rank <> r.garage_rank_expected) as rank_mismatches,
    count(*) filter (where abs(coalesce(m.revenue_per_online_hour, -1) - coalesce(m.gross_revenue / nullif(m.online_hours, 0), -1)) > 1e-9
                        or abs(coalesce(m.occupancy_rate, -1) - coalesce(m.on_trip_hours / nullif(m.online_hours, 0), -1)) > 1e-9) as rate_mismatches,
    count(*) filter (where m.is_below_ranking_floor <> (m.online_hours < 40)) as flag_mismatches,
    count(*) filter (where m.is_below_ranking_floor) as flagged,
    count(*) filter (where m.is_below_ranking_floor and (m.fleet_rank is null or m.garage_rank is null)) as flagged_unranked,
    string_agg(distinct strftime(m.month_start_date, '%Y-%m'), ',') filter (where m.is_incomplete_month) as incomplete_months
from ranked r left join {{ ref('mart_vehicle_scorecard') }} m using (month_start_date, vehicle_key)
```

## Gate results

| Gate | Command | Exit | Outcome |
| --- | --- | --- | --- |
| Nodes built and deferred | `dbt ls --resource-type model --select "mart_vehicle_scorecard state:modified+,+mart_vehicle_scorecard" --state /data/cache/prod-selection --target dev` and the deferred set | 0, 0 | builds `mart_vehicle_scorecard`; defers 25 ancestors; no changed ancestor |
| Model gate | `dbt build --select "mart_vehicle_scorecard state:modified+,+mart_vehicle_scorecard" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev` | 0 | PASS=12 |
| dbt data tests | `dbt build --select mart_vehicle_scorecard+ --exclude test_type:unit --defer --state /data/cache/prod-target --target dev` | 0 | PASS=11 WARN=1 (the existing levels finding) |
| dbt unit tests | `dbt test --select mart_vehicle_scorecard+,test_type:unit --defer --state /data/cache/prod-target --target dev` | 0 | PASS=2 |
| Project audit | `dbt build --select package:dbt_project_evaluator --vars '{dbt_project_evaluator_enabled: true}' --warn-error-options '{"error":["NoNodesForSelectionCriteria"]}' --target dev` | 0 | PASS=66 WARN=12 ERROR=0 |
| Ossie chain | `ossie.py validate`, `coverage logical-model/ transformation/models/marts/` (the layers declare no role, so the skill's fallback), `suppliers`, `notes`, `generate-tests --check` | 0 each | the three `validate` warnings `main` has; 35 of 35 named |
| validating-semantic-model | the review | — | verdict pass: `LTS9_vehicle_scorecard` binds only the shift metrics' columns at month and vehicle, its ranks, flags and rate columns refused; held by `assert_semantic_content_holds` (PASS) |
| Ontology | `ossie.py validate ontology/`, `refs`, `glossary` | 0, 0, 0 | pass |
| Baseline cross-check | `dbt ls -s state:modified+ --resource-type model --state /data/cache/prod-selection --target dev` | 0 | `mart_vehicle_scorecard` only = the Plan's target; `manifest-source.json` `build_sha` `7fcde94` |
| Weakening, words, dev artifacts | `git diff 7fcde94 HEAD` | — | nothing weakened; the record, `CONTEXT.md` and YAML agree with the built mart |
| Ship currency | `python3 <plugin>/scripts/ship_currency.py --rows .agents_tmp/ship-currency-rows.json` | 0 | fresh |
| Contract promotion | `access: protected` on `mart_vehicle_scorecard`, which sets no enforced contract; no touched model sets `contract: {enforced: true}` or `access: public` | — | manifest diff not applicable |
| Domain sweep | `CONTEXT.md`, `docs/adr/` | — | domain sweep: nothing new (incomplete month added at the requirement) |
| Publication | `gh pr create --head intent/new-intent-2b870cef ...`, then `gh pr view 1 --json state,headRefName,baseRefName` | 0, 0 | https://github.example.invalid/domain/repo/pull/1, OPEN, base `main` |

## Discovery

- `agg_vehicle_monthly` holds 1,376 vehicle-months, unique on (`vehicle_key`, `month_start_date`): December 2023 116 (115 under 40 online hours; its most active vehicle has 1 active day of 31), January to March 2024 420 each (none under 40; the most active vehicle has every calendar day) — `select month_start_date, count(*) as n, count(*) filter (where online_hours < 40) as under_floor, max(active_days) as max_active, max(calendar_days) as cal, count(distinct (vehicle_key, month_start_date)) as keys from {{ ref('agg_vehicle_monthly') }} group by 1 order by 1` (`dbt show --inline … --target dev --defer --state /data/cache/prod-target`)
- `mart_driver_scorecard` flags `p.online_hours < 40 as is_below_ranking_floor`; ADR 0010 names the flag but no number — `transformation/models/marts/ops/mart_driver_scorecard.sql`, `docs/adr/0010-driver-ranking-and-utilisation-definitions.md`
