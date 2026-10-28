from __future__ import annotations

from typing import Any

from app.observability.logging import get_logger

_logger = get_logger("queryn.eval.tracing")


class LocalTracer:
    def __init__(self) -> None:
        self._name: str | None = None
        self._metadata: dict[str, Any] = {}
        self._events: list[dict[str, Any]] = []
        self._outcome: str | None = None

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)

    @property
    def outcome(self) -> str | None:
        return self._outcome

    def start_run(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        self._name = name
        self._metadata = dict(metadata or {})
        self._events = []
        self._outcome = None

    def record_event(self, event: dict[str, Any]) -> None:
        self._events.append(dict(event))

    def end_run(self, outcome: str) -> None:
        self._outcome = outcome
        _logger.info(
            "trace_run",
            extra={
                "extra_fields": {
                    "event": "trace_run",
                    "run": self._name,
                    "metadata": self._metadata,
                    "outcome": outcome,
                    "events": self._events,
                }
            },
        )
