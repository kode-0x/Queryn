from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.graph.state import Source


@runtime_checkable
class SearchProvider(Protocol):
    def search(self, query: str) -> list[Source]: ...
