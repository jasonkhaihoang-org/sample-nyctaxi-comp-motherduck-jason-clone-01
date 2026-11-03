-- agg_driver_daily's grain: one row per shift_date, driver_key.
select shift_date, driver_key, count(*) as n
from {{ ref('agg_driver_daily') }}
group by shift_date, driver_key
having count(*) > 1
