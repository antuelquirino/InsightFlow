with subscriptions as (

    select *
    from {{ ref('fact_subscriptions') }}

),

churned as (

    select
        date_trunc(end_date, month) as month,
        count(distinct organization_id) as churned_customers
    from subscriptions
    where end_date is not null
    group by 1

),

active as (

    select
        date_trunc(start_date, month) as month,
        count(distinct organization_id) as active_customers
    from subscriptions
    group by 1

),

final as (

    select
        a.month,
        a.active_customers,
        coalesce(c.churned_customers, 0) as churned_customers,

        case
            when a.active_customers = 0 then 0
            else coalesce(
                safe_divide(c.churned_customers, a.active_customers),
                0
            )
        end as churn_rate

    from active a
    left join churned c
        on a.month = c.month

)

select *
from final