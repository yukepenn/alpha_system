from __future__ import annotations

from alpha_system.backtest.fast_path import (
    FAST_PATH_MODE_ACCELERATED,
    FAST_PATH_MODE_REFERENCE_FALLBACK,
)
from alpha_system.backtest.parity import ParityCaseResult, run_parity_case
from alpha_system.backtest.parity_cases import parity_case


def assert_parity_case(case_id: str, *, expected_mode: str | None = None) -> ParityCaseResult:
    result = run_parity_case(parity_case(case_id))
    assert result.passed, [difference.to_dict() for difference in result.differences]
    if expected_mode is not None:
        assert result.fast_mode == expected_mode
    return result


def assert_accelerated(case_id: str) -> ParityCaseResult:
    return assert_parity_case(case_id, expected_mode=FAST_PATH_MODE_ACCELERATED)


def assert_reference_fallback(case_id: str) -> ParityCaseResult:
    return assert_parity_case(case_id, expected_mode=FAST_PATH_MODE_REFERENCE_FALLBACK)
