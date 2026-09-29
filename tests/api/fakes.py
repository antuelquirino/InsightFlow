"""Test doubles for external services."""
from __future__ import annotations


class FakeBigQueryClient:
    """Stands in for google.cloud.bigquery.Client: records queries, returns canned rows."""

    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def query(self, sql, job_config=None):
        self.calls.append((sql, job_config))
        return _FakeJob(self.rows)


class _FakeJob:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return [dict(row) for row in self._rows]
