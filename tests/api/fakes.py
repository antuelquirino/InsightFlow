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


class FakeLLM:
    """Returns scripted replies in order (a dict, or an exception to raise) and records calls."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def complete_json(self, messages):
        self.calls.append([dict(m) for m in messages])
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


class FailingBigQueryClient(FakeBigQueryClient):
    """Raises the given errors on the first queries, then returns rows."""

    def __init__(self, errors, rows=None):
        super().__init__(rows)
        self.errors = list(errors)

    def query(self, sql, job_config=None):
        self.calls.append((sql, job_config))
        if self.errors:
            raise self.errors.pop(0)
        return _FakeJob(self.rows)
