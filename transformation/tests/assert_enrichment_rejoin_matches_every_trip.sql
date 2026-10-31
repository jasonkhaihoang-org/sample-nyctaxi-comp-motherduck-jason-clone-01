-- The fleet-specific rejoin must find a row for every conformed trip. A trip
-- whose natural key is computed from differently-typed inputs on the two sides
-- matches nothing, and the left join then reports every fee as missing without
-- failing anything else. Returns the trips the rejoin did not find.
select t.trip_key, t.service_type
from {{ ref('int_trips_conformed') }} t
left join {{ ref('stg_tlc__yellow_trip_extras') }} y on t.trip_key = y.trip_key
left join {{ ref('stg_tlc__green_trip_extras') }} g on t.trip_key = g.trip_key
where
    (t.service_type = 'yellow' and y.trip_key is null)
    or (t.service_type = 'green' and g.trip_key is null)
