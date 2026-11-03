---
artifacts: [mart_monthly_service_summary]
---

# mart_monthly_service_summary

Monthly volume and revenue by fleet and payment method.

## Grain

One row per pickup month, service type and payment method; the settlement class and the counts-as-revenue flag are attributes of the payment method.

## Schema

- `mart_monthly_service_summary`: `finance` (default). Source: user answer (schemas).

## Decisions

- `D-01` Apply the billable rule and the reporting window here, in gold, as every finance mart does ([ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md)). Source: existing model, [ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md).
- `D-02` Publish `avg_measurable_tip_rate` as the mean of the trip-level measurable tip rate over the trips where it is measurable, with `measurable_tip_trip_count` and `tip_measurable_share` (that count over all the row's trips) beside it, the exception [ADR 0016](../../../adr/0016-rates-are-rebuilt-from-summed-numerators-and-denominators.md) names for this rate. Tips count only where the payment method records them ([ADR 0011](../../../adr/0011-tips-are-measured-only-where-the-meter-records-them.md)), so a row whose method records none has a null rate and a share of 0. Source: docs/requirement/2026-11-03-the-v2-surcharge-split-and-tip-rate-on-the-full-motherduck-model-answer-domain-03d745f1 R-05, ADR 0016, ADR 0011.
- `D-03` In the trip Ossie document the rate is `billable_avg_measurable_tip_rate`, a `derived_expression` over `billable_measurable_tip_rate_total` and `billable_measurable_tip_trip_count`, bound to no column, so an engine rebuilds the mean at any grain. `LTS8_monthly_service_summary` binds `measurable_tip_trip_count` only and refuses the precomputed mean and share; `measurable_tip_rate` becomes a field of `trips`. Source: docs/requirement/2026-11-03-the-v2-surcharge-split-and-tip-rate-on-the-full-motherduck-model-answer-domain-03d745f1 R-07, [ADR 0016](../../../adr/0016-rates-are-rebuilt-from-summed-numerators-and-denominators.md), `.agents/skills/semantic-model/references/modeling-rules.md` (S3c).

## Logical Model

```yaml
documents:
  logical-model/nyc_taxi_analytics.ossie.yaml:
    datasets:
      changed: [trips]
    metrics:
      added: [billable_measurable_tip_rate_total, billable_measurable_tip_trip_count, billable_avg_measurable_tip_rate]
    logical_sources:
      changed: [trips.LTS1_detail, trips.LTS8_monthly_service_summary]
ontology:
  concepts: {added: [], changed: [], retired: []}
  mappings: {added: [], changed: [], retired: []}
```

## Rejected

- A blended rate, tip revenue over fare revenue across every trip: falls with the share of trips paying another way ([ADR 0011](../../../adr/0011-tips-are-measured-only-where-the-meter-records-them.md)).
- A ratio of summed tips to summed fares over measurable trips: ADR 0016 makes the measurable tip rate the exception to summed ratios.

## Consumers

None in this repo.

## History

- 2026-11-03 — new-intent-03d745f1 — design record written; measurable tip rate with its count and share and the Ossie metrics; terms: none new — D-01 to D-03
