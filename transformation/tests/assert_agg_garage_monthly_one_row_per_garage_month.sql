-- agg_garage_monthly's grain: one row per month_start_date, garage_key.
select month_start_date, garage_key, count(*) as n
from {{ ref('agg_garage_monthly') }}
group by month_start_date, garage_key
having count(*) > 1
