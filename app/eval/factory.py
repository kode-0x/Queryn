from __future__ import annotations

from app.config import Settings, resolve_modes
from app.eval.tracing_base import Tracer
from app.eval.tracing_local import LocalTracer
from app.eval.tracing_noop import NoopTracer
from app.observability.logging import get_logger

_logger = get_logger("queryn.eval.factory")


def build_tracer(settings: Settings) -> Tracer:
    modes = resolve_modes(settings)
    if modes["tracing"] == "noop":
        return NoopTracer()
    if modes["tracing"] == "langsmith":
        from app.eval.tracing_langsmith import LangSmithTracer

        try:
            return LangSmithTracer()
        except Exception as exc:
            _logger.warning(
                "langsmith_unavailable",
                extra={
                    "extra_fields": {
                        "event": "langsmith_unavailable",
                        "error": type(exc).__name__,
                    }
                },
            )
    return LocalTracer()
