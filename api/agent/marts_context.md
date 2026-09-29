# InsightFlow marts

BigQuery tables describing InsightFlow, a B2B SaaS company. Data covers 2024-09 to 2026-08; the latest month is 2026-08.

Conventions for every table:
- Month columns hold the first day of the month; values are as of the month end.
- Money is USD. Rates and ratios are fractions (0.05 = 5%), never percentages.
- A paying customer is an organization with a paid (non-trial) subscription.
- The company launched with the data window, so the first months have very few
  customers and noisy rates.
- Always reference tables with their full name, including project and dataset.

## `insightflow-analytics-489617.dbt_marts.fct_mrr_monthly`

Monthly recurring revenue at each month end, split by plan, acquisition channel and company size. One row per month, plan, channel and size that has at least one paying customer. Sum rows to get totals, e.g. total MRR per month = sum(mrr) group by month.

Columns:
- month (DATE): First day of the month; values are measured at the month end.
- plan_id (STRING): Plan of the customers at the month end. Values: 'starter', 'pro', 'enterprise'.
- acquisition_channel (STRING): Channel the customers came from. Values: 'organic', 'paid_ads', 'partner', 'outbound'.
- company_size (STRING): Customer segment by employees: small (1-50), medium (51-500), large (500+). Values: 'small', 'medium', 'large'.
- paying_customers (INT64): Number of paying customers in this group at the month end.
- seats (INT64): Total seats paid by those customers.
- mrr (NUMERIC): Monthly recurring revenue in USD at the month end.
- arr (NUMERIC): Annual recurring revenue in USD (mrr × 12).

## `insightflow-analytics-489617.dbt_marts.fct_mrr_movements`

Monthly MRR bridge, one row per month. starting_mrr + new_mrr + expansion_mrr + contraction_mrr + churned_mrr + reactivation_mrr = ending_mrr, and starting_mrr equals the previous month's ending_mrr. Losses (contraction, churn) are negative numbers. Price increases for existing customers count as expansion (the Starter price change of November 2025 shows up here).

Columns:
- month (DATE): First day of the month.
- starting_mrr (NUMERIC): MRR in USD at the end of the previous month.
- new_mrr (NUMERIC): MRR from customers paying for the first time this month (USD, positive).
- expansion_mrr (NUMERIC): MRR increase from existing customers who added seats, upgraded or had a price increase (USD, positive).
- contraction_mrr (NUMERIC): MRR decrease from existing customers who removed seats or downgraded but kept paying (USD, negative).
- churned_mrr (NUMERIC): MRR lost from customers who stopped paying this month (USD, negative).
- reactivation_mrr (NUMERIC): MRR from former customers who came back after churning (USD, positive).
- net_new_mrr (NUMERIC): Sum of all movements; ending_mrr - starting_mrr (USD).
- ending_mrr (NUMERIC): MRR in USD at the end of this month.
- customers_at_start (INT64): Paying customers at the end of the previous month.
- new_customers (INT64): Customers paying for the first time this month.
- expanded_customers (INT64): Customers whose MRR went up this month.
- contracted_customers (INT64): Customers whose MRR went down but stayed above zero.
- churned_customers (INT64): Customers who paid last month and pay nothing at this month end.
- reactivated_customers (INT64): Former customers who started paying again this month.
- customers_at_end (INT64): Paying customers at the end of this month.

## `insightflow-analytics-489617.dbt_marts.fct_churn`

Logo churn and revenue churn per month, in total and broken down by plan or by acquisition channel. Filter on breakdown ('total', 'plan' or 'channel') and read breakdown_value. A customer counts under the plan it had at the previous month end, so upgrades and downgrades are never churn. Amounts here are positive USD. Monthly churn is noisy for small groups; average several months before drawing conclusions.

Columns:
- month (DATE): First day of the month.
- breakdown (STRING): Dimension of the row: 'total' (all customers), 'plan' or 'channel'. Values: 'total', 'plan', 'channel'.
- breakdown_value (STRING): 'all' when breakdown = 'total'; the plan (starter, pro, enterprise) or the acquisition channel (organic, paid_ads, partner, outbound) otherwise.
- customers_at_start (INT64): Paying customers at the end of the previous month.
- churned_customers (INT64): Of those, how many pay nothing at this month end.
- mrr_at_start (NUMERIC): MRR in USD of customers_at_start at the end of the previous month.
- churned_mrr (NUMERIC): MRR in USD lost from churned customers (positive).
- contraction_mrr (NUMERIC): MRR in USD lost from customers who reduced seats or downgraded (positive).
- expansion_mrr (NUMERIC): MRR in USD gained from customers who added seats, upgraded or had a price increase (positive).
- logo_churn_rate (FLOAT64): churned_customers / customers_at_start, a fraction between 0 and 1.
- revenue_churn_rate (NUMERIC): churned_mrr / mrr_at_start.
- gross_mrr_churn_rate (NUMERIC): (churned_mrr + contraction_mrr) / mrr_at_start.
- net_mrr_churn_rate (NUMERIC): (churned_mrr + contraction_mrr - expansion_mrr) / mrr_at_start. Negative when expansion outweighs losses (net negative churn).

## `insightflow-analytics-489617.dbt_marts.fct_retention_cohorts`

Retention matrix. Customers are grouped into cohorts by the month they first paid; each row is one cohort observed months_since_first_paid months later. Month 0 is the cohort month itself. Revenue retention above 1 means the cohort pays more than when it started (expansion beats churn).

Columns:
- cohort_month (DATE): First day of the month in which the cohort's customers first paid.
- months_since_first_paid (INT64): Months elapsed since cohort_month (0 = the cohort month).
- cohort_customers (INT64): Number of customers in the cohort.
- cohort_starting_mrr (NUMERIC): Cohort MRR in USD at the end of the cohort month.
- active_customers (INT64): Cohort customers still paying at the end of this month.
- mrr (NUMERIC): Cohort MRR in USD at the end of this month.
- logo_retention (FLOAT64): active_customers / cohort_customers.
- revenue_retention (NUMERIC): mrr / cohort_starting_mrr; can exceed 1.

## `insightflow-analytics-489617.dbt_marts.fct_unit_economics`

Acquisition cost and customer value per acquisition channel and month. CAC, churn and the metrics derived from them use trailing 12-month sums (shorter at the start of the window) because monthly counts per channel are small. LTV and payback assume a gross margin of 80% (dbt var gross_margin). For the current picture, use the latest month.

Columns:
- month (DATE): First day of the month.
- acquisition_channel (STRING): organic, paid_ads, partner or outbound. Values: 'organic', 'paid_ads', 'partner', 'outbound'.
- spend (NUMERIC): Marketing spend in USD on this channel in this month.
- new_customers (INT64): Customers from this channel who paid for the first time this month.
- paying_customers (INT64): Paying customers from this channel at the month end.
- mrr (NUMERIC): MRR in USD of this channel's customers at the month end.
- spend_12m (NUMERIC): Spend in USD over the trailing 12 months.
- new_customers_12m (INT64): New customers over the trailing 12 months.
- cac (NUMERIC): Customer acquisition cost in USD, spend_12m / new_customers_12m.
- arpa (NUMERIC): Average revenue per account in USD, mrr / paying_customers.
- monthly_logo_churn_rate (FLOAT64): Average monthly logo churn over the trailing 12 months, a fraction.
- ltv (FLOAT64): Estimated lifetime value in USD, arpa × gross margin / monthly_logo_churn_rate.
- ltv_to_cac (FLOAT64): ltv / cac. Above 3 is usually considered healthy.
- payback_months (NUMERIC): Months of gross margin needed to recover the CAC, cac / (arpa × gross margin).

## `insightflow-analytics-489617.dbt_marts.dim_organizations`

One row per organization that ever started a trial, with its attributes and its state at the end of the window (August 2026). Use status = 'paying' for current customers. churn_risk flags paying customers whose usage is fading: activity fades for 6 to 10 weeks before a customer cancels.

Columns:
- organization_id (STRING): Unique organization id.
- organization_name (STRING): Company name.
- industry (STRING): Industry of the company.
- country (STRING): ISO 3166-1 alpha-2 country code.
- company_size (STRING): small (1-50 employees), medium (51-500) or large (500+).
- acquisition_channel (STRING): organic, paid_ads, partner or outbound.
- signup_date (DATE): Day the organization started its 14-day trial.
- first_paid_date (DATE): Day it first paid; null if the trial never converted.
- cohort_month (DATE): First day of the month of first_paid_date.
- first_plan_id (STRING): Plan it first paid for.
- status (STRING): At the window end: 'paying', 'churned' (paid before, not now), 'trial' (trial in progress) or 'trial_expired' (never paid). Values: 'paying', 'churned', 'trial', 'trial_expired'.
- current_plan_id (STRING): Current plan; null unless status = 'paying'.
- current_seats (INT64): Seats currently paid; 0 unless status = 'paying'.
- current_mrr (NUMERIC): Current MRR in USD; 0 unless status = 'paying'.
- last_churn_date (DATE): Day of its most recent churn, if any.
- lifetime_revenue (NUMERIC): Sum of paid invoices in USD.
- failed_invoices (INT64): Number of failed invoice payments.
- last_week_active_users (INT64): Active users in the last complete week of the window.
- active_users_avg_4w (FLOAT64): Average weekly active users over the last 4 weeks.
- active_users_avg_prior_8w (FLOAT64): Average weekly active users over the 8 weeks before those 4.
- usage_trend (FLOAT64): active_users_avg_4w / active_users_avg_prior_8w. 1 means stable usage, below 1 means fading usage.
- churn_risk (STRING): For paying customers: 'high' (usage_trend below 0.6), 'medium' (0.6 to 0.8), 'low' (0.8 or more) or 'unknown' (too new to compare). Null for organizations that are not paying. Values: 'high', 'medium', 'low', 'unknown'.

## `insightflow-analytics-489617.dbt_marts.kpi_summary`

One row per month with the headline KPIs and their change against the previous month, for dashboard cards. The latest month is the current state of the business.

Columns:
- month (DATE): First day of the month.
- mrr (NUMERIC): MRR in USD at the month end.
- arr (NUMERIC): ARR in USD (mrr × 12).
- paying_customers (INT64): Paying customers at the month end.
- arpa (NUMERIC): Average MRR per paying customer in USD.
- new_customers (INT64): Customers paying for the first time this month.
- churned_customers (INT64): Customers who stopped paying this month.
- net_new_mrr (NUMERIC): MRR change against the previous month in USD.
- logo_churn_rate (FLOAT64): Share of last month's customers who stopped paying this month.
- gross_mrr_churn_rate (NUMERIC): MRR lost to churn and contraction / MRR at the start of the month.
- nrr (NUMERIC): Net revenue retention over 12 months: MRR now of the customers who were paying 12 months earlier / their MRR back then. Above 1 means existing customers grow revenue even after churn. Null for the first 12 months.
- logo_retention_12m (FLOAT64): Share of the customers paying 12 months earlier who still pay.
- mrr_growth_rate (NUMERIC): MRR change against the previous month, as a fraction of last month's MRR.
- paying_customers_change (INT64): Change in paying customers against the previous month.
- arpa_growth_rate (NUMERIC): ARPA change against the previous month, as a fraction.
- logo_churn_rate_change (FLOAT64): Logo churn rate minus the previous month's (in fraction points).
- nrr_change (NUMERIC): NRR minus the previous month's (in fraction points).
