from __future__ import annotations

import pytest

from app.config import Settings
from app.memory.factory import build_stm
from app.memory.stm_memory import InMemorySTM


def test_factory_defaults_to_in_memory_when_redis_unset() -> None:
    settings = Settings(REDIS_URL="")
    stm = build_stm(settings)
    assert isinstance(stm, InMemorySTM)


def test_session_isolation() -> None:
    stm = InMemorySTM()
    stm.set("session-a", "k", "value-a")
    assert stm.get("session-b", "k") is None
    assert stm.get("session-a", "k") == "value-a"


def test_set_get_delete_roundtrip() -> None:
    stm = InMemorySTM()
    stm.set("s", "k", "v")
    assert stm.get("s", "k") == "v"
    stm.delete("s", "k")
    assert stm.get("s", "k") is None


def test_ttl_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    now = {"t": 1000.0}
    monkeypatch.setattr("app.memory.stm_memory.time.monotonic", lambda: now["t"])
    stm = InMemorySTM()
    stm.set("s", "k", "v", ttl_seconds=10)
    assert stm.get("s", "k") == "v"
    now["t"] = 1009.0
    assert stm.get("s", "k") == "v"
    now["t"] = 1011.0
    assert stm.get("s", "k") is None


def test_missing_session_returns_none() -> None:
    stm = InMemorySTM()
    assert stm.get("absent", "k") is None
    stm.delete("absent", "k")
