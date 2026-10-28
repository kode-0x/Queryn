from __future__ import annotations

from typing import Any


class NoopTracer:
    def start_run(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        return None

    def record_event(self, event: dict[str, Any]) -> None:
        return None

    def end_run(self, outcome: str) -> None:
        return None
