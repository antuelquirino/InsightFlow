"""The /ask flow: question -> SQL -> validation -> BigQuery -> written answer.

1. The LLM writes BigQuery SQL from the marts context (or says the question
   cannot be answered with this data).
2. sql_guard validates it. If validation or execution fails, or the query
   returns no rows (usually a wrong filter), the problem goes back to the LLM
   for one corrected attempt; a second failure ends the request with a clear
   message (or, after an empty result, answers that no data matched).
3. BigQuery runs the query with the byte cap (MartsClient).
4. A second LLM call sees the real rows and writes the answer, an insight and a
   chart suggestion, using only numbers found in the rows. If it cites any other
   number, or slips into another script (a stray Hebrew or Cyrillic word), it
   gets one rewrite; after that the rows are returned with a neutral answer
   instead.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
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
MAX_SERIES = 2  # more lines or bar groups than this stop being readable
MAX_SCALE_RATIO = 20  # series further apart than this cannot share an axis

SQL_PROMPT = """You are a senior data analyst at InsightFlow, a B2B SaaS company. Write one \
BigQuery Standard SQL query that answers the user's question with the tables described below.

Rules:
- Only SELECT from the tables below, always with their full name in backticks.
- Prefer the most aggregated table that answers the question: kpi_summary for headline KPIs \
per month, fct_churn for churn (filter on breakdown and breakdown_value), fct_mrr_movements for \
MRR changes, fct_unit_economics for CAC, LTV and payback, dim_organizations for individual \
customers, dim_plans for prices and price changes.
- When the question refers to an event such as a price change, look up its date (dim_plans) \
and include it in the result, so the answer can place the event in time.
- For a "why" question, return the columns that explain the figure, not only the figure.
- For a "before and after" question, return one row per month from about 6 months before the event to 6 months after it, with the event date as a column; do not collapse it into a single row.
- Never write a date or value in a filter unless the user gave it or you read it from a \
table in the same query; derive event dates from the data (for example from dim_plans).
- When the question names no period, look at the last 12 months rather than a single month, \
and compare groups (plans, channels) by rates rather than counts unless counts are asked for.
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

Write numbers for people: money as whole dollars ($855) or with k/M for large amounts \
($297k, $3.6M); rates as percentages with one decimal (9.2%); ratios with one decimal (2.5x); \
months as "January 2026", never as dates like 2026-01-01. Use the number and date conventions of \
the question's language: in Spanish write US$297 mil, US$3,6 M, 9,2%, 2,5x and "enero de 2026". \
Name categories as people say them, not as database ids: "paid ads" (Spanish: "anuncios pagos"), \
not paid_ads. Write plain text: no markdown, no asterisks.

Write:
- "answer": 1 to 3 sentences that answer the question directly, in the language of the question.
- "insight": one short sentence on why it matters for the business, or null.
- "chart": how to plot the rows. "type" is "line" (x is a month or date column), "bar" (x is a \
category column), "number" (a single headline value; y is that column) or "table". "x" is one \
column name from the rows (null for "number" and "table"); "y" is one or two numeric column \
names from the rows that share a scale, never money next to rates (empty for "table").

Reply with a JSON object: {"answer": "...", "insight": "... or null", "chart": {"type": "...", \
"x": "... or null", "y": ["..."]}}

For reference, the tables the query can read and what each column means:

"""

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
    foreign_words: list[str] = field(default_factory=list)
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
        empty_result = None  # a first query that ran but returned nothing, kept as a fallback
        for attempt_number in (1, 2):
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
            except SqlRejected as error:
                attempt["error"] = f"rejected: {error}"
                feedback = f"The query was rejected: {error}"
            except GoogleAPIError as error:
                attempt["error"] = f"bigquery: {_first_line(error)}"
                feedback = f"BigQuery could not run the query: {_first_line(error)}"
            else:
                if rows or attempt_number == 2:
                    break
                # No rows is usually a wrong filter, such as a guessed date: use the retry on it.
                attempt["error"] = "empty: the query returned no rows"
                empty_result = (query, rows)
                feedback = (
                    "The query ran but returned no rows. Check its filters and any hard-coded "
                    "dates or values. If no rows is really the answer, send the same query again."
                )
            messages += [
                {"role": "assistant", "content": draft.model_dump_json()},
                {"role": "user", "content": f"{feedback}\nWrite a corrected query. Reply with the same JSON format."},
            ]
        else:
            if empty_result is None:
                return AskResult(status="failed", answer=FAILED_ANSWER, attempts=attempts)
            query, rows = empty_result

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
            {"role": "system", "content": ANSWER_PROMPT + marts_context()},
            {"role": "user", "content": json.dumps(payload, default=str)},
        ]
        for _ in range(2):
            try:
                draft = AnswerDraft.model_validate(self.llm.complete_json(messages))
            except (LLMError, ValidationError):
                return  # keep the neutral answer; the rows still answer the question
            text = f"{draft.answer} {draft.insight or ''}"
            result.unsupported_numbers = unsupported_numbers(text, result.rows, question)
            result.foreign_words = foreign_words(text)
            if not result.unsupported_numbers and not result.foreign_words:
                result.answer, result.insight = draft.answer, draft.insight
                if draft.chart:
                    result.chart = draft.chart
                return
            problems = []
            if result.unsupported_numbers:
                problems.append(
                    f"These numbers are not in the rows: {', '.join(result.unsupported_numbers)}. "
                    "Use only numbers from the rows and describe comparisons in words."
                )
            if result.foreign_words:
                problems.append(
                    f"These words are not in the language of the question: {', '.join(result.foreign_words)}. "
                    "Write the whole answer in the language of the question."
                )
            messages += [
                {"role": "assistant", "content": draft.model_dump_json()},
                {"role": "user", "content": " ".join(problems) + " Rewrite the answer. Reply with the same JSON format."},
            ]


def foreign_words(text: str) -> list[str]:
    """Words written in a non-Latin script, such as a stray Hebrew or Cyrillic word.

    Questions come in English or Spanish, so any letter outside the Latin script
    means the model slipped into another language mid-sentence.
    """
    words = re.findall(r"[^\W\d_]+", text)
    return [word for word in words if any(not unicodedata.name(char, "").startswith("LATIN") for char in word)]


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
        return chart.model_copy(update={"y": _same_scale(chart.y[:MAX_SERIES], rows)})
    return default_chart(columns, rows, numeric)


def _same_scale(series: list[str], rows: list[dict[str, Any]]) -> list[str]:
    """Drop series whose magnitude is far from the first one's (they would flatten on one axis)."""
    def magnitude(column: str) -> float:
        return max((abs(row[column]) for row in rows if row.get(column) is not None), default=0.0)

    if not series:
        return series
    first = magnitude(series[0])
    kept = [series[0]]
    for column in series[1:]:
        other = magnitude(column)
        if first and other and max(first, other) / min(first, other) <= MAX_SCALE_RATIO:
            kept.append(column)
    return kept


def default_chart(columns: list[str], rows: list[dict[str, Any]], numeric: list[str]) -> Chart:
    if len(rows) == 1 and len(numeric) == 1:
        return Chart(type="number", y=numeric)
    labels = [c for c in columns if c not in numeric]
    if rows and labels and numeric:
        x = labels[0]
        kind = "line" if any(word in x.lower() for word in ("month", "date", "week")) else "bar"
        return Chart(type=kind, x=x, y=_same_scale(numeric[:MAX_SERIES], rows))
    return Chart(type="table")


def _is_numeric_column(column: str, rows: list[dict[str, Any]]) -> bool:
    values = [row.get(column) for row in rows if row.get(column) is not None]
    return bool(values) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values)


def _first_line(error: Exception) -> str:
    message = getattr(error, "message", None) or str(error)
    return message.strip().splitlines()[0][:300]
