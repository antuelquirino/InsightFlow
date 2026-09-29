select
    plan_id,
    plan_name,
    cast(monthly_price_per_seat as numeric) as monthly_price_per_seat,
    valid_from,
    valid_to
from {{ source('raw', 'plans') }}
