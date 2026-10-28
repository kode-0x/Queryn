from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

OutputFormat = Literal["markdown", "json", "pdf"]
Termination = Literal["verified", "max_retries_exhausted", "failed"]


class RequestBody(BaseModel):
    topic: str
    session_id: str | None = None
    output_format: OutputFormat = "markdown"
    evaluate: bool = False


class SourceOut(BaseModel):
    id: str
    title: str
    uri: str
    snippet: str
    mock: bool


class ClaimOut(BaseModel):
    text: str
    source_ids: list[str]


class ResearchResult(BaseModel):
    report: str
    output_format: OutputFormat
    sources: list[SourceOut] = Field(default_factory=list)
    claims: list[ClaimOut] = Field(default_factory=list)
    mode: dict[str, str | bool] = Field(default_factory=dict)
    termination: Termination
    cache_hit: bool = False
    scores: dict[str, float] | None = None
