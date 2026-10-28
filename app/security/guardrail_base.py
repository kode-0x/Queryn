from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

Boundary = Literal["input", "output"]


@dataclass
class GuardrailDecision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


@runtime_checkable
class Guardrail(Protocol):
    def check(self, text: str, boundary: Boundary) -> GuardrailDecision: ...
