---
kinds: [transformation]
---

# Requirement: The v2 surcharge split and tip rate, on the full MotherDuck model-answer Domain

## Ask

"split the surcharge revenue into congestion surcharge and airport fee mart_daily_zone_revenue. In mart_monthly_service_summary, add the tip rate." Finance reporting consumes both marts.

## Requirements

- [ ] `R-01` `mart_daily_zone_revenue` keeps `surcharge_revenue` unchanged — accept when every existing column of the built mart equals the Domain's `finance.mart_daily_zone_revenue` on every zone-day — source: answer (Surcharge columns)
- [ ] `R-02` `mart_daily_zone_revenue` gains `congestion_surcharge_revenue`, the sum of the zone-day's recorded congestion surcharges, a missing one adding nothing — accept when it equals an independent recomputation from `core.fct_trip` at the cent on every zone-day — source: request; answer (Missing congestion surcharges)
- [ ] `R-03` `mart_daily_zone_revenue` gains `airport_fee_revenue`, the sum of the zone-day's recorded airport fees, a missing one adding nothing — accept when it equals an independent recomputation from `core.fct_trip` at the cent on every zone-day — source: request; answer (Missing airport fees)
- [ ] `R-04` `mart_daily_zone_revenue` gains `airport_fee_trip_count`, the trips with `airport_fee > 0`, and `congestion_surcharge_trip_count`, the trips with `congestion_surcharge > 0` — accept when each equals an independent recount on every zone-day — source: answers (Airport-fee count, Congestion count)
- [ ] `R-05` `mart_monthly_service_summary` gains `avg_measurable_tip_rate`, the mean of `measurable_tip_rate` over the trips where it is measurable, with `measurable_tip_trip_count` and `tip_measurable_share` beside it — accept when each equals an independent recomputation from `core.fct_trip` within 1e-9 on every row, and the rate is null wherever the count is 0 — source: request; ADR 0016; ADR 0011
- [ ] `R-06` Both changes are additive and the grains are unchanged — accept when each mart's row count and key set equal the Domain's and no existing column changes — source: answer (Surcharge columns); request
- [ ] `R-07` The semantic layer moves with the change: the new fields and metrics in `logical-model/nyc_taxi_analytics.ossie.yaml`, the tip rate as a `derived_expression` — accept when the Ossie and ontology gates exit 0 — source: repository (`workarounds` skill)
- [ ] `R-08` Nothing is written to the Domain database `sa_prd` — accept when every build runs on target `dev` with the path selection and defer, and dbt's own output names `VD_EPHM_MOTHERDUCK_DATABASE` — source: repository (`workarounds` skill), plugin `motherduck/dbt.md`

## Business decisions

| Decision | Value | Source |
| --- | --- | --- |
| Grain of `mart_daily_zone_revenue` | One row per pickup date and pickup zone, unchanged | existing model |
| Grain of `mart_monthly_service_summary` | One row per month, service type and payment method, unchanged | existing model |
| `surcharge_revenue` | Kept exactly as it is; the two new revenues sit beside it (it already includes the congestion surcharge and never the airport fee) | user answer |
| A trip with no airport fee in `airport_fee_revenue` | Adds nothing: the total sums the recorded fees, and a zone-day with none recorded reads 0 | user answer |
| A trip with no congestion surcharge in `congestion_surcharge_revenue` | Adds nothing | user answer |
| Coverage beside `airport_fee_revenue` | `airport_fee_trip_count`: trips with a fee greater than zero | user answer |
| Coverage beside `congestion_surcharge_revenue` | `congestion_surcharge_trip_count`: trips with a congestion surcharge greater than zero | user answer |
| Tip rate | "The measurable tip rate is the exception: it is a trip-level measure with no denominator to sum, and its aggregate is a mean over the trips where it is measurable, with the measurable share published beside it (ADR 0011)." | ADR 0016 |
| Which trips the tip rate measures | "The measurable tip rate is the tip as a share of the fare, and it exists only for payment methods that record tips (the payment method master flags them). For every other method it is null, not zero, because an unrecorded tip is unmeasured rather than absent. Aggregates publish the share of trips for which it is measurable beside the rate." | ADR 0011 |
| Count beside the tip rate | "Averages of the rate ignore nulls by design; a count of measurable trips accompanies them." | ADR 0011 |
| Billable rule and report window | Unchanged: both marts keep their `is_billable` filter and `in_report_window` | existing models; ADR 0003 |

## Out of scope

No existing column of either mart is removed, renamed or recomputed; `total_surcharges` and every other model are untouched; no consumer changes.

## Open questions

None.

## Approvals
- 2026-11-03T19:42:00Z — requirement approved — "Approve and continue to design." — 2d08e96
- 2026-11-03T19:43:10Z — design approved — "Approve and continue to planning." — 8a7320c
- 2026-11-03T19:48:37Z — ship approved — "approved" — 8f13cda
