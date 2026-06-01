from __future__ import annotations

from tools.hooks.canary_runner import main


def test_canary_runner_negative_cases_pass() -> None:
    assert main() == 0
