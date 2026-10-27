from __future__ import annotations

import json
import logging
import re
from typing import Any

_SECRET_KEY_PATTERN = re.compile(
    r"(.*_api_key|.*_token|password|authorization|database_url|redis_url)$",
    re.IGNORECASE,
)
_SECRET_VALUE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")
_REDACTED = "[REDACTED]"


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return _SECRET_VALUE_PATTERN.sub(_REDACTED, value)
    if isinstance(value, dict):
        return _redact_mapping(value)
    if isinstance(value, list | tuple):
        return [_redact_value(item) for item in value]
    return value


def _redact_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(key, str) and _SECRET_KEY_PATTERN.match(key):
            redacted[key] = _REDACTED
        else:
            redacted[key] = _redact_value(value)
    return redacted


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SECRET_VALUE_PATTERN.sub(_REDACTED, record.msg)
        if isinstance(record.args, dict):
            record.args = _redact_mapping(record.args)
        elif isinstance(record.args, tuple):
            record.args = tuple(_redact_value(arg) for arg in record.args)
        extra = record.__dict__.get("extra_fields")
        if isinstance(extra, dict):
            record.__dict__["extra_fields"] = _redact_mapping(extra)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, default=str, sort_keys=True)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactionFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not any(isinstance(f, RedactionFilter) for f in logger.filters):
        logger.addFilter(RedactionFilter())
    return logger
