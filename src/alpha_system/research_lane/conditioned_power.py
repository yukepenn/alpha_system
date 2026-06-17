"""Conditioned (context AND trigger) power for the pre-test testability gate.

The pre-test gate's N_eff/MDE plausibility check historically read the
AUTHOR-SUPPLIED slice ``n_eff``/``minimum_detectable_effect``. For a
``main_effect`` study that figure is unconditioned-correct. For a
``context_not_equal_trigger`` (conditional SETUP) study it is NOT: the author
records the UNCONDITIONED full-slice figure, but the real power is governed by
the CONDITIONED event count -- the rows where the entry-context predicate AND the
event-trigger predicate BOTH fire -- collapsed to NON-OVERLAPPING at the label
horizon (the ratified #474 overlap rule applied to the conditioned event series).

A conditional setup whose joint-firing event subset is small and clustered (the
empirically observed FQ08 case: ~1.4% joint firing, heavy intra-horizon
clustering) has an unconditioned ``n_eff`` an order of magnitude above its honest
conditioned ``n_eff``. The unconditioned MDE then badly UNDERSTATES the smallest
effect the probe could detect, so an underpowered setup slips the gate and its
downstream verdict misrepresents power -- the "mass-production of underpowered
nulls" failure mode.

This module computes the honest conditioned N_eff/MDE by COMPOSING the existing
sanctioned primitives -- no second truth:

* ``ConditionalPredicate`` (the same predicate the fast probe runs) applies the
  context/trigger operator/threshold/value_field on the SAME feature value rows
  loaded by the fast-probe loader (``core.value_store.load_parquet_values`` ->
  ``research_lane.fast_probe._load_injected_rows``).
* ``forward_overlap_block_size`` + ``estimate_n_eff`` apply the SAME #474
  overlap discount the conditioned IC-power site (``conditional_probe.
  _conditioned_power_n_eff``) already uses.
* ``minimum_detectable_abs_ic`` recomputes the MDE from that conditioned N_eff
  with the SAME formula the gate's downstream verdict reports.

It performs local-only I/O (reading already-materialized feature parquet rows)
and makes no statistical-validity / tradability claim.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from alpha_system.data.storage import DataDependencyError
from alpha_system.governance.idea_draft import CONTEXT_NOT_EQUAL_TRIGGER
from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.setup_spec import SetupSpec
from alpha_system.research.conditional_probe import (
    ConditionalPredicate,
    ConditionalProbeError,
    ConditionalProbeSpec,
    compile_setup_spec_to_conditional_probe,
)
from alpha_system.research_lane.fast_probe import InjectedRows, _load_injected_rows
from alpha_system.research_lane.slice_spec import SliceSpec, SliceSpecError
from alpha_system.runtime.diagnostics.power import minimum_detectable_abs_ic
from alpha_system.runtime.diagnostics.splits.n_eff import (
    NEffSampleReportingError,
    estimate_n_eff,
    forward_overlap_block_size,
)

# A defensible PLAUSIBLE-EFFECT FLOOR for the conditioned minimum detectable
# absolute IC (task #52 Prong A). A conditional setup edge is a strong,
# detectable effect; if the honest conditioned MDE is ABOVE this floor the probe
# cannot even detect a |IC| as large as this floor at the z=1.96 level, so the
# slice is underpowered for any plausible conditional effect and the gate must
# fail closed. 0.05 means "the probe can detect a |rank-IC| of 0.05" -- a
# generous bar relative to the small per-instrument intraday effects this
# substrate has confirmed null, and small enough that a genuinely well-powered
# conditioned slice (n_eff >= ~1538) passes. Overridable per-call.
PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR = 0.05


class ConditionedPowerPreconditionError(ValueError):
    """Raised when the conditioned-power compute cannot resolve its inputs.

    This is a LOUD typed failure -- NEVER a silent pass on the unconditioned
    figure. It carries an ``is_environment`` discriminator so the gate honors the
    env/precondition-law distinction:

    * ``is_environment=True`` -- an unmet ENVIRONMENT precondition (e.g. the
      ``ALPHA_DATA_ROOT`` does not resolve, or the setup predicates cannot be
      compiled). The gate maps this to ``ENVIRONMENT_NOT_CONFIGURED``, never a
      data finding.
    * ``is_environment=False`` -- the root is fine but the specific materialized
      feature values are genuinely absent / unreadable at gate time. The gate
      maps this to a typed ``DATA_GAP`` (a distinct ``issue_code``), the same
      honest absent-data classification the resolver checks already use -- it must
      NOT be read as the conditioned-power UNDERPOWERED outcome.
    """

    def __init__(self, message: str, *, is_environment: bool) -> None:
        super().__init__(message)
        self.is_environment = is_environment


# Typed verdict for the conditioned-power gate decision. ``passed`` is the only
# decision the gate routes on; ``reason`` + ``issue_code`` are surfaced in the
# check detail. An underpowered conditioned slice carries the distinct
# ``UNDERPOWERED_CONDITIONED`` issue code (NOT a DATA_GAP / precondition).
UNDERPOWERED_CONDITIONED_ISSUE_CODE = "UNDERPOWERED_CONDITIONED"
CONDITIONED_MDE_EXCEEDS_FLOOR_REASON = "conditioned_mde_exceeds_plausible_floor"
CONDITIONED_N_EFF_TOO_SMALL_REASON = "conditioned_n_eff_too_small_for_plausible_pre_test"
CONDITIONED_POWER_OK_REASON = "conditioned_n_eff_mde_plausibly_powered"


@dataclass(frozen=True, slots=True)
class ConditionedPowerVerdict:
    """PASS/FAIL decision for a conditioned-power result against the floor."""

    passed: bool
    reason: str
    issue_code: str | None


def conditioned_power_verdict(
    result: ConditionedPowerResult,
    *,
    plausible_floor: float = PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR,
) -> ConditionedPowerVerdict:
    """Decide PASS/FAIL for a conditioned-power result against the plausible floor.

    A conditioned N_eff below 2 (no usable independent sample) or a conditioned MDE
    ABOVE the plausible-effect floor FAILS closed with the ``UNDERPOWERED_CONDITIONED``
    issue code. This is the single decision the gate routes on; it is a pure
    function of the result so it can be exercised in-memory by the regression
    canary without disk I/O.
    """

    mde = result.conditioned_mde_abs_ic
    if result.conditioned_n_eff < 2 or mde is None:
        return ConditionedPowerVerdict(
            passed=False,
            reason=CONDITIONED_N_EFF_TOO_SMALL_REASON,
            issue_code=UNDERPOWERED_CONDITIONED_ISSUE_CODE,
        )
    if mde > plausible_floor:
        return ConditionedPowerVerdict(
            passed=False,
            reason=CONDITIONED_MDE_EXCEEDS_FLOOR_REASON,
            issue_code=UNDERPOWERED_CONDITIONED_ISSUE_CODE,
        )
    return ConditionedPowerVerdict(
        passed=True,
        reason=CONDITIONED_POWER_OK_REASON,
        issue_code=None,
    )


@dataclass(frozen=True, slots=True)
class ConditionedPowerResult:
    """Honest conditioned (context AND trigger) power for a setup slice."""

    aligned_event_count: int
    conditioned_event_count: int
    overlap_block_size: int
    conditioned_n_eff: int
    conditioned_mde_abs_ic: float | None
    outcome_label_type: str | None
    context_factor_id: str
    trigger_factor_id: str

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "aligned_event_count": self.aligned_event_count,
            "conditioned_event_count": self.conditioned_event_count,
            "overlap_block_size": self.overlap_block_size,
            "conditioned_n_eff": self.conditioned_n_eff,
            "conditioned_mde_abs_ic": self.conditioned_mde_abs_ic,
            "outcome_label_type": self.outcome_label_type,
            "context_factor_id": self.context_factor_id,
            "trigger_factor_id": self.trigger_factor_id,
        }


def compute_conditioned_power(
    setup_spec: SetupSpec,
    conditioned_power_slice: SliceSpec,
    *,
    env: Mapping[str, str] | None = None,
) -> ConditionedPowerResult:
    """Compute the honest conditioned non-overlapping N_eff/MDE for a setup slice.

    The conditioned event count is the number of joined (instrument, event_ts,
    session, data_version) grid points where BOTH the entry-context predicate AND
    the event-trigger predicate fire on the materialized feature values. That
    event series is then discounted to NON-OVERLAPPING at the label horizon via
    the sanctioned #474 estimator, and the MDE is recomputed from THAT N_eff.

    Raises ``ConditionedPowerPreconditionError`` (LOUD, typed) when the inputs
    cannot be resolved at gate time -- never a silent pass. The data-root tier is
    handled by the gate's resolver preflight; this helper only needs the slice's
    feature parquet rows.
    """

    if conditioned_power_slice.study_kind != CONTEXT_NOT_EQUAL_TRIGGER:
        raise ConditionedPowerPreconditionError(
            "conditioned power is only defined for context_not_equal_trigger slices",
            is_environment=True,
        )
    try:
        probe = compile_setup_spec_to_conditional_probe(setup_spec)
    except ConditionalProbeError as exc:
        raise ConditionedPowerPreconditionError(
            f"setup predicates could not be compiled: {exc}",
            is_environment=True,
        ) from exc

    root = conditioned_power_slice.resolve_data_root(env=env)
    if not root.exists():
        # The ALPHA_DATA_ROOT itself does not resolve -- an ENVIRONMENT precondition.
        raise ConditionedPowerPreconditionError(
            f"data root for conditioned power does not resolve: {root}",
            is_environment=True,
        )
    try:
        injected = _load_injected_rows(root, conditioned_power_slice)
    except (DataDependencyError, OSError, ValueError, KeyError, SliceSpecError) as exc:
        # The root is fine but the specific materialized feature values are absent /
        # unreadable -- the honest absent-data classification, not an env fault.
        raise ConditionedPowerPreconditionError(
            f"conditioned-power feature rows could not be loaded: {exc}",
            is_environment=False,
        ) from exc

    return conditioned_power_from_injected_rows(probe, conditioned_power_slice, injected)


def conditioned_power_from_injected_rows(
    probe: ConditionalProbeSpec,
    conditioned_power_slice: SliceSpec,
    injected: InjectedRows,
) -> ConditionedPowerResult:
    """Conditioned power from already-loaded feature rows (no I/O).

    This is the pure compute core shared by ``compute_conditioned_power`` (which
    loads parquet first) and by the in-memory regression canary (which injects
    synthetic rows so it is CI-runnable WITHOUT a data root or the optional parquet
    backend, per the #503 CI-equivalent-env lesson).
    """

    context_rows = injected.feature_rows_by_role.get("context")
    trigger_rows = injected.feature_rows_by_role.get("trigger")
    if not context_rows or not trigger_rows:
        # The slice resolved but its context/trigger feature values are absent --
        # an honest absent-data gap, not an environment fault.
        raise ConditionedPowerPreconditionError(
            "conditioned-power slice is missing materialized 'context' and 'trigger' "
            "feature rows; cannot compute the joint-firing event count",
            is_environment=False,
        )

    aligned, conditioned = _count_conditioned_events(
        context_rows,
        trigger_rows,
        context=probe.context,
        trigger=probe.trigger,
    )

    outcome_label_type = conditioned_power_slice.outcome_label_type
    try:
        block_size = forward_overlap_block_size(
            outcome_label_type,
            required_future_bars=conditioned_power_slice.required_future_bars,
        )
    except NEffSampleReportingError as exc:
        # A forward-overlapping outcome with no derivable horizon must fail LOUD
        # (the #474 law) rather than silently use raw, un-discounted events. This
        # is a malformed-slice CONTRACT fault (the slice must carry the horizon),
        # so it surfaces as an environment/precondition failure, never a data gap.
        raise ConditionedPowerPreconditionError(
            f"conditioned-power overlap block size could not be derived: {exc}",
            is_environment=True,
        ) from exc

    conditioned_n_eff = _overlap_discounted_n_eff(conditioned, block_size)
    conditioned_mde = minimum_detectable_abs_ic(conditioned_n_eff)
    return ConditionedPowerResult(
        aligned_event_count=aligned,
        conditioned_event_count=conditioned,
        overlap_block_size=block_size,
        conditioned_n_eff=conditioned_n_eff,
        conditioned_mde_abs_ic=conditioned_mde,
        outcome_label_type=outcome_label_type,
        context_factor_id=probe.context.factor_id,
        trigger_factor_id=probe.trigger.factor_id,
    )


def _count_conditioned_events(
    context_rows: tuple[Mapping[str, Any], ...],
    trigger_rows: tuple[Mapping[str, Any], ...],
    *,
    context: ConditionalPredicate,
    trigger: ConditionalPredicate,
) -> tuple[int, int]:
    """Return (aligned_event_count, conditioned_event_count).

    ``aligned`` is the number of grid points present in BOTH the context and the
    trigger feature series (joined on the conditional-probe alignment key).
    ``conditioned`` is the subset of those where BOTH predicates fire -- the
    joint-firing event series whose size governs honest conditioned power.
    """

    trigger_index = {_alignment_key(row): row for row in trigger_rows}
    aligned = 0
    conditioned = 0
    for context_row in context_rows:
        trigger_row = trigger_index.get(_alignment_key(context_row))
        if trigger_row is None:
            continue
        aligned += 1
        if context.evaluate(context_row) and trigger.evaluate(trigger_row):
            conditioned += 1
    return aligned, conditioned


def _overlap_discounted_n_eff(conditioned_events: int, block_size: int) -> int:
    """Non-overlapping conditioned N_eff via the sanctioned #474 estimator.

    Mirrors ``conditional_probe._conditioned_power_n_eff`` exactly: a block size
    of 1 (no/single-bar overlap) leaves the conditioned event count untouched; a
    multi-bar horizon discounts the conditioned EVENT series (not the full slice)
    by that horizon.
    """

    if conditioned_events <= 0:
        return 0
    if block_size <= 1:
        return conditioned_events
    estimate = estimate_n_eff(
        conditioned_events,
        {
            "horizon_bars": block_size,
            "sampling_cadence_bars": 1,
            "discount_factor": block_size,
            "metadata_source": "testability_gate_conditioned_event_overlap",
        },
        purge_gap=0,
        embargo_gap=0,
    )
    return estimate.n_eff


def _alignment_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    """The (instrument, event_ts, session, data_version) conditional join key.

    Matches ``conditional_probe._factor_index`` keying so the context/trigger
    series are joined on the SAME grid the fast probe conditions on. ``event_ts``
    is normalized to an ISO string so a datetime and its ISO text key alike.
    """

    return (
        str(row.get("instrument_id", "")),
        _event_ts_text(row.get("event_ts")),
        str(row.get("session_id", "")),
        str(row.get("data_version", "")),
    )


def _event_ts_text(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


__all__ = [
    "CONDITIONED_MDE_EXCEEDS_FLOOR_REASON",
    "CONDITIONED_N_EFF_TOO_SMALL_REASON",
    "CONDITIONED_POWER_OK_REASON",
    "PLAUSIBLE_CONDITIONED_ABS_IC_FLOOR",
    "UNDERPOWERED_CONDITIONED_ISSUE_CODE",
    "ConditionedPowerPreconditionError",
    "ConditionedPowerResult",
    "ConditionedPowerVerdict",
    "compute_conditioned_power",
    "conditioned_power_from_injected_rows",
    "conditioned_power_verdict",
]
