"""FastAPI application. Run with `uvicorn api.main:app --reload`."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.api_core.exceptions import GoogleAPIError

from api.bigquery import MartsClient
from api.routers import customers, metrics
from api.settings import Settings, get_settings

DESCRIPTION = """
Metrics and an AI analyst for InsightFlow, a fictional B2B SaaS company.

Every endpoint reads the dbt marts in BigQuery (read-only, results cached in
memory). Money is USD and rates are fractions between 0 and 1; formatting is
left to the client.
"""


def create_app(settings: Settings | None = None, marts: MartsClient | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="InsightFlow API", version="0.1.0", description=DESCRIPTION)
    app.state.settings = settings
    app.state.marts = marts or MartsClient(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(GoogleAPIError)
    async def bigquery_error(request: Request, exc: GoogleAPIError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": "The data warehouse could not answer this request."})

    @app.get("/health", tags=["system"], summary="Liveness check")
    def health() -> dict[str, str]:
        """Returns `ok` when the API is up. Does not query BigQuery."""
        return {"status": "ok"}

    app.include_router(metrics.router)
    app.include_router(customers.router)
    return app


app = create_app()
