select *
from {{ ref('fact_mrr') }}
where total_mrr < 0