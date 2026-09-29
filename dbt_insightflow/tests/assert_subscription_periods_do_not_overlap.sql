-- An organization has at most one subscription period on any day; the MRR
-- snapshot relies on it. Periods cover [start_date, end_date).
with ordered as (

    select
        organization_id,
        subscription_id,
        start_date,
        end_date,
        lead(start_date) over (
            partition by organization_id order by start_date, subscription_id
        ) as next_start_date
    from {{ ref('stg_subscriptions') }}

)

select *
from ordered
where next_start_date is not null
    and (end_date is null or next_start_date < end_date)
