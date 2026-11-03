-- mart_revenue_component_bridge's grain: one row per trip_month, service_type_key, borough_name, component_name.
select trip_month, service_type_key, borough_name, component_name, count(*) as n
from {{ ref('mart_revenue_component_bridge') }}
group by trip_month, service_type_key, borough_name, component_name
having count(*) > 1
