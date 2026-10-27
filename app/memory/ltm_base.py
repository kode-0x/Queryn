from __future__ import annotations

from typing import Any, Protocol, TypedDict, runtime_checkable


class LTMRecord(TypedDict):
    id: str
    content: str
    metadata: dict[str, Any]
    score: float


@runtime_checkable
class LongTermMemory(Protocol):
    def store(self, content: str, metadata: dict[str, Any]) -> str: ...

    def retrieve(
        self, query: str, k: int = 5, filters: dict[str, Any] | None = None
    ) -> list[LTMRecord]: ...
