# Verification: The v2 surcharge split and tip rate, on the full MotherDuck model-answer Domain

## Verification

`verdict: verified` at `d45d4f3`: both marts are rebuilt in the Intent's Ephemeral MotherDuck database (`vd_eval_20261103194016_02ed7f0a991f_eph`) on target `dev`, each by its own path-selection run with its ancestors deferred. `mart_daily_zone_revenue` keeps `surcharge_revenue` and every existing column, and its four new columns equal a recomputation from `fct_trip` on all 20,770 zone-days. `mart_monthly_service_summary`'s measurable tip rate, count and share equal a recomputation within 1e-9 on all 30 rows, the rate null on the 21 rows with no measurable trip. The trip Ossie document's fields, metrics and bindings pass every gate. No golden baseline is configured: an independent recomputation from `fct_trip` stands in, and the existing columns are recomputed from it too rather than read from `sa_prd`. Limits: `assert_semantic_levels_hold` warns once, the existing `trips.LTS5_weather…` finding; this repo publishes no data contracts.

## Coverage

| Item | Evidence | Result | At |
| --- | --- | --- | --- |
| `R-01` `surcharge_revenue` and every existing column unchanged | per zone-day recomputation from `fct_trip` joined to `dim_zone` (trip count exact; fare, tip, surcharge, toll and total revenue at the cent) | 20,770 of 20,770 matched, 0 mismatches | `d45d4f3` |
| `R-02` `congestion_surcharge_revenue` | the same recomputation, `sum(coalesce(congestion_surcharge, 0))` | 0 mismatches; total 20,236,949.75 | `d45d4f3` |
| `R-03` `airport_fee_revenue` | the same, for `airport_fee` | 0 mismatches; total 1,241,469.25 | `d45d4f3` |
| `R-04` the two trip counts | recounted (`> 0`), exact | 0 mismatches; 709,411 fee trips, 8,090,401 surcharge trips (the discovery counts); unit test PASS | `d45d4f3` |
| `R-05` the measurable tip rate, count and share | recomputed per month, service type and payment method, within 1e-9 | 30 of 30 matched, 0 mismatches; the rate null on all 21 rows with a count of 0; unit test PASS | `d45d4f3` |
| `R-06` additive, grains unchanged | the two joins above match every key both ways; `git diff --name-only 7fcde94 HEAD` | 20,770 and 30 keys matched; the SQL diffs add columns only | `d45d4f3` |
| `R-07` semantic layer | Gate results below | exit 0 each | `d45d4f3` |
| `R-08` nothing in `sa_prd` | each gate's `run_results.json`; every command on `--target dev` | both relations in `vd_eval_20261103194016_02ed7f0a991f_eph` = `VD_EPHM_MOTHERDUCK_DATABASE`; no Flight run | `d45d4f3` |

Acceptance query (`dbt show --inline … --output json --target dev --defer --state /data/cache/prod-target`):

```sql
with e as (
    select f.pickup_date as trip_date, z.zone_natural_key as pickup_location_id,
        count(*) as trip_count, sum(f.fare_amount) as fare, sum(f.tip_amount) as tip, sum(f.total_surcharges) as surcharge,
        sum(f.tolls_amount) as tolls, sum(f.total_amount) as total,
        sum(coalesce(f.congestion_surcharge, 0)) as cs, sum(case when f.congestion_surcharge > 0 then 1 else 0 end) as csn,
        sum(coalesce(f.airport_fee, 0)) as af, sum(case when f.airport_fee > 0 then 1 else 0 end) as afn
    from {{ ref('fct_trip') }} f join {{ ref('dim_zone') }} z on f.pickup_zone_key = z.zone_key
    where f.pickup_datetime >= timestamp '2024-01-01' and f.pickup_datetime < timestamp '2024-04-01' and f.is_billable
    group by 1, 2
), d as (
    select
        count(*) as zone_days, count(m.trip_date) as matched,
        count(*) filter (where m.trip_count <> e.trip_count or abs(m.fare_revenue - e.fare) > 0.005 or abs(m.tip_revenue - e.tip) > 0.005
            or abs(m.surcharge_revenue - e.surcharge) > 0.005 or abs(m.toll_revenue - e.tolls) > 0.005 or abs(m.total_revenue - e.total) > 0.005) as existing_mismatch,
        count(*) filter (where abs(m.congestion_surcharge_revenue - e.cs) > 0.005 or abs(m.airport_fee_revenue - e.af) > 0.005
            or m.congestion_surcharge_trip_count <> e.csn or m.airport_fee_trip_count <> e.afn) as new_mismatch,
        round(sum(m.airport_fee_revenue), 2) as airport_fee_total, sum(m.airport_fee_trip_count) as fee_trips,
        round(sum(m.congestion_surcharge_revenue), 2) as congestion_total, sum(m.congestion_surcharge_trip_count) as congestion_trips
    from e left join {{ ref('mart_daily_zone_revenue') }} m using (trip_date, pickup_location_id)
), t as (
    select date_trunc('month', f.pickup_datetime) as trip_month, f.service_type_key as service_type, p.payment_method_name,
        count(*) as n, avg(f.measurable_tip_rate) as r, count(f.measurable_tip_rate) as mn, count(f.measurable_tip_rate)::double / count(*) as sh
    from {{ ref('fct_trip') }} f join {{ ref('dim_payment_method') }} p on f.payment_method_key = p.payment_method_key
    where f.pickup_datetime >= timestamp '2024-01-01' and f.pickup_datetime < timestamp '2024-04-01' and f.is_billable
    group by 1, 2, 3
), mo as (
    select count(*) as summary_rows, count(m.trip_month) as matched_rows,
        count(*) filter (where m.trip_count <> t.n or abs(coalesce(m.avg_measurable_tip_rate, -1) - coalesce(t.r, -1)) > 1e-9
            or m.measurable_tip_trip_count <> t.mn or abs(m.tip_measurable_share - t.sh) > 1e-9) as tip_mismatch,
        count(*) filter (where m.measurable_tip_trip_count = 0) as no_measurable_rows,
        count(*) filter (where m.measurable_tip_trip_count = 0 and m.avg_measurable_tip_rate is not null) as rate_not_null_on_zero
    from t left join {{ ref('mart_monthly_service_summary') }} m using (trip_month, service_type, payment_method_name)
)
select * from d cross join mo
```

## Gate results

| Gate | Command | Exit | Outcome |
| --- | --- | --- | --- |
| Model gates | `dbt build --select "<mart> state:modified+,+<mart>" --state /data/cache/prod-selection --defer --defer-state /data/cache/prod-target --target dev`, once per mart | 0, 0 | PASS=12 WARN=1 and PASS=11 WARN=1; each built only its mart (21 and 22 ancestors deferred) |
| dbt data tests | `dbt build --select mart_daily_zone_revenue+ mart_monthly_service_summary+ --exclude test_type:unit --defer --state /data/cache/prod-target --target dev` | 0 | PASS=19 WARN=1 (the existing levels finding) |
| dbt unit tests | `dbt test --select mart_daily_zone_revenue+,test_type:unit mart_monthly_service_summary+,test_type:unit --defer --state /data/cache/prod-target --target dev` | 0 | PASS=2 |
| Project audit | `dbt build --select package:dbt_project_evaluator --vars '{dbt_project_evaluator_enabled: true}' --warn-error-options '{"error":["NoNodesForSelectionCriteria"]}' --target dev` | 0 | PASS=66 WARN=12 ERROR=0 |
| Ossie chain | `ossie.py validate`, `coverage logical-model/ transformation/models/marts/`, `suppliers`, `notes`, `generate-tests --check` | 0 each | the three `validate` warnings `main` has; 34 of 34 named |
| validating-semantic-model | the review | — | verdict pass: the seven metrics carry the billable `filter`; the tip rate is a `derived_expression` over its total and count, bound to no column; `LTS8` refuses the precomputed mean and share; held by `assert_semantic_content_holds` (PASS) |
| Ontology | `ossie.py validate ontology/`, `refs`, `glossary` | 0, 0, 0 | pass |
| Baseline cross-check | `dbt ls -s state:modified+ --resource-type model --state /data/cache/prod-selection --target dev` | 0 | exactly the two marts = the Plan's two targets; `manifest-source.json` `build_sha` `7fcde94` |
| Weakening, words, dev artifacts | `git diff 7fcde94 HEAD` | — | nothing weakened; the records and YAML agree with the built marts |
| Ship currency | `python3 <plugin>/scripts/ship_currency.py --rows .agents_tmp/ship-currency-rows.json` | 0 | fresh |
| Contract promotion | `access: protected` on both marts, which set no enforced contract | — | manifest diff not applicable |
| Domain sweep | `CONTEXT.md`, `docs/adr/` | — | domain sweep: nothing new |
| Publication | `gh pr create --head intent/new-intent-03d745f1 ...`, then `gh pr view 1 --json state,headRefName,baseRefName` | 0, 0 | https://github.example.invalid/domain/repo/pull/1, OPEN, base `main` |

## Discovery

- Billable trips in the reporting window run from 2024-01-01 to 2024-03-31 (9,604,511 trips). Among them, 751,889 yellow trips have `airport_fee_status` `missing` and 166,941 green trips `not_applicable`; 8,685,681 record an airport fee and 709,411 a fee above zero; 751,889 yellow and 8,434 green trips have no congestion surcharge, and 8,090,401 carry one above zero — `select count(*) filter (where service_type_key = 'yellow' and airport_fee_status = 'missing') as yellow_fee_missing, count(*) filter (where service_type_key = 'green' and airport_fee_status = 'not_applicable') as green_fee_not_applicable, count(*) filter (where airport_fee is not null) as fee_recorded, count(*) filter (where airport_fee > 0) as fee_above_zero, count(*) filter (where congestion_surcharge is null and service_type_key = 'yellow') as yellow_congestion_null, count(*) filter (where congestion_surcharge is null and service_type_key = 'green') as green_congestion_null, count(*) filter (where congestion_surcharge > 0) as congestion_above_zero, count(*) as billable_in_window, min(pickup_date) as first_day, max(pickup_date) as last_day from {{ ref('fct_trip') }} where pickup_datetime >= timestamp '2024-01-01' and pickup_datetime < timestamp '2024-04-01' and is_billable ` (`dbt show --inline … --target dev --defer --state /data/cache/prod-target`)
- `total_surcharges` sums `coalesce(<column>, 0)` over `extra`, `mta_tax`, `improvement_surcharge` and `congestion_surcharge`, so `surcharge_revenue` holds the congestion surcharge and no airport fee — `transformation/macros/finance.sql`
