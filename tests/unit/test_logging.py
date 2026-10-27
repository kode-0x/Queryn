from __future__ import annotations

import json
import logging

from app.observability.logging import JsonFormatter, RedactionFilter


def _make_record(msg: str, extra_fields: dict | None = None) -> logging.LogRecord:
    record = logging.LogRecord(
        name="queryn.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=None,
        exc_info=None,
    )
    if extra_fields is not None:
        record.extra_fields = extra_fields
    return record


def test_redaction_masks_secret_keyed_fields() -> None:
    flt = RedactionFilter()
    record = _make_record(
        "startup",
        {
            "openrouter_api_key": "placeholder",
            "database_url": "postgresql://u:p@host/db",
            "redis_url": "redis://host:6379",
            "session_token": "abc",
            "password": "hunter2",
            "authorization": "Bearer xyz",
            "mode": "mock",
        },
    )
    flt.filter(record)

    fields = record.extra_fields
    assert fields["openrouter_api_key"] == "[REDACTED]"
    assert fields["database_url"] == "[REDACTED]"
    assert fields["redis_url"] == "[REDACTED]"
    assert fields["session_token"] == "[REDACTED]"
    assert fields["password"] == "[REDACTED]"
    assert fields["authorization"] == "[REDACTED]"
    assert fields["mode"] == "mock"


def test_redaction_masks_sk_shaped_values() -> None:
    flt = RedactionFilter()
    secret = "sk-" + "A1b2C3d4E5f6G7h8I9j0"
    record = _make_record(f"leaked {secret} here")
    flt.filter(record)
    assert secret not in record.msg
    assert "[REDACTED]" in record.msg


def test_redaction_masks_sk_shaped_values_in_extra() -> None:
    flt = RedactionFilter()
    secret = "sk-" + "A1b2C3d4E5f6G7h8I9j0"
    record = _make_record("event", {"note": f"token is {secret}"})
    flt.filter(record)
    assert secret not in record.extra_fields["note"]
    assert "[REDACTED]" in record.extra_fields["note"]


def test_json_formatter_emits_valid_json_with_extra_fields() -> None:
    formatter = JsonFormatter()
    record = _make_record("hello", {"mode": "mock", "count": 3})
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["message"] == "hello"
    assert parsed["level"] == "INFO"
    assert parsed["mode"] == "mock"
    assert parsed["count"] == 3
