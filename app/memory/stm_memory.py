from __future__ import annotations

import time


class InMemorySTM:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, tuple[str, float | None]]] = {}

    def _session(self, session_id: str) -> dict[str, tuple[str, float | None]]:
        return self._store.setdefault(session_id, {})

    def get(self, session_id: str, key: str) -> str | None:
        session = self._store.get(session_id)
        if session is None:
            return None
        entry = session.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() >= expires_at:
            del session[key]
            return None
        return value

    def set(self, session_id: str, key: str, value: str, ttl_seconds: int | None = None) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds is not None else None
        self._session(session_id)[key] = (value, expires_at)

    def delete(self, session_id: str, key: str) -> None:
        session = self._store.get(session_id)
        if session is not None:
            session.pop(key, None)
