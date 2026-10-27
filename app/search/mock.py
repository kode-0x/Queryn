from __future__ import annotations

import hashlib
import re

from app.graph.state import Source

_SIMULATED_PREFIX = "[SIMULATED SOURCE]"
_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")


def _query_tokens(query: str) -> list[str]:
    return [t for t in _TOKEN_SPLIT.split(query.lower()) if t]


def _seed(query: str, index: int) -> str:
    return hashlib.sha256(f"{query}\x00{index}".encode()).hexdigest()


class MockSearchProvider:
    def __init__(self, count: int = 3) -> None:
        self._count = max(1, count)

    def search(self, query: str) -> list[Source]:
        tokens = _query_tokens(query)
        sources: list[Source] = []
        for index in range(self._count):
            seed = _seed(query, index)
            if tokens:
                chosen = tokens[index % len(tokens) :] + tokens[: index % len(tokens)]
                body = " ".join(chosen)
            else:
                body = seed[:24]
            snippet = f"{_SIMULATED_PREFIX} {body}".strip()
            title = f"{_SIMULATED_PREFIX} result {index + 1}"
            source: Source = {
                "id": f"mock-{seed[:12]}",
                "title": title,
                "uri": f"mock://{seed[:12]}",
                "snippet": snippet,
                "mock": True,
            }
            sources.append(source)
        return sources
