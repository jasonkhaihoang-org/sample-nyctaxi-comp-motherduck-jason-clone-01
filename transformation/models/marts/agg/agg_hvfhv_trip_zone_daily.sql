-- Daily HVFHV trip volume per pickup zone, keyed and windowed like
-- agg_trip_zone_daily so the two read side by side. Every HVFHV trip in the
-- window counts: no billable rule applies (ADR 0003), and trips in unknown
-- zones are kept, because the zone id is grouped as the source gives it
-- (ADR 0012). The key is cast to the bigint that agg_trip_zone_daily
-- publishes; the HVFHV file carries it as an integer.
with final as (
    -- grain: one row per pickup_location_id, pickup_date
    select
        cast(pickup_location_id as bigint) as pickup_location_id,
        cast(pickup_datetime as date) as pickup_date,
        count(*) as hvfhv_trip_count
    from {{ ref('stg_tlc__fhvhv_tripdata') }}
    where {{ in_report_window('pickup_datetime') }}
    group by 1, 2
)

select
    pickup_location_id,
    pickup_date,
    hvfhv_trip_count
from final
