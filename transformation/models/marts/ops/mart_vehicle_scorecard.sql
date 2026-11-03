-- Vehicle performance per month, ranked within garage and fleet-wide, the way
-- mart_driver_scorecard ranks drivers: on revenue per online hour, because gross
-- revenue rewards whoever was rostered the most hours (ADR 0010). Vehicle-months
-- under the hours floor are carried, ranked and flagged, never dropped.
--
-- Built on the vehicle-month aggregate and nothing below it (ADR 0016): the
-- month's hours, trips and revenue are the aggregate's own.
with monthly as (
    select
        m.month_start_date,
        m.vehicle_key,
        m.medallion_number,
        m.garage_key,
        m.active_days,
        m.calendar_days,
        m.trip_count,
        m.online_hours,
        m.on_trip_hours,
        m.gross_revenue,
        {{ safe_divide('m.gross_revenue', 'm.online_hours') }} as revenue_per_online_hour,
        -- A month the data window cuts short has no vehicle active on all its
        -- days; a vehicle idle on some days of a full month does not mark it.
        max(m.active_days) over (partition by m.month_start_date)
        < m.calendar_days as is_incomplete_month
    from {{ ref('agg_vehicle_monthly') }} m
),

-- One row per vehicle per calendar month.
final as (
    select
        month_start_date,
        vehicle_key,
        medallion_number,
        garage_key,
        active_days,
        trip_count,
        online_hours,
        on_trip_hours,
        gross_revenue,
        revenue_per_online_hour,
        {{ safe_divide('on_trip_hours', 'online_hours') }} as occupancy_rate,
        {{ safe_divide('gross_revenue', 'cast(trip_count as double)') }} as revenue_per_trip,
        {{ safe_divide('cast(trip_count as double)', 'online_hours') }} as trips_per_online_hour,
        online_hours < 40 as is_below_ranking_floor,
        is_incomplete_month,
        -- Tied rates share a rank; a vehicle-month with no rate ranks last.
        rank() over (
            partition by month_start_date
            order by revenue_per_online_hour desc nulls last
        ) as fleet_rank,
        rank() over (
            partition by month_start_date, garage_key
            order by revenue_per_online_hour desc nulls last
        ) as garage_rank
    from monthly
)

select
    month_start_date,
    vehicle_key,
    medallion_number,
    garage_key,
    active_days,
    trip_count,
    online_hours,
    on_trip_hours,
    gross_revenue,
    revenue_per_online_hour,
    occupancy_rate,
    revenue_per_trip,
    trips_per_online_hour,
    is_below_ranking_floor,
    is_incomplete_month,
    fleet_rank,
    garage_rank
from final
