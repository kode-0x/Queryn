from __future__ import annotations

from app.graph.build import bump_retries_node, route_after_verify
from app.graph.state import ResearchState


def test_route_on_seeded_initial_state_raises_no_keyerror() -> None:
    state: ResearchState = {
        "query": "q",
        "mode": {},
        "retries": 0,
        "max_retries": 2,
        "verified": False,
    }
    assert route_after_verify(state) == "bump_retries"


def test_route_verified_finalizes() -> None:
    state: ResearchState = {"verified": True, "retries": 0, "max_retries": 2}
    assert route_after_verify(state) == "finalize_verified"


def test_route_exhausted_when_retries_reach_max() -> None:
    state: ResearchState = {"verified": False, "retries": 2, "max_retries": 2}
    assert route_after_verify(state) == "finalize_exhausted"


def test_bump_retries_increments() -> None:
    assert bump_retries_node({"retries": 1}) == {"retries": 2}
