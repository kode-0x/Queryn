from __future__ import annotations

import importlib.util

from red_team.harness import HarnessReport, run_harness
from red_team.scenarios import SCENARIOS, Scenario


def pyrit_available() -> bool:
    return importlib.util.find_spec("pyrit") is not None


def run_pyrit(scenarios: list[Scenario] | None = None) -> HarnessReport:
    if not pyrit_available():
        raise RuntimeError("pyrit is not installed")
    active = scenarios if scenarios is not None else SCENARIOS
    return run_harness(scenarios=active)
