from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from langgraph.errors import GraphRecursionError

from app.config import Settings
from app.gateway.base import LLMGateway
from app.graph.build import build_graph
from app.graph.state import Claim, ProviderCall, ResearchState, Source, VerifyFinding
from app.search.base import SearchProvider


@dataclass
class RunResult:
    query: str
    report: str
    sources: list[Source]
    claims: list[Claim]
    verify_findings: list[VerifyFinding]
    verified: bool
    termination: str
    mode: dict[str, str | bool]
    provider_calls: list[ProviderCall] = field(default_factory=list)


class ResearchRunner:
    def __init__(
        self,
        settings: Settings,
        gateway: LLMGateway,
        search_provider: SearchProvider,
        mode: dict[str, str | bool],
    ) -> None:
        self._settings = settings
        self._mode = mode
        self._graph = build_graph(gateway, search_provider)
        self._recursion_limit = 5 + 3 * settings.max_verify_retries + 2

    async def run(self, query: str, mode: dict[str, str | bool] | None = None) -> RunResult:
        resolved_mode = mode if mode is not None else self._mode
        initial: ResearchState = {
            "query": query,
            "mode": resolved_mode,
            "retries": 0,
            "max_retries": self._settings.max_verify_retries,
            "verified": False,
        }
        final: ResearchState
        try:
            raw = await self._graph.ainvoke(
                initial, config={"recursion_limit": self._recursion_limit}
            )
            final = cast(ResearchState, raw)
            termination = final.get("termination") or "failed"
        except GraphRecursionError:
            final = initial
            termination = "failed"
        return self._to_result(query, resolved_mode, final, termination)

    def _to_result(
        self,
        query: str,
        mode: dict[str, str | bool],
        state: ResearchState,
        termination: str,
    ) -> RunResult:
        return RunResult(
            query=query,
            report=state.get("draft", ""),
            sources=list(state.get("sources", [])),
            claims=list(state.get("claims", [])),
            verify_findings=list(state.get("verify_findings", [])),
            verified=bool(state.get("verified", False)),
            termination=termination,
            mode=mode,
            provider_calls=list(state.get("provider_calls", [])),
        )
