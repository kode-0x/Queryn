from __future__ import annotations

import re
from dataclasses import dataclass

_MARKER = "[neutralized-injection]"

_EXFILTRATION = (
    r"(?:print|exfiltrate|send|leak|disclose)\b.*" r"\b(?:api[_ -]?key|secret|token|credentials)"
)

_PATTERNS = [
    re.compile(r"ignore (?:all |any )?(?:the )?previous instructions", re.IGNORECASE),
    re.compile(
        r"disregard (?:all |any )?(?:the )?(?:previous|prior|above) instructions",
        re.IGNORECASE,
    ),
    re.compile(r"you are now\b", re.IGNORECASE),
    re.compile(r"</?(?:system|system-prompt)>", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*(?:override|:)", re.IGNORECASE),
    re.compile(r"reveal (?:your |the )?(?:system )?prompt", re.IGNORECASE),
    re.compile(_EXFILTRATION, re.IGNORECASE),
]


@dataclass
class InjectionScan:
    sanitized: str
    wrapped: str
    count: int
    boundary: str


def _neutralize(text: str) -> tuple[str, int]:
    count = 0
    sanitized = text
    for pattern in _PATTERNS:
        sanitized, replaced = pattern.subn(_MARKER, sanitized)
        count += replaced
    return sanitized, count


def scan(text: str, boundary: str) -> InjectionScan:
    sanitized, count = _neutralize(text)
    wrapped = f"<untrusted>\n{sanitized}\n</untrusted>"
    return InjectionScan(sanitized=sanitized, wrapped=wrapped, count=count, boundary=boundary)


def injection_event(result: InjectionScan) -> dict[str, object]:
    return {
        "type": "injection_neutralized",
        "count": result.count,
        "boundary": result.boundary,
    }
