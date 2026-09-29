"""Shared fixtures for API tests. Nothing here touches BigQuery or an LLM."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.bigquery import MartsClient
from api.main import create_app
from api.settings import Settings
from tests.api.fakes import FakeBigQueryClient


@pytest.fixture
def settings():
    return Settings(_env_file=None, allowed_origins="http://localhost:3000,https://insightflow.example.com")


@pytest.fixture
def fake_bq():
    return FakeBigQueryClient()


@pytest.fixture
def marts(settings, fake_bq):
    return MartsClient(settings, client=fake_bq)


@pytest.fixture
def client(settings, marts):
    return TestClient(create_app(settings, marts))
