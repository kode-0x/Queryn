from __future__ import annotations

from app.config import Settings
from app.memory.factory import build_ltm
from app.memory.ltm_memory import InMemoryLTM


def test_factory_defaults_to_in_memory_when_database_unset() -> None:
    settings = Settings(DATABASE_URL="")
    ltm = build_ltm(settings)
    assert isinstance(ltm, InMemoryLTM)


def test_store_returns_distinct_ids() -> None:
    ltm = InMemoryLTM()
    first = ltm.store("alpha content", {})
    second = ltm.store("beta content", {})
    assert first != second


def test_top_k_semantic_ordering() -> None:
    ltm = InMemoryLTM()
    ltm.store("quantum computing qubits and entanglement", {"topic": "physics"})
    ltm.store("medieval european agriculture and crop rotation", {"topic": "history"})
    ltm.store("quantum computing error correction codes", {"topic": "physics"})

    results = ltm.retrieve("quantum computing qubits", k=2)
    assert len(results) == 2
    assert "quantum computing" in results[0]["content"]
    assert results[0]["score"] >= results[1]["score"]


def test_retrieve_respects_filters() -> None:
    ltm = InMemoryLTM()
    ltm.store("quantum computing qubits", {"topic": "physics"})
    ltm.store("quantum computing qubits history", {"topic": "history"})

    results = ltm.retrieve("quantum computing qubits", k=5, filters={"topic": "history"})
    assert len(results) == 1
    assert results[0]["metadata"]["topic"] == "history"


def test_retrieve_k_limits_results() -> None:
    ltm = InMemoryLTM()
    for i in range(5):
        ltm.store(f"record number {i}", {})
    assert len(ltm.retrieve("record number", k=3)) == 3
