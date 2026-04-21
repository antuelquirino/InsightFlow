with source as (
    select
        user_id,
        organization_id,
        user_name, 
        email,
        role,
        safe_cast(signup_date as date) as signup_date
    from {{ source('raw','users') }}
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
)

select *
from cleaned