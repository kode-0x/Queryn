from __future__ import annotations

import importlib
import tempfile
from pathlib import Path

from app.config import ConfigurationError
from app.gateway.base import GatewayResult

_FUNCTION_NAME = "queryn_generate"


def _render_config(model_name: str) -> str:
    return (
        f"[functions.{_FUNCTION_NAME}]\n"
        'type = "chat"\n\n'
        f"[functions.{_FUNCTION_NAME}.variants.openrouter]\n"
        'type = "chat_completion"\n'
        'model = "queryn_openrouter_model"\n\n'
        "[models.queryn_openrouter_model]\n"
        'routing = ["openrouter"]\n\n'
        "[models.queryn_openrouter_model.providers.openrouter]\n"
        'type = "openrouter"\n'
        f'model_name = "{model_name}"\n'
    )


class TensorZeroGateway:
    def __init__(self, model_name: str, api_key: str) -> None:
        if not model_name.strip():
            raise ConfigurationError("TensorZeroGateway requires a non-empty model id")
        self._model_name = model_name
        self._api_key = api_key
        self._client: object | None = None

    @property
    def provider(self) -> str:
        return "openrouter"

    def _build_client(self) -> object:
        module = importlib.import_module("tensorzero")
        gateway_cls = module.AsyncTensorZeroGateway
        config_dir = Path(tempfile.mkdtemp(prefix="queryn_tz_"))
        config_path = config_dir / "tensorzero.toml"
        config_path.write_text(_render_config(self._model_name), encoding="utf-8")
        return gateway_cls.build_embedded(config_file=str(config_path))

    async def complete(self, *, agent: str, system: str, prompt: str) -> GatewayResult:
        if self._client is None:
            self._client = self._build_client()
        client = self._client
        response = await client.inference(  # type: ignore[attr-defined]
            function_name=_FUNCTION_NAME,
            input={
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        content = response.content
        text = content[0].text if content else ""
        return GatewayResult(
            text=text,
            provider="openrouter",
            model=self._model_name,
            fallback_used=False,
        )
