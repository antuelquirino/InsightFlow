"""Read-only access to the marts, with a byte cap and an in-memory cache.

The data is static (generated once), so identical queries always return the
same rows: results are cached until the process restarts. Values come back as
plain JSON-friendly Python types (NUMERIC becomes float).
"""
from __future__ import annotations

import threading
from collections import OrderedDict
from datetime import date
from decimal import Decimal
from typing import Any

from google.cloud import bigquery

from api.settings import Settings

Row = dict[str, Any]


class MartsClient:
    def __init__(self, settings: Settings, client: bigquery.Client | None = None):
        self.settings = settings
        self._client = client
        self._cache: OrderedDict[tuple, list[Row]] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def client(self) -> bigquery.Client:
        # Created on first use, so the app starts (and tests run) without credentials.
        if self._client is None:
            self._client = bigquery.Client(
                project=self.settings.gcp_project, location=self.settings.bq_location
            )
        return self._client

    def query(self, sql: str, params: dict[str, Any] | None = None, *, cache: bool = True) -> list[Row]:
        params = params or {}
        key = (sql, tuple(sorted(params.items())))
        if cache:
            with self._lock:
                if key in self._cache:
                    self._cache.move_to_end(key)
                    return self._cache[key]

        job_config = bigquery.QueryJobConfig(
            query_parameters=[_parameter(name, value) for name, value in params.items()],
            maximum_bytes_billed=self.settings.max_bytes_billed,
        )
        rows = [
            {column: _plain(value) for column, value in row.items()}
            for row in self.client.query(sql, job_config=job_config).result()
        ]

        if cache:
            with self._lock:
                self._cache[key] = rows
                while len(self._cache) > self.settings.query_cache_size:
                    self._cache.popitem(last=False)
        return rows


def _parameter(name: str, value: Any) -> bigquery.ScalarQueryParameter:
    # bool before int: bool is a subclass of int.
    for python_type, bq_type in ((bool, "BOOL"), (int, "INT64"), (float, "FLOAT64"), (date, "DATE"), (str, "STRING")):
        if isinstance(value, python_type):
            return bigquery.ScalarQueryParameter(name, bq_type, value)
    raise TypeError(f"Unsupported query parameter {name!r} of type {type(value).__name__}")


def _plain(value: Any) -> Any:
    return float(value) if isinstance(value, Decimal) else value
