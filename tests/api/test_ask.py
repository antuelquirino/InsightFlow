"""POST /ask with a scripted LLM and a fake BigQuery client."""
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient
from google.api_core.exceptions import BadRequest

from api.bigquery import MartsClient
from api.llm import LLMError
from api.main import create_app
from tests.api.fakes import FailingBigQueryClient, FakeBigQueryClient, FakeLLM, SequenceBigQueryClient

QUESTION = "What happened to Starter churn after the price change?"
GOOD_SQL = {"sql": "SELECT month, logo_churn_rate FROM fct_churn WHERE breakdown_value = 'starter' ORDER BY month", "cannot_answer": None}
ROWS = [
    {"month": date(2025, 10, 1), "logo_churn_rate": 0.0398},
    {"month": date(2026, 1, 1), "logo_churn_rate": 0.0918},
]
GOOD_ANSWER = {
    "answer": "Starter churn rose from 4.0% in October 2025 to 9.2% in January 2026.",
    "insight": "The price increase more than doubled churn.",
    "chart": {"type": "line", "x": "month", "y": ["logo_churn_rate"]},
}


@pytest.fixture
def ask_settings(settings, tmp_path):
    return settings.model_copy(update={"ask_log_path": str(tmp_path / "ask.jsonl")})


def make_client(ask_settings, llm, bq=None):
    marts = MartsClient(ask_settings, client=bq or FakeBigQueryClient(ROWS))
    return TestClient(create_app(ask_settings, marts, llm))


def read_log(ask_settings):
    with open(ask_settings.ask_log_path, encoding="utf-8") as log:
        return [json.loads(line) for line in log]


def test_answers_a_question(ask_settings):
    llm = FakeLLM(GOOD_SQL, GOOD_ANSWER)
    bq = FakeBigQueryClient(ROWS)
    response = make_client(ask_settings, llm, bq).post("/ask", json={"question": QUESTION})
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "answered"
    assert body["answer"] == GOOD_ANSWER["answer"]
    assert body["columns"] == ["month", "logo_churn_rate"]
    assert body["rows"][1] == {"month": "2026-01-01", "logo_churn_rate": 0.0918}
    assert body["chart"] == {"type": "line", "x": "month", "y": ["logo_churn_rate"]}
    # The validated SQL ran, not the raw draft.
    executed, job_config = bq.calls[0]
    assert "`insightflow-analytics-489617`.dbt_marts.fct_churn" in executed and executed.endswith("LIMIT 500")
    assert job_config.maximum_bytes_billed == ask_settings.max_bytes_billed
    assert body["sql"] == executed


def test_sql_prompt_contains_the_marts_context(ask_settings):
    llm = FakeLLM(GOOD_SQL, GOOD_ANSWER)
    make_client(ask_settings, llm).post("/ask", json={"question": QUESTION})
    system = llm.calls[0][0]["content"]
    assert "fct_churn" in system and "breakdown_value" in system
    answer_payload = json.loads(llm.calls[1][1]["content"])
    assert answer_payload["rows"][1]["logo_churn_rate"] == 0.0918  # the answer step sees the real rows


def test_rejected_sql_is_retried_once_with_the_reason(ask_settings):
    llm = FakeLLM({"sql": "DELETE FROM fct_churn WHERE TRUE"}, GOOD_SQL, GOOD_ANSWER)
    body = make_client(ask_settings, llm).post("/ask", json={"question": QUESTION}).json()
    assert body["status"] == "answered"
    feedback = llm.calls[1][-1]["content"]
    assert "rejected" in feedback and "SELECT" in feedback


def test_bigquery_error_is_retried_once(ask_settings):
    llm = FakeLLM(GOOD_SQL, GOOD_SQL, GOOD_ANSWER)
    bq = FailingBigQueryClient([BadRequest("Unrecognized name: churn_rate at [1:8]")], ROWS)
    body = make_client(ask_settings, llm, bq).post("/ask", json={"question": QUESTION}).json()
    assert body["status"] == "answered"
    assert "Unrecognized name: churn_rate" in llm.calls[1][-1]["content"]


OTHER_SQL = {"sql": "SELECT month, logo_churn_rate FROM fct_churn WHERE breakdown = 'plan' ORDER BY month"}


def test_empty_result_is_retried_once(ask_settings):
    llm = FakeLLM(GOOD_SQL, OTHER_SQL, GOOD_ANSWER)
    bq = SequenceBigQueryClient([], ROWS)
    body = make_client(ask_settings, llm, bq).post("/ask", json={"question": QUESTION}).json()
    assert body["status"] == "answered" and body["rows"]
    assert "no rows" in llm.calls[1][-1]["content"]
    assert [a["error"] for a in read_log(ask_settings)[0]["attempts"]] == ["empty: the query returned no rows", None]


def test_empty_result_twice_answers_that_nothing_matched(ask_settings):
    no_data = {"answer": "No data matched the question.", "insight": None, "chart": None}
    llm = FakeLLM(GOOD_SQL, OTHER_SQL, no_data)
    body = make_client(ask_settings, llm, SequenceBigQueryClient([])).post("/ask", json={"question": QUESTION}).json()
    assert body["status"] == "answered" and body["rows"] == []
    assert body["answer"] == "No data matched the question."


def test_empty_result_then_invalid_query_keeps_the_empty_result(ask_settings):
    no_data = {"answer": "No data matched the question.", "insight": None, "chart": None}
    llm = FakeLLM(GOOD_SQL, {"sql": "DROP TABLE fct_churn"}, no_data)
    body = make_client(ask_settings, llm, SequenceBigQueryClient([])).post("/ask", json={"question": QUESTION}).json()
    assert body["status"] == "answered" and "fct_churn" in body["sql"]


def test_two_failures_end_with_a_clear_message(ask_settings):
    llm = FakeLLM({"sql": "SELECT * FROM raw.organizations"}, {"sql": "DROP TABLE fct_churn"})
    bq = FakeBigQueryClient(ROWS)
    body = make_client(ask_settings, llm, bq).post("/ask", json={"question": QUESTION}).json()
    assert body["status"] == "failed"
    assert "rephrasing" in body["answer"]
    assert body["sql"] is None and body["rows"] == []
    assert bq.calls == []  # nothing invalid ever reached BigQuery
    assert len(llm.calls) == 2  # exactly one retry


def test_llm_errors_count_as_a_failed_attempt(ask_settings):
    llm = FakeLLM(LLMError("timeout"), GOOD_SQL, GOOD_ANSWER)
    assert make_client(ask_settings, llm).post("/ask", json={"question": QUESTION}).json()["status"] == "answered"


def test_questions_the_data_cannot_answer(ask_settings):
    llm = FakeLLM({"sql": None, "cannot_answer": "The data has no weather information."})
    bq = FakeBigQueryClient(ROWS)
    body = make_client(ask_settings, llm, bq).post("/ask", json={"question": "Will it rain tomorrow?"}).json()
    assert body["status"] == "cannot_answer"
    assert body["answer"] == "The data has no weather information."
    assert bq.calls == []


def test_invented_numbers_trigger_one_rewrite(ask_settings):
    invented = {**GOOD_ANSWER, "answer": "Starter churn rose by 5.2 points, 2.3x its previous level."}
    llm = FakeLLM(GOOD_SQL, invented, GOOD_ANSWER)
    body = make_client(ask_settings, llm).post("/ask", json={"question": QUESTION}).json()
    assert body["answer"] == GOOD_ANSWER["answer"]
    assert "5.2" in llm.calls[2][-1]["content"] and "2.3" in llm.calls[2][-1]["content"]


def test_persistent_invented_numbers_fall_back_to_a_neutral_answer(ask_settings):
    invented = {**GOOD_ANSWER, "answer": "Churn rose by 5.2 points."}
    llm = FakeLLM(GOOD_SQL, invented, invented)
    body = make_client(ask_settings, llm).post("/ask", json={"question": QUESTION}).json()
    assert body["status"] == "answered"
    assert "5.2" not in body["answer"] and body["insight"] is None
    assert body["rows"]  # the data still answers the question
    assert read_log(ask_settings)[0]["unsupported_numbers"] == ["5.2"]


def test_page_language_is_passed_to_the_answer(ask_settings):
    llm = FakeLLM(GOOD_SQL, GOOD_ANSWER)
    make_client(ask_settings, llm).post("/ask", json={"question": QUESTION, "language": "es"})
    note = llm.calls[1][-1]
    assert note["role"] == "system" and "coma decimal" in note["content"] and "Anuncios pagos" in note["content"]


def test_without_language_there_is_no_language_note(ask_settings):
    llm = FakeLLM(GOOD_SQL, GOOD_ANSWER)
    make_client(ask_settings, llm).post("/ask", json={"question": QUESTION})
    assert llm.calls[1][-1]["role"] == "user"


def test_unknown_language_is_rejected(ask_settings):
    response = make_client(ask_settings, FakeLLM()).post("/ask", json={"question": QUESTION, "language": "fr"})
    assert response.status_code == 422


def test_words_in_another_script_trigger_one_rewrite(ask_settings):
    slipped = {**GOOD_ANSWER, "answer": "El churn de Starter subió a 9,2%, בעיקר por bajas."}
    fixed = {**GOOD_ANSWER, "answer": "El churn de Starter subió a 9,2%, sobre todo por bajas."}
    llm = FakeLLM(GOOD_SQL, slipped, fixed)
    body = make_client(ask_settings, llm).post("/ask", json={"question": "¿Qué pasó con el churn de Starter?"}).json()
    assert body["answer"] == fixed["answer"]
    assert "בעיקר" in llm.calls[2][-1]["content"]


def test_persistent_foreign_words_fall_back_to_a_neutral_answer(ask_settings):
    slipped = {**GOOD_ANSWER, "answer": "Churn rose to 9.2% всего."}
    llm = FakeLLM(GOOD_SQL, slipped, slipped)
    body = make_client(ask_settings, llm).post("/ask", json={"question": QUESTION}).json()
    assert body["status"] == "answered" and body["rows"]
    assert "9.2%" not in body["answer"]
    assert read_log(ask_settings)[0]["foreign_words"] == ["всего"]


def test_chart_that_does_not_fit_the_rows_is_replaced(ask_settings):
    bad_chart = {**GOOD_ANSWER, "chart": {"type": "bar", "x": "plan", "y": ["mrr"]}}
    llm = FakeLLM(GOOD_SQL, bad_chart)
    body = make_client(ask_settings, llm).post("/ask", json={"question": QUESTION}).json()
    assert body["chart"] == {"type": "line", "x": "month", "y": ["logo_churn_rate"]}


def test_single_value_defaults_to_a_number_chart(ask_settings):
    llm = FakeLLM(GOOD_SQL, {"answer": "MRR is $297,287.", "insight": None, "chart": None})
    bq = FakeBigQueryClient([{"mrr": 297287.0}])
    body = make_client(ask_settings, llm, bq).post("/ask", json={"question": "What is MRR?"}).json()
    assert body["chart"] == {"type": "number", "x": None, "y": ["mrr"]}


def test_every_question_is_logged(ask_settings):
    llm = FakeLLM({"sql": "SELECT * FROM raw.plans"}, GOOD_SQL, GOOD_ANSWER)
    make_client(ask_settings, llm).post("/ask", json={"question": QUESTION})
    [entry] = read_log(ask_settings)
    assert entry["question"] == QUESTION
    assert entry["status"] == "answered"
    assert entry["validation_passed"] is True
    assert [a["valid"] for a in entry["attempts"]] == [False, True]
    assert entry["attempts"][0]["sql"] == "SELECT * FROM raw.plans"
    assert "LIMIT 500" in entry["sql"]
    assert isinstance(entry["duration_ms"], int) and entry["timestamp"]


@pytest.mark.parametrize("question", ["", "hi", "x" * 501])
def test_question_length_is_validated(ask_settings, question):
    assert make_client(ask_settings, FakeLLM()).post("/ask", json={"question": question}).status_code == 422


def test_ask_without_llm_configured_is_503(ask_settings):
    client = TestClient(create_app(ask_settings, MartsClient(ask_settings, client=FakeBigQueryClient())))
    assert client.post("/ask", json={"question": QUESTION}).status_code == 503


def test_rate_limit_per_client(ask_settings):
    limited = ask_settings.model_copy(update={"ask_requests_per_minute": 2})
    llm = FakeLLM(*[GOOD_SQL, GOOD_ANSWER] * 2)
    client = make_client(limited, llm)
    assert [client.post("/ask", json={"question": QUESTION}).status_code for _ in range(3)] == [200, 200, 429]
    response = client.post("/ask", json={"question": QUESTION})
    assert response.status_code == 429 and int(response.headers["retry-after"]) > 0


def test_daily_limit_for_everyone(ask_settings):
    limited = ask_settings.model_copy(update={"ask_requests_per_day": 1})
    client = make_client(limited, FakeLLM(GOOD_SQL, GOOD_ANSWER))
    assert client.post("/ask", json={"question": QUESTION}).status_code == 200
    response = client.post("/ask", json={"question": QUESTION})
    assert response.status_code == 429 and "daily" in response.json()["detail"]


def test_ask_log_can_go_to_stdout(ask_settings, capsys):
    stdout_settings = ask_settings.model_copy(update={"ask_log_path": "-"})
    make_client(stdout_settings, FakeLLM(GOOD_SQL, GOOD_ANSWER)).post("/ask", json={"question": QUESTION})
    line = capsys.readouterr().out.strip().splitlines()[-1]
    entry = json.loads(line)
    assert entry["message"] == "ask" and entry["question"] == QUESTION
