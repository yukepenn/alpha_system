"""Regression tests for horizon-agnostic feature-partition matching.

A feature pack is materialized once per ``<instrument>_<year>_full_year`` and is
independent of the label horizon; it must satisfy a horizon-specific runtime
partition ``<instrument>_<year>_<horizon>`` (e.g. ``ES_2020_full_year`` serves
``ES_2020_120m``) WITHOUT loosening anything else. Labels stay strict. The join is
no-lookahead on ``event_ts``/``available_ts``, never on the partition string.

See ``input_resolver._feature_partition_is_horizon_agnostic_match`` and the opt-in
``resolve_feature_packs(..., allow_horizon_agnostic_partition=True)`` used only by
the exploratory lane (fast_probe / testability gate).
"""

from __future__ import annotations

import pytest

from alpha_system.runtime.input_resolver import (
    _feature_partition_is_horizon_agnostic_match as matches,
)


def test_exact_match_always_ok() -> None:
    assert matches("ES_2020_120m", "ES_2020_120m") is True
    assert matches("ES_2020_full_year", "ES_2020_full_year") is True


def test_horizon_agnostic_full_year_serves_horizon_specific_runtime() -> None:
    # the legitimate case this fix enables
    assert matches("ES_2020_full_year", "ES_2020_120m") is True
    assert matches("NQ_2021_full_year", "NQ_2021_60m") is True
    assert matches("RTY_2024_full_year", "RTY_2024_30m") is True


def test_wrong_instrument_still_rejected() -> None:
    assert matches("NQ_2020_full_year", "ES_2020_120m") is False


def test_wrong_year_still_rejected() -> None:
    assert matches("ES_2021_full_year", "ES_2020_120m") is False


def test_non_full_year_feature_scope_still_rejected() -> None:
    # a DIFFERENT horizon scope must NOT be silently accepted
    assert matches("ES_2020_60m", "ES_2020_120m") is False
    assert matches("ES_2020_full_quarter", "ES_2020_120m") is False


def test_malformed_runtime_partition_rejected() -> None:
    assert matches("ES_2020_full_year", "ES_2020") is False
    assert matches("ES_2020_full_year", "locked_test_candidate") is False


@pytest.mark.parametrize(
    "actual,expected",
    [
        ("ES_2020_full_year", "ES_2020_120m"),
        ("ES_2020_120m", "ES_2020_120m"),
    ],
)
def test_only_full_year_or_exact_open_the_gate(actual: str, expected: str) -> None:
    assert matches(actual, expected) is True
