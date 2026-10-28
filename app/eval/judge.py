from __future__ import annotations

import re

from app.agents.verify import containment
from app.gateway.base import LLMGateway
from app.graph.state import Claim, KnowledgePoint, Source

_SYSTEM = "Score a research report for relevance, faithfulness, groundedness, and completeness."
_SECTION_HEADING = re.compile(r"^#{1,6}\s+", re.MULTILINE)


def _sources_by_id(sources: list[Source]) -> dict[str, Source]:
    return {source["id"]: source for source in sources}


def _best_snippet_containment(claim: Claim, index_by_id: dict[str, Source]) -> float:
    resolving = [index_by_id[sid] for sid in claim["source_ids"] if sid in index_by_id]
    if not resolving:
        return 0.0
    return max(containment(claim["text"], source["snippet"]) for source in resolving)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _faithfulness(claims: list[Claim], index_by_id: dict[str, Source]) -> float:
    return _mean([_best_snippet_containment(claim, index_by_id) for claim in claims])


def _completeness(knowledge: list[KnowledgePoint], claims: list[Claim]) -> float:
    if not knowledge:
        return 0.0
    referenced = {sid for claim in claims for sid in claim["source_ids"]}
    covered = sum(1 for point in knowledge if any(sid in referenced for sid in point["source_ids"]))
    return covered / len(knowledge)


def _relevance(claims: list[Claim], query: str) -> float:
    return _mean([containment(claim["text"], query) for claim in claims])


def _coherence(draft: str) -> float:
    sections = [section for section in _SECTION_HEADING.split(draft) if section != ""]
    if not sections:
        return 0.0
    non_empty = sum(1 for section in sections if section.strip())
    return min(1.0, non_empty / len(sections))


class Judge:
    def __init__(self, gateway: LLMGateway) -> None:
        self._gateway = gateway

    async def score(
        self,
        query: str,
        draft: str,
        claims: list[Claim],
        sources: list[Source],
        knowledge: list[KnowledgePoint],
    ) -> dict[str, float]:
        await self._gateway.complete(agent="judge", system=_SYSTEM, prompt=query)
        index_by_id = _sources_by_id(sources)
        faithfulness = _faithfulness(claims, index_by_id)
        return {
            "relevance": _relevance(claims, query),
            "faithfulness": faithfulness,
            "groundedness": faithfulness,
            "completeness": _completeness(knowledge, claims),
            "coherence": _coherence(draft),
        }
