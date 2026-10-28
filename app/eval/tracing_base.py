from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Tracer(Protocol):
    def start_run(self, name: str, metadata: dict[str, Any] | None = None) -> None: ...

    def record_event(self, event: dict[str, Any]) -> None: ...

    def end_run(self, outcome: str) -> None: ...
