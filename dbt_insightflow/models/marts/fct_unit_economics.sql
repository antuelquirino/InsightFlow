-- Acquisition cost and customer value per channel and month. CAC and churn use
-- trailing 12-month sums (fewer months at the start of the window), since a
-- single month has too few new customers per channel to be stable.
{% set gross_margin = var('gross_margin') %}

with customers as (

    select
        movements.month,
        organizations.acquisition_channel,
        countif(movements.movement_type = 'new') as new_customers,
        countif(movements.previous_mrr > 0) as customers_at_start,
        countif(movements.movement_type = 'churn') as churned_customers,
        countif(movements.mrr > 0) as paying_customers,
        sum(movements.mrr) as mrr
    from {{ ref('int_mrr_movements') }} as movements
    inner join {{ ref('stg_organizations') }} as organizations
        on organizations.organization_id = movements.organization_id
    group by 1, 2

),

monthly as (

    select
        spend.month,
        spend.acquisition_channel,
        spend.spend,
        coalesce(customers.new_customers, 0) as new_customers,
        coalesce(customers.customers_at_start, 0) as customers_at_start,
        coalesce(customers.churned_customers, 0) as churned_customers,
        coalesce(customers.paying_customers, 0) as paying_customers,
        coalesce(customers.mrr, 0) as mrr
    from {{ ref('stg_marketing_spend') }} as spend
    left join customers
        on customers.month = spend.month
        and customers.acquisition_channel = spend.acquisition_channel

),

trailing as (

    select
        *,
        sum(spend) over last_12_months as spend_12m,
        sum(new_customers) over last_12_months as new_customers_12m,
        sum(churned_customers) over last_12_months as churned_customers_12m,
        sum(customers_at_start) over last_12_months as customer_months_12m
    from monthly
    window last_12_months as (
        partition by acquisition_channel order by month
        rows between 11 preceding and current row
    )

),

metrics as (

    select
        *,
        safe_divide(spend_12m, new_customers_12m) as cac,
        safe_divide(mrr, paying_customers) as arpa,
        safe_divide(churned_customers_12m, customer_months_12m) as monthly_logo_churn_rate
    from trailing

)

select
    month,
    acquisition_channel,
    spend,
    new_customers,
    paying_customers,
    mrr,
    spend_12m,
    new_customers_12m,
    cac,
    arpa,
    monthly_logo_churn_rate,
    safe_divide(arpa * {{ gross_margin }}, monthly_logo_churn_rate) as ltv,
    safe_divide(safe_divide(arpa * {{ gross_margin }}, monthly_logo_churn_rate), cac) as ltv_to_cac,
    safe_divide(cac, arpa * {{ gross_margin }}) as payback_months
from metrics
