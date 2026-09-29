"""Configuration from environment variables (and `.env` in development)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gcp_project: str = "insightflow-analytics-489617"
    bq_location: str = "EU"
    marts_dataset: str = "dbt_marts"
    # BigQuery bills at least 10 MB per table read; the marts are a few MB.
    max_bytes_billed: int = 200_000_000
    query_cache_size: int = 512

    # Comma-separated list of frontend origins allowed by CORS.
    allowed_origins: str = "http://localhost:3000"

    # LLM behind POST /ask. Without a key and a model, /ask answers 503.
    openai_api_key: SecretStr | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = 60.0

    # POST /ask limits, so a public demo cannot run up costs.
    ask_requests_per_minute: int = 5  # per client IP
    ask_requests_per_day: int = 200  # for the whole API
    ask_log_path: str = "logs/ask.jsonl"

    @property
    def llm_configured(self) -> bool:
        return bool(self.openai_api_key and self.llm_model)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def marts(self) -> str:
        """Fully qualified marts dataset, ready to prefix table names in SQL."""
        return f"`{self.gcp_project}.{self.marts_dataset}`"


@lru_cache
def get_settings() -> Settings:
    return Settings()
