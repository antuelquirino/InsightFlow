-- Weekly activity per organization with trailing averages of active users:
-- the last 4 weeks against the 8 weeks before them. A ratio well below 1 means
-- usage is fading, which precedes churn (docs/data-stories.md, story 4).
with activity as (

    select
        *,
        unix_date(week_start) as day_number
    from {{ ref('stg_product_events') }}

),

averages as (

    select
        organization_id,
        week_start,
        active_users,
        logins,
        dashboards_viewed,
        queries_run,
        reports_exported,
        avg(active_users) over (
            partition by organization_id order by day_number
            range between 21 preceding and current row
        ) as active_users_avg_4w,
        avg(active_users) over (
            partition by organization_id order by day_number
            range between 77 preceding and 28 preceding
        ) as active_users_avg_prior_8w
    from activity

)

select
    *,
    safe_divide(active_users_avg_4w, active_users_avg_prior_8w) as usage_trend
from averages
