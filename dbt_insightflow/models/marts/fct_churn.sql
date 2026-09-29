-- Logo and revenue churn per month, in total and broken down by plan and by
-- acquisition channel. Customers count under the plan they had at the
-- previous month end, so an upgrade or downgrade is never a churn.
with at_start as (

    select
        movements.month,
        movements.previous_plan_id as plan_id,
        organizations.acquisition_channel,
        movements.previous_mrr,
        movements.mrr,
        movements.movement_type
    from {{ ref('int_mrr_movements') }} as movements
    inner join {{ ref('stg_organizations') }} as organizations
        on organizations.organization_id = movements.organization_id
    where movements.previous_mrr > 0

),

breakdowns as (

    select 'total' as breakdown, 'all' as breakdown_value, * except (plan_id, acquisition_channel)
    from at_start
    union all
    select 'plan', plan_id, * except (plan_id, acquisition_channel)
    from at_start
    union all
    select 'channel', acquisition_channel, * except (plan_id, acquisition_channel)
    from at_start

),

aggregated as (

    select
        month,
        breakdown,
        breakdown_value,
        count(*) as customers_at_start,
        countif(movement_type = 'churn') as churned_customers,
        sum(previous_mrr) as mrr_at_start,
        sum(if(movement_type = 'churn', previous_mrr, 0)) as churned_mrr,
        sum(if(movement_type = 'contraction', previous_mrr - mrr, 0)) as contraction_mrr,
        sum(if(movement_type = 'expansion', mrr - previous_mrr, 0)) as expansion_mrr
    from breakdowns
    group by 1, 2, 3

)

select
    *,
    safe_divide(churned_customers, customers_at_start) as logo_churn_rate,
    safe_divide(churned_mrr, mrr_at_start) as revenue_churn_rate,
    safe_divide(churned_mrr + contraction_mrr, mrr_at_start) as gross_mrr_churn_rate,
    safe_divide(churned_mrr + contraction_mrr - expansion_mrr, mrr_at_start) as net_mrr_churn_rate
from aggregated
