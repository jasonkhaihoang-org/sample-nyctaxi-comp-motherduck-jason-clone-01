-- agg_vehicle_monthly's grain: one row per month_start_date, vehicle_key.
select month_start_date, vehicle_key, count(*) as n
from {{ ref('agg_vehicle_monthly') }}
group by month_start_date, vehicle_key
having count(*) > 1
