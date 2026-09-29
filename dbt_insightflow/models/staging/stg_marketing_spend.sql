select
    month,
    acquisition_channel,
    round(cast(spend as numeric), 2) as spend
from {{ source('raw', 'marketing_spend') }}
