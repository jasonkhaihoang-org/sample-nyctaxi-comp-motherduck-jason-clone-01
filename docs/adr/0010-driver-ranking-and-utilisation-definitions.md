---
status: decided
date: 2026-10-14
---

# Drivers are ranked on revenue per online hour; asset utilisation is taken against the 24-hour day

Driver performance is ranked on revenue per online hour, not gross revenue: gross revenue rewards whoever worked the most hours, which is a roster fact. A driver below a minimum number of online hours is flagged with `is_below_ranking_floor` and still ranked; a consumer who wants only stable ranks filters the flag, because a rank on a few shifts is noise. Asset utilisation is taken against the 24-hour day, and labour utilisation (occupancy) against sign-on time. A medallion idle in the depot is the asset question; a driver idle on the road is the labour question, and they are different numbers.

## Considered options

- **Rank on gross revenue** — rejected: it measures hours worked.
- **Rank on revenue per trip** — rejected: it rewards long fares over steady work.
- **Asset utilisation against sign-on time** — rejected: it hides a vehicle that sat unused.
- **Revenue per online hour; 24-hour day for assets** — chosen.

## Consequences

- `mart_driver_scorecard` carries the floor flag and the ranks.
- Vehicle aggregates report both asset utilisation and occupancy.
- The semantic model's `revenue_per_online_hour` uses the same ratio of sums (ADR 0016).

## Affected designs

- [`models/ops/mart_driver_scorecard.md`](../design/models/ops/mart_driver_scorecard.md)
- [`models/core/fct_shift.md`](../design/models/core/fct_shift.md)
- [`models/ops/mart_vehicle_scorecard.md`](../design/models/ops/mart_vehicle_scorecard.md)
