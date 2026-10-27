from __future__ import annotations

import functools
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.search import search_node
from app.agents.summarize import summarize_node
from app.agents.verify import verify_node
from app.agents.writer import writer_node
from app.gateway.base import LLMGateway
from app.graph.state import ResearchState
from app.search.base import SearchProvider


def route_after_verify(
    state: ResearchState,
) -> Literal["finalize_verified", "finalize_exhausted", "bump_retries"]:
    if state["verified"]:
        return "finalize_verified"
    if state["retries"] >= state["max_retries"]:
        return "finalize_exhausted"
    return "bump_retries"


def bump_retries_node(state: ResearchState) -> dict[str, Any]:
    return {"retries": state["retries"] + 1}


def finalize_verified_node(state: ResearchState) -> dict[str, Any]:
    return {"termination": "verified"}


def finalize_exhausted_node(state: ResearchState) -> dict[str, Any]:
    return {"termination": "max_retries_exhausted"}


def build_graph(
    gateway: LLMGateway, search_provider: SearchProvider
) -> CompiledStateGraph[ResearchState, Any, ResearchState, ResearchState]:
    graph: StateGraph[ResearchState, Any, ResearchState, ResearchState] = StateGraph(ResearchState)

    graph.add_node("search", functools.partial(search_node, provider=search_provider))
    graph.add_node("summarize", functools.partial(summarize_node, gateway=gateway))
    graph.add_node("bump_retries", bump_retries_node)
    graph.add_node("writer", functools.partial(writer_node, gateway=gateway))
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
