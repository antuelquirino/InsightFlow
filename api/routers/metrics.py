"""Dashboard metrics. Every query is fixed SQL over the marts with bound parameters."""
from __future__ import annotations

from itertools import groupby
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from api.bigquery import MartsClient
from api.deps import MONTH_PATTERN, MonthRange, get_marts, month_range, parse_month, where_clause
from api.schemas import (
    Channel,
    ChurnBreakdown,
    ChurnResponse,
    Kpi,
    MrrBreakdown,
    MrrMovementsResponse,
    MrrResponse,
    Plan,
    RetentionResponse,
    SummaryResponse,
    UnitEconomicsResponse,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])

Marts = Annotated[MartsClient, Depends(get_marts)]
Months = Annotated[MonthRange, Depends(month_range)]
SingleMonth = Annotated[
    str | None,
    Query(pattern=MONTH_PATTERN, description="Month, YYYY-MM. Defaults to the latest month.", examples=["2026-08"]),
]

# KPI -> (how its change is expressed, whether an increase is good news).
SUMMARY_KPIS = {
    "mrr": ("relative", True),
    "arr": ("relative", True),
    "nrr": ("absolute", True),
    "logo_churn_rate": ("absolute", False),
    "paying_customers": ("relative", True),
    "arpa": ("relative", True),
    "new_customers": ("relative", True),
    "net_new_mrr": ("relative", True),
}

# Breakdown -> column of fct_mrr_monthly. Only these trusted names reach the SQL.
MRR_GROUP_COLUMNS = {
    MrrBreakdown.total: "'total'",
    MrrBreakdown.plan: "plan_id",
    MrrBreakdown.channel: "acquisition_channel",
    MrrBreakdown.company_size: "company_size",
}


@router.get("/summary", response_model=SummaryResponse, summary="Headline KPIs of a month")
def summary(marts: Marts, month: SingleMonth = None) -> SummaryResponse:
    """KPIs of the latest month (or `month`) and their change against the previous month,
    from `kpi_summary`. `change_type` says whether `change` is relative (amounts, counts) or
    a difference in fraction points (rates), and `higher_is_better` whether it is good news."""
    target = parse_month(month)
    sql = f"""
        select month, {', '.join(SUMMARY_KPIS)}
        from {marts.settings.marts}.kpi_summary
        {'where month <= @month' if target else ''}
        order by month desc
        limit 2
    """
    rows = marts.query(sql, {"month": target} if target else {})
    if not rows or (target and rows[0]["month"] != target):
        raise HTTPException(status_code=404, detail="No data for that month.")
    current, previous = rows[0], rows[1] if len(rows) > 1 else {}
    kpis = {
        name: _kpi(current.get(name), previous.get(name), change_type, higher_is_better)
        for name, (change_type, higher_is_better) in SUMMARY_KPIS.items()
    }
    return SummaryResponse(month=current["month"], **kpis)


def _kpi(value, previous, change_type: str, higher_is_better: bool) -> Kpi:
    change = None
    if value is not None and previous is not None:
        if change_type == "absolute":
            change = value - previous
        elif previous != 0:
            change = (value - previous) / abs(previous)
    return Kpi(
        value=value,
        previous_value=previous,
        change=change,
        change_type=change_type,
        higher_is_better=higher_is_better,
    )


@router.get("/mrr", response_model=MrrResponse, summary="Monthly MRR, total or broken down")
def mrr(
    marts: Marts,
    months: Months,
    breakdown: MrrBreakdown = MrrBreakdown.total,
    plan: Plan | None = None,
    channel: Channel | None = None,
) -> MrrResponse:
    """Month-end MRR, ARR and paying customers from `fct_mrr_monthly`, as one series (`total`)
    or one per plan, channel or company size. `plan` and `channel` filter before grouping."""
    conditions, params = months.where()
    if plan:
        conditions.append("plan_id = @plan")
        params["plan"] = plan.value
    if channel:
        conditions.append("acquisition_channel = @channel")
        params["channel"] = channel.value
    sql = f"""
        select
            month,
            {MRR_GROUP_COLUMNS[breakdown]} as series_group,
            sum(mrr) as mrr,
            sum(arr) as arr,
            sum(paying_customers) as paying_customers
        from {marts.settings.marts}.fct_mrr_monthly
        {where_clause(conditions)}
        group by 1, 2
        order by 1, 2
    """
    rows = marts.query(sql, params)
    series = [{**row, "group": row["series_group"]} for row in rows]
    return MrrResponse(breakdown=breakdown, series=series)


@router.get("/mrr-movements", response_model=MrrMovementsResponse, summary="Monthly MRR bridge")
def mrr_movements(marts: Marts, months: Months) -> MrrMovementsResponse:
    """From `fct_mrr_movements`: starting MRR + new + expansion + contraction + churned +
    reactivation = ending MRR, every month. Losses are negative numbers."""
    conditions, params = months.where()
    sql = f"""
        select *
        from {marts.settings.marts}.fct_mrr_movements
        {where_clause(conditions)}
        order by month
    """
    return MrrMovementsResponse(months=marts.query(sql, params))


@router.get("/churn", response_model=ChurnResponse, summary="Logo and revenue churn per month")
def churn(marts: Marts, months: Months, breakdown: ChurnBreakdown = ChurnBreakdown.total) -> ChurnResponse:
    """From `fct_churn`, in total or per plan or channel. A customer counts under the plan it
    had at the previous month end, so upgrades and downgrades are never churn."""
    conditions, params = months.where()
    conditions.append("breakdown = @breakdown")
    params["breakdown"] = breakdown.value
    sql = f"""
        select
            month,
            breakdown_value as series_group,
            customers_at_start,
            churned_customers,
            logo_churn_rate,
            revenue_churn_rate,
            gross_mrr_churn_rate,
            net_mrr_churn_rate
        from {marts.settings.marts}.fct_churn
        {where_clause(conditions)}
        order by month, series_group
    """
    rows = marts.query(sql, params)
    return ChurnResponse(breakdown=breakdown, series=[{**row, "group": row["series_group"]} for row in rows])


@router.get("/retention", response_model=RetentionResponse, summary="Cohort retention matrix")
def retention(
    marts: Marts,
    months: Months,
    max_months: Annotated[
        int | None, Query(ge=0, le=36, description="Only periods up to this many months after the first payment.")
    ] = None,
) -> RetentionResponse:
    """From `fct_retention_cohorts`: one cohort per month of first payment (filtered by the
    month range), each with its logo and revenue retention for every later month."""
    conditions, params = months.where("cohort_month")
    if max_months is not None:
        conditions.append("months_since_first_paid <= @max_months")
        params["max_months"] = max_months
    sql = f"""
        select
            cohort_month,
            cohort_customers,
            cohort_starting_mrr,
            months_since_first_paid,
            active_customers,
            logo_retention,
            revenue_retention
        from {marts.settings.marts}.fct_retention_cohorts
        {where_clause(conditions)}
        order by cohort_month, months_since_first_paid
    """
    rows = marts.query(sql, params)
    cohorts = []
    for cohort_month, periods in groupby(rows, key=lambda row: row["cohort_month"]):
        periods = list(periods)
        cohorts.append(
            {
                "cohort_month": cohort_month,
                "cohort_customers": periods[0]["cohort_customers"],
                "cohort_starting_mrr": periods[0]["cohort_starting_mrr"],
                "periods": periods,
            }
        )
    return RetentionResponse(cohorts=cohorts)


@router.get("/unit-economics", response_model=UnitEconomicsResponse, summary="Unit economics per channel")
def unit_economics(marts: Marts, month: SingleMonth = None) -> UnitEconomicsResponse:
    """CAC, ARPA, LTV, LTV:CAC and payback per acquisition channel for the latest month (or
    `month`), from `fct_unit_economics`. CAC and churn use trailing 12-month sums."""
    target = parse_month(month)
    table = f"{marts.settings.marts}.fct_unit_economics"
    month_filter = "@month" if target else f"(select max(month) from {table})"
    sql = f"""
        select *
        from {table}
        where month = {month_filter}
        order by acquisition_channel
    """
    rows = marts.query(sql, {"month": target} if target else {})
    if not rows:
        raise HTTPException(status_code=404, detail="No data for that month.")
    return UnitEconomicsResponse(month=rows[0]["month"], channels=rows)
