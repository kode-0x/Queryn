from __future__ import annotations

import re
from dataclasses import dataclass

from app.graph.state import Claim, Source

_TOPIC_MIN = 1
_TOPIC_MAX = 2000
_SESSION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_OUTPUT_FORMATS = ("markdown", "json", "pdf")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")
_SECRET_VALUE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")
_REDACTED = "[REDACTED]"


class InputValidationError(Exception):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


class OutputIntegrityError(Exception):
    pass


@dataclass
class ValidatedInput:
    topic: str
    session_id: str | None
    output_format: str


def _strip_control(value: str) -> str:
    return _CONTROL_CHARS.sub("", value)


def validate_topic(topic: object) -> str:
    if not isinstance(topic, str):
        raise InputValidationError("topic", "topic must be a string")
    cleaned = _strip_control(topic).strip()
    if _WHITESPACE.sub("", cleaned) == "":
        raise InputValidationError("topic", "topic must not be empty or whitespace")
    if len(cleaned) < _TOPIC_MIN or len(cleaned) > _TOPIC_MAX:
        raise InputValidationError(
            "topic", f"topic length must be between {_TOPIC_MIN} and {_TOPIC_MAX} characters"
        )
    return cleaned


def validate_session_id(session_id: object) -> str | None:
    if session_id is None:
        return None
    if not isinstance(session_id, str) or not _SESSION_PATTERN.match(session_id):
        raise InputValidationError("session_id", "session_id must match ^[A-Za-z0-9_-]{1,64}$")
    return session_id


def validate_output_format(output_format: object) -> str:
    if output_format is None:
        return "markdown"
    if not isinstance(output_format, str) or output_format not in _OUTPUT_FORMATS:
        raise InputValidationError(
            "output_format", "output_format must be one of markdown, json, pdf"
        )
    return output_format


def validate_input(
    topic: object,
    session_id: object = None,
    output_format: object = None,
) -> ValidatedInput:
    return ValidatedInput(
        topic=validate_topic(topic),
        session_id=validate_session_id(session_id),
        output_format=validate_output_format(output_format),
    )


def validate_attribution_integrity(claims: list[Claim], sources: list[Source]) -> None:
    source_ids = {source["id"] for source in sources}
    for claim in claims:
        for source_id in claim["source_ids"]:
            if source_id not in source_ids:
                raise OutputIntegrityError(
                    "claim references a source id absent from produced sources"
                )


def validate_output(report: str, claims: list[Claim], sources: list[Source]) -> None:
    if not report or not report.strip():
        raise OutputIntegrityError("report must not be empty")
    validate_attribution_integrity(claims, sources)


def redact_secrets(report: str, live_secrets: list[str] | None = None) -> str:
    result = report
    for secret in live_secrets or []:
        if secret:
            result = result.replace(secret, _REDACTED)
    return _SECRET_VALUE_PATTERN.sub(_REDACTED, result)
