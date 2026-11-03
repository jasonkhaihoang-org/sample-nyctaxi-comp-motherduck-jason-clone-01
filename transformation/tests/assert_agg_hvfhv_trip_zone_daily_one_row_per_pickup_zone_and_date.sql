-- The HVFHV aggregate's grain, as its design record states it: one row per
-- pickup zone per pickup date. The contract's composite primaryKey has no
-- per-column test, so this holds it in the build.
select pickup_location_id, pickup_date, count(*) as n
from {{ ref('agg_hvfhv_trip_zone_daily') }}
group by all
having count(*) > 1
