"""Binary-path-label conditioned-N_eff overlap canary (task #74).

Guards the fix for the #74 divergence between the conditioned-power GATE and the
fast-probe conditioned-power READOUT on a BINARY multi-bar path label.

The #52 conditioned-power gate derived its overlap block via
``forward_overlap_block_size(outcome_label_type, ...)`` (keyed on label TYPE). For
a binary path label like ``target_before_stop`` the ``outcome_label_type`` is None
and that type-only helper returns block size 1 -- NO overlap discount -- even when
the slice carries ``required_future_bars > 1``. But a binary path label whose
lookahead window spans ``required_future_bars`` bars on a 1m cadence IS
forward-OVERLAPPING by its HORIZON: consecutive joint-firing events share
``required_future_bars - 1`` of their lookahead bars. So the gate reported the RAW
joint-firing count as the conditioned N_eff -- a ~horizon-fold inflation that
resurrects the exact #474 regression the #52 gate was meant to prevent.

Meanwhile the fast-probe READOUT (``conditional_probe._conditioned_power_n_eff``,
wired from ``fast_probe`` with ``outcome_overlap_bars=slice_spec.required_future_bars``)
ALREADY discounts the conditioned event series by ``required_future_bars`` whenever
it exceeds 1 -- regardless of label type. So pre-fix the GATE (block 1) and the
READOUT (block ``required_future_bars``) reported TWO DIFFERENT conditioned N_eff
for the SAME binary multi-bar slice. The fix makes the gate's block derivation
mirror the readout's exactly (``conditioned_power._conditioned_overlap_block_size``).

This canary builds SYNTHETIC in-memory context + trigger feature rows (NO data
root, NO parquet backend, per the #503 CI-equivalent-env lesson) for a BINARY path
label (``outcome_label_type`` None) with ``required_future_bars`` > 1 and a
clustered joint-firing series, and asserts:

1. The gate's conditioned N_eff is #474-DISCOUNTED to ~events / required_future_bars
   (NOT the raw joint-firing count). This assertion FAILS on the pre-fix code, which
   left the binary block at 1 and reported the raw count.
2. The gate's conditioned N_eff EQUALS the fast-probe readout's
   ``_conditioned_power_n_eff`` for the SAME conditioned event count and horizon
   (gate == readout -- the single-truth requirement of the fix).
3. The gate FAILS CLOSED with the typed ``UNDERPOWERED_CONDITIONED`` issue code on
   the honest (discounted) conditioned MDE above the plausible-effect floor.
4. A genuinely single-bar binary path label (``required_future_bars`` None / 1)
   stays UNDISCOUNTED (block 1, raw events) and still agrees with the readout, so
   the fix does not over-penalize a contemporaneous binary outcome.

This is research-only diagnostic plumbing. A passing canary validates the
conditioned-power gate==readout overlap contract only and implies NO alpha,
profitability, or tradability claim. The gate is a deterministic RECORD; the
machine never auto-promotes.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

from alpha_system.governance.ids import GovernanceIdKind, generate_governance_id
from alpha_system.governance.setup_spec import SetupSpec, create_setup_spec
from alpha_system.research.conditional_probe import (
    _conditioned_power_n_eff,
    compile_setup_spec_to_conditional_probe,
)
from alpha_system.research_lane.conditioned_power import (
    PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR,
    UNDERPOWERED_CONDITIONED_ISSUE_CODE,
    conditioned_power_from_injected_rows,
    conditioned_power_verdict,
)
from alpha_system.research_lane.fast_probe import InjectedRows
from alpha_system.research_lane.slice_spec import SliceSpec

# A binary path label (target_before_stop) on a multi-bar horizon. The lookahead
# window spans 15 bars on a 1m cadence, so the joint-firing event series is
# forward-overlapping by HORIZON even though outcome_label_type is None.
_INSTRUMENT = "ES"
_SESSION = "ES:RTH"
_DATA_VERSION = "dsv_databento_ohlcv_canary"
_HORIZON_BARS = 15
_CTX_FACTOR = "ctx_trendiness"
_TRG_FACTOR = "trg_distance_to_vwap"
_CTX_VER = "fver_" + "a" * 64
_TRG_VER = "fver_" + "b" * 64
_CTX_THRESHOLD = 0.05  # context fires when value <= 0.05 (broad low-trendiness chop)
_TRG_THRESHOLD = -0.004  # trigger fires when value <= -0.004 (far-below-vwap stretch)

_BASE_TS = datetime(2020, 1, 2, 14, 30, tzinfo=UTC)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _setup_spec() -> SetupSpec:
    label_id = generate_governance_id(
        GovernanceIdKind.LABEL_SPEC, {"canary": "binary_overlap_conditioned_neff"}
    )
    mech_id = generate_governance_id(
        GovernanceIdKind.MECHANISM_CARD, {"canary": "binary_overlap_conditioned_neff"}
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
        # A binary target_before_stop path outcome (NOT a continuous net_excursion).
        target={"geometry": "unchanged", "path_outcome": "target_before_stop"},
        hold_time={"horizon": "15m", "max_minutes": 15},
        horizon="15m",
        path_label=label_id,
        allowed_variants=["baseline"],
        forbidden_post_hoc_changes=["no_context_change_after_readout"],
        mechanism_id=mech_id,
    )


def _slice_spec(setup: SetupSpec, *, required_future_bars: int | None) -> SliceSpec:
    """A BINARY-path-label SliceSpec (outcome_label_type None) on a multi-bar horizon."""

    payload = {
        "slice_id": "ES_2020_15m_binary_canary",
        "study_kind": "context_not_equal_trigger",
        "dataset_version_id": _DATA_VERSION,
        "partition_id": "ES_2020_15m",
        "instrument_id": _INSTRUMENT,
        "session_id": _SESSION,
        "data_version": _DATA_VERSION,
        # NO outcome_label_type -> the degenerate binary target_before_stop path.
        # feature_inputs carry pack_refs so SliceSpec validates; the canary injects
        # rows directly and never reads these paths.
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
    if required_future_bars is not None:
        payload["required_future_bars"] = required_future_bars
    return SliceSpec.from_mapping(payload)


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

    The context fires everywhere (value below its threshold) and the trigger fires
    only at ``joint_fire_indices`` (value below its threshold), so a row is
    conditioned ONLY where it is in ``joint_fire_indices`` -- mirroring a broad
    context bucket gating a rare stretch event.
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
        trigger_rows.append(_factor_row(_TRG_FACTOR, _TRG_VER, index=index, value=trigger_value))
    return InjectedRows(
        feature_rows_by_role={
            "context": tuple(context_rows),
            "trigger": tuple(trigger_rows),
        },
        label_rows_by_role={},
    )


def _clustered_joint(total: int) -> set[int]:
    """A sparse, intra-horizon-CLUSTERED joint-firing set (consecutive fired bars overlap)."""

    joint: set[int] = set()
    for start in range(0, total, 600):  # ~50 clusters
        joint.update(range(start, min(start + 9, total)))  # 9 contiguous fired bars
    return joint


def _check_binary_multibar_discounted_and_matches_readout(setup: SetupSpec) -> None:
    """A binary path label on a multi-bar horizon: discounted + gate == readout + fail-closed."""

    total = 30_000
    joint = _clustered_joint(total)
    injected = _injected_rows(total=total, joint_fire_indices=joint)
    slice_spec = _slice_spec(setup, required_future_bars=_HORIZON_BARS)
    probe = compile_setup_spec_to_conditional_probe(setup)

    result = conditioned_power_from_injected_rows(probe, slice_spec, injected)

    _assert(
        result.outcome_label_type is None,
        f"fixture is not a binary path label (outcome_label_type={result.outcome_label_type!r})",
    )
    _assert(
        result.conditioned_event_count == len(joint),
        f"conditioned events {result.conditioned_event_count} != joint-fired {len(joint)}",
    )
    # (1) The block size for a binary MULTI-bar path label must be the horizon (the
    # #74 fix), NOT the type-only 1. This is the assertion that FAILS on pre-fix code.
    _assert(
        result.overlap_block_size == _HORIZON_BARS,
        f"binary multi-bar path label block_size {result.overlap_block_size} != horizon "
        f"{_HORIZON_BARS}: a binary path label with required_future_bars>1 must be treated "
        "as forward-OVERLAPPING by its horizon (the #74 fix)",
    )
    # The conditioned N_eff must be #474-discounted to ~events / horizon, NOT the raw
    # joint-firing count. Pre-fix code reported the RAW count (block 1) and FAILS here.
    raw_events = result.conditioned_event_count
    _assert(
        result.conditioned_n_eff < raw_events,
        f"conditioned n_eff {result.conditioned_n_eff} was NOT discounted below the raw "
        f"joint-firing count {raw_events} (#74 binary-horizon inflation regressed)",
    )
    _assert(
        result.conditioned_n_eff <= raw_events // _HORIZON_BARS + 1,
        f"conditioned n_eff {result.conditioned_n_eff} not #474-discounted by the "
        f"{_HORIZON_BARS}-bar horizon (raw events {raw_events})",
    )
    # (2) gate == readout: the gate must report the SAME conditioned N_eff as the
    # fast-probe readout's _conditioned_power_n_eff for the same events + horizon.
    readout_n_eff = _conditioned_power_n_eff(raw_events, _HORIZON_BARS)
    _assert(
        result.conditioned_n_eff == readout_n_eff,
        "gate != readout: gate conditioned n_eff "
        f"{result.conditioned_n_eff} != readout {readout_n_eff} for the SAME binary "
        f"multi-bar slice (events {raw_events}, horizon {_HORIZON_BARS}) -- the #74 "
        "two-truths divergence",
    )
    # (3) The gate must FAIL CLOSED on the honest (discounted) conditioned MDE.
    _assert(
        result.conditioned_mde_abs_ic is not None
        and result.conditioned_mde_abs_ic > PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR,
        f"honest conditioned MDE {result.conditioned_mde_abs_ic} not above floor "
        f"{PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR} for this underpowered binary setup",
    )
    verdict = conditioned_power_verdict(result)
    _assert(
        not verdict.passed,
        "rail defeated: underpowered binary multi-bar conditional setup PASSED the gate "
        f"(conditioned n_eff {result.conditioned_n_eff}, MDE {result.conditioned_mde_abs_ic})",
    )
    _assert(
        verdict.issue_code == UNDERPOWERED_CONDITIONED_ISSUE_CODE,
        f"underpowered binary conditioned failure issue_code {verdict.issue_code!r} != "
        f"{UNDERPOWERED_CONDITIONED_ISSUE_CODE!r}",
    )


def _check_binary_single_bar_not_overpenalized(setup: SetupSpec) -> None:
    """A genuinely single-bar binary path label stays UNDISCOUNTED and matches the readout."""

    total = 30_000
    joint = _clustered_joint(total)
    injected = _injected_rows(total=total, joint_fire_indices=joint)
    probe = compile_setup_spec_to_conditional_probe(setup)

    for required_future_bars in (None, 1):
        slice_spec = _slice_spec(setup, required_future_bars=required_future_bars)
        result = conditioned_power_from_injected_rows(probe, slice_spec, injected)
        _assert(
            result.overlap_block_size == 1,
            f"single-bar binary path label (required_future_bars={required_future_bars!r}) "
            f"block_size {result.overlap_block_size} != 1 (over-penalized a contemporaneous "
            "binary outcome)",
        )
        _assert(
            result.conditioned_n_eff == result.conditioned_event_count,
            f"single-bar binary conditioned n_eff {result.conditioned_n_eff} != raw events "
            f"{result.conditioned_event_count} (block 1 must leave the count untouched)",
        )
        readout_n_eff = _conditioned_power_n_eff(
            result.conditioned_event_count, required_future_bars
        )
        _assert(
            result.conditioned_n_eff == readout_n_eff,
            "gate != readout for a single-bar binary path label "
            f"(required_future_bars={required_future_bars!r}): gate {result.conditioned_n_eff} "
            f"!= readout {readout_n_eff}",
        )


def run_binary_overlap_conditioned_neff_canary() -> None:
    """Run all binary-overlap conditioned-N_eff assertions; raise on the first failure."""

    setup = _setup_spec()
    _check_binary_multibar_discounted_and_matches_readout(setup)
    _check_binary_single_bar_not_overpenalized(setup)


def main(argv: list[str] | None = None) -> int:
    try:
        run_binary_overlap_conditioned_neff_canary()
    except AssertionError as exc:
        print(f"FAIL binary_overlap_conditioned_neff: {exc}", file=sys.stderr)
        return 1
    print(
        "binary_overlap_conditioned_neff OK: a BINARY multi-bar path label "
        "(outcome_label_type None, required_future_bars>1) is treated as "
        "forward-overlapping by its horizon -- the gate's conditioned N_eff is "
        "#474-discounted to ~events/horizon (not the raw joint-firing count), it EQUALS "
        "the fast-probe readout's conditioned N_eff for the same slice, the gate fails "
        "closed (UNDERPOWERED_CONDITIONED) on its honest MDE above the floor, and a "
        "genuinely single-bar binary outcome stays undiscounted"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
