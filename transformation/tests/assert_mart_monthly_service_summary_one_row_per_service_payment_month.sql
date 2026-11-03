-- mart_monthly_service_summary's grain: one row per trip_month, service_type, payment_method_name.
select trip_month, service_type, payment_method_name, count(*) as n
from {{ ref('mart_monthly_service_summary') }}
group by trip_month, service_type, payment_method_name
having count(*) > 1
