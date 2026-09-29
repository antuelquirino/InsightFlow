-- Rates that are shares of a group must be between 0 and 1, and counts must
-- not exceed the group they come from. Revenue retention and NRR can exceed 1.
select 'fct_churn' as model, cast(month as string) as row_key
from {{ ref('fct_churn') }}
where logo_churn_rate not between 0 and 1
    or revenue_churn_rate not between 0 and 1
    or gross_mrr_churn_rate not between 0 and 1
    or churned_customers > customers_at_start

union all

select 'fct_retention_cohorts', concat(cast(cohort_month as string), ' +', cast(months_since_first_paid as string))
from {{ ref('fct_retention_cohorts') }}
where logo_retention not between 0 and 1
    or active_customers > cohort_customers
    or revenue_retention < 0

union all

select 'fct_unit_economics', concat(cast(month as string), ' ', acquisition_channel)
from {{ ref('fct_unit_economics') }}
where monthly_logo_churn_rate not between 0 and 1
    or spend <= 0
    or cac < 0

union all

select 'kpi_summary', cast(month as string)
from {{ ref('kpi_summary') }}
where logo_churn_rate not between 0 and 1
    or logo_retention_12m not between 0 and 1
    or nrr < 0
