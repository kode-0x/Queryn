from __future__ import annotations

import importlib
from typing import Any

from app.eval.tracing_local import LocalTracer
from app.observability.logging import get_logger

_logger = get_logger("queryn.eval.tracing")


class LangSmithTracer:
    def __init__(self, project: str = "queryn", client: Any | None = None) -> None:
        self._project = project
        self._fallback = LocalTracer()
        if client is not None:
            self._client: Any = client
        else:
            langsmith = importlib.import_module("langsmith")
            self._client = langsmith.Client()

    def start_run(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        self._fallback.start_run(name, metadata)

    def record_event(self, event: dict[str, Any]) -> None:
        self._fallback.record_event(event)

    def end_run(self, outcome: str) -> None:
        self._fallback.end_run(outcome)
        try:
            self._client.create_run(
                name=self._project,
                run_type="chain",
                outputs={"outcome": outcome, "events": self._fallback.events},
            )
        except Exception as exc:
            _logger.warning(
                "langsmith_export_failed",
                extra={
                    "extra_fields": {
                        "event": "langsmith_export_failed",
                        "error": type(exc).__name__,
                    }
                },
            )
