from __future__ import annotations

from app.config import Settings, resolve_modes
from app.gateway.fallback import FallbackGateway
from app.gateway.mock import MockGateway


def build_gateway(settings: Settings) -> FallbackGateway:
    modes = resolve_modes(settings)
    if modes["llm"] == "openrouter":
        from app.gateway.tensorzero_gw import TensorZeroGateway

        real = TensorZeroGateway(
            model_name=settings.openrouter_model,
            api_key=settings.openrouter_api_key,
        )
        return FallbackGateway([real, MockGateway()])
    return FallbackGateway([MockGateway()])
