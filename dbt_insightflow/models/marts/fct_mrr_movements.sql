-- Monthly MRR bridge: starting_mrr + new + expansion + contraction + churned
-- + reactivation = ending_mrr. Losses are negative so the bridge adds up.
select
    month,
    sum(previous_mrr) as starting_mrr,
    sum(if(movement_type = 'new', mrr_change, 0)) as new_mrr,
    sum(if(movement_type = 'expansion', mrr_change, 0)) as expansion_mrr,
    sum(if(movement_type = 'contraction', mrr_change, 0)) as contraction_mrr,
    sum(if(movement_type = 'churn', mrr_change, 0)) as churned_mrr,
    sum(if(movement_type = 'reactivation', mrr_change, 0)) as reactivation_mrr,
    sum(mrr_change) as net_new_mrr,
    sum(mrr) as ending_mrr,
    countif(previous_mrr > 0) as customers_at_start,
    countif(movement_type = 'new') as new_customers,
    countif(movement_type = 'expansion') as expanded_customers,
    countif(movement_type = 'contraction') as contracted_customers,
    countif(movement_type = 'churn') as churned_customers,
    countif(movement_type = 'reactivation') as reactivated_customers,
    countif(mrr > 0) as customers_at_end
from {{ ref('int_mrr_movements') }}
group by month
