from __future__ import annotations

import importlib
from typing import Any

from app.memory.stm_base import ShortTermMemory
from app.memory.stm_memory import InMemorySTM
from app.observability.logging import get_logger

_logger = get_logger("queryn.memory.stm")


def _namespaced(session_id: str, key: str) -> str:
    return f"queryn:stm:{session_id}:{key}"


class RedisSTM:
    def __init__(self, url: str, fallback: ShortTermMemory | None = None) -> None:
        redis = importlib.import_module("redis")
        self._client: Any = redis.Redis.from_url(url, decode_responses=True)
        self._fallback = fallback or InMemorySTM()

    @classmethod
    def connect(cls, url: str, fallback: ShortTermMemory | None = None) -> RedisSTM:
        instance = cls(url, fallback)
        instance._client.ping()
        return instance

    def _warn(self, operation: str, exc: Exception) -> None:
        _logger.warning(
            "redis_stm_fallback",
            extra={
                "extra_fields": {
                    "event": "redis_stm_fallback",
                    "operation": operation,
                    "error": type(exc).__name__,
                }
            },
        )

    def get(self, session_id: str, key: str) -> str | None:
        try:
            value = self._client.get(_namespaced(session_id, key))
        except Exception as exc:
            self._warn("get", exc)
            return self._fallback.get(session_id, key)
        if value is None:
            return None
        return str(value)

    def set(self, session_id: str, key: str, value: str, ttl_seconds: int | None = None) -> None:
        try:
            self._client.set(_namespaced(session_id, key), value, ex=ttl_seconds)
        except Exception as exc:
            self._warn("set", exc)
            self._fallback.set(session_id, key, value, ttl_seconds)

    def delete(self, session_id: str, key: str) -> None:
        try:
            self._client.delete(_namespaced(session_id, key))
        except Exception as exc:
            self._warn("delete", exc)
            self._fallback.delete(session_id, key)
