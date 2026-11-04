-- Daily revenue by pickup zone.
--
-- The billable rule (ADR 0003) is applied here, in gold, and nowhere upstream,
-- so data-quality work can still see the rows this excludes. The zone-day
-- roll-up itself is agg_trip_zone_daily_base, shared with agg_trip_zone_daily;
-- a zone-day with no billable trip has no row here.
select
    pickup_date as trip_date,
    pickup_location_id,
    borough_name as borough,
    zone_name,
    reporting_region,
    billable_trip_count as trip_count,
    billable_fare_revenue as fare_revenue,
    billable_tip_revenue as tip_revenue,
    billable_surcharge_revenue as surcharge_revenue,
    billable_toll_revenue as toll_revenue,
    billable_total_revenue as total_revenue
from {{ ref('agg_trip_zone_daily_base') }}
where billable_trip_count > 0
