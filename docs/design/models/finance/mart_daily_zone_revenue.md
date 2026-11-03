---
artifacts: [mart_daily_zone_revenue]
---

# mart_daily_zone_revenue

Daily revenue by pickup zone.

## Grain

One row per pickup zone and trip date.

## Decisions

- `D-01` Apply the billable rule and the reporting window here, in gold, and nowhere upstream, so quality work can still see the rows this excludes ([ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md)). Source: docs/requirement/2026-08-29-the-trip-fact.md R-03, [ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md).
- `D-02` Keep `surcharge_revenue` exactly as it is and publish `congestion_surcharge_revenue` and `airport_fee_revenue` beside it, so no published column changes. `surcharge_revenue` already includes the congestion surcharge and never the airport fee, so the new columns are not a partition of it. Source: user answer, docs/requirement/2026-11-03-the-v2-surcharge-split-and-tip-rate-on-the-full-motherduck-model-answer-domain-03d745f1 R-01, R-02, R-03.
- `D-03` A trip with no recorded congestion surcharge or airport fee adds nothing to its revenue column, as `total_surcharges` already treats a missing surcharge; a zone-day with none recorded reads 0. Source: user answers, docs/requirement/2026-11-03-the-v2-surcharge-split-and-tip-rate-on-the-full-motherduck-model-answer-domain-03d745f1 R-02, R-03.
- `D-04` Publish `airport_fee_trip_count` (trips with an airport fee above zero) and `congestion_surcharge_trip_count` (trips with a congestion surcharge above zero) beside the two revenues, so a total over trips that lack the measure does not read as complete. Source: user answers, docs/requirement/2026-11-03-the-v2-surcharge-split-and-tip-rate-on-the-full-motherduck-model-answer-domain-03d745f1 R-04.
- `D-05` In the trip Ossie document, the four columns bind new billable metrics on `LTS7_daily_zone_revenue`, and the detail source supplies them from `fct_trip`'s `congestion_surcharge` and `airport_fee`, two new fields of `trips`. Source: docs/requirement/2026-11-03-the-v2-surcharge-split-and-tip-rate-on-the-full-motherduck-model-answer-domain-03d745f1 R-07, `.agents/skills/workarounds/SKILL.md`, `.agents/skills/semantic-model/SKILL.md`.

## Logical Model

```yaml
documents:
  logical-model/nyc_taxi_analytics.ossie.yaml:
    datasets:
      changed: [trips]
    metrics:
      added: [billable_congestion_surcharge_revenue, billable_congestion_surcharge_trip_count, billable_airport_fee_revenue, billable_airport_fee_trip_count]
    logical_sources:
      changed: [trips.LTS1_detail, trips.LTS7_daily_zone_revenue]
ontology:
  concepts: {added: [], changed: [], retired: []}
  mappings: {added: [], changed: [], retired: []}
```

## Rejected

- Replacing `surcharge_revenue` with its parts: changes a published column; the user kept it.
- Nulling a zone-day total when any trip lacks the measure: most zone-days would read null; the user chose to sum what is recorded and publish the count beside it.

- Applying the rule in silver: the excluded rows would be invisible to quality work.

## Consumers

None in this repo.

## History

- - 2026-10-14 — trip-fact — design record written; audience wording removed from the model description — D-01
- 2026-11-03 — new-intent-03d745f1 — congestion-surcharge and airport-fee revenue with their trip counts, the Ossie metrics; terms: none new — D-02 to D-05
