-- agg_od_flow_matrix's grain: one row per origin_location_id, dest_location_id.
select origin_location_id, dest_location_id, count(*) as n
from {{ ref('agg_od_flow_matrix') }}
group by origin_location_id, dest_location_id
having count(*) > 1
