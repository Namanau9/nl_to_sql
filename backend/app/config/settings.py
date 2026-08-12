"""Application configuration managed entirely via environment variables."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Allow values sourced from the shell environment too.
        env_nested_delimiter=".",
    )

    # --- Runtime ---
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Database ---
    database_url: str = ""
    readonly_database_url: str = ""

    # --- LLM ---
    llm_provider: str = "mock"
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 30

    # --- Query guardrails ---
    query_timeout_seconds: int = 10
    max_result_rows: int = 1000
    max_repair_attempts: int = 2

    @property
    def is_readonly_configured(self) -> bool:
        return bool(self.readonly_database_url)

    @property
    def llm_is_configured(self) -> bool:
        return self.llm_provider not in {"mock", ""} and bool(self.llm_api_key)


settings = Settings()
