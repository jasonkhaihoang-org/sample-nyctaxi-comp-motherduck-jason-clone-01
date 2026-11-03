---
kinds: [transformation]
---

# Requirement: Pending request R1: a vehicle scorecard per medallion and month, on the full MotherDuck model-answer Domain

## Ask

"Build a vehicle scorecard — same idea as `ops.mart_driver_scorecard`, but per medallion and month by month. The depot managers want to compare vehicles the way they compare drivers." Consumed by depot managers comparing vehicles with their peers, fleet-wide and within their garage.

## Requirements

- [ ] `R-01` A new mart holds one row per vehicle per calendar month, carrying the medallion number, the month and the vehicle's garage — accept when (`vehicle_key`, `month_start_date`) is unique and the mart has exactly the rows of `agg_vehicle_monthly`, matched on that key — source: request, answer (reuse)
- [ ] `R-02` Built on `agg_vehicle_monthly` as published: no hours or revenue are recomputed from a lower layer; every rate is a ratio of the month's summed numerator and denominator, null on a zero denominator, with both published beside it — accept when the model reads only `agg_vehicle_monthly`, online hours agree within 1e-6 and gross revenue at the cent with it per vehicle and month, and each rate recomputed from the row's own numerator and denominator agrees with the published rate within 1e-9 — source: answer (reuse), [ADR 0016](../adr/0016-rates-are-rebuilt-from-summed-numerators-and-denominators.md)
- [ ] `R-03` Vehicles are ranked on revenue per online hour, descending, within each month: a fleet-wide rank and a within-garage rank; tied rates share a rank and the next rank is skipped — accept when both ranks equal a competition rank recomputed from the published rate per month and per month and garage, and a unit test pins a tie — source: request, [ADR 0010](../adr/0010-driver-ranking-and-utilisation-definitions.md), answer (ties)
- [ ] `R-04` A vehicle-month under 40 online hours is kept, ranked and flagged with `is_below_ranking_floor`, never dropped — accept when the flag is true exactly for rows with fewer than 40 online hours and every flagged row carries both ranks — source: answer (floor), [ADR 0010](../adr/0010-driver-ranking-and-utilisation-definitions.md)
- [ ] `R-05` The month the data window cuts short is kept and marked incomplete; a vehicle idle on some days of a full month is not marked — accept when only December 2023 is marked — source: answer (cut-short month)
- [ ] `R-06` Additive only, and nothing is written to the Domain database `sa_prd` — accept when no existing model's SQL or columns change, every build runs on target `dev`, and dbt's own output names the Ephemeral database (`VD_EPHM_MOTHERDUCK_DATABASE`) — source: request, repository (`workarounds` skill), plugin `motherduck/dbt.md`
- [ ] `R-07` The semantic layer moves with the new mart — accept when the Ossie and ontology gates exit 0 — source: repository (`workarounds` skill)

## Business decisions

| Decision | Value | Source |
| --- | --- | --- |
| Grain | One row per vehicle per calendar month | request ("per medallion and month by month") |
| Reuse | Built on `agg_vehicle_monthly`, read as published | user answer |
| Ranking measure | "Driver performance is ranked on revenue per online hour, not gross revenue: gross revenue rewards whoever worked the most hours, which is a roster fact." Applied to vehicles, as the request asks | [ADR 0010](../adr/0010-driver-ranking-and-utilisation-definitions.md), request |
| Ranking scope | Within each month: fleet-wide, and within the vehicle's garage | request |
| Hours floor | 40 online hours; "A driver below a minimum number of online hours is flagged with `is_below_ranking_floor` and still ranked"; the 40 is the user's figure, the same as `mart_driver_scorecard`'s | user answer, [ADR 0010](../adr/0010-driver-ranking-and-utilisation-definitions.md) |
| Ties | Tied rates share a rank; the next rank is skipped, as the driver scorecard ranks | user answer |
| Rates | "computed as a sum of numerators over a sum of denominators, through the `safe_divide` macro, which returns null when the denominator is zero" | [ADR 0016](../adr/0016-rates-are-rebuilt-from-summed-numerators-and-denominators.md) |
| Cut-short month | Kept and marked incomplete; idle days in a full month do not mark it | user answer |
| Reporting window | Not applied: it bounds the revenue and flow marts, and the fleet-operations marts do not use the rule | [ADR 0003](../adr/0003-billable-trip-definition-and-where-it-applies.md) |
| Unmatched and null keys | Keep every row; the mart joins nothing, and no vehicle, garage or medallion is null | playbook default; profiled |
| Coverage | No coverage column: no measure the mart reads is null | profiled |

## Out of scope

`agg_vehicle_monthly`, `mart_driver_scorecard`, `mart_vehicle_utilisation` and every other published model are unchanged.

## Open questions

None.

## Approvals
- 2026-11-03T19:31:28Z — requirement approved — "Approve and continue to design." — abf00af
- 2026-11-03T19:32:01Z — design approved — "Approve and continue to planning." — 77fcf8d
- 2026-11-03T19:36:37Z — ship approved — "approved" — 7d83e43
