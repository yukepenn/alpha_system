"""Conditioned-power testability-gate canary (task #52, conditional SETUP power).

Guards the fix for the "mass-production of underpowered nulls" failure mode. The
pre-test testability gate's N_eff/MDE check historically accepted the
AUTHOR-SUPPLIED, UNCONDITIONED slice n_eff/MDE for EVERY study kind. For a
``context_not_equal_trigger`` (conditional SETUP) study that is wrong: the real
power is governed by the CONDITIONED (entry-context AND event-trigger) joint-firing
event count, collapsed to NON-OVERLAPPING at the label horizon (the #474 rule
applied to the conditioned event series). A setup whose joint-firing subset is
small and clustered (the empirically observed FQ08 case: ~1.4% joint firing, heavy
intra-horizon clustering) has an unconditioned n_eff an order of magnitude above
its honest conditioned n_eff, so it slipped the gate and its downstream verdict
misrepresented power.

This canary builds SYNTHETIC in-memory context + trigger feature rows (NO data
root, NO parquet backend, per the #503 CI-equivalent-env lesson) and asserts:

1. The conditioned non-overlapping n_eff is computed FAR BELOW the unconditioned
   row count for an FQ08-shaped sparse + clustered joint-firing series.
2. The gate FAILS CLOSED (``UNDERPOWERED_CONDITIONED``) on that underpowered
   conditioned slice -- it does NOT pass on the unconditioned figure.
3. The gate PASSES on a well-powered conditioned case (a dense joint-firing
   series whose conditioned MDE is at/below the plausible-effect floor).

This is research-only diagnostic plumbing. A passing canary validates the
conditioned-power gate contract only and implies NO alpha, profitability, or
tradability claim. The gate is a deterministic RECORD; the machine never
auto-promotes.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.setup_spec import SetupSpec, create_setup_spec
from alpha_system.research.conditional_probe import compile_setup_spec_to_conditional_probe
from alpha_system.research_lane.conditioned_power import (
    PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR,
    UNDERPOWERED_CONDITIONED_ISSUE_CODE,
    conditioned_power_from_injected_rows,
    conditioned_power_verdict,
)
from alpha_system.research_lane.fast_probe import InjectedRows
from alpha_system.research_lane.slice_spec import SliceSpec

# FQ08-shaped fixture knobs. The unconditioned grid is large; the joint-firing
# subset is sparse (~1.4%) and the outcome horizon is multi-bar (30) so the #474
# discount on the conditioned EVENT series collapses it to a tiny n_eff.
_INSTRUMENT = "ES"
_SESSION = "ES:RTH"
_DATA_VERSION = "dsv_databento_ohlcv_canary"
_HORIZON_BARS = 30
_CTX_FACTOR = "ctx_trendiness"
_TRG_FACTOR = "trg_distance_to_vwap"
_CTX_VER = "fver_" + "a" * 64
_TRG_VER = "fver_" + "b" * 64
_CTX_THRESHOLD = 0.05  # context fires when value <= 0.05 (low-trendiness chop)
_TRG_THRESHOLD = -0.004  # trigger fires when value <= -0.004 (far-below-vwap)

_BASE_TS = datetime(2020, 1, 2, 14, 30, tzinfo=UTC)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _setup_spec() -> SetupSpec:
    label_id = generate_governance_id(GovernanceIdKind.LABEL_SPEC, {"canary": "conditioned_power"})
    mech_id = generate_governance_id(
        GovernanceIdKind.MECHANISM_CARD, {"canary": "conditioned_power"}
    )
    return create_setup_spec(
        entry_context={
            "factor_id": _CTX_FACTOR,
            "factor_version": _CTX_VER,
            "operator": "<=",
            "threshold": _CTX_THRESHOLD,
            "value_field": "normalized_value",
            "bucket": "low_trendiness_quiet_chop_regime",
        },
        event_trigger={
            "factor_id": _TRG_FACTOR,
            "factor_version": _TRG_VER,
            "operator": "<=",
            "threshold": _TRG_THRESHOLD,
            "value_field": "normalized_value",
            "event": "far_below_vwap_stretch",
        },
        regime_filter={"session": "RTH", "instrument_root": "ES"},
        confirmation={"policy": "none_added"},
        invalidation={"policy": "fixed_path_stop_binding"},
        stop={"binding": "fixed_stop_from_path_label"},
        target={"geometry": "unchanged", "path_outcome": "net_excursion"},
        hold_time={"horizon": "30m", "max_minutes": 30},
        horizon="30m",
        path_label=label_id,
        allowed_variants=["baseline"],
        forbidden_post_hoc_changes=["no_context_change_after_readout"],
        mechanism_id=mech_id,
    )


def _slice_spec(setup: SetupSpec) -> SliceSpec:
    """A SliceSpec whose net_excursion outcome carries the 30-bar overlap horizon."""

    return SliceSpec.from_mapping(
        {
            "slice_id": "ES_2020_30m_canary",
            "study_kind": "context_not_equal_trigger",
            "dataset_version_id": _DATA_VERSION,
            "partition_id": "ES_2020_30m",
            "instrument_id": _INSTRUMENT,
            "session_id": _SESSION,
            "data_version": _DATA_VERSION,
            "outcome_label_type": "net_excursion",
            "required_future_bars": _HORIZON_BARS,
            # feature_inputs carry pack_refs so SliceSpec validates; the canary
            # injects rows directly and never reads these paths.
            "feature_inputs": [
                {
                    "role": "context",
                    "factor_id": _CTX_FACTOR,
                    "factor_version": _CTX_VER,
                    "pack_ref": _CTX_VER,
                },
                {
                    "role": "trigger",
                    "factor_id": _TRG_FACTOR,
                    "factor_version": _TRG_VER,
                    "pack_ref": _TRG_VER,
                },
            ],
            "label_inputs": [
                {"role": "path", "label_id": setup.path_label, "pack_ref": "lver_" + "c" * 64}
            ],
        }
    )


def _factor_row(factor_id: str, factor_version: str, *, index: int, value: float) -> dict:
    event_ts = (_BASE_TS + timedelta(minutes=index)).isoformat()
    return {
        "factor_id": factor_id,
        "factor_version": factor_version,
        "instrument_id": _INSTRUMENT,
        "event_ts": event_ts,
        "session_id": _SESSION,
        "data_version": _DATA_VERSION,
        "bar_index": index,
        "value": value,
        "normalized_value": value,
    }


def _injected_rows(*, total: int, joint_fire_indices: set[int]) -> InjectedRows:
    """Build aligned context + trigger rows; both predicates fire only at joint indices.

    Off the joint set, the trigger value is well ABOVE its threshold (does not
    fire), so a row is conditioned ONLY where it is in ``joint_fire_indices``. The
    context fires everywhere (value below its threshold) to isolate the
    trigger-driven sparsity, mirroring a context bucket that is broad relative to a
    rare stretch event.
    """

    context_rows = []
    trigger_rows = []
    for index in range(total):
        context_rows.append(
            _factor_row(_CTX_FACTOR, _CTX_VER, index=index, value=_CTX_THRESHOLD - 0.01)
        )
        if index in joint_fire_indices:
            trigger_value = _TRG_THRESHOLD - 0.001  # fires (<= threshold)
        else:
            trigger_value = _TRG_THRESHOLD + 0.05  # does NOT fire
        trigger_rows.append(
            _factor_row(_TRG_FACTOR, _TRG_VER, index=index, value=trigger_value)
        )
    return InjectedRows(
        feature_rows_by_role={
            "context": tuple(context_rows),
            "trigger": tuple(trigger_rows),
        },
        label_rows_by_role={},
    )


def _check_underpowered_fails_closed(setup: SetupSpec, slice_spec: SliceSpec) -> None:
    # FQ08-shaped: a large grid, a sparse (~1.4%) joint-firing subset CLUSTERED into
    # contiguous runs (so consecutive fired events overlap at the 30-bar horizon).
    total = 30_000
    cluster_starts = range(0, total, 600)  # ~50 clusters
    joint: set[int] = set()
    for start in cluster_starts:
        joint.update(range(start, min(start + 9, total)))  # 9 contiguous fired bars
    injected = _injected_rows(total=total, joint_fire_indices=joint)

    probe = compile_setup_spec_to_conditional_probe(setup)
    result = conditioned_power_from_injected_rows(probe, slice_spec, injected)

    _assert(
        result.aligned_event_count == total,
        f"aligned event count {result.aligned_event_count} != grid {total}",
    )
    _assert(
        result.conditioned_event_count == len(joint),
        f"conditioned events {result.conditioned_event_count} != joint-fired {len(joint)}",
    )
    # (a) conditioned n_eff is computed FAR BELOW the unconditioned row count.
    _assert(
        result.conditioned_n_eff < total,
        f"conditioned n_eff {result.conditioned_n_eff} not below unconditioned grid {total}",
    )
    _assert(
        result.conditioned_n_eff <= result.conditioned_event_count // _HORIZON_BARS + 1,
        f"conditioned n_eff {result.conditioned_n_eff} was not #474-discounted by the "
        f"{_HORIZON_BARS}-bar horizon (events {result.conditioned_event_count})",
    )
    # The honest conditioned MDE must be ABOVE the plausible floor (underpowered).
    _assert(
        result.conditioned_mde_abs_ic is not None
        and result.conditioned_mde_abs_ic > PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR,
        f"conditioned MDE {result.conditioned_mde_abs_ic} not above floor "
        f"{PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR} for an FQ08-shaped underpowered setup",
    )
    # (b) the gate decision FAILS CLOSED with the typed UNDERPOWERED code.
    verdict = conditioned_power_verdict(result)
    _assert(
        not verdict.passed,
        "rail defeated: underpowered conditioned setup PASSED the gate "
        f"(conditioned n_eff {result.conditioned_n_eff}, MDE {result.conditioned_mde_abs_ic})",
    )
    _assert(
        verdict.issue_code == UNDERPOWERED_CONDITIONED_ISSUE_CODE,
        f"underpowered conditioned failure issue_code {verdict.issue_code!r} != "
        f"{UNDERPOWERED_CONDITIONED_ISSUE_CODE!r}",
    )


def _check_well_powered_passes(setup: SetupSpec, slice_spec: SliceSpec) -> None:
    # A well-powered conditioned case: a dense joint-firing series large enough that
    # the #474-discounted conditioned n_eff yields an MDE at/below the floor. Floor
    # 0.05 needs conditioned n_eff >= ~1538; events = n_eff * horizon, so 60_000
    # joint-fired bars / 30-bar horizon = 2000 effective samples >> 1538.
    total = 100_000
    joint = set(range(0, 60_000))
    injected = _injected_rows(total=total, joint_fire_indices=joint)

    probe = compile_setup_spec_to_conditional_probe(setup)
    result = conditioned_power_from_injected_rows(probe, slice_spec, injected)

    _assert(
        result.conditioned_event_count == len(joint),
        f"well-powered conditioned events {result.conditioned_event_count} != {len(joint)}",
    )
    _assert(
        result.conditioned_mde_abs_ic is not None
        and result.conditioned_mde_abs_ic <= PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR,
        f"well-powered conditioned MDE {result.conditioned_mde_abs_ic} not at/below floor "
        f"{PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR}",
    )
    verdict = conditioned_power_verdict(result)
    _assert(
        verdict.passed,
        "rail over-fired: a genuinely well-powered conditioned setup FAILED the gate "
        f"(conditioned n_eff {result.conditioned_n_eff}, MDE {result.conditioned_mde_abs_ic})",
    )


def run_conditioned_power_gate_canary() -> None:
    """Run all conditioned-power gate assertions; raise on the first failure."""

    setup = _setup_spec()
    slice_spec = _slice_spec(setup)
    _check_underpowered_fails_closed(setup, slice_spec)
    _check_well_powered_passes(setup, slice_spec)


def main(argv: list[str] | None = None) -> int:
    try:
        run_conditioned_power_gate_canary()
    except AssertionError as exc:
        print(f"FAIL conditioned_power_gate: {exc}", file=sys.stderr)
        return 1
    print(
        "conditioned_power_gate OK: an FQ08-shaped conditional setup has a "
        "conditioned non-overlapping n_eff far below its unconditioned grid, the "
        "gate fails closed (UNDERPOWERED_CONDITIONED) on its conditioned MDE above "
        "the plausible-effect floor, and a genuinely well-powered conditioned setup "
        "still passes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
