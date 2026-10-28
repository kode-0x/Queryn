from __future__ import annotations

from dataclasses import dataclass, field

from app.gateway.mock import MockGateway
from app.security import injection
from app.security.guardrail_base import Boundary, Guardrail
from app.security.guardrail_local import LocalGuardrail
from red_team.scenarios import SCENARIOS, Scenario

HARNESS_LABEL = "LOCAL ADVERSARIAL HARNESS - NOT PyRIT"


@dataclass
class TurnResult:
    prompt: str
    neutralized_injections: int
    allowed: bool
    reasons: list[str]


@dataclass
class ScenarioResult:
    scenario_id: str
    family: str
    config_under_test: str
    expected_outcome: str
    observed_blocked: bool
    passed: bool
    turns: list[TurnResult] = field(default_factory=list)


@dataclass
class HarnessReport:
    label: str
    results: list[ScenarioResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)


def _run_turn(guardrail: Guardrail, prompt: str, boundary: Boundary) -> TurnResult:
    scan = injection.scan(prompt, boundary)
    decision = guardrail.check(scan.sanitized, boundary)
    return TurnResult(
        prompt=prompt,
        neutralized_injections=scan.count,
        allowed=decision.allowed,
        reasons=decision.reasons,
    )


def run_scenario(scenario: Scenario, guardrail: Guardrail) -> ScenarioResult:
    turns = [_run_turn(guardrail, prompt, scenario.boundary) for prompt in scenario.prompts]
    observed_blocked = any(not turn.allowed for turn in turns)
    if scenario.expected_outcome == "blocked":
        passed = observed_blocked
    else:
        passed = not observed_blocked
    return ScenarioResult(
        scenario_id=scenario.id,
        family=scenario.family,
        config_under_test=scenario.config_under_test,
        expected_outcome=scenario.expected_outcome,
        observed_blocked=observed_blocked,
        passed=passed,
        turns=turns,
    )


def run_harness(
    guardrail: Guardrail | None = None,
    scenarios: list[Scenario] | None = None,
) -> HarnessReport:
    active_guardrail = guardrail or LocalGuardrail()
    _ = MockGateway()
    active_scenarios = scenarios if scenarios is not None else SCENARIOS
    results = [run_scenario(scenario, active_guardrail) for scenario in active_scenarios]
    return HarnessReport(label=HARNESS_LABEL, results=results)
