---
artifacts: [agg_hvfhv_trip_zone_daily]
---

# agg_hvfhv_trip_zone_daily

Daily HVFHV trip volume per pickup zone, to read beside the taxi volume in `agg_trip_zone_daily`.

## Grain

One row per pickup zone per pickup date, unique on (`pickup_location_id`, `pickup_date`).

## Schema

- `agg_hvfhv_trip_zone_daily`: `agg` (default). Source: user answer (schemas).

## Decisions

- `D-01` The HVFHV trip count (`hvfhv_trip_count`) is the only measure: one combined count, with no fare, revenue, driver pay or miles, and no split by licensee. Source: docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md R-03, user answer (measure).
- `D-02` Keyed by `pickup_location_id` and `pickup_date` with the names, types and meaning `agg_trip_zone_daily` publishes (`BIGINT` and `DATE`), and filtered to the reporting window the same way (`in_report_window` on the pickup timestamp). Source: docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md R-04, user answer (grain).
- `D-03` Every HVFHV trip in the window counts; no billable rule applies. Source: [ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md) (the rule applies where revenue and flows are reported), user answer.
- `D-04` Trips in unknown zones are kept, never dropped or remapped: the zone id is grouped as the source gives it, with no join to `dim_zone`. Source: [ADR 0012](../../../adr/0012-unresolved-zones-are-retained-and-flagged.md).
- `D-05` A new aggregate built from `stg_tlc__fhvhv_tripdata`, beside `agg_trip_zone_daily`, which is left unchanged: it counts taxi trips from `fct_trip`, and HVFHV does not enter the trip fact. Source: docs/requirement/2026-11-03-pending-request-r4-onboard-the-tlc-high-volume-for-hire-feed-with-a-daily-zone-aggregate-on-the-full-motherduck-model-answer-domain-d0d80c5b.md R-05, user answer (reuse), [ADR 0006](../../../adr/0006-silver-is-built-in-dbt.md).
- `D-06` In the semantic layer it is a new star in the trip document, `logical-model/nyc_taxi_analytics.ossie.yaml`: its own dataset `hvfhv_zone_day` with the metric `hvfhv_trip_count`, joined to the document's `zone` dimension at the zone level by `pickup_location_id` and to `date` at the day level by `pickup_date`. It is not an aggregate source of the trip star, whose fact holds no HVFHV trips. Sharing the two dimensions is what lets a query read HVFHV volume beside `trip_count` by zone and day. Source: user answer (semantic routing), `.agents/skills/workarounds/SKILL.md`, `.agents/skills/semantic-model/SKILL.md` (a new business process is a new star).
- `D-07` It carries no ontology concept: an aggregate mart gets none, and HVFHV trips have no boundary fact a concept could map. The Ossie dataset's description says so. Source: `.agents/skills/ontology/references/classification.md` (aggregate or report mart).
- `D-08` A table, as every mart is. Source: `.agents/skills/dbt-models/SKILL.md`, `dbt_project.yml`.

## Logical Model

```yaml
documents:
  logical-model/nyc_taxi_analytics.ossie.yaml:
    datasets:
      added: [hvfhv_zone_day]
    metrics:
      added: [hvfhv_trip_count]
    logical_sources:
      added: [hvfhv_zone_day.LTS1_detail]
    relationships:
      added: [hvfhv_zone_day_to_pickup_zone, hvfhv_zone_day_to_date]
ontology:
  ontology/nyc_taxi.ontology.yaml:
    concepts: {added: [], changed: [], retired: []}
  mappings: {added: [], changed: [], retired: []}
```

## Rejected

- Extending `agg_trip_zone_daily` with an HVFHV column: it is built from the trip fact, which HVFHV does not enter.
- An aggregate source of the trip star: its rows are not the star's rows rolled up.
- `semantic_exclusions`: nothing about its rows defeats a mapping, and an excluded table cannot be read beside the taxi volume through the semantic layer.
- A separate Ossie document: a star in another document would carry its own copies of `zone` and `date`; in the trip document the two stars share one copy.

## Consumers

None in this repo.

## History

- 2026-11-03 — new-intent-d0d80c5b — design record written; terms: added HVFHV trip — D-01 to D-08
