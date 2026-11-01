-- The trip fact must neither gain nor lose rows against its conformed source.
-- A gain means one of the dimension joins multiplied; a loss means an inner
-- join crept in where a left join belongs. Both are silent otherwise.
with counts as (
    select
        (select count(*) from {{ ref('fct_trip') }}) as fact_rows,
        (select count(*) from {{ ref('int_trips_conformed') }}) as conformed_rows
)

select * from counts
where fact_rows <> conformed_rows
