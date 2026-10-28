from __future__ import annotations

import importlib
from typing import Any

from app.observability.logging import get_logger
from app.security.guardrail_base import Boundary, GuardrailDecision
from app.security.guardrail_local import LocalGuardrail

_logger = get_logger("queryn.security.guardrail")


class BedrockGuardrail:
    def __init__(
        self,
        guardrail_id: str,
        guardrail_version: str,
        region: str,
        fallback: LocalGuardrail | None = None,
        client: Any | None = None,
    ) -> None:
        self._guardrail_id = guardrail_id
        self._guardrail_version = guardrail_version
        self._fallback = fallback or LocalGuardrail()
        if client is not None:
            self._client: Any = client
        else:
            boto3 = importlib.import_module("boto3")
            self._client = boto3.client("bedrock-runtime", region_name=region)

    def _warn(self, exc: Exception) -> None:
        _logger.warning(
            "bedrock_guardrail_fallback",
            extra={
                "extra_fields": {
                    "event": "bedrock_guardrail_fallback",
                    "error": type(exc).__name__,
                }
            },
        )

    def check(self, text: str, boundary: Boundary) -> GuardrailDecision:
        source = "INPUT" if boundary == "input" else "OUTPUT"
        try:
            response = self._client.apply_guardrail(
                guardrailIdentifier=self._guardrail_id,
                guardrailVersion=self._guardrail_version,
                source=source,
                content=[{"text": {"text": text}}],
            )
        except Exception as exc:
            self._warn(exc)
            return self._fallback.check(text, boundary)
        allowed = response["action"] != "GUARDRAIL_INTERVENED"
        reasons = [cat for a in response.get("assessments", []) for cat in a.keys()]
        return GuardrailDecision(allowed=allowed, reasons=reasons)
