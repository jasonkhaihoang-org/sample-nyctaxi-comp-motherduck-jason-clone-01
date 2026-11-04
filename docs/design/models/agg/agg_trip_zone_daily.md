---
artifacts: [agg_trip_zone_daily]
---

# agg_trip_zone_daily

Daily zone demand with period-over-period context: the lag, the 7-day average, the 28-day rolling revenue and the revenue rank at the cent.

## Grain

One row per pickup date and pickup zone.

## Schema

`agg`, unchanged.

## Decisions

- `D-01` Builds on `agg_trip_zone_daily_base`'s all-trip columns, no longer on `fct_trip` and `dim_zone` directly; its columns, order, types and rows are unchanged. Source: docs/requirement/2026-11-04-migrate-not-add-one-zone-day-roll-up-shared-by-mart-daily-zone-revenue-and-agg-trip-zone-daily-nothing-a-consumer-reads-changed-on-the-full-motherduck-model-answer-domain-3e385ecb.md R-01, R-03.

## Consumers

The semantic model's `LTS2_zone_day_agg` (`logical-model/nyc_taxi_analytics.ossie.yaml`).

## Logical Model

Unchanged: `LTS2_zone_day_agg` binds the same columns.

```yaml
documents: [logical-model/nyc_taxi_analytics.ossie.yaml]
datasets: {added: [], changed: [], retired: []}
metrics: {added: [], changed: [], retired: []}
logical_sources: {added: [], changed: [], retired: []}
```

## History

- 2026-11-04 — new-intent-3e385ecb — design record written; builds on agg_trip_zone_daily_base — D-01
