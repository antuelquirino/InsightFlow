-- MRR snapshot per organization at each month end, from its first paid month
-- onwards. Months without a paid period have mrr = 0, so churn shows up as a row.
with paid_periods as (

    select *
    from {{ ref('stg_subscriptions') }}
    where not is_trial

),

first_paid as (

    select
        organization_id,
        min(start_date) as first_paid_date
    from paid_periods
    group by organization_id

),

grid as (

    select
        months.month,
        months.month_end,
        first_paid.organization_id
    from {{ ref('int_months') }} as months
    inner join first_paid
        on first_paid.first_paid_date <= months.month_end

)

select
    grid.month,
    grid.organization_id,
    periods.plan_id,
    coalesce(periods.seats, 0) as seats,
    coalesce(periods.mrr, 0) as mrr,
    periods.subscription_id is not null as is_paying
from grid
left join paid_periods as periods
    on periods.organization_id = grid.organization_id
    and periods.start_date <= grid.month_end
    and (periods.end_date is null or periods.end_date > grid.month_end)
