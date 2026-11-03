---
artifacts: [agg_driver_weekly]
---

# agg_driver_weekly

The driver-week, for the weekly shift-bidding cycle: the level between the driver-day and the driver-month.

## Grain

One row per driver and week (`driver_key`, `week_start_date`), for the weeks the driver worked at least one shift.

## Schema

- `agg_driver_weekly`: `agg` (default). Source: user answer (schemas).

## Decisions

- `D-01` The week is `dim_date.week_start_date`, joined on the day's `date_key`; the model truncates no date itself. Source: docs/requirement/2026-11-03-pending-request-r7-a-driver-by-week-aggregate-on-the-full-motherduck-model-answer-domain-97da04c4.md R-02, [ADR 0014](../../../adr/0014-weeks-start-on-monday.md).
- `D-02` Built from `agg_driver_daily`, the level below, as `agg_driver_monthly` is, so the week cannot disagree with its days; never from `agg_driver_monthly` (a week can span two months) or from shifts again. Source: docs/requirement/2026-11-03-pending-request-r7-a-driver-by-week-aggregate-on-the-full-motherduck-model-answer-domain-97da04c4.md R-04, `agg_driver_daily` `D-02`.
- `D-03` Every additive daily measure is summed. Occupancy, revenue per online hour and revenue per trip are ratios of the week's sums through `safe_divide`, null on a zero denominator, and the week carries their numerators and denominators. Source: docs/requirement/2026-11-03-pending-request-r7-a-driver-by-week-aggregate-on-the-full-motherduck-model-answer-domain-97da04c4.md R-04, [ADR 0016](../../../adr/0016-rates-are-rebuilt-from-summed-numerators-and-denominators.md).
- `D-04` `vehicles_driven` is left out: it is a distinct count per day, so summing the days counts a vehicle once per day it was driven. Source: docs/requirement/2026-11-03-pending-request-r7-a-driver-by-week-aggregate-on-the-full-motherduck-model-answer-domain-97da04c4.md R-04, user answer (measures).
- `D-05` `days_worked` counts the driver's days in the week; it is the driver's own activity and never marks a week incomplete. Source: docs/requirement/2026-11-03-pending-request-r7-a-driver-by-week-aggregate-on-the-full-motherduck-model-answer-domain-97da04c4.md R-03.
- `D-06` `week_days_covered` is the number of the week's seven days inside the data window (the first and last `shift_date` of `agg_driver_daily`), and `is_complete_week` is true when it is seven. Both are the same on every row of a week. Source: docs/requirement/2026-11-03-pending-request-r7-a-driver-by-week-aggregate-on-the-full-motherduck-model-answer-domain-97da04c4.md R-03, user answer (edge week).
- `D-07` No row for a week in which the driver worked no shift. Source: docs/requirement/2026-11-03-pending-request-r7-a-driver-by-week-aggregate-on-the-full-motherduck-model-answer-domain-97da04c4.md R-01, user answer.
- `D-08` A table, as every mart is. Source: `.agents/skills/dbt-models/SKILL.md`.
- `D-09` In the semantic layer it is an aggregate source of the shift star in `logical-model/nyc_taxi_fleet.ossie.yaml`, beside `agg_driver_daily` and `agg_driver_monthly`, at the week level of `date`. `week_days_covered`, `is_complete_week` and `days_worked` are no field of the star, and its rate columns are refused as the other driver sources refuse theirs (ADR 0016). Source: `.agents/skills/workarounds/SKILL.md`, [ADR 0016](../../../adr/0016-rates-are-rebuilt-from-summed-numerators-and-denominators.md).

## Logical Model

```yaml
documents:
  logical-model/nyc_taxi_fleet.ossie.yaml:
    datasets:
      changed: [shift]
    metrics: {added: [], changed: [], retired: []}
    logical_sources:
      added: [shift.LTS_driver_week]
ontology:
  concepts: {added: [], changed: [], retired: []}
  mappings: {added: [], changed: [], retired: []}
```

## Rejected

- Truncating `shift_date` to a week in the model: ADR 0014 makes `dim_date.week_start_date` the only week boundary.
- Marking a week incomplete from the driver's days worked: a short week of work is not a cut-short window.
- Building from `agg_driver_monthly`: a week spans two months.

## Consumers

None in this repo.

## History

- 2026-11-03 — new-intent-97da04c4 — design record written; terms: added driver-week, incomplete week — D-01 to D-09
