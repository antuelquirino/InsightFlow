with source as (

    select
        subscription_id,
        organization_id,
        plan_id,
        mrr,

        
        date(start_date) as start_date,
        date(end_date) as end_date,

        lower(trim(status)) as raw_status

    from {{ source('raw','subscriptions') }}

),

cleaned as (

    select
        subscription_id,
        organization_id,
        plan_id,
        mrr,
        start_date,
        end_date,

        case
            when raw_status = 'active' then 'active'
            when raw_status in ('canceled', 'cancelled') then 'canceled'
            when raw_status = 'churned' then 'churned'
            else 'unknown'
        end as status

    from source

)

select *
from cleaned