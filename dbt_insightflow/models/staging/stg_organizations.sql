select
    organization_id,
    name as organization_name,
    industry,
    country,
    company_size,
    acquisition_channel,
    signup_date,
    date_trunc(signup_date, month) as signup_month
from {{ source('raw', 'organizations') }}
