---
artifacts: [mart_daily_zone_revenue]
---

# mart_daily_zone_revenue

Daily revenue by pickup zone.

## Grain

One row per pickup zone and trip date.

## Schema

`finance`, unchanged.

## Decisions

- `D-01` Apply the billable rule and the reporting window here, in gold, and nowhere upstream, so quality work can still see the rows this excludes ([ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md)). Source: docs/requirement/2026-08-29-the-trip-fact.md R-03, [ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md).
- `D-02` Builds on `agg_trip_zone_daily_base`'s billable columns, shared with `agg_trip_zone_daily`, no longer on `fct_trip` and `dim_zone` directly; a zone-day with no billable trip has no row, as before. Columns, order, types and rows unchanged. Source: docs/requirement/2026-11-04-migrate-not-add-one-zone-day-roll-up-shared-by-mart-daily-zone-revenue-and-agg-trip-zone-daily-nothing-a-consumer-reads-changed-on-the-full-motherduck-model-answer-domain-3e385ecb.md R-01, R-02.

## Rejected

- Applying the rule in silver: the excluded rows would be invisible to quality work.

## Consumers

None in this repo.

## Logical Model

Unchanged: `LTS7_daily_zone_revenue` binds the same columns.

```yaml
documents: [logical-model/nyc_taxi_analytics.ossie.yaml]
datasets: {added: [], changed: [], retired: []}
metrics: {added: [], changed: [], retired: []}
logical_sources: {added: [], changed: [], retired: []}
```

## History

- - 2026-10-14 — trip-fact — design record written; audience wording removed from the model description — D-01
- 2026-11-04 — new-intent-3e385ecb — builds on agg_trip_zone_daily_base — D-02
