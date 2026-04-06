select *
from {{ ref('fact_product_events') }}
where timestamp(event_timestamp) > current_timestamp()
