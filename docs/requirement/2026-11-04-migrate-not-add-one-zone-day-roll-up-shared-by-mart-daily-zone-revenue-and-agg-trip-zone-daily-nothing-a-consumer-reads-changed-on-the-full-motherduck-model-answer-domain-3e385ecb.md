---
kinds: [transformation]
---

# Requirement: Migrate, not add: one zone-day roll-up shared by mart_daily_zone_revenue and agg_trip_zone_daily, nothing a consumer reads changed, on the full MotherDuck model-answer Domain

## Ask

"mart_daily_zone_revenue and agg_trip_zone_daily both roll the trip fact up to zone and day, each with its own copy of the same query. Move that roll-up into one place and build both on it, and remove the duplicated SQL. Nothing anyone reads may change: the same table names, columns, column order, types and rows." Finance reporting reads `mart_daily_zone_revenue`; zone demand reporting and the semantic model read both.

## Requirements

- [ ] `R-01` One model computes the zone-day roll-up of `fct_trip` and `dim_zone` over the reporting window; `mart_daily_zone_revenue` and `agg_trip_zone_daily` both build on it and neither reads `fct_trip` itself — accept when neither model's SQL refs `fct_trip` and both ref the shared model — source: request
- [ ] `R-02` `mart_daily_zone_revenue` is unchanged for its readers: name, its 11 columns in order, their types, and its 20,770 rows — accept when the rebuilt relation equals the Domain's `finance.mart_daily_zone_revenue` column by column (non-null count and value hash per column, a DOUBLE at the cent, the rest exact) — source: request; transformation playbook (Refactor equivalence)
- [ ] `R-03` `agg_trip_zone_daily` is unchanged for its readers: name, its 14 columns in order, their types, and its 20,771 rows — accept as `R-02`, against the Domain's `agg.agg_trip_zone_daily` — source: request; transformation playbook (Refactor equivalence)
- [ ] `R-04` The billable rule stays in gold and `attributed_driver_count` stays a distinct count over all of a zone-day's trips — accept when a unit test of the shared model with billable and non-billable trips of one driver passes, and `R-02`, `R-03` hold — source: ADR 0003; existing models
- [ ] `R-05` The semantic layer stays valid with no mapping changed; the new gold model is registered with a note — accept when `ossie_lint` exits 0 — source: repository (`tools/ossie_lint.py`, the coverage gate)
- [ ] `R-06` Nothing is written to the Domain database `sa_prd` — accept when every build runs on target `dev` with the path selection and defer, and dbt's own run results name `VD_EPHM_MOTHERDUCK_DATABASE` — source: plugin `motherduck/dbt.md`

## Business decisions

| Decision | Value | Source |
| --- | --- | --- |
| Grain of both models | One row per pickup date and pickup zone, unchanged | existing models |
| Populations | `mart_daily_zone_revenue` billable trips only; `agg_trip_zone_daily` every trip in the window | existing models; ADR 0003 |
| Change for readers | None: names, columns, order, types and rows unchanged | user request |

## Out of scope

No column is added, removed, renamed or recomputed in either published model; no other model changes; no consumer changes.

## Open questions

None.

## Approvals
- 2026-11-04T07:29:40Z — requirement approved — "Approve and continue to design." — df77118
- 2026-11-04T07:30:20Z — design approved — "Approve and continue to planning." — ba0f2a6
- 2026-11-04T07:49:37Z — ship approved — "approved" — fa67167
