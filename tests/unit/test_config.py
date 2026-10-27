from __future__ import annotations

import pytest

from app.config import ConfigurationError, Settings, resolve_modes


def test_default_resolution_is_mock_memory_local() -> None:
    settings = Settings(
        QUERYN_LLM_PROVIDER="mock",
        QUERYN_OPENROUTER_MODEL="",
        OPENROUTER_API_KEY="",
        QUERYN_GUARDRAIL="local",
        QUERYN_TRACING="local",
        REDIS_URL="",
        DATABASE_URL="",
    )
    modes = resolve_modes(settings)

    assert modes["llm"] == "mock"
    assert modes["stm"] == "memory"
    assert modes["ltm"] == "memory"
    assert modes["guardrail"] == "local"
    assert modes["tracing"] == "local"
    assert isinstance(modes["pdf_enabled"], bool)


def test_openrouter_without_model_id_raises() -> None:
    settings = Settings(
        QUERYN_LLM_PROVIDER="openrouter",
        OPENROUTER_API_KEY="placeholder-key",
        QUERYN_OPENROUTER_MODEL="",
    )
    with pytest.raises(ConfigurationError):
        resolve_modes(settings)


def test_openrouter_with_model_id_resolves() -> None:
    settings = Settings(
        QUERYN_LLM_PROVIDER="openrouter",
        OPENROUTER_API_KEY="placeholder-key",
        QUERYN_OPENROUTER_MODEL="vendor/some-model",
    )
    modes = resolve_modes(settings)
    assert modes["llm"] == "openrouter"


def test_openrouter_requested_without_key_falls_back_to_mock() -> None:
    settings = Settings(
        QUERYN_LLM_PROVIDER="openrouter",
        OPENROUTER_API_KEY="",
        QUERYN_OPENROUTER_MODEL="vendor/some-model",
    )
    modes = resolve_modes(settings)
    assert modes["llm"] == "mock"


def test_configured_services_select_service_modes() -> None:
    settings = Settings(
        REDIS_URL="redis://localhost:6379/0",
        DATABASE_URL="postgresql://localhost:5432/queryn",
        QUERYN_GUARDRAIL="bedrock",
        AWS_BEDROCK_GUARDRAIL_ID="gr-123",
        AWS_REGION="us-east-1",
        LANGCHAIN_TRACING_V2="true",
        LANGCHAIN_API_KEY="placeholder-key",
    )
    modes = resolve_modes(settings)
    assert modes["stm"] == "redis"
    assert modes["ltm"] == "pgvector"
    assert modes["guardrail"] == "bedrock"
    assert modes["tracing"] == "langsmith"


def test_tracing_noop_override() -> None:
    settings = Settings(QUERYN_TRACING="noop")
    modes = resolve_modes(settings)
    assert modes["tracing"] == "noop"
