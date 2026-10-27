from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ShortTermMemory(Protocol):
    def get(self, session_id: str, key: str) -> str | None: ...

    def set(
        self, session_id: str, key: str, value: str, ttl_seconds: int | None = None
    ) -> None: ...

    def delete(self, session_id: str, key: str) -> None: ...
