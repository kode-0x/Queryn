from __future__ import annotations

import hashlib

from app.gateway.base import GatewayResult


class MockGateway:
    def __init__(self, provider: str = "mock") -> None:
        self._provider = provider

    @property
    def provider(self) -> str:
        return self._provider

    async def complete(self, *, agent: str, system: str, prompt: str) -> GatewayResult:
        seed = hashlib.sha256(f"{agent}\x00{system}\x00{prompt}".encode()).hexdigest()
        text = f"{agent}:{seed[:16]}"
        return GatewayResult(
            text=text,
            provider=self._provider,
            model=None,
            fallback_used=False,
        )


class FlakyMockGateway:
    def __init__(self, provider: str = "flaky", error: Exception | None = None) -> None:
        self._provider = provider
        self._error = error or TimeoutError("injected gateway failure")

    @property
    def provider(self) -> str:
        return self._provider

    async def complete(self, *, agent: str, system: str, prompt: str) -> GatewayResult:
        raise self._error
