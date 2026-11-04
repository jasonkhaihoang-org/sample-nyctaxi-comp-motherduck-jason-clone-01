-- Daily zone demand, with period-over-period context computed once here rather
-- than in every consuming report. The window functions are the point: a raw
-- daily count answers "how many", and the lag and rolling average answer "is
-- that normal", which is the question anyone actually asks next.
with daily as (
    -- The roll-up lives in agg_trip_zone_daily_base, shared with mart_daily_zone_revenue.
    select
        pickup_date_key,
        pickup_date,
        pickup_location_id,
        zone_name,
        borough_name,
        trip_count,
        total_revenue,
        total_miles,
        attributed_driver_count
    from {{ ref('agg_trip_zone_daily_base') }}
)

select
    d.pickup_date_key,
    d.pickup_date,
    d.pickup_location_id,
    d.zone_name,
    d.borough_name,
    d.trip_count,
    d.total_revenue,
    d.total_miles,
    d.attributed_driver_count,
    lag(d.trip_count, 1) over w as prev_day_trip_count,
    lag(d.trip_count, 7) over w as same_day_last_week_trip_count,
    avg(d.trip_count) over (
        partition by d.pickup_location_id
        order by d.pickup_date
        rows between 6 preceding and current row
    ) as trip_count_7d_avg,
    sum(d.total_revenue) over (
        partition by d.pickup_location_id
        order by d.pickup_date
        rows between 27 preceding and current row
    ) as revenue_28d_rolling,
    rank() over (
        partition by d.pickup_date order by round(d.total_revenue, 2) desc
    ) as revenue_rank_that_day
from daily d
window w as (partition by d.pickup_location_id order by d.pickup_date)
