from __future__ import annotations

import re
from typing import Any

from app.graph.state import Claim, ResearchState, Source, VerifyFinding

_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")
_SUPPORT_THRESHOLD = 0.5


def tokens(s: str) -> set[str]:
    return {t for t in _TOKEN_SPLIT.split(s.lower()) if t}


def containment(text: str, reference: str) -> float:
    text_tokens = tokens(text)
    if not text_tokens:
        return 0.0
    reference_tokens = tokens(reference)
    return len(text_tokens & reference_tokens) / len(text_tokens)


def _sources_by_id(sources: list[Source]) -> dict[str, Source]:
    return {source["id"]: source for source in sources}


def _claim_status(claim: Claim, index_by_id: dict[str, Source]) -> VerifyFinding:
    resolving = [index_by_id[sid] for sid in claim["source_ids"] if sid in index_by_id]
    if not resolving:
        return VerifyFinding(
            claim_index=0,
            status="unsupported",
            note="no resolving source",
        )
    best = max(containment(claim["text"], source["snippet"]) for source in resolving)
    if best >= _SUPPORT_THRESHOLD:
        return VerifyFinding(claim_index=0, status="supported", note="")
    return VerifyFinding(
        claim_index=0,
        status="unsupported",
        note="containment below threshold",
    )


def verify_node(state: ResearchState) -> dict[str, Any]:
    sources = state.get("sources", [])
    claims = state.get("claims", [])
    index_by_id = _sources_by_id(sources)
    findings: list[VerifyFinding] = []
    verified = True
    for position, claim in enumerate(claims):
        finding = _claim_status(claim, index_by_id)
        finding["claim_index"] = position
        findings.append(finding)
        if finding["status"] != "supported":
            verified = False
    if not claims:
        verified = False
    return {"verify_findings": findings, "verified": verified}
