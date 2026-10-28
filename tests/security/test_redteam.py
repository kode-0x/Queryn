from __future__ import annotations

import pytest

from app.security.guardrail_local import LocalGuardrail
from red_team.harness import HARNESS_LABEL, run_harness, run_scenario
from red_team.pyrit_runner import pyrit_available
from red_team.scenarios import SCENARIOS, scenarios_by_family

_FAMILIES = {"jailbreak", "xpia", "crescendo", "skeleton_key"}


def test_all_attack_families_present() -> None:
    assert set(scenarios_by_family().keys()) == _FAMILIES


def test_harness_is_labeled_not_pyrit() -> None:
    report = run_harness()
    assert report.label == HARNESS_LABEL
    assert "NOT PyRIT" in report.label


def test_harness_blocks_labeled_unsafe_scenarios() -> None:
    report = run_harness(LocalGuardrail())
    assert report.results
    for result in report.results:
        assert result.observed_blocked is True
        assert result.passed is True
    assert report.passed is True


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
def test_each_scenario_records_config_response_and_outcome(scenario) -> None:  # type: ignore[no-untyped-def]
    result = run_scenario(scenario, LocalGuardrail())
    assert result.config_under_test
    assert result.turns
    assert result.expected_outcome in {"blocked", "allowed"}
    assert isinstance(result.passed, bool)
    if scenario.labeled_unsafe:
        assert result.observed_blocked is True


def test_crescendo_is_multiturn() -> None:
    crescendo = scenarios_by_family()["crescendo"]
    assert crescendo
    assert any(len(scenario.prompts) > 1 for scenario in crescendo)


def test_pyrit_runner_absent_offline() -> None:
    assert pyrit_available() is False
