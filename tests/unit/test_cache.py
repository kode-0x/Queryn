from __future__ import annotations

from dataclasses import dataclass, field

from app.config import Settings
from app.memory.cache import SemanticCache
from app.memory.factory import build_cache
from app.memory.ltm_memory import InMemoryLTM


@dataclass
class _Result:
    report: str
    cache_hit: bool = False
    sources: list[str] = field(default_factory=list)


_HIT_A = "large language model evaluation and benchmarking methods across many tasks"
_HIT_B = "large language model evaluation and benchmarking methods across many tasks today"

_BORDER_A = "machine learning model training"
_BORDER_B = "machine learning model training data"


def test_factory_uses_configured_threshold() -> None:
    settings = Settings(QUERYN_CACHE_SIMILARITY_THRESHOLD=0.5)
    cache = build_cache(settings)
    assert cache.threshold == 0.5


def test_hit_above_threshold() -> None:
    cache: SemanticCache[_Result] = SemanticCache(threshold=0.95)
    cache.store(_HIT_A, _Result(report="cached report"))
    hit = cache.lookup(_HIT_B)
    assert hit is not None
    assert hit.cache_hit is True
    assert hit.report == "cached report"


def test_miss_below_threshold() -> None:
    cache: SemanticCache[_Result] = SemanticCache(threshold=0.95)
    cache.store(_BORDER_A, _Result(report="cached report"))
    assert cache.lookup(_BORDER_B) is None


def test_threshold_flips_borderline_pair() -> None:
    strict: SemanticCache[_Result] = SemanticCache(threshold=0.95)
    strict.store(_BORDER_A, _Result(report="r"))
    assert strict.lookup(_BORDER_B) is None

    lenient: SemanticCache[_Result] = SemanticCache(threshold=0.8)
    lenient.store(_BORDER_A, _Result(report="r"))
    flipped = lenient.lookup(_BORDER_B)
    assert flipped is not None
    assert flipped.cache_hit is True


def test_empty_cache_is_miss() -> None:
    cache: SemanticCache[_Result] = SemanticCache(threshold=0.95)
    assert cache.lookup("anything") is None


def test_cache_result_has_no_source_field() -> None:
    cache: SemanticCache[_Result] = SemanticCache(threshold=0.95)
    cache.store(_HIT_A, _Result(report="r"))
    hit = cache.lookup(_HIT_A)
    assert hit is not None
    assert not hasattr(hit, "source")


def test_cache_does_not_pollute_ltm() -> None:
    ltm = InMemoryLTM()
    cache: SemanticCache[_Result] = SemanticCache(threshold=0.95)
    cache.store(_HIT_A, _Result(report="cached report"))
    assert ltm.retrieve(_HIT_A, k=5) == []
