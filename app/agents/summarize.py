from __future__ import annotations

from typing import Any

from app.gateway.base import LLMGateway
from app.graph.state import Finding, KnowledgePoint, ResearchState

_SYSTEM = "Summarize research findings into grounded knowledge points."


def _knowledge_from_findings(findings: list[Finding]) -> list[KnowledgePoint]:
    return [
        {"statement": finding["content"], "source_ids": [finding["source_id"]]}
        for finding in findings
    ]


async def summarize_node(state: ResearchState, *, gateway: LLMGateway) -> dict[str, Any]:
    findings = state.get("findings", [])
    prompt = "\n".join(finding["content"] for finding in findings)
    result = await gateway.complete(agent="summarize", system=_SYSTEM, prompt=prompt)
    knowledge = _knowledge_from_findings(findings)
    call = {
        "agent": "summarize",
        "provider": result.provider,
        "outcome": "ok",
        "fallback_used": result.fallback_used,
    }
    return {"knowledge": knowledge, "provider_calls": [call]}
