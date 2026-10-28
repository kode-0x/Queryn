from __future__ import annotations

import re

from app.security.guardrail_base import Boundary, GuardrailDecision

_IGNORE_INSTRUCTIONS = r"ignore (?:all |any )?(?:the )?previous instructions"
_EXFILTRATION = (
    r"(?:print|exfiltrate|send|leak|disclose)\b.*" r"\b(?:api[_ -]?key|secret|token|credentials)"
)
_WEAPONS = r"\b(?:build|make|create)\b.*\b(?:bomb|explosive|biological weapon)\b"
_SELF_HARM = r"\bhow to (?:kill|harm) (?:myself|yourself)\b"

_UNSAFE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("injection", re.compile(_IGNORE_INSTRUCTIONS, re.IGNORECASE)),
    ("injection", re.compile(r"\[neutralized-injection\]")),
    ("prompt_override", re.compile(r"you are now\b", re.IGNORECASE)),
    ("secret_exfiltration", re.compile(_EXFILTRATION, re.IGNORECASE)),
    ("weapons", re.compile(_WEAPONS, re.IGNORECASE)),
    ("self_harm", re.compile(_SELF_HARM, re.IGNORECASE)),
]


class LocalGuardrail:
    def check(self, text: str, boundary: Boundary) -> GuardrailDecision:
        reasons = sorted(
            {category for category, pattern in _UNSAFE_PATTERNS if pattern.search(text)}
        )
        return GuardrailDecision(allowed=not reasons, reasons=reasons)
