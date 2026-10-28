from __future__ import annotations

import functools
from typing import cast

from app.agents.search import search_node
from app.agents.summarize import summarize_node
from app.agents.verify import containment, tokens, verify_node
from app.agents.writer import writer_node
from app.gateway.mock import MockGateway
from app.graph.state import ResearchState
from app.search.mock import MockSearchProvider


def test_tokens_splits_and_lowercases() -> None:
    assert tokens("Hello, World! 42") == {"hello", "world", "42"}


def test_containment_boundary() -> None:
    assert containment("alpha beta", "alpha beta gamma") == 1.0
    assert containment("alpha beta", "alpha") == 0.5
    assert containment("alpha beta", "gamma") == 0.0


def test_containment_empty_text_is_zero() -> None:
    assert containment("", "anything") == 0.0


async def test_search_node_produces_mock_labeled_sources() -> None:
    node = functools.partial(search_node, provider=MockSearchProvider())
    out = await node({"query": "quantum computing basics"})
    assert out["sources"]
    for source in out["sources"]:
        assert source["mock"] is True
        assert source["uri"].startswith("mock://")
        assert "[SIMULATED SOURCE]" in source["snippet"]


async def test_normal_pipeline_slice_verifies() -> None:
    query = "renewable energy storage"
    search = functools.partial(search_node, provider=MockSearchProvider())
    summarize = functools.partial(summarize_node, gateway=MockGateway())
    writer = functools.partial(writer_node, gateway=MockGateway())

    state: ResearchState = {"query": query}
    state.update(cast(ResearchState, await search(state)))
    state.update(cast(ResearchState, await summarize(state)))
    state.update(cast(ResearchState, await writer(state)))
    result = verify_node(state)

    assert result["verified"] is True
    assert all(f["status"] == "supported" for f in result["verify_findings"])


async def test_disjoint_claims_fail_verification() -> None:
    state: ResearchState = {
        "sources": [
            {
                "id": "mock-1",
                "title": "t",
                "uri": "mock://1",
                "snippet": "[SIMULATED SOURCE] alpha beta",
                "mock": True,
            }
        ],
        "claims": [{"text": "zzz qqq", "source_ids": ["mock-1"]}],
    }
    result = verify_node(state)
    assert result["verified"] is False
    assert result["verify_findings"][0]["status"] == "unsupported"
