from __future__ import annotations

import importlib.util
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    llm_provider: str = Field(default="mock", alias="QUERYN_LLM_PROVIDER")
    openrouter_model: str = Field(default="", alias="QUERYN_OPENROUTER_MODEL")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")

    guardrail: str = Field(default="local", alias="QUERYN_GUARDRAIL")
    tracing: str = Field(default="local", alias="QUERYN_TRACING")

    max_verify_retries: int = Field(default=2, alias="QUERYN_MAX_VERIFY_RETRIES")
    cache_similarity_threshold: float = Field(
        default=0.95, alias="QUERYN_CACHE_SIMILARITY_THRESHOLD"
    )

    redis_url: str = Field(default="", alias="REDIS_URL")
    database_url: str = Field(default="", alias="DATABASE_URL")

    langchain_tracing_v2: str = Field(default="", alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")

    aws_region: str = Field(default="", alias="AWS_REGION")
    aws_bedrock_guardrail_id: str = Field(default="", alias="AWS_BEDROCK_GUARDRAIL_ID")
    aws_bedrock_guardrail_version: str = Field(default="", alias="AWS_BEDROCK_GUARDRAIL_VERSION")


def _pdf_available() -> bool:
    return importlib.util.find_spec("fpdf") is not None


def _resolve_llm(settings: Settings) -> str:
    if settings.llm_provider.strip().lower() != "openrouter":
        return "mock"
    if not settings.openrouter_api_key.strip():
        return "mock"
    if not settings.openrouter_model.strip():
        raise ConfigurationError(
            "QUERYN_OPENROUTER_MODEL must be set to a non-empty model id "
            "when QUERYN_LLM_PROVIDER=openrouter"
        )
    return "openrouter"


def _resolve_stm(settings: Settings) -> str:
    return "redis" if settings.redis_url.strip() else "memory"


def _resolve_ltm(settings: Settings) -> str:
    return "pgvector" if settings.database_url.strip() else "memory"


def _resolve_guardrail(settings: Settings) -> str:
    if (
        settings.guardrail.strip().lower() == "bedrock"
        and settings.aws_bedrock_guardrail_id.strip()
        and settings.aws_region.strip()
    ):
        return "bedrock"
    return "local"


def _resolve_tracing(settings: Settings) -> str:
    if settings.tracing.strip().lower() == "noop":
        return "noop"
    if (
        settings.langchain_tracing_v2.strip().lower() == "true"
        and settings.langchain_api_key.strip()
    ):
        return "langsmith"
    return "local"


def resolve_modes(settings: Settings) -> dict[str, str | bool]:
    modes: dict[str, str | bool] = {
        "llm": _resolve_llm(settings),
        "stm": _resolve_stm(settings),
        "ltm": _resolve_ltm(settings),
        "guardrail": _resolve_guardrail(settings),
        "tracing": _resolve_tracing(settings),
        "pdf_enabled": _pdf_available(),
    }
    return modes


@lru_cache
def get_settings() -> Settings:
    return Settings()
