from __future__ import annotations

import pytest

from app.config import ConfigurationError, Settings
from app.gateway.factory import build_gateway
from app.gateway.fallback import AllGatewaysFailedError, FallbackGateway
from app.gateway.mock import FlakyMockGateway, MockGateway


async def test_mock_gateway_is_deterministic() -> None:
    gateway = MockGateway()
    first = await gateway.complete(agent="writer", system="s", prompt="p")
    second = await gateway.complete(agent="writer", system="s", prompt="p")
    assert first.text == second.text
    assert first.provider == "mock"
    assert first.fallback_used is False


def test_factory_defaults_to_mock_chain() -> None:
    settings = Settings(QUERYN_LLM_PROVIDER="mock")
    gateway = build_gateway(settings)
    assert isinstance(gateway, FallbackGateway)


def test_factory_openrouter_without_model_raises() -> None:
    settings = Settings(
        QUERYN_LLM_PROVIDER="openrouter",
        OPENROUTER_API_KEY="placeholder-key",
        QUERYN_OPENROUTER_MODEL="",
    )
    with pytest.raises(ConfigurationError):
        build_gateway(settings)


async def test_fallback_engages_on_injected_failure() -> None:
    gateway = FallbackGateway([FlakyMockGateway(), MockGateway()])
    result = await gateway.complete(agent="summarize", system="s", prompt="p")
    assert result.provider == "mock"
    assert result.fallback_used is True
    outcomes = [event["outcome"] for event in gateway.events]
    assert outcomes == ["error", "ok"]


async def test_all_failures_raise() -> None:
    gateway = FallbackGateway([FlakyMockGateway(), FlakyMockGateway()])
    with pytest.raises(AllGatewaysFailedError):
        await gateway.complete(agent="writer", system="s", prompt="p")
