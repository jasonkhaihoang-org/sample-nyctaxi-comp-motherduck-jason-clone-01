-- High-volume for-hire (HVFHV) trip records, one row per bronze row: renamed
-- and typed, nothing else. See stg_tlc__yellow_tripdata for the timestamp
-- handling.
select
    hvfhs_license_num,
    dispatching_base_num,
    originating_base_num,
    timezone('UTC', request_datetime) as request_datetime,
    timezone('UTC', on_scene_datetime) as on_scene_datetime,
    timezone('UTC', pickup_datetime) as pickup_datetime,
    timezone('UTC', dropoff_datetime) as dropoff_datetime,
    "PULocationID" as pickup_location_id,
    "DOLocationID" as dropoff_location_id,
    trip_miles,
    trip_time,
    base_passenger_fare,
    tolls,
    bcf,
    sales_tax,
    congestion_surcharge,
    airport_fee,
    tips,
    driver_pay,
    shared_request_flag,
    shared_match_flag,
    access_a_ride_flag,
    wav_request_flag,
    wav_match_flag,
    _dlt_load_id
from {{ source('bronze', 'fhvhv_tripdata') }}
