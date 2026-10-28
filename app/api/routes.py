from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.auth import require_api_key
from app.api.rate_limit import TokenBucketLimiter, client_key
from app.api.schemas import (
    ClaimOut,
    OutputFormat,
    RequestBody,
    ResearchResult,
    SourceOut,
    Termination,
)
from app.config import Settings
from app.eval.judge import Judge
from app.eval.tracing_base import Tracer
from app.graph.runner import ResearchRunner
from app.memory.cache import SemanticCache
from app.observability.logging import get_logger
from app.output.factory import render_pdf_bytes, render_report
from app.security import injection
from app.security.guardrail_base import Guardrail
from app.security.validation import (
    InputValidationError,
    OutputIntegrityError,
    redact_secrets,
    validate_input,
    validate_output,
)

_logger = get_logger("queryn.api.routes")

_REFUSAL = "This request was blocked by the content guardrail and cannot be fulfilled."


@dataclass
class Collaborators:
    settings: Settings
    modes: dict[str, str | bool]
    runner: ResearchRunner
    guardrail: Guardrail
    cache: SemanticCache[ResearchResult]
    tracer: Tracer
    judge: Judge
    limiter: TokenBucketLimiter


def _collaborators(request: Request) -> Collaborators:
    collaborators = getattr(request.app.state, "collaborators", None)
    if collaborators is None:
        raise HTTPException(status_code=500, detail="application not initialized")
    return collaborators


def _to_result(
    report: str,
    output_format: str,
    sources: list[dict[str, object]],
    claims: list[dict[str, object]],
    modes: dict[str, str | bool],
    termination: str,
    scores: dict[str, float] | None,
) -> ResearchResult:
    return ResearchResult(
        report=report,
        output_format=cast(OutputFormat, output_format),
        sources=[SourceOut.model_validate(source) for source in sources],
        claims=[ClaimOut.model_validate(claim) for claim in claims],
        mode=modes,
        termination=cast(Termination, termination),
        cache_hit=False,
        scores=scores,
    )


router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    collaborators = _collaborators(request)
    return {"status": "ok", "modes": collaborators.modes}


@router.post("/research")
async def research(
    request: Request,
    body: RequestBody,
    _auth: None = Depends(require_api_key),
) -> Response:
    collaborators = _collaborators(request)
    client_host = request.client.host if request.client else None
    key = client_key(client_host, request.headers.get("X-API-Key"))
    if not collaborators.limiter.allow(key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate limited")

    pdf_enabled = bool(collaborators.modes.get("pdf_enabled", False))

    try:
        validated = validate_input(body.topic, body.session_id, body.output_format)
    except InputValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"field": exc.field, "message": exc.message},
        ) from exc

    if validated.output_format == "pdf" and not pdf_enabled:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="pdf output is disabled in this deployment",
        )

    collaborators.tracer.start_run("research", {"mode": collaborators.modes})

    scan = injection.scan(validated.topic, "input")
    if scan.count:
        collaborators.tracer.record_event(injection.injection_event(scan))

    input_decision = collaborators.guardrail.check(validated.topic, "input")
    if not input_decision.allowed:
        collaborators.tracer.record_event(
            {"type": "guardrail_block", "boundary": "input", "reasons": input_decision.reasons}
        )
        collaborators.tracer.end_run("blocked_input")
        result = _to_result(
            _REFUSAL, validated.output_format, [], [], collaborators.modes, "failed", None
        )
        return _respond(result, pdf_enabled)

    cached = collaborators.cache.lookup(validated.topic)
    if cached is not None:
        cached.output_format = cast(OutputFormat, validated.output_format)
        collaborators.tracer.record_event({"type": "cache_hit"})
        collaborators.tracer.end_run("cache_hit")
        return _respond(cached, pdf_enabled)

    run = await collaborators.runner.run(validated.topic, collaborators.modes)

    output_decision = collaborators.guardrail.check(run.report, "output")
    if not output_decision.allowed:
        collaborators.tracer.record_event(
            {"type": "guardrail_block", "boundary": "output", "reasons": output_decision.reasons}
        )
        collaborators.tracer.end_run("blocked_output")
        result = _to_result(
            _REFUSAL, validated.output_format, [], [], collaborators.modes, run.termination, None
        )
        return _respond(result, pdf_enabled)

    report = redact_secrets(run.report, [collaborators.settings.openrouter_api_key])

    try:
        validate_output(report, run.claims, run.sources)
    except OutputIntegrityError as exc:
        _logger.error(
            "output_integrity_violation",
            extra={"extra_fields": {"event": "output_integrity_violation"}},
        )
        collaborators.tracer.end_run("integrity_error")
        raise HTTPException(status_code=500, detail="internal error") from exc

    scores: dict[str, float] | None = None
    if body.evaluate:
        scores = await collaborators.judge.score(
            validated.topic,
            report,
            run.claims,
            run.sources,
            [],
        )

    result = _to_result(
        report,
        validated.output_format,
        [dict(s) for s in run.sources],
        [dict(c) for c in run.claims],
        collaborators.modes,
        run.termination,
        scores,
    )
    collaborators.cache.store(validated.topic, result)
    collaborators.tracer.end_run(run.termination)
    return _respond(result, pdf_enabled)


def _respond(result: ResearchResult, pdf_enabled: bool) -> Response:
    if result.output_format == "pdf":
        payload = render_pdf_bytes(result, pdf_enabled)
        return Response(content=payload, media_type="application/pdf")
    if result.output_format == "markdown":
        rendered = result.model_copy()
        rendered.report = render_report(result, pdf_enabled)
        return JSONResponse(content=rendered.model_dump())
    return JSONResponse(content=result.model_dump())
