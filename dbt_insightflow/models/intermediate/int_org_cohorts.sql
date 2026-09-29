-- Acquisition cohort of each organization: when it signed up and when (and on
-- which plan) it first paid. Retention cohorts are based on the first paid month.
with first_paid as (

    select
        organization_id,
        min(start_date) as first_paid_date,
        array_agg(plan_id order by start_date limit 1)[offset(0)] as first_plan_id
    from {{ ref('stg_subscriptions') }}
    where not is_trial
    group by organization_id

)

select
    organizations.organization_id,
    organizations.acquisition_channel,
    organizations.signup_date,
    organizations.signup_month,
    first_paid.first_paid_date,
    date_trunc(first_paid.first_paid_date, month) as cohort_month,
    first_paid.first_plan_id,
    first_paid.first_paid_date is not null as converted
from {{ ref('stg_organizations') }} as organizations
left join first_paid
    on first_paid.organization_id = organizations.organization_id
