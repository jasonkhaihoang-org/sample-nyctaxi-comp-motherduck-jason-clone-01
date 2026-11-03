---
artifacts: [mart_vehicle_scorecard]
---

# mart_vehicle_scorecard

Vehicle performance per month, ranked within garage and fleet-wide, so vehicles are compared the way `mart_driver_scorecard` compares drivers.

## Grain

One row per vehicle per calendar month, unique on `vehicle_key` and `month_start_date`.

## Schema

- `mart_vehicle_scorecard`: `ops` (default). Source: user answer (schemas).

## Decisions

- `D-01` Read `agg_vehicle_monthly` as published and nothing below it; the month's hours, trips and revenue are the aggregate's own ([ADR 0016](../../../adr/0016-rates-are-rebuilt-from-summed-numerators-and-denominators.md)). Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-02, user answer (reuse).
- `D-02` Carry the vehicle's medallion number and garage beside its key, so a row is read without a join and peers are compared within a garage. Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-01.
- `D-03` Carry the driver scorecard's rates that the vehicle-month aggregate can build (occupancy, revenue per online hour, revenue per trip, trips per online hour), each rebuilt with `safe_divide` from the month's summed numerator and denominator, null on a zero denominator, with both published beside it ([ADR 0016](../../../adr/0016-rates-are-rebuilt-from-summed-numerators-and-denominators.md)). Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-02, request ("same idea as `ops.mart_driver_scorecard`").
- `D-04` Rank on revenue per online hour, descending, within each month: `fleet_rank` across the fleet, `garage_rank` within the vehicle's garage ([ADR 0010](../../../adr/0010-driver-ranking-and-utilisation-definitions.md)). A vehicle-month with no rate ranks after every rated one. Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-03.
- `D-05` Tied rates share a rank and the next rank is skipped (`rank()`), as the driver scorecard ranks drivers. Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-03, user answer (ties).
- `D-06` Flag a vehicle-month under 40 online hours with `is_below_ranking_floor`; it is still ranked and never dropped ([ADR 0010](../../../adr/0010-driver-ranking-and-utilisation-definitions.md)). Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-04, user answer (floor).
- `D-07` Mark a month the data window cuts short with `is_incomplete_month`: true when the month's most active vehicle was active on fewer days than the calendar month has. It reads the aggregate's own `active_days` and `calendar_days`, so it needs no lower layer, and a vehicle idle on some days of a full month leaves the month unmarked. The reason this fleet-wide test separates a cut-short month from idle vehicles is a measurement, recorded in the Verification's `## Discovery`. Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-05, user answer (cut-short month).
- `D-08` Keep every month the aggregate holds: the reporting window bounds the revenue and flow marts, not the fleet-operations marts ([ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md)). Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-01, [ADR 0003](../../../adr/0003-billable-trip-definition-and-where-it-applies.md).
- `D-09` In the semantic layer it is an aggregate source of the shift star in `logical-model/nyc_taxi_fleet.ossie.yaml`, at the month level and the vehicle, as `agg_vehicle_monthly` and `mart_driver_scorecard` are: its rows are the star's rows rolled up, the routing table's one disposition for them. Its ranks, flags and rate columns are refused, as the driver scorecard's are (ADR 0016). Source: docs/requirement/2026-11-03-pending-request-r1-a-vehicle-scorecard-per-medallion-and-month-on-the-full-motherduck-model-answer-domain-2b870cef.md R-07, `.agents/skills/workarounds/SKILL.md`, `.agents/skills/semantic-model/SKILL.md`.

## Logical Model

```yaml
documents:
  logical-model/nyc_taxi_fleet.ossie.yaml:
    datasets:
      changed: [shift]
    metrics: {added: [], changed: [], retired: []}
    logical_sources:
      added: [shift.LTS9_vehicle_scorecard]
ontology:
  concepts: {added: [], changed: [], retired: []}
  mappings: {added: [], changed: [], retired: []}
```

## Rejected

- Ranking on gross revenue, or across the whole period instead of within each month.
- Dropping vehicle-months under the floor, or dropping the cut-short month.
- Rebuilding the month from `agg_vehicle_daily`: it repeats the aggregate's work and can drift from it.
- Marking the cut-short month from the data window's first and last dates in `agg_vehicle_daily`: it reads a lower layer the aggregate already summarises.
- Marking months outside the reporting window: ADR 0003 does not apply the window to fleet-operations marts, and a month inside it can still be cut short.
- The driver scorecard's quartile and percentile: the request asks for ranks.

## Consumers

None in this repo.

## History

- 2026-11-03 — new-intent-2b870cef — design record written; terms: added incomplete month — D-01 to D-09
