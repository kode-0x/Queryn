from __future__ import annotations

import functools

from langgraph.graph import END, START, StateGraph

from app.agents.search import search_node
from app.agents.summarize import summarize_node
from app.agents.verify import verify_node
from app.config import Settings
from app.gateway.mock import MockGateway
from app.graph.build import (
    bump_retries_node,
    finalize_exhausted_node,
    finalize_verified_node,
    route_after_verify,
)
from app.graph.runner import ResearchRunner
from app.graph.state import ResearchState
from app.search.mock import MockSearchProvider


def _mode() -> dict[str, str | bool]:
    return {"llm": "mock", "stm": "memory", "ltm": "memory"}


async def test_normal_offline_run_terminates_verified_with_attribution() -> None:
    settings = Settings()
    runner = ResearchRunner(settings, MockGateway(), MockSearchProvider(), _mode())
    result = await runner.run("sustainable urban transport")

    assert result.termination == "verified"
    assert result.verified is True
    assert len(result.sources) >= 1
    for source in result.sources:
        assert source["mock"] is True
        assert source["uri"].startswith("mock://")
        assert "[SIMULATED SOURCE]" in source["snippet"]
    assert result.claims
    source_ids = {s["id"] for s in result.sources}
    for claim in result.claims:
        assert claim["source_ids"]
        assert all(sid in source_ids for sid in claim["source_ids"])


def _disjoint_writer_node(state: ResearchState) -> dict:
    claims = [{"text": "zzz qqq", "source_ids": [s["id"]]} for s in state.get("sources", [])]
    return {"draft": "# forced", "claims": claims}


def _build_forced_graph(max_retries: int):
    graph: StateGraph = StateGraph(ResearchState)
    graph.add_node("search", functools.partial(search_node, provider=MockSearchProvider()))
    graph.add_node("summarize", functools.partial(summarize_node, gateway=MockGateway()))
    graph.add_node("bump_retries", bump_retries_node)
    graph.add_node("writer", _disjoint_writer_node)
    graph.add_node("verify", verify_node)
    graph.add_node("finalize_verified", finalize_verified_node)
    graph.add_node("finalize_exhausted", finalize_exhausted_node)
    graph.add_edge(START, "search")
    graph.add_edge("search", "summarize")
    graph.add_edge("summarize", "writer")
    graph.add_edge("writer", "verify")
    graph.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "finalize_verified": "finalize_verified",
            "finalize_exhausted": "finalize_exhausted",
            "bump_retries": "bump_retries",
        },
    )
    graph.add_edge("bump_retries", "writer")
    graph.add_edge("finalize_verified", END)
    graph.add_edge("finalize_exhausted", END)
    return graph.compile()


async def test_forced_disjoint_run_exhausts_after_max_retries() -> None:
    max_retries = 2
    compiled = _build_forced_graph(max_retries)
    initial: ResearchState = {
        "query": "deterministic exhaustion fixture",
        "mode": _mode(),
        "retries": 0,
        "max_retries": max_retries,
        "verified": False,
    }
    final = await compiled.ainvoke(initial, config={"recursion_limit": 5 + 3 * max_retries + 2})
    assert final["termination"] == "max_retries_exhausted"
    assert final["retries"] == max_retries
    assert final["verified"] is False
