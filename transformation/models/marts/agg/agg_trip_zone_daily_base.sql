-- The zone-day roll-up of the trip fact, computed once for the two models that
-- report it: mart_daily_zone_revenue (billable trips, ADR 0003) and
-- agg_trip_zone_daily (every trip in the window). The billable sums sit beside
-- the all-trip ones rather than in a row per billable flag, because
-- attributed_driver_count is a distinct count and cannot be summed back across
-- such a split.
select
    f.pickup_date_key,
    f.pickup_date,
    z.zone_natural_key as pickup_location_id,
    z.zone_name,
    z.borough_name,
    z.reporting_region,
    count(*) as trip_count,
    sum(f.total_amount) as total_revenue,
    sum(f.trip_distance) as total_miles,
    count(distinct f.driver_key) as attributed_driver_count,
    count(*) filter (where f.is_billable) as billable_trip_count,
    sum(f.fare_amount) filter (where f.is_billable) as billable_fare_revenue,
    sum(f.tip_amount) filter (where f.is_billable) as billable_tip_revenue,
    sum(f.total_surcharges) filter (where f.is_billable) as billable_surcharge_revenue,
    sum(f.tolls_amount) filter (where f.is_billable) as billable_toll_revenue,
    sum(f.total_amount) filter (where f.is_billable) as billable_total_revenue
from {{ ref('fct_trip') }} f
join {{ ref('dim_zone') }} z on f.pickup_zone_key = z.zone_key
where {{ in_report_window('f.pickup_datetime') }}
group by 1, 2, 3, 4, 5, 6
