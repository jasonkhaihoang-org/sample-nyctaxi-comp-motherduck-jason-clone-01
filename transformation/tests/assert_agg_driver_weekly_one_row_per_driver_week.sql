-- agg_driver_weekly's grain: one row per week_start_date, driver_key.
select week_start_date, driver_key, count(*) as n
from {{ ref('agg_driver_weekly') }}
group by week_start_date, driver_key
having count(*) > 1
