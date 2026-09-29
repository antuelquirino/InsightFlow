-- One row per organization with its attributes and its state at the end of the
-- window: status, plan, MRR, recent usage and a churn-risk flag based on usage
-- fading (last 4 weeks vs the 8 before; docs/data-stories.md, story 4).
with current_snapshot as (

    select snapshot.*
    from {{ ref('int_mrr_by_org_monthly') }} as snapshot
    where snapshot.month = (select max(month) from {{ ref('int_months') }})

),

current_activity as (

    select activity.*
    from {{ ref('int_weekly_activity') }} as activity
    where activity.week_start = (select max(week_start) from {{ ref('int_weekly_activity') }})

),

open_trials as (

    select distinct organization_id
    from {{ ref('stg_subscriptions') }}
    where is_trial and end_date is null

),

last_churn as (

    select
        organization_id,
        max(end_date) as last_churn_date
    from {{ ref('stg_subscriptions') }}
    where end_reason = 'churned'
    group by organization_id

),

revenue as (

    select
        organization_id,
        sum(if(status = 'paid', amount, 0)) as lifetime_revenue,
        countif(status = 'failed') as failed_invoices
    from {{ ref('stg_invoices') }}
    group by organization_id

),

joined as (

    select
        organizations.organization_id,
        organizations.organization_name,
        organizations.industry,
        organizations.country,
        organizations.company_size,
        organizations.acquisition_channel,
        organizations.signup_date,
        cohorts.first_paid_date,
        cohorts.cohort_month,
        cohorts.first_plan_id,
        case
            when current_snapshot.is_paying then 'paying'
            when current_snapshot.organization_id is not null then 'churned'
            when open_trials.organization_id is not null then 'trial'
            else 'trial_expired'
        end as status,
        current_snapshot.plan_id as current_plan_id,
        coalesce(current_snapshot.seats, 0) as current_seats,
        coalesce(current_snapshot.mrr, 0) as current_mrr,
        last_churn.last_churn_date,
        coalesce(revenue.lifetime_revenue, 0) as lifetime_revenue,
        coalesce(revenue.failed_invoices, 0) as failed_invoices,
        current_activity.active_users as last_week_active_users,
        current_activity.active_users_avg_4w,
        current_activity.active_users_avg_prior_8w,
        current_activity.usage_trend
    from {{ ref('stg_organizations') }} as organizations
    left join {{ ref('int_org_cohorts') }} as cohorts
        on cohorts.organization_id = organizations.organization_id
    left join current_snapshot
        on current_snapshot.organization_id = organizations.organization_id
    left join open_trials
        on open_trials.organization_id = organizations.organization_id
    left join last_churn
        on last_churn.organization_id = organizations.organization_id
    left join revenue
        on revenue.organization_id = organizations.organization_id
    left join current_activity
        on current_activity.organization_id = organizations.organization_id

)

select
    *,
    case
        when status != 'paying' then null
        when usage_trend is null then 'unknown'
        when usage_trend < 0.6 then 'high'
        when usage_trend < 0.8 then 'medium'
        else 'low'
    end as churn_risk
from joined
