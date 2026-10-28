from __future__ import annotations

from app.eval.tracing_local import LocalTracer
from app.eval.tracing_noop import NoopTracer


def test_local_tracer_captures_order_and_outcome() -> None:
    tracer = LocalTracer()
    tracer.start_run("research", {"mode": {"llm": "mock"}})
    tracer.record_event({"agent": "search", "provider": "mock", "mode": "mock"})
    tracer.record_event({"agent": "summarize", "provider": "mock", "mode": "mock"})
    tracer.record_event({"type": "fallback", "agent": "writer", "fallback_used": True})
    tracer.end_run("verified")

    events = tracer.events
    agents = [e.get("agent") for e in events if "agent" in e]
    assert agents == ["search", "summarize", "writer"]
    assert any(e.get("type") == "fallback" for e in events)
    assert tracer.outcome == "verified"


def test_local_tracer_records_no_secret_values() -> None:
    secret = "sk-" + "A1b2C3d4E5f6G7h8I9j0"
    tracer = LocalTracer()
    tracer.start_run("research")
    tracer.record_event({"agent": "writer", "provider": "mock"})
    tracer.end_run("verified")
    assert secret not in str(tracer.events)


def test_noop_tracer_is_inert() -> None:
    tracer = NoopTracer()
    assert tracer.start_run("x") is None
    assert tracer.record_event({"a": 1}) is None
    assert tracer.end_run("verified") is None
