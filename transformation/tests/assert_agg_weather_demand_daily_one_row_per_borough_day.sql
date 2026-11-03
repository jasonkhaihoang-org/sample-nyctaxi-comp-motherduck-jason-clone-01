-- agg_weather_demand_daily's grain: one row per obs_date, borough_name.
select obs_date, borough_name, count(*) as n
from {{ ref('agg_weather_demand_daily') }}
group by obs_date, borough_name
having count(*) > 1
