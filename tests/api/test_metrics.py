"""Metrics and customer endpoints, with BigQuery replaced by canned rows."""
from datetime import date

import pytest

KPI_ROW = {
    "mrr": 297287.0, "arr": 3567444.0, "nrr": 1.2391, "logo_churn_rate": 0.0429,
    "paying_customers": 458, "arpa": 649.1, "new_customers": 33, "net_new_mrr": 11593.0,
}


def last_query(fake_bq):
    sql, job_config = fake_bq.calls[-1]
    params = {p.name: p.values if hasattr(p, "values") else p.value for p in job_config.query_parameters}
    return " ".join(sql.split()), params


# --- /metrics/summary ------------------------------------------------------------

def test_summary_compares_with_previous_month(client, fake_bq):
    fake_bq.rows = [
        {"month": date(2026, 8, 1), **KPI_ROW},
        {"month": date(2026, 7, 1), **KPI_ROW, "mrr": 285694.0, "nrr": 1.2526, "logo_churn_rate": 0.0235},
    ]
    body = client.get("/metrics/summary").json()
    assert body["month"] == "2026-08-01"
    assert body["mrr"]["change_type"] == "relative"
    assert body["mrr"]["change"] == pytest.approx(297287 / 285694 - 1)
    assert body["nrr"]["change_type"] == "absolute"
    assert body["nrr"]["change"] == pytest.approx(1.2391 - 1.2526)
    assert body["logo_churn_rate"]["higher_is_better"] is False
    assert body["paying_customers"]["change"] == 0


def test_summary_first_month_has_no_change(client, fake_bq):
    fake_bq.rows = [{"month": date(2024, 9, 1), **KPI_ROW, "nrr": None}]
    body = client.get("/metrics/summary").json()
    assert body["mrr"]["previous_value"] is None and body["mrr"]["change"] is None
    assert body["nrr"]["value"] is None


def test_summary_for_a_given_month(client, fake_bq):
    fake_bq.rows = [{"month": date(2025, 12, 1), **KPI_ROW}]
    assert client.get("/metrics/summary?month=2025-12").status_code == 200
    sql, params = last_query(fake_bq)
    assert "month <= @month" in sql and params == {"month": date(2025, 12, 1)}


def test_summary_unknown_month_is_404(client, fake_bq):
    fake_bq.rows = [{"month": date(2026, 8, 1), **KPI_ROW}]  # latest month before the requested one
    assert client.get("/metrics/summary?month=2030-01").status_code == 404
    fake_bq.rows = []
    assert client.get("/metrics/summary").status_code == 404


# --- /metrics/mrr --------------------------------------------------------------------

def test_mrr_total_by_default(client, fake_bq):
    fake_bq.rows = [{"month": date(2026, 8, 1), "series_group": "total", "mrr": 1.0, "arr": 12.0, "paying_customers": 1}]
    body = client.get("/metrics/mrr").json()
    assert body["breakdown"] == "total"
    assert body["series"][0]["group"] == "total"
    sql, params = last_query(fake_bq)
    assert "'total' as series_group" in sql and "where" not in sql and params == {}


def test_mrr_breakdown_and_filters(client, fake_bq):
    client.get("/metrics/mrr?breakdown=company_size&plan=pro&channel=paid_ads&start_month=2025-09&end_month=2026-08")
    sql, params = last_query(fake_bq)
    assert "company_size as series_group" in sql
    assert "plan_id = @plan" in sql and "acquisition_channel = @channel" in sql
    assert params == {"plan": "pro", "channel": "paid_ads",
                      "start_month": date(2025, 9, 1), "end_month": date(2026, 8, 1)}


@pytest.mark.parametrize("query", [
    "breakdown=industry", "plan=gold", "channel=tv", "start_month=2026-13", "start_month=2026-8",
    "start_month=2026-08&end_month=2026-01",
])
def test_mrr_rejects_invalid_filters(client, fake_bq, query):
    assert client.get(f"/metrics/mrr?{query}").status_code == 422
    assert fake_bq.calls == []


# --- other metrics ---------------------------------------------------------------------

def test_mrr_movements_filters_by_month(client, fake_bq):
    client.get("/metrics/mrr-movements?start_month=2026-01")
    sql, params = last_query(fake_bq)
    assert "fct_mrr_movements" in sql and params == {"start_month": date(2026, 1, 1)}


def test_churn_breakdown(client, fake_bq):
    fake_bq.rows = [{
        "month": date(2026, 1, 1), "series_group": "starter", "customers_at_start": 186,
        "churned_customers": 22, "logo_churn_rate": 0.118, "revenue_churn_rate": 0.1,
        "gross_mrr_churn_rate": 0.11, "net_mrr_churn_rate": 0.05,
    }]
    body = client.get("/metrics/churn?breakdown=plan").json()
    assert body["series"][0]["group"] == "starter"
    _, params = last_query(fake_bq)
    assert params == {"breakdown": "plan"}
    assert client.get("/metrics/churn?breakdown=company_size").status_code == 422


def test_retention_groups_periods_by_cohort(client, fake_bq):
    def row(cohort, months, active):
        return {"cohort_month": cohort, "cohort_customers": 10, "cohort_starting_mrr": 500.0,
                "months_since_first_paid": months, "active_customers": active,
                "logo_retention": active / 10, "revenue_retention": 1.0}
    fake_bq.rows = [row(date(2025, 3, 1), 0, 10), row(date(2025, 3, 1), 1, 9), row(date(2025, 4, 1), 0, 10)]
    body = client.get("/metrics/retention?max_months=1").json()
    assert [c["cohort_month"] for c in body["cohorts"]] == ["2025-03-01", "2025-04-01"]
    assert [p["active_customers"] for p in body["cohorts"][0]["periods"]] == [10, 9]
    _, params = last_query(fake_bq)
    assert params == {"max_months": 1}


def test_unit_economics_latest_month(client, fake_bq):
    fake_bq.rows = [{
        "month": date(2026, 8, 1), "acquisition_channel": "paid_ads", "spend_12m": 216000.0,
        "new_customers_12m": 92, "cac": 2339.0, "arpa": 454.0, "monthly_logo_churn_rate": 0.062,
        "ltv": 5839.0, "ltv_to_cac": 2.5, "payback_months": 6.4,
    }]
    body = client.get("/metrics/unit-economics").json()
    assert body["month"] == "2026-08-01" and body["channels"][0]["ltv_to_cac"] == 2.5
    sql, params = last_query(fake_bq)
    assert "select max(month)" in sql and params == {}
    fake_bq.rows = []
    assert client.get("/metrics/unit-economics?month=2030-01").status_code == 404


# --- /customers/at-risk -----------------------------------------------------------------

def test_at_risk_defaults_to_high_and_medium(client, fake_bq):
    client.get("/customers/at-risk")
    sql, params = last_query(fake_bq)
    assert "order by current_mrr desc" in sql
    assert params == {"risks": ["high", "medium"], "limit": 50}


def test_at_risk_filters(client, fake_bq):
    client.get("/customers/at-risk?risk=high&limit=5")
    _, params = last_query(fake_bq)
    assert params == {"risks": ["high"], "limit": 5}
    for query in ["risk=low", "limit=0", "limit=201"]:
        assert client.get(f"/customers/at-risk?{query}").status_code == 422


# --- every endpoint ----------------------------------------------------------------------

ENDPOINTS = [
    "/metrics/summary", "/metrics/mrr", "/metrics/mrr-movements", "/metrics/churn",
    "/metrics/retention", "/metrics/unit-economics", "/customers/at-risk",
]


@pytest.mark.parametrize("path", ENDPOINTS)
def test_endpoints_read_only_the_marts(client, fake_bq, settings, path):
    client.get(path)
    sql, _ = last_query(fake_bq)
    assert sql.lstrip().startswith("select")
    tables = [word for word in sql.split() if "`" in word]
    assert tables and all(t.startswith(settings.marts) for t in tables)


def test_openapi_documents_every_endpoint(client):
    spec = client.get("/openapi.json").json()
    for path in ENDPOINTS + ["/health"]:
        operation = spec["paths"][path]["get"]
        assert operation.get("summary") and operation.get("description"), path
        assert "200" in operation["responses"], path
