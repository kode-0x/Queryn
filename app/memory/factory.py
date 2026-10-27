from __future__ import annotations

from typing import Any

from app.config import Settings, resolve_modes
from app.memory.cache import CacheableResult, SemanticCache
from app.memory.ltm_base import LongTermMemory
from app.memory.ltm_memory import InMemoryLTM
from app.memory.stm_base import ShortTermMemory
from app.memory.stm_memory import InMemorySTM
from app.observability.logging import get_logger

_logger = get_logger("queryn.memory.factory")


def build_stm(settings: Settings) -> ShortTermMemory:
    modes = resolve_modes(settings)
    if modes["stm"] == "redis":
        from app.memory.stm_redis import RedisSTM

        try:
            return RedisSTM.connect(settings.redis_url, InMemorySTM())
        except Exception as exc:
            _logger.warning(
                "redis_stm_unavailable",
                extra={
                    "extra_fields": {
                        "event": "redis_stm_unavailable",
                        "error": type(exc).__name__,
                    }
                },
            )
    return InMemorySTM()


def build_ltm(settings: Settings) -> LongTermMemory:
    modes = resolve_modes(settings)
    if modes["ltm"] == "pgvector":
        from app.memory.ltm_pgvector import PgVectorLTM

        try:
            return PgVectorLTM.connect(settings.database_url, InMemoryLTM())
        except Exception as exc:
            _logger.warning(
                "pgvector_ltm_unavailable",
                extra={
                    "extra_fields": {
                        "event": "pgvector_ltm_unavailable",
                        "error": type(exc).__name__,
                    }
                },
            )
    return InMemoryLTM()


def build_cache(settings: Settings) -> SemanticCache[Any]:
    return SemanticCache[CacheableResult](threshold=settings.cache_similarity_threshold)
