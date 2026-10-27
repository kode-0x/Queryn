from __future__ import annotations

from collections.abc import Sequence

from app.gateway.base import GatewayResult, LLMGateway


class AllGatewaysFailedError(RuntimeError):
    pass


class FallbackGateway:
    def __init__(self, gateways: Sequence[LLMGateway]) -> None:
        if not gateways:
            raise ValueError("FallbackGateway requires at least one gateway")
        self._gateways = list(gateways)
        self.events: list[dict[str, str]] = []

    async def complete(self, *, agent: str, system: str, prompt: str) -> GatewayResult:
        last_error: Exception | None = None
        for index, gateway in enumerate(self._gateways):
            try:
                result = await gateway.complete(agent=agent, system=system, prompt=prompt)
            except Exception as exc:
                last_error = exc
                self.events.append(
                    {
                        "agent": agent,
                        "provider": type(gateway).__name__,
                        "outcome": "error",
                        "error": type(exc).__name__,
                    }
                )
                continue
            if index > 0:
                result.fallback_used = True
            self.events.append(
                {
                    "agent": agent,
                    "provider": result.provider,
                    "outcome": "ok",
                }
            )
            return result
        raise AllGatewaysFailedError(str(last_error) if last_error else "no gateways available")
