// Response shapes of the InsightFlow API (api/schemas.py). Months are ISO dates
// ("2026-08-01"), money is USD, rates are fractions.

export type Plan = "starter" | "pro" | "enterprise"
export type Channel = "organic" | "paid_ads" | "partner" | "outbound"

export interface Kpi {
  value: number | null
  previous_value: number | null
  change: number | null
  change_type: "relative" | "absolute"
  higher_is_better: boolean
}

export interface SummaryResponse {
  month: string
  mrr: Kpi
  arr: Kpi
  nrr: Kpi
  logo_churn_rate: Kpi
  paying_customers: Kpi
  arpa: Kpi
  new_customers: Kpi
  net_new_mrr: Kpi
}

export interface MrrPoint {
  month: string
  group: string
  mrr: number
  arr: number
  paying_customers: number
}

export interface MrrResponse {
  breakdown: "total" | "plan" | "channel" | "company_size"
  series: MrrPoint[]
}

export interface MrrMovementsMonth {
  month: string
  starting_mrr: number
  new_mrr: number
  expansion_mrr: number
  contraction_mrr: number
  churned_mrr: number
  reactivation_mrr: number
  net_new_mrr: number
  ending_mrr: number
  new_customers: number
  churned_customers: number
  reactivated_customers: number
}

export interface MrrMovementsResponse {
  months: MrrMovementsMonth[]
}

export interface ChurnPoint {
  month: string
  group: string
  customers_at_start: number
  churned_customers: number
  logo_churn_rate: number | null
  revenue_churn_rate: number | null
  gross_mrr_churn_rate: number | null
  net_mrr_churn_rate: number | null
}

export interface ChurnResponse {
  breakdown: "total" | "plan" | "channel"
  series: ChurnPoint[]
}

export interface RetentionPeriod {
  months_since_first_paid: number
  active_customers: number
  logo_retention: number
  revenue_retention: number
}

export interface RetentionCohort {
  cohort_month: string
  cohort_customers: number
  cohort_starting_mrr: number
  periods: RetentionPeriod[]
}

export interface RetentionResponse {
  cohorts: RetentionCohort[]
}

export interface ChannelEconomics {
  acquisition_channel: Channel
  spend_12m: number
  new_customers_12m: number
  cac: number | null
  arpa: number | null
  monthly_logo_churn_rate: number | null
  ltv: number | null
  ltv_to_cac: number | null
  payback_months: number | null
}

export interface UnitEconomicsResponse {
  month: string
  channels: ChannelEconomics[]
}

export interface AtRiskCustomer {
  organization_id: string
  organization_name: string
  industry: string
  country: string
  company_size: string
  acquisition_channel: Channel
  current_plan_id: Plan
  current_seats: number
  current_mrr: number
  churn_risk: "high" | "medium"
  usage_trend: number
  active_users_avg_4w: number
  active_users_avg_prior_8w: number
  first_paid_date: string
}

export interface AtRiskResponse {
  customers: AtRiskCustomer[]
}

export interface AskChart {
  type: "line" | "bar" | "number" | "table"
  x: string | null
  y: string[]
}

export interface AskResponse {
  status: "answered" | "cannot_answer" | "failed"
  answer: string
  insight: string | null
  sql: string | null
  columns: string[]
  rows: Record<string, string | number | boolean | null>[]
  chart: AskChart
}
