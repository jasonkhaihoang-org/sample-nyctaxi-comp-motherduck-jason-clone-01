-- agg_trip_band_profile's grain: one row per distance, duration and fare band,
-- service type, pickup borough and daypart.
select distance_band, duration_band, fare_band, service_type_key, pickup_borough, daypart_code, count(*) as n
from {{ ref('agg_trip_band_profile') }}
group by distance_band, duration_band, fare_band, service_type_key, pickup_borough, daypart_code
having count(*) > 1
