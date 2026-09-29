"""Customer-level views."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.bigquery import MartsClient
from api.deps import get_marts
from api.schemas import AtRiskResponse, ChurnRisk

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/at-risk", response_model=AtRiskResponse, summary="Paying customers at risk of churning")
def at_risk(
    marts: Annotated[MartsClient, Depends(get_marts)],
    risk: Annotated[list[ChurnRisk], Query(description="Risk levels to include.")] = [ChurnRisk.high, ChurnRisk.medium],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AtRiskResponse:
    """Paying customers whose usage is fading (`churn_risk` from `dim_organizations`), largest
    MRR first. `high`: the last 4 weeks have under 60% of the active users of the 8 weeks
    before; `medium`: 60% to 80%. Usage fades 6 to 10 weeks before a customer cancels."""
    sql = f"""
        select
            organization_id,
            organization_name,
            industry,
            country,
            company_size,
            acquisition_channel,
            current_plan_id,
            current_seats,
            current_mrr,
            churn_risk,
            usage_trend,
            active_users_avg_4w,
            active_users_avg_prior_8w,
            first_paid_date
        from {marts.settings.marts}.dim_organizations
        where status = 'paying' and churn_risk in unnest(@risks)
        order by current_mrr desc, organization_id
        limit @limit
    """
    rows = marts.query(sql, {"risks": sorted({level.value for level in risk}), "limit": limit})
    return AtRiskResponse(customers=rows)
