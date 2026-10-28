from __future__ import annotations

from app.eval.judge import Judge
from app.gateway.mock import MockGateway
from app.graph.state import Claim, KnowledgePoint, Source

_SCORE_KEYS = ("relevance", "faithfulness", "groundedness", "completeness", "coherence")


def _fixture() -> tuple[str, str, list[Claim], list[Source], list[KnowledgePoint]]:
    query = "renewable energy adoption trends"
    sources: list[Source] = [
        {
            "id": "s1",
            "title": "[SIMULATED SOURCE] renewable",
            "uri": "mock://s1",
            "snippet": "renewable energy adoption trends are rising worldwide",
            "mock": True,
        }
    ]
    claims: list[Claim] = [
        {"text": "renewable energy adoption trends are rising", "source_ids": ["s1"]}
    ]
    knowledge: list[KnowledgePoint] = [{"statement": "adoption rising", "source_ids": ["s1"]}]
    draft = "# renewable energy\n\n## Findings\n\n- renewable energy adoption trends are rising"
    return query, draft, claims, sources, knowledge


async def test_judge_produces_five_scores_in_range() -> None:
    query, draft, claims, sources, knowledge = _fixture()
    judge = Judge(MockGateway())
    scores = await judge.score(query, draft, claims, sources, knowledge)
    assert set(scores.keys()) == set(_SCORE_KEYS)
    for key in _SCORE_KEYS:
        assert 0.0 <= scores[key] <= 1.0


async def test_judge_is_deterministic() -> None:
    query, draft, claims, sources, knowledge = _fixture()
    judge = Judge(MockGateway())
    first = await judge.score(query, draft, claims, sources, knowledge)
    second = await judge.score(query, draft, claims, sources, knowledge)
    assert first == second


async def test_judge_groundedness_tracks_faithfulness() -> None:
    query, draft, claims, sources, knowledge = _fixture()
    judge = Judge(MockGateway())
    scores = await judge.score(query, draft, claims, sources, knowledge)
    assert scores["groundedness"] == scores["faithfulness"]
    assert scores["faithfulness"] > 0.0
    assert scores["completeness"] == 1.0
