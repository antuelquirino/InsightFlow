"""POST /ask: business questions in plain language, answered from the marts."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from api.agent.audit import log_ask
from api.rate_limit import RateLimitExceeded
from api.schemas import AskRequest, AskResponse, Chart

router = APIRouter(tags=["agent"])


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a business question",
    responses={
        429: {"description": "Too many questions (per client per minute, or for the whole demo per day)."},
        503: {"description": "The AI analyst is not configured on this server."},
    },
)
def ask(body: AskRequest, request: Request) -> AskResponse:
    """The AI analyst writes a SQL query over the marts, the query is validated (read-only,
    marts only, row limit) and run, and a second step writes the answer using only numbers
    from the result rows. The response includes the SQL, the rows and a chart suggestion.
    `status` is `cannot_answer` when the data cannot answer the question and `failed` when
    no valid query could be built after one retry."""
    state = request.app.state
    if state.analyst is None:
        raise HTTPException(status_code=503, detail="The AI analyst is not configured on this server.")
    try:
        state.ask_limiter.check(request.client.host if request.client else "unknown")
    except RateLimitExceeded as error:
        raise HTTPException(status_code=429, detail=str(error), headers={"Retry-After": str(error.retry_after)})

    result = state.analyst.ask(body.question)
    log_ask(state.settings.ask_log_path, {
        "question": body.question,
        "status": result.status,
        "attempts": result.attempts,
        "sql": result.sql,
        "validation_passed": any(attempt["valid"] for attempt in result.attempts),
        "row_count": len(result.rows),
        "unsupported_numbers": result.unsupported_numbers,
        "foreign_words": result.foreign_words,
        "duration_ms": result.duration_ms,
    })
    return AskResponse(
        status=result.status,
        answer=result.answer,
        insight=result.insight,
        sql=result.sql,
        columns=result.columns,
        rows=result.rows,
        chart=result.chart or Chart(type="table"),
    )
