-- Driver-week, for the weekly shift-bidding cycle: built from driver-day, as the
-- month is, so the week cannot disagree with its days. The week is the date
-- dimension's (ADR 0014); nothing here truncates a date. Rates are rebuilt from
-- the week's sums, never averaged from the days (ADR 0016).
--
-- A week the data window cuts short is kept and marked: week_days_covered counts
-- the week's days inside the window, so it is the same on every row of a week
-- and says nothing about one driver. days_worked is the driver's own.
with daily as (
    select
        d.week_start_date,
        a.*
    from {{ ref('agg_driver_daily') }} a
    join {{ ref('dim_date') }} d on a.date_key = d.date_key
),

data_window as (
    select
        min(shift_date) as first_day,
        max(shift_date) as last_day
    from {{ ref('agg_driver_daily') }}
),

week_coverage as (
    select
        d.week_start_date,
        count(*) as week_days_covered
    from {{ ref('dim_date') }} d
    cross join data_window w
    where d.calendar_date between w.first_day and w.last_day
    group by d.week_start_date
)

select
    daily.week_start_date,
    daily.driver_key,
    daily.driver_ref,
    daily.engagement_type,
    daily.garage_key,
    daily.home_garage_name,

    c.week_days_covered,
    c.week_days_covered = 7 as is_complete_week,
    count(*) as days_worked,

    sum(daily.shift_count) as shift_count,
    sum(daily.trip_count) as trip_count,
    sum(daily.online_hours) as online_hours,
    sum(daily.on_trip_hours) as on_trip_hours,
    sum(daily.break_hours) as break_hours,
    sum(daily.gross_revenue) as gross_revenue,
    sum(daily.tip_revenue) as tip_revenue,
    sum(daily.airport_fee_collected) as airport_fee_collected,
    sum(daily.total_cost) as total_cost,
    sum(daily.total_margin) as total_margin,
    sum(daily.paid_miles) as paid_miles,
    sum(daily.unclosed_shift_count) as unclosed_shift_count,

    {{ safe_divide('sum(daily.on_trip_hours)', 'nullif(sum(daily.online_hours), 0)') }} as occupancy_rate,
    {{ safe_divide('sum(daily.gross_revenue)', 'nullif(sum(daily.online_hours), 0)') }} as revenue_per_online_hour,
    {{ safe_divide('sum(daily.gross_revenue)', 'nullif(sum(daily.trip_count), 0)') }} as revenue_per_trip
from daily
join week_coverage c on daily.week_start_date = c.week_start_date
group by 1, 2, 3, 4, 5, 6, 7, 8
