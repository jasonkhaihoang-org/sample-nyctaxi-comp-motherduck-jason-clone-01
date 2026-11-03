-- Daily revenue by pickup zone.
--
-- The billable rule (ADR 0003) is applied here, in gold, and nowhere upstream,
-- so data-quality work can still see the rows this excludes.
select
    f.pickup_date as trip_date,
    z.zone_natural_key as pickup_location_id,
    z.borough_name as borough,
    z.zone_name,
    z.reporting_region,
    count(*) as trip_count,
    sum(f.fare_amount) as fare_revenue,
    sum(f.tip_amount) as tip_revenue,
    sum(f.total_surcharges) as surcharge_revenue,
    -- Beside surcharge_revenue, not a partition of it: that total already holds the
    -- congestion surcharge and never the airport fee. A missing value adds nothing,
    -- and the trip counts say how many trips the totals rest on.
    sum(coalesce(f.congestion_surcharge, 0)) as congestion_surcharge_revenue,
    sum(case when f.congestion_surcharge > 0 then 1 else 0 end) as congestion_surcharge_trip_count,
    sum(coalesce(f.airport_fee, 0)) as airport_fee_revenue,
    sum(case when f.airport_fee > 0 then 1 else 0 end) as airport_fee_trip_count,
    sum(f.tolls_amount) as toll_revenue,
    sum(f.total_amount) as total_revenue
from {{ ref('fct_trip') }} f
join {{ ref('dim_zone') }} z on f.pickup_zone_key = z.zone_key
where
    {{ in_report_window('f.pickup_datetime') }}
    and f.is_billable
group by 1, 2, 3, 4, 5
