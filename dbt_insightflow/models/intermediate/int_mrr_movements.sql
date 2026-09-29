-- Classifies each organization's month-over-month MRR change.
-- previous_mrr + mrr_change = mrr for every row, so summing by month gives a
-- bridge that always closes.
with snapshot as (

    select
        *,
        coalesce(lag(mrr) over by_org, 0) as previous_mrr,
        lag(plan_id) over by_org as previous_plan_id,
        coalesce(
            countif(is_paying) over (
                partition by organization_id order by month
                rows between unbounded preceding and 1 preceding
            ),
            0
        ) > 0 as paid_before
    from {{ ref('int_mrr_by_org_monthly') }}
    window by_org as (partition by organization_id order by month)

)

select
    month,
    organization_id,
    plan_id,
    previous_plan_id,
    previous_mrr,
    mrr,
    mrr - previous_mrr as mrr_change,
    case
        when previous_mrr = 0 and mrr = 0 then 'inactive'
        when previous_mrr = 0 and not paid_before then 'new'
        when previous_mrr = 0 then 'reactivation'
        when mrr = 0 then 'churn'
        when mrr > previous_mrr then 'expansion'
        when mrr < previous_mrr then 'contraction'
        else 'unchanged'
    end as movement_type
from snapshot
