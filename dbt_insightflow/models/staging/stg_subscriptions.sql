select
    subscription_id,
    organization_id,
    plan_id,
    is_trial,
    seats,
    cast(monthly_price_per_seat as numeric) as monthly_price_per_seat,
    round(cast(mrr as numeric), 2) as mrr,
    start_date,
    end_date,
    end_reason
from {{ source('raw', 'subscriptions') }}
