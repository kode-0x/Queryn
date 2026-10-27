from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict


class Source(TypedDict):
    id: str
    title: str
    uri: str
    snippet: str
    mock: bool


class Finding(TypedDict):
    source_id: str
    content: str
    relevance: float


class KnowledgePoint(TypedDict):
    statement: str
    source_ids: list[str]


class Claim(TypedDict):
    text: str
    source_ids: list[str]


class VerifyFinding(TypedDict):
    claim_index: int
    status: Literal["supported", "unsupported", "contradicted"]
    note: str


class ProviderCall(TypedDict):
    agent: str
    provider: str
    outcome: str
    fallback_used: bool


class ResearchState(TypedDict, total=False):
    query: str
    mode: dict[str, str | bool]
    sources: Annotated[list[Source], operator.add]
    findings: list[Finding]
    knowledge: list[KnowledgePoint]
    draft: str
    claims: list[Claim]
    verify_findings: list[VerifyFinding]
    verified: bool
    retries: int
    max_retries: int
    termination: Literal["verified", "max_retries_exhausted", "failed"] | None
    provider_calls: Annotated[list[ProviderCall], operator.add]
    error: str | None
