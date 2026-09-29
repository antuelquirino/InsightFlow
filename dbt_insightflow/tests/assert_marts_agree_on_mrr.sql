-- MRR and paying customers must be the same in every mart that reports them.
with monthly as (

    select
        month,
        sum(mrr) as mrr,
        sum(paying_customers) as paying_customers
    from {{ ref('fct_mrr_monthly') }}
    group by month

),

current_customers as (

    select
        (select max(month) from {{ ref('kpi_summary') }}) as month,
        sum(current_mrr) as mrr,
        count(*) as paying_customers
    from {{ ref('dim_organizations') }}
    where status = 'paying'

)

select
    kpis.month,
    kpis.mrr as kpi_mrr,
    monthly.mrr as monthly_mrr,
    movements.ending_mrr as bridge_mrr,
    current_customers.mrr as dim_mrr,
    kpis.paying_customers as kpi_customers,
    monthly.paying_customers as monthly_customers,
    current_customers.paying_customers as dim_customers
from {{ ref('kpi_summary') }} as kpis
left join monthly
    on monthly.month = kpis.month
left join {{ ref('fct_mrr_movements') }} as movements
    on movements.month = kpis.month
left join current_customers
    on current_customers.month = kpis.month
where kpis.mrr != coalesce(monthly.mrr, 0)
    or kpis.mrr != movements.ending_mrr
    or kpis.paying_customers != coalesce(monthly.paying_customers, 0)
    or kpis.mrr != coalesce(current_customers.mrr, kpis.mrr)
    or kpis.paying_customers != coalesce(current_customers.paying_customers, kpis.paying_customers)
