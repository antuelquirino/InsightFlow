-- One row per month with the headline KPIs and their change against the
-- previous month, for the dashboard cards.
with net_revenue_retention as (

    -- Customers paying 12 months earlier: their MRR now / their MRR then.
    select
        current_month.month,
        safe_divide(sum(current_month.mrr), sum(year_ago.mrr)) as nrr,
        safe_divide(countif(current_month.is_paying), count(*)) as logo_retention_12m
    from {{ ref('int_mrr_by_org_monthly') }} as year_ago
    inner join {{ ref('int_mrr_by_org_monthly') }} as current_month
        on current_month.organization_id = year_ago.organization_id
        and current_month.month = date_add(year_ago.month, interval 12 month)
    where year_ago.is_paying
    group by current_month.month

),

kpis as (

    select
        movements.month,
        movements.ending_mrr as mrr,
        movements.ending_mrr * 12 as arr,
        movements.customers_at_end as paying_customers,
        safe_divide(movements.ending_mrr, movements.customers_at_end) as arpa,
        movements.new_customers,
        movements.churned_customers,
        movements.net_new_mrr,
        churn.logo_churn_rate,
        churn.gross_mrr_churn_rate,
        net_revenue_retention.nrr,
        net_revenue_retention.logo_retention_12m
    from {{ ref('fct_mrr_movements') }} as movements
    left join {{ ref('fct_churn') }} as churn
        on churn.month = movements.month
        and churn.breakdown = 'total'
    left join net_revenue_retention
        on net_revenue_retention.month = movements.month

)

select
    *,
    safe_divide(mrr - lag(mrr) over by_month, lag(mrr) over by_month) as mrr_growth_rate,
    paying_customers - lag(paying_customers) over by_month as paying_customers_change,
    safe_divide(arpa - lag(arpa) over by_month, lag(arpa) over by_month) as arpa_growth_rate,
    logo_churn_rate - lag(logo_churn_rate) over by_month as logo_churn_rate_change,
    nrr - lag(nrr) over by_month as nrr_change
from kpis
window by_month as (order by month)
