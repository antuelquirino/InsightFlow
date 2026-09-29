"""The /ask flow: question -> SQL -> validation -> BigQuery -> written answer.

1. The LLM writes BigQuery SQL from the marts context (or says the question
   cannot be answered with this data).
2. sql_guard validates it. If validation or execution fails, the error goes
   back to the LLM for one corrected attempt; a second failure ends the request
   with a clear message.
3. BigQuery runs the query with the byte cap (MartsClient).
4. A second LLM call sees the real rows and writes the answer, an insight and a
   chart suggestion, using only numbers found in the rows. If it cites any other
   number it gets one rewrite; after that the rows are returned with a neutral
   answer instead.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from google.api_core.exceptions import GoogleAPIError
from pydantic import BaseModel, ValidationError

from api.agent.context import marts_context
from api.agent.numbers import unsupported_numbers
from api.agent.sql_guard import SqlRejected, validate
from api.bigquery import MartsClient
from api.llm import LLM, LLMError
from api.schemas import Chart

ROWS_SHOWN_TO_LLM = 200

SQL_PROMPT = """You are a senior data analyst at InsightFlow, a B2B SaaS company. Write one \
BigQuery Standard SQL query that answers the user's question with the tables described below.

Rules:
- Only SELECT from the tables below, always with their full name in backticks.
- Prefer the most aggregated table that answers the question: kpi_summary for headline KPIs \
per month, fct_churn for churn (filter on breakdown and breakdown_value), fct_mrr_movements for \
MRR changes, fct_unit_economics for CAC, LTV and payback, dim_organizations for individual \
customers.
- Rates are fractions (0.05 = 5%). Keep them as fractions; do not multiply by 100.
- Give every computed column a short snake_case alias. Order rows in a meaningful way \
(usually by month). Return at most 500 rows; for a single figure, return one row.
- For a "trend" or "over time" question, return one row per month.
- If the question is not about this business data, or the tables cannot answer it, do not \
guess: set "sql" to null and explain why in "cannot_answer" in one sentence.

Reply with a JSON object: {"sql": "<query or null>", "cannot_answer": "<reason or null>"}

"""

ANSWER_PROMPT = """You explain query results to a business user of InsightFlow, a B2B SaaS \
company. You receive the question, the SQL that was run and the result rows as JSON.

Rules for every number you write:
- Use only numbers that appear in the rows. You may round them, add units, and show \
fractions as percentages (0.0918 -> 9.2%).
- Never calculate new numbers: no differences, sums, averages, ratios or growth rates that \
are not in the rows. Describe comparisons in words instead ("more than doubled", "fell").
- If there are no rows, say that no data matched the question.

Write:
- "answer": 1 to 3 sentences that answer the question directly, in the language of the question.
- "insight": one short sentence on why it matters for the business, or null.
- "chart": how to plot the rows. "type" is "line" (x is a month or date column), "bar" (x is a \
category column), "number" (a single headline value; y is that column) or "table". "x" is one \
column name from the rows (null for "number" and "table"); "y" is a list of numeric column names \
from the rows (empty for "table").

Reply with a JSON object: {"answer": "...", "insight": "... or null", "chart": {"type": "...", \
"x": "... or null", "y": ["..."]}}"""

FAILED_ANSWER = (
    "I couldn't build a reliable query for that question. Try rephrasing it, for example by "
    "naming the metric and the period you are interested in."
)
NEUTRAL_ANSWER = "Here are the results for your question; the table below has the details."


class SqlDraft(BaseModel):
    sql: str | None = None
    cannot_answer: str | None = None


class AnswerDraft(BaseModel):
    answer: str
    insight: str | None = None
    chart: Chart | None = None


@dataclass
class AskResult:
    status: Literal["answered", "cannot_answer", "failed"]
    answer: str
    insight: str | None = None
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    chart: Chart | None = None  # the LLM suggestion until checked_chart settles it
    # For the audit log only.
    attempts: list[dict[str, Any]] = field(default_factory=list)
    unsupported_numbers: list[str] = field(default_factory=list)
    duration_ms: int = 0


class Analyst:
    def __init__(self, llm: LLM, marts: MartsClient):
        self.llm = llm
        self.marts = marts

    def ask(self, question: str) -> AskResult:
        started = time.perf_counter()
        result = self._ask(question)
        result.duration_ms = round((time.perf_counter() - started) * 1000)
        return result

    def _ask(self, question: str) -> AskResult:
        attempts: list[dict[str, Any]] = []
        messages = [
            {"role": "system", "content": SQL_PROMPT + marts_context()},
            {"role": "user", "content": question},
        ]
        for _ in range(2):
            attempt: dict[str, Any] = {"sql": None, "valid": False, "error": None}
            attempts.append(attempt)
            try:
                draft = SqlDraft.model_validate(self.llm.complete_json(messages))
            except (LLMError, ValidationError) as error:
                attempt["error"] = f"llm: {error}"
                continue
            attempt["sql"] = draft.sql
            if not draft.sql:
                return AskResult(
                    status="cannot_answer",
                    answer=draft.cannot_answer or "This question can't be answered with InsightFlow's data.",
                    attempts=attempts,
                )
            try:
                query = validate(draft.sql)
                attempt["valid"] = True
                rows = self.marts.query(query.sql)
                break
            except SqlRejected as error:
                attempt["error"] = f"rejected: {error}"
                feedback = f"The query was rejected: {error}"
            except GoogleAPIError as error:
                attempt["error"] = f"bigquery: {_first_line(error)}"
                feedback = f"BigQuery could not run the query: {_first_line(error)}"
            messages += [
                {"role": "assistant", "content": draft.model_dump_json()},
                {"role": "user", "content": f"{feedback}\nWrite a corrected query. Reply with the same JSON format."},
            ]
        else:
            return AskResult(status="failed", answer=FAILED_ANSWER, attempts=attempts)

        columns = list(rows[0]) if rows else []
        result = AskResult(status="answered", answer=NEUTRAL_ANSWER, sql=query.sql,
                           columns=columns, rows=rows, attempts=attempts)
        self._write_answer(question, result)
        result.chart = checked_chart(result.chart, columns, rows)
        return result

    def _write_answer(self, question: str, result: AskResult) -> None:
        payload = {
            "question": question,
            "sql": result.sql,
            "row_count": len(result.rows),
            "rows": result.rows[:ROWS_SHOWN_TO_LLM],
        }
        if len(result.rows) > ROWS_SHOWN_TO_LLM:
            payload["note"] = f"Only the first {ROWS_SHOWN_TO_LLM} of {len(result.rows)} rows are shown."
        messages = [
            {"role": "system", "content": ANSWER_PROMPT},
            {"role": "user", "content": json.dumps(payload, default=str)},
        ]
        for _ in range(2):
            try:
                draft = AnswerDraft.model_validate(self.llm.complete_json(messages))
            except (LLMError, ValidationError):
                return  # keep the neutral answer; the rows still answer the question
            text = f"{draft.answer} {draft.insight or ''}"
            result.unsupported_numbers = unsupported_numbers(text, result.rows, question)
            if not result.unsupported_numbers:
                result.answer, result.insight = draft.answer, draft.insight
                if draft.chart:
                    result.chart = draft.chart
                return
            messages += [
                {"role": "assistant", "content": draft.model_dump_json()},
                {"role": "user", "content": (
                    f"These numbers are not in the rows: {', '.join(result.unsupported_numbers)}. "
                    "Rewrite the answer using only numbers from the rows and describe comparisons "
                    "in words. Reply with the same JSON format."
                )},
            ]


def checked_chart(chart: Chart | None, columns: list[str], rows: list[dict[str, Any]]) -> Chart:
    """The suggested chart if it fits the rows, otherwise a sensible default."""
    numeric = [c for c in columns if _is_numeric_column(c, rows)]
    fits = chart is not None and (
        (chart.type == "table")
        or (chart.type == "number" and len(chart.y) == 1 and chart.y[0] in numeric and len(rows) >= 1)
        or (chart.type in ("line", "bar") and chart.x in columns and chart.x not in chart.y
            and chart.y and all(y in numeric for y in chart.y))
    )
    if fits:
        if chart.type == "table":
            return Chart(type="table")
        if chart.type == "number":
            return Chart(type="number", y=chart.y)
        return chart
    return default_chart(columns, rows, numeric)


def default_chart(columns: list[str], rows: list[dict[str, Any]], numeric: list[str]) -> Chart:
    if len(rows) == 1 and len(numeric) == 1:
        return Chart(type="number", y=numeric)
    labels = [c for c in columns if c not in numeric]
    if rows and labels and numeric:
        x = labels[0]
        kind = "line" if any(word in x.lower() for word in ("month", "date", "week")) else "bar"
        return Chart(type=kind, x=x, y=numeric[:3])
    return Chart(type="table")


def _is_numeric_column(column: str, rows: list[dict[str, Any]]) -> bool:
    values = [row.get(column) for row in rows if row.get(column) is not None]
    return bool(values) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values)


def _first_line(error: Exception) -> str:
    message = getattr(error, "message", None) or str(error)
    return message.strip().splitlines()[0][:300]
