from __future__ import annotations

from app.config import Settings, resolve_modes
from app.observability.logging import get_logger
from app.security.guardrail_base import Guardrail
from app.security.guardrail_local import LocalGuardrail

_logger = get_logger("queryn.security.factory")


def build_guardrail(settings: Settings) -> Guardrail:
    modes = resolve_modes(settings)
    if modes["guardrail"] == "bedrock":
        from app.security.guardrail_bedrock import BedrockGuardrail

        try:
            return BedrockGuardrail(
                guardrail_id=settings.aws_bedrock_guardrail_id,
                guardrail_version=settings.aws_bedrock_guardrail_version,
                region=settings.aws_region,
                fallback=LocalGuardrail(),
            )
        except Exception as exc:
            _logger.warning(
                "bedrock_guardrail_unavailable",
                extra={
                    "extra_fields": {
                        "event": "bedrock_guardrail_unavailable",
                        "error": type(exc).__name__,
                    }
                },
            )
    return LocalGuardrail()
