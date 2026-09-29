"""Dependencies shared by the routers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Annotated

from fastapi import HTTPException, Query, Request

from api.bigquery import MartsClient
from api.settings import Settings

MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


def get_marts(request: Request) -> MartsClient:
    return request.app.state.marts


def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings


def parse_month(value: str | None) -> date | None:
    return datetime.strptime(value, "%Y-%m").date() if value else None


@dataclass(frozen=True)
class MonthRange:
    start: date | None
    end: date | None

    def where(self, column: str = "month") -> tuple[list[str], dict[str, date]]:
        """SQL conditions and parameters for this range on a trusted column name."""
        conditions, params = [], {}
        if self.start:
            conditions.append(f"{column} >= @start_month")
            params["start_month"] = self.start
        if self.end:
            conditions.append(f"{column} <= @end_month")
            params["end_month"] = self.end
        return conditions, params


def month_range(
    start_month: Annotated[
        str | None,
        Query(pattern=MONTH_PATTERN, description="First month to include, YYYY-MM.", examples=["2025-09"]),
    ] = None,
    end_month: Annotated[
        str | None,
        Query(pattern=MONTH_PATTERN, description="Last month to include, YYYY-MM.", examples=["2026-08"]),
    ] = None,
) -> MonthRange:
    months = MonthRange(parse_month(start_month), parse_month(end_month))
    if months.start and months.end and months.start > months.end:
        raise HTTPException(status_code=422, detail="start_month must not be after end_month.")
    return months


def where_clause(conditions: list[str]) -> str:
    return f"where {' and '.join(conditions)}" if conditions else ""
