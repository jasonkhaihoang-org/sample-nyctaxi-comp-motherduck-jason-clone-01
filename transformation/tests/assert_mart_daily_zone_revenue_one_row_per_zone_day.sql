-- mart_daily_zone_revenue's grain: one row per trip_date, pickup_location_id.
select trip_date, pickup_location_id, count(*) as n
from {{ ref('mart_daily_zone_revenue') }}
group by trip_date, pickup_location_id
having count(*) > 1
