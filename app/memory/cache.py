from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

import numpy as np

from app.memory.embeddings import cosine, embed


class CacheableResult(Protocol):
    cache_hit: bool


ResultT = TypeVar("ResultT", bound=CacheableResult)


@dataclass
class _Entry(Generic[ResultT]):
    vector: np.ndarray
    result: ResultT


@dataclass
class SemanticCache(Generic[ResultT]):
    threshold: float = 0.95
    _entries: list[_Entry[ResultT]] = field(default_factory=list)

    def store(self, query: str, result: ResultT) -> None:
        self._entries.append(_Entry(vector=embed(query), result=result))

    def lookup(self, query: str) -> ResultT | None:
        if not self._entries:
            return None
        query_vector = embed(query)
        best_entry: _Entry[ResultT] | None = None
        best_score = -1.0
        for entry in self._entries:
            score = cosine(query_vector, entry.vector)
            if score > best_score:
                best_score = score
                best_entry = entry
        if best_entry is None or best_score < self.threshold:
            return None
        best_entry.result.cache_hit = True
        return best_entry.result
