"""Request filters and response models. Field examples feed the OpenAPI docs."""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# --- Shared enums ----------------------------------------------------------------

class Plan(str, Enum):
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class Channel(str, Enum):
    organic = "organic"
    paid_ads = "paid_ads"
    partner = "partner"
    outbound = "outbound"


class MrrBreakdown(str, Enum):
    total = "total"
    plan = "plan"
    channel = "channel"
    company_size = "company_size"


class ChurnBreakdown(str, Enum):
    total = "total"
    plan = "plan"
    channel = "channel"


class ChurnRisk(str, Enum):
    high = "high"
    medium = "medium"


# --- /metrics/summary --------------------------------------------------------------

class Kpi(BaseModel):
    value: float | None = Field(examples=[297287.0])
    previous_value: float | None = Field(description="Value in the previous month.", examples=[285694.0])
    change: float | None = Field(
        description="Relative change (0.04 = +4%) for amounts and counts; difference in "
        "fraction points for rates (see change_type).",
        examples=[0.0406],
    )
    change_type: str = Field(description="'relative' or 'absolute'.", examples=["relative"])
    higher_is_better: bool = Field(
        description="Whether an increase is good news, to color the change.", examples=[True]
    )


class SummaryResponse(BaseModel):
    month: date = Field(description="First day of the month the KPIs describe.", examples=["2026-08-01"])
    mrr: Kpi
    arr: Kpi
    nrr: Kpi = Field(description="Net revenue retention over 12 months (1.24 = 124%).")
    logo_churn_rate: Kpi
    paying_customers: Kpi
    arpa: Kpi
    new_customers: Kpi
    net_new_mrr: Kpi


# --- /metrics/mrr -----------------------------------------------------------------

class MrrPoint(BaseModel):
    month: date = Field(examples=["2026-08-01"])
    group: str = Field(description="'total' or the breakdown value.", examples=["enterprise"])
    mrr: float = Field(examples=[226809.0])
    arr: float = Field(examples=[2721708.0])
    paying_customers: int = Field(examples=[97])


class MrrResponse(BaseModel):
    breakdown: MrrBreakdown
    series: list[MrrPoint]


# --- /metrics/mrr-movements ----------------------------------------------------------

class MrrMovementsMonth(BaseModel):
    month: date = Field(examples=["2026-08-01"])
    starting_mrr: float = Field(examples=[285694.0])
    new_mrr: float = Field(examples=[10284.0])
    expansion_mrr: float = Field(examples=[6217.0])
    contraction_mrr: float = Field(description="Negative.", examples=[-294.0])
    churned_mrr: float = Field(description="Negative.", examples=[-5160.0])
    reactivation_mrr: float = Field(examples=[546.0])
    net_new_mrr: float = Field(examples=[11593.0])
    ending_mrr: float = Field(examples=[297287.0])
    new_customers: int = Field(examples=[16])
    churned_customers: int = Field(examples=[19])
    reactivated_customers: int = Field(examples=[2])


class MrrMovementsResponse(BaseModel):
    months: list[MrrMovementsMonth]


# --- /metrics/churn ------------------------------------------------------------------

class ChurnPoint(BaseModel):
    month: date = Field(examples=["2026-01-01"])
    group: str = Field(description="'all' or the plan / channel.", examples=["starter"])
    customers_at_start: int = Field(examples=[186])
    churned_customers: int = Field(examples=[22])
    logo_churn_rate: float | None = Field(examples=[0.118])
    revenue_churn_rate: float | None = Field(examples=[0.109])
    gross_mrr_churn_rate: float | None = Field(examples=[0.115])
    net_mrr_churn_rate: float | None = Field(examples=[0.052])


class ChurnResponse(BaseModel):
    breakdown: ChurnBreakdown
    series: list[ChurnPoint]


# --- /metrics/retention ---------------------------------------------------------------

class RetentionPeriod(BaseModel):
    months_since_first_paid: int = Field(examples=[12])
    active_customers: int = Field(examples=[22])
    logo_retention: float = Field(examples=[0.815])
    revenue_retention: float = Field(description="Can exceed 1.", examples=[1.38])


class RetentionCohort(BaseModel):
    cohort_month: date = Field(examples=["2025-03-01"])
    cohort_customers: int = Field(examples=[27])
    cohort_starting_mrr: float = Field(examples=[9811.0])
    periods: list[RetentionPeriod]


class RetentionResponse(BaseModel):
    cohorts: list[RetentionCohort]


# --- /metrics/unit-economics ----------------------------------------------------------

class ChannelEconomics(BaseModel):
    acquisition_channel: Channel
    spend_12m: float = Field(description="Marketing spend over the trailing 12 months.", examples=[216000.0])
    new_customers_12m: int = Field(examples=[92])
    cac: float | None = Field(examples=[2339.0])
    arpa: float | None = Field(examples=[454.0])
    monthly_logo_churn_rate: float | None = Field(examples=[0.062])
    ltv: float | None = Field(description="Assumes an 80% gross margin.", examples=[5839.0])
    ltv_to_cac: float | None = Field(examples=[2.5])
    payback_months: float | None = Field(examples=[6.4])


class UnitEconomicsResponse(BaseModel):
    month: date = Field(examples=["2026-08-01"])
    channels: list[ChannelEconomics]


# --- /customers/at-risk ---------------------------------------------------------------

class AtRiskCustomer(BaseModel):
    organization_id: str = Field(examples=["org_00412"])
    organization_name: str = Field(examples=["Ramirez, Kent and Cole"])
    industry: str = Field(examples=["Software"])
    country: str = Field(examples=["US"])
    company_size: str = Field(examples=["medium"])
    acquisition_channel: Channel
    current_plan_id: Plan
    current_seats: int = Field(examples=[12])
    current_mrr: float = Field(examples=[468.0])
    churn_risk: ChurnRisk
    usage_trend: float = Field(
        description="Active users, last 4 weeks / previous 8 weeks (1 = stable).", examples=[0.52]
    )
    active_users_avg_4w: float = Field(examples=[3.25])
    active_users_avg_prior_8w: float = Field(examples=[6.25])
    first_paid_date: date = Field(examples=["2025-04-18"])


class AtRiskResponse(BaseModel):
    customers: list[AtRiskCustomer]


# --- POST /ask -----------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=500,
        description="A business question in plain language.",
        examples=["What happened to Starter churn after the price change?"],
    )


class Chart(BaseModel):
    type: Literal["line", "bar", "number", "table"] = Field(
        description="'line' (x is a month or date), 'bar' (x is a category), 'number' "
        "(one headline value) or 'table'.",
        examples=["line"],
    )
    x: str | None = Field(default=None, description="Column for the x axis.", examples=["month"])
    y: list[str] = Field(default=[], description="Numeric columns to plot.", examples=[["logo_churn_rate"]])


class AskResponse(BaseModel):
    status: Literal["answered", "cannot_answer", "failed"] = Field(
        description="'answered'; 'cannot_answer' when the data cannot answer the question; "
        "'failed' when no valid query could be built (answer explains).",
        examples=["answered"],
    )
    answer: str = Field(examples=[
        "Starter churn rose from 4.0% before the November 2025 price change to 9.2% in the "
        "three months after it, then settled back to about 4.5%."
    ])
    insight: str | None = Field(examples=["The price increase cost more customers than it looked like at first."])
    sql: str | None = Field(description="The query that produced the rows.", examples=[
        "SELECT month, logo_churn_rate FROM `insightflow-analytics-489617`.dbt_marts.fct_churn "
        "WHERE breakdown = 'plan' AND breakdown_value = 'starter' ORDER BY month LIMIT 500"
    ])
    columns: list[str] = Field(examples=[["month", "logo_churn_rate"]])
    rows: list[dict[str, Any]] = Field(examples=[[{"month": "2026-01-01", "logo_churn_rate": 0.118}]])
    chart: Chart
