with source as (
    select
        organization_id,
        name as organization_name,
        industry,
        country,
        company_size,
        safe_cast(parse_timestamp('%Y-%m-%d %H:%M:%S', created_at) as date) as created_at
    from {{ source('raw','organizations') }}
)

select *
from source