from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.rate_limit import TokenBucketLimiter
from app.api.routes import Collaborators, router
from app.api.schemas import ResearchResult
from app.config import get_settings, resolve_modes
from app.eval.factory import build_tracer
from app.eval.judge import Judge
from app.gateway.factory import build_gateway
from app.graph.runner import ResearchRunner
from app.memory.cache import SemanticCache
from app.observability.logging import configure_logging, get_logger
from app.search.mock import MockSearchProvider

_logger = get_logger("queryn.main")


def _build_collaborators() -> Collaborators:
    settings = get_settings()
    modes = resolve_modes(settings)
    gateway = build_gateway(settings)
    search_provider = MockSearchProvider()
    runner = ResearchRunner(settings, gateway, search_provider, modes)
    from app.security.factory import build_guardrail

    guardrail = build_guardrail(settings)
    cache: SemanticCache[ResearchResult] = SemanticCache[ResearchResult](
        threshold=settings.cache_similarity_threshold
    )
    tracer = build_tracer(settings)
    judge = Judge(gateway)
    limiter = TokenBucketLimiter(
        rate=settings.rate_limit_per_minute / 60.0,
        capacity=settings.rate_limit_per_minute,
    )
    return Collaborators(
        settings=settings,
        modes=modes,
        runner=runner,
        guardrail=guardrail,
        cache=cache,
        tracer=tracer,
        judge=judge,
        limiter=limiter,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    collaborators = _build_collaborators()
    app.state.collaborators = collaborators
    app.state.api_key = collaborators.settings.api_key
    _logger.info(
        "startup",
        extra={"extra_fields": {"event": "startup", "modes": collaborators.modes}},
    )
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="Queryn", lifespan=lifespan)
    application.include_router(router)
    return application


app = create_app()
