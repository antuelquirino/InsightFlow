"""The agent must surface the stories in docs/data-stories.md.

These tests call BigQuery and the LLM (cost and credentials needed), so they only
run on demand:

    pytest -m live

They need OPENAI_API_KEY and LLM_MODEL (in .env) and Google Application Default
Credentials. Answers are checked for the key facts, not for exact wording.
"""
import re

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.settings import Settings

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def client():
    settings = Settings()
    if not settings.llm_configured:
        pytest.skip("OPENAI_API_KEY and LLM_MODEL are not set")
    settings = settings.model_copy(update={"ask_requests_per_minute": 100})
    return TestClient(create_app(settings))


def ask(client, question):
    response = client.post("/ask", json={"question": question})
    assert response.status_code == 200, response.text
    body = response.json()
    print(f"\nQ: {question}\nSQL: {body['sql']}\nA: {body['answer']}\nInsight: {body['insight']}\nChart: {body['chart']}")
    assert body["status"] == "answered", body["answer"]
    return body


def text_of(body):
    return f"{body['answer']} {body['insight'] or ''}".lower()


def test_story_1_starter_price_change(client):
    body = ask(client, "What happened to Starter churn after the price change?")
    text = text_of(body)
    assert "starter" in text
    assert re.search(r"doubl|rose|increas|spik|jump|higher", text)
    assert "november" in text  # the date of the change comes from dim_plans
    assert "fct_churn" in body["sql"] or "starter" in body["sql"].lower()


def test_story_2_paid_ads_customers_leave_fast(client):
    body = ask(client, "Which acquisition channel has the highest churn rate, and how do the unit economics compare by channel?")
    assert "paid" in text_of(body)


def test_story_3_enterprise_expansion_drives_nrr(client):
    body = ask(client, "Why is net revenue retention above 100% if we are losing customers?")
    text = text_of(body)
    assert "expansion" in text or "enterprise" in text or "seat" in text


def test_story_4_customers_at_risk(client):
    body = ask(client, "Which paying customers are at high risk of churning?")
    assert body["rows"], "expected at-risk customers"
    assert "dim_organizations" in body["sql"]


def test_story_5_signup_seasonality(client):
    body = ask(client, "In which month of the year do we get the most new customers, and which months are slowest?")
    text = text_of(body)
    assert "march" in text or "mar" in text


def test_off_topic_question_is_declined(client):
    response = client.post("/ask", json={"question": "What is the capital of France?"})
    assert response.json()["status"] == "cannot_answer"
