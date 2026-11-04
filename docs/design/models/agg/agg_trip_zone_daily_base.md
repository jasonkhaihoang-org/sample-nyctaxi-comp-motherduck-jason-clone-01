---
artifacts: [agg_trip_zone_daily_base]
---

# agg_trip_zone_daily_base

The zone-day roll-up of the trip fact over the reporting window, computed once for the two models that report it: `agg_trip_zone_daily` (every trip) and `mart_daily_zone_revenue` (billable trips).

## Grain

One row per pickup date and pickup zone version (`pickup_date`, `pickup_location_id`, with the zone's name, borough and reporting region).

## Schema

`agg`, the folder's current schema (user answer, design stop).

## Decisions

- `D-01` A gold `agg_` model, not a silver `int_` one: it is a grain-committed aggregate built from a fact, which the repository's dbt-models skill places in gold, and a silver model reading `fct_trip` would make silver depend on gold. Source: docs/requirement/2026-11-04-migrate-not-add-one-zone-day-roll-up-shared-by-mart-daily-zone-revenue-and-agg-trip-zone-daily-nothing-a-consumer-reads-changed-on-the-full-motherduck-model-answer-domain-3e385ecb.md R-01; `.agents/skills/dbt-models/SKILL.md`.
- `D-02` The billable sums sit beside the all-trip sums in one row, rather than a row per billable flag: `attributed_driver_count` is a distinct count over all of the zone-day's trips and cannot be summed back across such a split. The billable rule is still applied in gold (ADR 0003). Source: docs/requirement/2026-11-04-migrate-not-add-one-zone-day-roll-up-shared-by-mart-daily-zone-revenue-and-agg-trip-zone-daily-nothing-a-consumer-reads-changed-on-the-full-motherduck-model-answer-domain-3e385ecb.md R-04.
- `D-03` Grouped by the zone version's name, borough and reporting region, the union of both models' former keys; on the Domain this gives the same 20,771 zone-days as `agg_trip_zone_daily`'s own grouping. Source: docs/requirement/2026-11-04-migrate-not-add-one-zone-day-roll-up-shared-by-mart-daily-zone-revenue-and-agg-trip-zone-daily-nothing-a-consumer-reads-changed-on-the-full-motherduck-model-answer-domain-3e385ecb.md R-02, R-03.

## Rejected

- A silver `int_` model: silver would read gold.
- One row per billable flag: the distinct driver count would break.
- A macro called by both models: it removes the duplicated text but not the duplicated scan, and gives neither model a relation to build on.

## Consumers

Depended on by: `agg_trip_zone_daily`, `mart_daily_zone_revenue`. Nothing reads it directly.

## Logical Model

Registered in `logical-model/nyc_taxi_analytics.ossie.yaml`'s `physical_tables` with a note saying why it is not mapped; no dataset, metric or logical source changes.

```yaml
documents: [logical-model/nyc_taxi_analytics.ossie.yaml]
datasets: {added: [], changed: [], retired: []}
metrics: {added: [], changed: [], retired: []}
logical_sources: {added: [], changed: [], retired: []}
```

## History

- 2026-11-04 — new-intent-3e385ecb — design record written — D-01, D-02, D-03
