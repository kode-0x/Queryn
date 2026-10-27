from __future__ import annotations

from typing import Any

from app.gateway.base import LLMGateway
from app.graph.state import Claim, KnowledgePoint, ResearchState, Source

_SYSTEM = "Write a grounded, source-attributed research report."


def _sources_by_id(sources: list[Source]) -> dict[str, Source]:
    return {source["id"]: source for source in sources}


def _claims_from_knowledge(knowledge: list[KnowledgePoint], sources: list[Source]) -> list[Claim]:
    index_by_id = _sources_by_id(sources)
    claims: list[Claim] = []
    for point in knowledge:
        resolving = [index_by_id[sid] for sid in point["source_ids"] if sid in index_by_id]
        if not resolving:
            continue
        text = resolving[0]["snippet"]
        claims.append({"text": text, "source_ids": list(point["source_ids"])})
    return claims


def _render_draft(query: str, claims: list[Claim]) -> str:
    lines = [f"# {query}".strip() or "# Report", "", "## Findings", ""]
    for claim in claims:
        lines.append(f"- {claim['text']}")
    return "\n".join(lines)


async def writer_node(state: ResearchState, *, gateway: LLMGateway) -> dict[str, Any]:
    query = state.get("query", "")
    knowledge = state.get("knowledge", [])
    sources = state.get("sources", [])
    prior = state.get("verify_findings", [])
    prompt_parts = [query]
    if prior:
        prompt_parts.append("revise: " + str(len(prior)))
    result = await gateway.complete(agent="writer", system=_SYSTEM, prompt="\n".join(prompt_parts))
    claims = _claims_from_knowledge(knowledge, sources)
    draft = _render_draft(query, claims)
    call = {
        "agent": "writer",
        "provider": result.provider,
        "outcome": "ok",
        "fallback_used": result.fallback_used,
    }
    return {"draft": draft, "claims": claims, "provider_calls": [call]}
