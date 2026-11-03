---
kinds: [transformation]
---

# Requirement: Pending request R7: a driver-by-week aggregate, on the full MotherDuck model-answer Domain

## Ask

"Build a driver-by-week aggregate. We have `agg.agg_driver_daily` and `agg.agg_driver_monthly`; the shift-bidding cycle is weekly and we keep deriving it by hand." Shift bidding consumes it; revenue per online hour and occupancy matter most.

## Requirements

- [ ] `R-01` A new aggregate holds one row per driver per week, only for driver-weeks with activity — accept when (`driver_key`, `week_start_date`) is unique and every row has at least one shift — source: request, answer (no zero rows)
- [ ] `R-02` The week is `dim_date.week_start_date`, Monday-based — accept when every row's week equals `dim_date.week_start_date` of its days and the model truncates no date itself — source: ADR 0014
- [ ] `R-03` A week the data window cuts short is kept and marked incomplete; a driver who worked fewer days in a full week is not — accept when every row of the cut-short week is marked, no row of a full week is, and the mark depends on the window, not the driver — source: answer (edge week)
- [ ] `R-04` The week carries every daily measure that adds up to a week, summed, and its rates rebuilt as ratios of the week's sums, null on a zero denominator — accept when the weekly shifts, online hours and gross revenue reconcile to `agg_driver_daily` week by week, and each rate equals its own row's numerator over denominator — source: answer (measures), ADR 0016
- [ ] `R-05` The change is additive — accept when no existing model's SQL or columns change — source: answer (new model only)
- [ ] `R-06` The semantic layer moves with the new aggregate — accept when the Ossie and ontology gates exit 0 — source: repository (`workarounds` skill)
- [ ] `R-07` Nothing is written to the Domain database `sa_prd` — accept when every build runs on target `dev` and dbt's output names the Ephemeral database — source: repository (`workarounds` skill), plugin `motherduck/dbt.md`

## Business decisions

| Decision | Value | Source |
| --- | --- | --- |
| Grain | One row per driver per week | request |
| Week start | Monday, from `dim_date.week_start_date` | ADR 0014: "A weekly metric uses `week_start_date`; none truncates a date itself." |
| Edge weeks | The week of 2023-12-25 holds only 2023-12-31 of the data window: kept and marked incomplete, not dropped or padded | user answer |
| Weeks with no activity | No row | user answer |
| Measures | Every additive daily measure, summed; `vehicles_driven` left out, because a distinct count of the days does not add up to the week; no ranking | user answer (recommended) |
| Rates | Ratio of the week's sums through `safe_divide`, null on a zero denominator | ADR 0016: "Such a rate is never the average of lower-level rates." |
| Reuse | Built from `agg_driver_daily` and `dim_date`; not from `agg_driver_monthly`, because a week can span two months | transformation playbook (build on the published model at a finer grain) |

## Out of scope

`agg_driver_daily`, `agg_driver_monthly`, `mart_driver_scorecard` and every other existing model are unchanged. No ranking.

## Open questions

None.

## Approvals
- 2026-11-03T17:18:58Z — requirement approved — "Approve and continue to design." — 1f9c81e
- 2026-11-03T17:19:42Z — design approved — "Approve and continue to planning." — f8047ea
- 2026-11-03T17:32:47Z — ship approved — "approved" — 174ad23
