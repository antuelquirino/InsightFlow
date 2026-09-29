-- Logo and revenue retention of each monthly cohort (customers grouped by the
-- month they first paid), for every month since then.
with cohort_months as (

    select
        cohorts.cohort_month,
        date_diff(snapshot.month, cohorts.cohort_month, month) as months_since_first_paid,
        snapshot.organization_id,
        snapshot.is_paying,
        snapshot.mrr
    from {{ ref('int_mrr_by_org_monthly') }} as snapshot
    inner join {{ ref('int_org_cohorts') }} as cohorts
        on cohorts.organization_id = snapshot.organization_id

),

cohort_size as (

    select
        cohort_month,
        count(*) as cohort_customers,
        sum(mrr) as cohort_starting_mrr
    from cohort_months
    where months_since_first_paid = 0
    group by cohort_month

)

select
    cohort_months.cohort_month,
    cohort_months.months_since_first_paid,
    cohort_size.cohort_customers,
    cohort_size.cohort_starting_mrr,
    countif(cohort_months.is_paying) as active_customers,
    sum(cohort_months.mrr) as mrr,
    safe_divide(countif(cohort_months.is_paying), cohort_size.cohort_customers) as logo_retention,
    safe_divide(sum(cohort_months.mrr), cohort_size.cohort_starting_mrr) as revenue_retention
from cohort_months
inner join cohort_size
    on cohort_size.cohort_month = cohort_months.cohort_month
group by 1, 2, 3, 4
