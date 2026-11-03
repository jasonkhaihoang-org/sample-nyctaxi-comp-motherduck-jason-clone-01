-- The scorecard's grain is one row per vehicle per calendar month.
select
    vehicle_key,
    month_start_date,
    count(*) as n_rows
from {{ ref('mart_vehicle_scorecard') }}
group by vehicle_key, month_start_date
having count(*) > 1
