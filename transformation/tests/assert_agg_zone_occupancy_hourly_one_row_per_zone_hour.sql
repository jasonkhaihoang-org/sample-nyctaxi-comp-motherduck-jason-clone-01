-- agg_zone_occupancy_hourly's grain: one row per interval_date, interval_hour, location_id.
select interval_date, interval_hour, location_id, count(*) as n
from {{ ref('agg_zone_occupancy_hourly') }}
group by interval_date, interval_hour, location_id
having count(*) > 1
