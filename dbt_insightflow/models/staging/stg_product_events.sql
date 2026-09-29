select
    organization_id,
    week_start,
    active_users,
    logins,
    dashboards_viewed,
    queries_run,
    reports_exported
from {{ source('raw', 'product_events') }}
