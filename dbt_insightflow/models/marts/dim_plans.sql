-- Price history of each plan: one row per price version.
select
    plan_id,
    plan_name,
    monthly_price_per_seat,
    lag(monthly_price_per_seat) over (partition by plan_id order by valid_from)
        as previous_monthly_price_per_seat,
    valid_from,
    valid_to,
    valid_to is null as is_current_price
from {{ ref('stg_plans') }}
