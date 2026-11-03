-- agg_driver_monthly's grain: one row per month_start_date, driver_key.
select month_start_date, driver_key, count(*) as n
from {{ ref('agg_driver_monthly') }}
group by month_start_date, driver_key
having count(*) > 1
