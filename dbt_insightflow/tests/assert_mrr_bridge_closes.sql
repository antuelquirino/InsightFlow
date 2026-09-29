-- The MRR bridge must close every month: starting MRR plus the movements equals
-- ending MRR, and starting MRR equals the previous month's ending MRR.
with bridge as (

    select
        month,
        starting_mrr,
        ending_mrr,
        starting_mrr + new_mrr + expansion_mrr + contraction_mrr + churned_mrr + reactivation_mrr
            as rebuilt_ending_mrr,
        coalesce(lag(ending_mrr) over (order by month), 0) as previous_ending_mrr,
        customers_at_start
            + new_customers + reactivated_customers - churned_customers as rebuilt_customers_at_end,
        customers_at_end
    from {{ ref('fct_mrr_movements') }}

)

select *
from bridge
where rebuilt_ending_mrr != ending_mrr
    or starting_mrr != previous_ending_mrr
    or rebuilt_customers_at_end != customers_at_end
