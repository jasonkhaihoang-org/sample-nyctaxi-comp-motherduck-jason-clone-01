-- Every in-window trip appears exactly once in each aggregate that claims to
-- cover the whole population: the band profile (which keeps unbanded and
-- unresolved rows) and the weather profile (borough x day spine). `is distinct
-- from` keeps the check honest when a profile is empty, where a bare `!=` on
-- NULLs would pass.
with profile as (
    select 'band' as agg, sum(trip_count) as trips from {{ ref('agg_trip_band_profile') }}
    union all
    select 'weather' as agg, sum(trip_count) as trips from {{ ref('agg_weather_demand_daily') }}
),

fact as (
    select count(*) as trips
    from {{ ref('fct_trip') }}
    where {{ in_report_window('pickup_datetime') }}
)

select p.agg, p.trips as profile_trips, f.trips as fact_trips
from profile p
cross join fact f
where p.trips is distinct from f.trips
