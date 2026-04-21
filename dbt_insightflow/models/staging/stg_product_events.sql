with source as (

    select
        event_id,
        user_id,
        organization_id,
        event_name,
        safe_cast(event_timestamp as datetime) as event_timestamp
    from {{ source('raw','product_events') }}

),

valid_orgs as (

    select organization_id
    from {{ ref('stg_organizations') }}

),

cleaned as (

    select s.*
    from source s
    inner join valid_orgs o
        on s.organization_id = o.organization_id
    where s.event_timestamp is not null

)

select *
from cleaned