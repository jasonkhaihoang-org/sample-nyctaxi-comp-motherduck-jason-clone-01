-- agg_vehicle_daily's grain: one row per shift_date, vehicle_key.
select shift_date, vehicle_key, count(*) as n
from {{ ref('agg_vehicle_daily') }}
group by shift_date, vehicle_key
having count(*) > 1
