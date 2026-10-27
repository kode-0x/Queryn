from __future__ import annotations

from typing import Any

from app.graph.state import Finding, ResearchState, Source
from app.search.base import SearchProvider

_SIMULATED_PREFIX = "[SIMULATED SOURCE]"


def _fallback_source(query: str) -> Source:
    return {
        "id": "mock-empty",
        "title": f"{_SIMULATED_PREFIX} placeholder",
        "uri": "mock://placeholder",
        "snippet": f"{_SIMULATED_PREFIX} {query}".strip(),
        "mock": True,
    }


async def search_node(state: ResearchState, *, provider: SearchProvider) -> dict[str, Any]:
    query = state.get("query", "")
    sources = provider.search(query)
    if not sources:
        sources = [_fallback_source(query)]
    findings: list[Finding] = [
        {
            "source_id": source["id"],
            "content": source["snippet"],
            "relevance": 1.0,
        }
        for source in sources
    ]
    call = {
        "agent": "search",
        "provider": "mock" if all(s["mock"] for s in sources) else "search",
        "outcome": "ok",
        "fallback_used": False,
    }
    return {"sources": sources, "findings": findings, "provider_calls": [call]}
