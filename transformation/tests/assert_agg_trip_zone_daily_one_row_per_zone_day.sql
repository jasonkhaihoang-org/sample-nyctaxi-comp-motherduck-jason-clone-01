-- agg_trip_zone_daily's grain: one row per pickup_date, pickup_location_id.
select pickup_date, pickup_location_id, count(*) as n
from {{ ref('agg_trip_zone_daily') }}
group by pickup_date, pickup_location_id
having count(*) > 1
