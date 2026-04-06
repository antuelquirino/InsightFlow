with events as (

    select *
    from {{ ref('fact_product_events') }}

),

final as (

    select
        date_trunc(event_timestamp, month) as month,
        count(distinct organization_id) as active_companies
    from events
    where event_timestamp is not null
    group by 1

)

select *
from final