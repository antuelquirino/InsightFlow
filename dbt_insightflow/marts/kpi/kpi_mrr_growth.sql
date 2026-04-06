with mrr as (

    select *
    from {{ ref('fact_mrr') }}

),

aggregated as (

    select
        month,
        sum(total_mrr) as total_mrr
    from mrr
    group by 1

),

final as (

    select
        month,
        total_mrr,
        lag(total_mrr) over (order by month) as previous_mrr,
        total_mrr - lag(total_mrr) over (order by month) as mrr_growth,
        safe_divide(
            total_mrr - lag(total_mrr) over (order by month),
            lag(total_mrr) over (order by month)
        ) as growth_rate
    from aggregated

)

select *
from final