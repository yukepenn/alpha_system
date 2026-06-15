"""Unit tests for the shared fail-closed forward-overlap block-size helper.

Guards the ratified #474 law at the source: a forward-overlapping outcome label
MUST derive an overlap-discounted block size or fail loud; it can NEVER silently
collapse to raw rows (block size 1 / discount_factor 1) just because an optional
horizon field was left unset. A genuinely contemporaneous (non-overlapping)
outcome is correctly left undiscounted.
"""

from __future__ import annotations

import pytest

from alpha_system.runtime.diagnostics.splits.n_eff import (
    NEffSampleReportingError,
    forward_overlap_block_size,
    is_forward_overlapping_outcome,
)


@pytest.mark.parametrize(
    "label_type",
    [
        "forward_return_5m",
        "fwd_ret_30m",
        "cost_adjusted_forward_return",
        "cost_adj_fwd_ret_10m",
        "mfe_by_horizon",
        "mae_by_horizon",
        "triple_barrier_60m",
        "net_excursion",
        "MFE_BY_HORIZON",  # case-insensitive
    ],
)
def test_forward_overlapping_outcomes_are_classified(label_type: str) -> None:
    assert is_forward_overlapping_outcome(label_type) is True


@pytest.mark.parametrize(
    "label_type",
    [None, "", "   ", "target_before_stop", "stop_before_target", "some_contemporaneous"],
)
def test_non_overlapping_outcomes_are_not_classified(label_type: str | None) -> None:
    assert is_forward_overlapping_outcome(label_type) is False


def test_non_overlapping_outcome_block_size_is_one() -> None:
    # Binary contemporaneous outcome (outcome_label_type None): no overlap, no
    # discount -- and it does NOT need a horizon to be supplied.
    assert forward_overlap_block_size(None) == 1
    assert forward_overlap_block_size("target_before_stop") == 1


def test_forward_overlapping_outcome_uses_required_future_bars() -> None:
    assert (
        forward_overlap_block_size("net_excursion", required_future_bars=120) == 120
    )
    assert (
        forward_overlap_block_size("forward_return_5m", required_future_bars=5) == 5
    )


def test_single_bar_forward_label_has_block_size_one() -> None:
    # A genuinely 1-bar-ahead forward label legitimately has no overlap; this is
    # the honest no-discount case (distinct from the silent-raw bug because the
    # horizon is KNOWN to be 1 bar).
    assert forward_overlap_block_size("forward_return_1m", required_future_bars=1) == 1


def test_forward_overlapping_derives_block_from_horizon_and_cadence() -> None:
    # When required_future_bars is unset but horizon/cadence are known, derive
    # block size = floor(horizon_seconds / cadence_seconds).
    assert (
        forward_overlap_block_size(
            "net_excursion", horizon_seconds=7200, cadence_seconds=60
        )
        == 120
    )


def test_forward_overlapping_fails_closed_when_horizon_unknown() -> None:
    # The load-bearing guard: a forward-overlapping label with NO derivable
    # horizon must RAISE, never silently return 1 (raw rows / discount_factor 1).
    with pytest.raises(NEffSampleReportingError):
        forward_overlap_block_size("net_excursion")
    with pytest.raises(NEffSampleReportingError):
        forward_overlap_block_size("forward_return_5m", required_future_bars=None)
    # horizon_seconds without cadence is insufficient -> still fail closed.
    with pytest.raises(NEffSampleReportingError):
        forward_overlap_block_size("net_excursion", horizon_seconds=7200)


def test_forward_overlapping_fails_closed_on_non_positive_bars() -> None:
    with pytest.raises(NEffSampleReportingError):
        forward_overlap_block_size("net_excursion", required_future_bars=0)
