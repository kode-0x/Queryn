from __future__ import annotations

from app.api.schemas import ResearchResult


def render_json(result: ResearchResult) -> str:
    return result.model_dump_json(indent=2)
