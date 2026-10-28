from __future__ import annotations

import pytest

from app.graph.state import Claim, Source
from app.security.validation import (
    InputValidationError,
    OutputIntegrityError,
    redact_secrets,
    validate_input,
    validate_output,
)


def test_topic_trimmed_and_control_chars_stripped() -> None:
    result = validate_input("  hello\x00world  ")
    assert result.topic == "helloworld"
    assert result.output_format == "markdown"
    assert result.session_id is None


def test_empty_topic_rejected() -> None:
    with pytest.raises(InputValidationError) as exc:
        validate_input("   ")
    assert exc.value.field == "topic"


def test_topic_too_long_rejected() -> None:
    with pytest.raises(InputValidationError):
        validate_input("a" * 2001)


def test_session_id_pattern_enforced() -> None:
    assert validate_input("t", session_id="abc_DEF-123").session_id == "abc_DEF-123"
    with pytest.raises(InputValidationError) as exc:
        validate_input("t", session_id="bad id!")
    assert exc.value.field == "session_id"


def test_output_format_enum_enforced() -> None:
    assert validate_input("t", output_format="json").output_format == "json"
    with pytest.raises(InputValidationError) as exc:
        validate_input("t", output_format="xml")
    assert exc.value.field == "output_format"


def test_output_validation_fails_on_unknown_source_id() -> None:
    sources: list[Source] = [{"id": "s1", "title": "", "uri": "", "snippet": "", "mock": True}]
    claims: list[Claim] = [{"text": "x", "source_ids": ["s2"]}]
    with pytest.raises(OutputIntegrityError):
        validate_output("report", claims, sources)


def test_output_validation_passes_on_known_source_id() -> None:
    sources: list[Source] = [{"id": "s1", "title": "", "uri": "", "snippet": "", "mock": True}]
    claims: list[Claim] = [{"text": "x", "source_ids": ["s1"]}]
    validate_output("report", claims, sources)


def test_empty_report_rejected() -> None:
    with pytest.raises(OutputIntegrityError):
        validate_output("   ", [], [])


def test_secret_denylist_replaces_live_value_and_sk_pattern() -> None:
    secret = "sk-" + "A1b2C3d4E5f6G7h8I9j0"
    text = f"report with {secret} and live-abc123"
    redacted = redact_secrets(text, live_secrets=["live-abc123"])
    assert secret not in redacted
    assert "live-abc123" not in redacted
    assert redacted.count("[REDACTED]") == 2


def test_secret_denylist_noop_offline() -> None:
    text = "a clean report with no secrets"
    assert redact_secrets(text, live_secrets=[]) == text
