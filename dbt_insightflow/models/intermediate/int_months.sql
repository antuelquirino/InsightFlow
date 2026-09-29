-- Month spine of the reporting window: from the first to the last signup month.
with bounds as (

    select
        min(signup_month) as first_month,
        max(signup_month) as last_month
    from {{ ref('stg_organizations') }}

)

select
    month,
    last_day(month, month) as month_end
from bounds,
    unnest(generate_date_array(first_month, last_month, interval 1 month)) as month
