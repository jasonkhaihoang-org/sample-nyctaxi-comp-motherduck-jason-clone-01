-- mart_trip_quality_scorecard's grain: one row per trip_month, vendor_id, service_type_key.
select trip_month, vendor_id, service_type_key, count(*) as n
from {{ ref('mart_trip_quality_scorecard') }}
group by trip_month, vendor_id, service_type_key
having count(*) > 1
