"""Unit tests for the number check, the OpenAI adapter and the rate limiter."""
from datetime import date
from types import SimpleNamespace

import pytest

from api.agent.numbers import unsupported_numbers
from api.agent.pipeline import foreign_words
from api.llm import LLMError, OpenAILLM
from api.rate_limit import AskRateLimiter, RateLimitExceeded

ROWS = [
    {"month": date(2026, 1, 1), "logo_churn_rate": 0.0918, "mrr": 297287.0, "churned_mrr": -5160.0, "ltv_to_cac": 2.5},
    {"month": date(2025, 10, 1), "logo_churn_rate": 0.0398, "mrr": 1234567.0, "churned_mrr": 0.0, "ltv_to_cac": 15.7},
]


@pytest.mark.parametrize("text", [
    "Starter churn rose from 4.0% to 9.2%.",
    "Churn went from 4% to 9%.",
    "MRR is $297,287, about $297k or $0.3M; the other month had $1.2M.",
    "We lost $5,160 of MRR.",
    "LTV:CAC is 2.5x for paid ads and 15.7x for partners.",
    "Churn more than doubled within 3 months.",
    "In January 2026 churn was 9.2%.",
])
def test_supported_numbers(text):
    assert unsupported_numbers(text, ROWS) == []


@pytest.mark.parametrize("text, invented", [
    ("Churn rose by 5.2 points.", ["5.2"]),
    ("Churn was 2.3x its previous level.", ["2.3"]),
    ("MRR reached $300,000.", ["$300,000"]),
    ("Churn was 9.3%.", ["9.3%"]),
    ("We have 458 customers.", ["458"]),
])
def test_unsupported_numbers(text, invented):
    assert unsupported_numbers(text, ROWS) == invented


def test_numbers_from_the_question_are_allowed():
    assert unsupported_numbers("Over the last 24 months churn was 9.2%.", ROWS, "Churn in the last 24 months?") == []
    assert unsupported_numbers("NRR is above 100%.", ROWS, "Why is NRR above 100%?") == []


def test_reference_values_are_allowed_only_in_their_natural_form():
    assert unsupported_numbers("NRR stayed above 1.0, that is above 100%.", ROWS) == []
    assert unsupported_numbers("Churn was 1% and 0%.", ROWS) == ["1%"]


def test_date_parts_do_not_support_percentages():
    # The rows have January 1 dates, but "1" does not make "25%" or "2026%" valid.
    assert unsupported_numbers("Churn was 25% in 2026.", ROWS) == ["25%"]


def test_chart_series_on_different_scales_are_not_mixed():
    from api.agent.pipeline import checked_chart
    from api.schemas import Chart

    rows = [{"channel": "paid_ads", "churn": 0.062, "ltv_to_cac": 2.5, "cac": 2339.0},
            {"channel": "organic", "churn": 0.029, "ltv_to_cac": 21.5, "cac": 855.0}]
    columns = list(rows[0])
    mixed = checked_chart(Chart(type="bar", x="channel", y=["churn", "cac"]), columns, rows)
    assert mixed.y == ["churn"]
    close = checked_chart(Chart(type="bar", x="channel", y=["ltv_to_cac", "churn"]), columns, rows)
    assert close.y == ["ltv_to_cac"]  # 21.5 vs 0.062 is too far apart as well
    too_many = checked_chart(Chart(type="bar", x="channel", y=["cac", "cac", "cac"]), columns, rows)
    assert too_many.y == ["cac", "cac"]


def _openai_stub(content):
    create = lambda **kwargs: SimpleNamespace(
        kwargs=kwargs, choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_openai_adapter_requests_json_and_parses_it():
    llm = OpenAILLM(api_key="unused", model="some-model", timeout=5, client=_openai_stub('{"sql": null}'))
    assert llm.complete_json([{"role": "user", "content": "hi"}]) == {"sql": None}


@pytest.mark.parametrize("content", ["not json", "[1, 2]", ""])
def test_openai_adapter_rejects_non_objects(content):
    llm = OpenAILLM(api_key="unused", model="some-model", timeout=5, client=_openai_stub(content))
    with pytest.raises(LLMError):
        llm.complete_json([{"role": "user", "content": "hi"}])


def test_openai_adapter_wraps_provider_errors():
    def boom(**kwargs):
        raise TimeoutError("slow")
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom)))
    with pytest.raises(LLMError, match="TimeoutError"):
        OpenAILLM(api_key="unused", model="m", timeout=5, client=client).complete_json([])


def test_rate_limit_window_slides():
    now = [0.0]
    limiter = AskRateLimiter(per_minute=2, per_day=100, clock=lambda: now[0], today=lambda: date(2026, 9, 1))
    limiter.check("a")
    limiter.check("a")
    with pytest.raises(RateLimitExceeded):
        limiter.check("a")
    limiter.check("b")  # other clients are unaffected
    now[0] = 60.0
    limiter.check("a")  # the oldest request left the window


def test_daily_limit_resets_the_next_day():
    day = [date(2026, 9, 1)]
    limiter = AskRateLimiter(per_minute=100, per_day=1, clock=lambda: 0.0, today=lambda: day[0])
    limiter.check("a")
    with pytest.raises(RateLimitExceeded):
        limiter.check("b")
    day[0] = date(2026, 9, 2)
    limiter.check("b")


@pytest.mark.parametrize("text", [
    "La tasa de Starter fue 9,2% y el MRR llegó a US$297 mil.",
    "El MRR exacto fue US$297.287; CAC de US$2,3 mil.",
    "LTV / CAC de 2,5x contra 15,7x.",
])
def test_spanish_formats_are_supported(text):
    rows = ROWS + [{"cac": 2339.0}]
    assert unsupported_numbers(text, rows) == []


def test_spanish_invented_numbers_are_flagged():
    assert unsupported_numbers("Subió 5,2 pp.", ROWS) == ["5,2"]


def test_foreign_words_ignore_english_and_spanish():
    assert foreign_words("La retención neta cayó en añadidos; ¿por qué? Churn rose to 9.2% in São Paulo.") == []


def test_foreign_words_catch_other_scripts():
    assert foreign_words("Subió בעיקר por bajas y всего.") == [
        "בעיקר", "всего"]
