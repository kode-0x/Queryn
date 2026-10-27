from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.memory.embeddings import cosine, embed
from app.memory.ltm_base import LTMRecord


@dataclass
class _Entry:
    id: str
    vector: np.ndarray
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class InMemoryLTM:
    def __init__(self) -> None:
        self._entries: list[_Entry] = []

    def store(self, content: str, metadata: dict[str, Any]) -> str:
        record_id = uuid.uuid4().hex
        self._entries.append(
            _Entry(id=record_id, vector=embed(content), content=content, metadata=dict(metadata))
        )
        return record_id

    def _matches(self, metadata: dict[str, Any], filters: dict[str, Any] | None) -> bool:
        if not filters:
            return True
        return all(metadata.get(key) == value for key, value in filters.items())

    def retrieve(
        self, query: str, k: int = 5, filters: dict[str, Any] | None = None
    ) -> list[LTMRecord]:
        query_vector = embed(query)
        scored: list[LTMRecord] = []
        for entry in self._entries:
            if not self._matches(entry.metadata, filters):
                continue
            scored.append(
                LTMRecord(
                    id=entry.id,
                    content=entry.content,
                    metadata=dict(entry.metadata),
                    score=cosine(query_vector, entry.vector),
                )
            )
        scored.sort(key=lambda record: record["score"], reverse=True)
        return scored[: max(k, 0)]
