-- Paying organizations have a plan, seats and MRR; the others have none, and
-- only paying organizations get a churn-risk flag.
select organization_id, status, current_plan_id, current_seats, current_mrr, churn_risk
from {{ ref('dim_organizations') }}
where (status = 'paying' and (current_plan_id is null or current_seats = 0 or current_mrr <= 0 or churn_risk is null))
    or (status != 'paying' and (current_plan_id is not null or current_mrr != 0 or churn_risk is not null))
    or (status in ('paying', 'churned') and first_paid_date is null)
    or (status = 'churned' and last_churn_date is null)
