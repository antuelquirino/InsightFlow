from datetime import date
from decimal import Decimal

from google.api_core.exceptions import BadRequest

from api.bigquery import MartsClient
from tests.api.fakes import FakeBigQueryClient


def test_health(client, fake_bq):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert fake_bq.calls == []  # health never costs a query


def test_cors_allows_configured_origins(client):
    for origin in ["http://localhost:3000", "https://insightflow.example.com"]:
        response = client.options(
            "/health", headers={"Origin": origin, "Access-Control-Request-Method": "GET"}
        )
        assert response.headers.get("access-control-allow-origin") == origin


def test_cors_rejects_other_origins(client):
    response = client.options(
        "/health", headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "GET"}
    )
    assert "access-control-allow-origin" not in response.headers


def test_queries_are_capped_and_parameterized(marts, fake_bq, settings):
    marts.query("select @month as m, @plan as p", {"month": date(2026, 8, 1), "plan": "pro"})
    _, job_config = fake_bq.calls[0]
    assert job_config.maximum_bytes_billed == settings.max_bytes_billed
    types = {p.name: p.type_ for p in job_config.query_parameters}
    assert types == {"month": "DATE", "plan": "STRING"}


def test_identical_queries_hit_the_cache(marts, fake_bq):
    for _ in range(3):
        marts.query("select 1", {"n": 1})
    marts.query("select 1", {"n": 2})
    assert len(fake_bq.calls) == 2


def test_cache_can_be_bypassed(marts, fake_bq):
    marts.query("select 1", cache=False)
    marts.query("select 1", cache=False)
    assert len(fake_bq.calls) == 2


def test_cache_is_bounded(settings, fake_bq):
    small = MartsClient(settings.model_copy(update={"query_cache_size": 2}), client=fake_bq)
    for n in range(3):
        small.query("select @n", {"n": n})
    small.query("select @n", {"n": 0})  # evicted, so it runs again
    assert len(fake_bq.calls) == 4


def test_numeric_values_become_floats(settings):
    marts = MartsClient(settings, client=FakeBigQueryClient([{"mrr": Decimal("297287.00"), "month": date(2026, 8, 1)}]))
    assert marts.query("select 1") == [{"mrr": 297287.0, "month": date(2026, 8, 1)}]


def test_bigquery_errors_become_502(settings, marts):
    from fastapi.testclient import TestClient

    from api.main import create_app

    app = create_app(settings, marts)

    @app.get("/boom")
    def boom():
        raise BadRequest("Query exceeded limit for bytes billed")

    response = TestClient(app).get("/boom")
    assert response.status_code == 502
    assert "bytes" not in response.json()["detail"]  # internal details stay internal
