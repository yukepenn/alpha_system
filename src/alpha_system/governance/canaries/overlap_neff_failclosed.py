"""Overlap-aware N_eff fail-closed canary for the family-FDR/power rail (#474).

Guards the ratified #474 law at its enforcement point: a FORWARD-OVERLAPPING
outcome label (forward/cost-adjusted return, mfe/mae excursion, triple-barrier,
derived net_excursion) looks several bars ahead, so consecutive bar-spaced
observations overlap and the raw row count badly overstates the independent
sample. Such an outcome MUST carry an overlap-discounted N_eff. The latent
regression this canary catches is the SILENT fallback to raw rows /
``discount_factor == 1`` when an OPTIONAL horizon field is left unset.

It asserts four things the independent reviewer rail relies on:

1. **Forward-overlapping outcomes are classified by TYPE**, not by whether an
   optional horizon field happens to be set. Forward families classify True;
   the binary contemporaneous outcome classifies False.

2. **A forward-overlapping outcome with a known multi-bar horizon is
   discounted.** ``forward_overlap_block_size`` returns the horizon block and the
   estimator's N_eff is STRICTLY below the raw row count (discount applied).

3. **Fail-closed when the horizon is unknown.** A forward-overlapping outcome
   with NO derivable horizon RAISES ``NEffSampleReportingError`` -- it NEVER
   silently returns block size 1 / raw rows. Both the shared helper and the
   main-effect fast-probe metadata builder fail closed.

4. **A non-overlapping outcome is left undiscounted** (block size 1, raw rows),
   so the fix does not over-penalize a contemporaneous outcome.

This is research-only diagnostic plumbing. A passing canary validates the
overlap-aware N_eff fail-closed contract only and implies NO alpha,
profitability, or tradability claim. The gate is a deterministic RECORD; the
machine never auto-promotes.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

from alpha_system.research_lane.fast_probe import _main_effect_overlap_metadata
from alpha_system.runtime.diagnostics.splits.n_eff import (
    NEffSampleReportingError,
    estimate_n_eff,
    forward_overlap_block_size,
    is_forward_overlapping_outcome,
)

# A representative forward-overlapping outcome and its multi-bar horizon.
_FORWARD_OUTCOME = "net_excursion"
_FORWARD_HORIZON_BARS = 120
_RAW_ROWS = 1000


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _check_classification() -> None:
    for label_type in (
        "forward_return_5m",
        "fwd_ret_30m",
        "cost_adjusted_forward_return",
        "mfe_by_horizon",
        "mae_by_horizon",
        "triple_barrier_60m",
        "net_excursion",
    ):
        _assert(
            is_forward_overlapping_outcome(label_type),
            f"{label_type!r} must classify as forward-overlapping",
        )
    for label_type in (None, "target_before_stop", "stop_before_target"):
        _assert(
            not is_forward_overlapping_outcome(label_type),
            f"{label_type!r} must NOT classify as forward-overlapping",
        )


def _check_discount_applied() -> None:
    block_size = forward_overlap_block_size(
        _FORWARD_OUTCOME, required_future_bars=_FORWARD_HORIZON_BARS
    )
    _assert(
        block_size == _FORWARD_HORIZON_BARS,
        f"forward-overlapping block size {block_size} != horizon {_FORWARD_HORIZON_BARS}",
    )
    metadata = {
        "horizon_bars": block_size,
        "sampling_cadence_bars": 1,
        "discount_factor": block_size,
        "metadata_source": "overlap_neff_failclosed_canary",
    }
    estimate = estimate_n_eff(_RAW_ROWS, metadata)
    # The load-bearing assertion: a forward-overlapping outcome's N_eff is
    # STRICTLY discounted below the raw rows -- never raw / discount_factor 1.
    _assert(
        estimate.overlap_metadata.discount_factor > 1.0,
        f"rail defeated: discount_factor {estimate.overlap_metadata.discount_factor} <= 1 "
        "for a forward-overlapping outcome (silent raw-rows regression)",
    )
    _assert(
        estimate.n_eff < _RAW_ROWS,
        f"rail defeated: n_eff {estimate.n_eff} not discounted below raw rows {_RAW_ROWS}",
    )


def _check_fail_closed_when_horizon_unknown() -> None:
    # Shared helper: forward-overlapping + no derivable horizon must RAISE.
    try:
        forward_overlap_block_size(_FORWARD_OUTCOME)
    except NEffSampleReportingError:
        pass
    else:
        raise AssertionError(
            "fail-closed defeated: forward-overlapping outcome with no horizon "
            "did not raise -- it would silently use raw rows"
        )

    # Main-effect fast-probe metadata builder: a forward outcome (by
    # construction) with required_future_bars unset must RAISE, not return a
    # discount_factor=1 / None raw fallback.
    slice_spec = SimpleNamespace(required_future_bars=None, label_version_bindings=())
    try:
        _main_effect_overlap_metadata(slice_spec)
    except NEffSampleReportingError:
        pass
    else:
        raise AssertionError(
            "fail-closed defeated: _main_effect_overlap_metadata with no horizon "
            "did not raise -- it would feed raw rows into IC power"
        )


def _check_non_overlapping_outcome_undiscounted() -> None:
    # A contemporaneous (binary) outcome has no overlap to discount; block size 1
    # is correct and does NOT require a horizon.
    _assert(
        forward_overlap_block_size(None) == 1,
        "non-overlapping outcome (None) must yield block size 1",
    )
    _assert(
        forward_overlap_block_size("target_before_stop") == 1,
        "non-overlapping binary outcome must yield block size 1",
    )


def run_overlap_neff_failclosed_canary() -> None:
    """Run all overlap-N_eff fail-closed assertions; raise on the first failure."""

    _check_classification()
    _check_discount_applied()
    _check_fail_closed_when_horizon_unknown()
    _check_non_overlapping_outcome_undiscounted()


def main(argv: list[str] | None = None) -> int:
    try:
        run_overlap_neff_failclosed_canary()
    except AssertionError as exc:
        print(f"FAIL overlap_neff_failclosed: {exc}", file=sys.stderr)
        return 1
    print(
        "overlap_neff_failclosed OK: forward-overlapping outcomes classified by "
        "type, a known multi-bar horizon is discounted (n_eff < rows, "
        "discount_factor > 1), an unknown horizon fails closed at both the shared "
        "helper and the main-effect metadata builder, and a non-overlapping "
        "outcome stays undiscounted"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
