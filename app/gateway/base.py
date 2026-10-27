from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class GatewayResult:
    text: str
    provider: str
    model: str | None
    fallback_used: bool


@runtime_checkable
class LLMGateway(Protocol):
    async def complete(self, *, agent: str, system: str, prompt: str) -> GatewayResult: ...
