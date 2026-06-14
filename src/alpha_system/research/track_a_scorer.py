"""Pure-research Track A mechanism scorer (DK-P03, post FDR/zero-pass gate).

This module is the value-bearing research probe for the DIFFERENTIATED_KILLSHOT_V1
Track A real-data evidence phase. It is intentionally pure: callers inject the
already-loaded factor/label observation rows; this module never opens a Parquet,
never touches a registry, and imports **none** of
``backtest`` / ``management`` / ``fast_path`` / ``core.value_store`` (the
no-second-PnL rail). It delegates the real Pearson / rank IC, bucket
monotonicity, coverage, and walk-forward read to the existing runtime factor
diagnostics engine and attaches the deterministic N_eff / power statement.

The returned :class:`MechanismDiagnostics` carries a runtime
``StudyRunResultState`` and a closed campaign-taxonomy ``primary_state``
(``REJECT`` / ``INCONCLUSIVE`` / ``WATCH`` / ``CANDIDATE_RESEARCH``) plus a
``VerdictReasonCode`` for any ``INCONCLUSIVE`` row. No runtime enum is added; the
closed taxonomy stays a document/human layer exactly as the FUTSUB verdict
refresh does it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from alpha_system.governance.serialization import JsonValue
from alpha_system.governance.verdict_reason_code import VerdictReasonCode
from alpha_system.runtime.contracts.run_record import StudyRunResultState
from alpha_system.runtime.diagnostics.factor.runtime import (
    build_factor_diagnostics_run,
)
from alpha_system.runtime.diagnostics.power import (
    build_ic_power_statement,
    minimum_detectable_abs_ic,
)
from alpha_system.runtime.diagnostics.splits.n_eff import (
    HorizonOverlapMetadata,
    estimate_n_eff,
)

# Closed campaign verdict taxonomy (document/human layer only; not a runtime enum).
PRIMARY_STATE_REJECT = "REJECT"
PRIMARY_STATE_INCONCLUSIVE = "INCONCLUSIVE"
PRIMARY_STATE_WATCH = "WATCH"
PRIMARY_STATE_CANDIDATE_RESEARCH = "CANDIDATE_RESEARCH"
CLOSED_TAXONOMY_PRIMARY_STATES = frozenset(
    {
        PRIMARY_STATE_REJECT,
        PRIMARY_STATE_INCONCLUSIVE,
        PRIMARY_STATE_WATCH,
        PRIMARY_STATE_CANDIDATE_RESEARCH,
    }
)

TRACK_A_DIAGNOSTICS_FAMILY = "factor"
TRACK_A_SCORER_SCHEMA = "alpha_system.research.track_a_scorer.mechanism_diagnostics.v1"


class TrackAScorerError(ValueError):
    """Raised when Track A scoring inputs are invalid."""


@dataclass(frozen=True, slots=True)
class MechanismDiagnostics:
    """Value-bearing per-mechanism diagnostics + closed-taxonomy verdict.

    ``primary_state`` is the closed campaign taxonomy. ``reason_code`` is always
    present for an ``INCONCLUSIVE`` ``primary_state`` and is ``None`` otherwise
    unless an explicit caveat code is supplied. ``runtime_state`` is the raw
    runtime ``StudyRunResultState`` the verdict was mapped from.
    """

    mechanism_id: str
    factor_id: str
    runtime_state: StudyRunResultState
    primary_state: str
    pearson_ic: float | None
    rank_ic: float | None
    usable_pair_count: int
    total_observations: int
    coverage_ratio: float | None
    bucket_count: int
    bucket_populated_count: int
    bucket_is_monotonic: bool
    bucket_direction: str
    n_eff: int
    se_ic: float | None
    mde_abs_ic: float | None
    ic_power_statement: dict[str, JsonValue]
    n_eff_report: dict[str, JsonValue]
    reason_code: str | None = None
    rejection_reason_codes: tuple[str, ...] = ()
    caveats: tuple[str, ...] = ()
    diagnostics_quality_summary: dict[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.primary_state not in CLOSED_TAXONOMY_PRIMARY_STATES:
            raise TrackAScorerError(
                f"primary_state must be one of {sorted(CLOSED_TAXONOMY_PRIMARY_STATES)}, "
                f"got {self.primary_state!r}"
            )
        if self.primary_state == PRIMARY_STATE_INCONCLUSIVE and self.reason_code is None:
            raise TrackAScorerError(
                "an INCONCLUSIVE mechanism diagnostics row must carry a VerdictReasonCode"
            )

    @property
    def is_survivor(self) -> bool:
        """A WATCH / CANDIDATE_RESEARCH survivor requires a reviewer verdict."""

        return self.primary_state in {PRIMARY_STATE_WATCH, PRIMARY_STATE_CANDIDATE_RESEARCH}

    def to_dict(self) -> dict[str, JsonValue]:
        """Return a JSON-serializable value-bearing diagnostics block."""

        return {
            "schema": TRACK_A_SCORER_SCHEMA,
            "mechanism_id": self.mechanism_id,
            "factor_id": self.factor_id,
            "runtime_state": self.runtime_state.value,
            "primary_state": self.primary_state,
            "reason_code": self.reason_code,
            "pearson_ic": self.pearson_ic,
            "rank_ic": self.rank_ic,
            "usable_pair_count": self.usable_pair_count,
            "total_observations": self.total_observations,
            "coverage_ratio": self.coverage_ratio,
            "bucket_count": self.bucket_count,
            "bucket_populated_count": self.bucket_populated_count,
            "bucket_is_monotonic": self.bucket_is_monotonic,
            "bucket_direction": self.bucket_direction,
            "n_eff": self.n_eff,
            "se_ic": self.se_ic,
            "mde_abs_ic": self.mde_abs_ic,
            "ic_power_statement": self.ic_power_statement,
            "n_eff_report": self.n_eff_report,
            "rejection_reason_codes": list(self.rejection_reason_codes),
            "caveats": list(self.caveats),
            "is_survivor": self.is_survivor,
            "requires_reviewer_verdict": self.is_survivor,
            "statistical_validity_claim": False,
        }


def _scalar_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scalar_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool) or value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def map_runtime_state_to_primary_state(
    runtime_state: StudyRunResultState,
    *,
    n_eff: int,
    pearson_ic: float | None,
    rank_ic: float | None,
    mde_abs_ic: float | None,
    bucket_is_monotonic: bool,
    rejection_reason_codes: Sequence[str] = (),
) -> tuple[str, str | None]:
    """Map a runtime ``StudyRunResultState`` to the closed campaign taxonomy.

    Returns ``(primary_state, reason_code)``. The mapping is conservative and
    evidence-driven, never prior-driven:

    - ``REJECTED`` / ``DIAGNOSTICS_FAILED`` -> ``REJECT`` (a hard runtime block
      such as a missing ``available_ts`` or a failed coverage gate).
    - ``INCONCLUSIVE`` -> ``INCONCLUSIVE`` with a ``VerdictReasonCode``
      (``UNDERPOWERED`` whenever the effective sample cannot resolve a usable
      MDE, otherwise ``DATA_QUALITY``).
    - ``DIAGNOSTICS_COMPLETE`` -> ``REJECT`` unless the complete read is also
      underpowered (the MDE swamps any plausible effect), in which case it is the
      honest ``INCONCLUSIVE`` + ``UNDERPOWERED``. A complete read is *never*
      auto-promoted to ``WATCH`` / ``CANDIDATE_RESEARCH`` here; a survivor is a
      reviewer/coordinator decision, surfaced separately, and this scorer keeps
      the asymmetric gate by refusing to mint a survivor from diagnostics alone.
    """

    codes = tuple(rejection_reason_codes)
    if runtime_state in {
        StudyRunResultState.REJECTED,
        StudyRunResultState.DIAGNOSTICS_FAILED,
    }:
        return PRIMARY_STATE_REJECT, None

    underpowered = n_eff <= 1 or mde_abs_ic is None
    if runtime_state == StudyRunResultState.INCONCLUSIVE:
        if underpowered:
            return PRIMARY_STATE_INCONCLUSIVE, VerdictReasonCode.UNDERPOWERED.value
        # An IC/bucket-unavailable inconclusive with usable N_eff is a data
        # quality / degenerate-distribution caveat, not a power limit.
        return PRIMARY_STATE_INCONCLUSIVE, VerdictReasonCode.DATA_QUALITY.value

    # DIAGNOSTICS_COMPLETE: the read resolved. Decide REJECT vs INCONCLUSIVE on
    # power only. Effect size never *promotes* here (survivor is reviewer-gated);
    # it can only fail to clear the underpowered floor.
    if underpowered:
        return PRIMARY_STATE_INCONCLUSIVE, VerdictReasonCode.UNDERPOWERED.value
    return PRIMARY_STATE_REJECT, None


def score_mechanism(
    *,
    mechanism_id: str,
    factor_id: str,
    rows: Iterable[Mapping[str, Any]],
    horizon_overlap_metadata: HorizonOverlapMetadata | Mapping[str, Any],
    diagnostics_run_spec: Mapping[str, Any] | None = None,
    walk_forward_config: Mapping[str, Any] | None = None,
    thresholds: Mapping[str, Any] | None = None,
    caveats: Sequence[str] = (),
    purge_gap: int | None = None,
    embargo_gap: int | None = None,
) -> MechanismDiagnostics:
    """Score one mechanism over injected, pooled factor/label observation rows.

    ``rows`` is the pooled (ES/NQ/RTY, all partitions) iterable of observation
    mappings, each carrying at least ``factor_value`` / ``label_value`` and the
    no-lookahead ``available_ts`` / ``label_available_ts``. This function does
    not load anything; the tools/runtime harness injects rows. The real metric
    read comes from the existing runtime ``build_factor_diagnostics_run``.
    """

    materialized_rows = [dict(row) for row in rows]
    # The factor diagnostics engine treats a mapping spec as a *reference* and
    # only accepts {diagnostics_run_spec_id, content_hash}; the factor family is
    # asserted only for a full DiagnosticsRunSpec object (a mapping is the FACTOR
    # path by construction here). Lineage carries the factor/mechanism ids.
    spec = dict(diagnostics_run_spec or {})
    spec.setdefault("diagnostics_run_spec_id", f"dk_p03_{mechanism_id}")
    spec.setdefault(
        "content_hash",
        hashlib.sha256(f"{mechanism_id}|{factor_id}".encode()).hexdigest(),
    )

    result = build_factor_diagnostics_run(
        diagnostics_run_spec=spec,
        observations=materialized_rows,
        lineage_refs={"factor_id": factor_id, "mechanism_id": mechanism_id},
        thresholds=thresholds,
        walk_forward_config=walk_forward_config,
    )
    report = result.report.report
    runtime_state = report.status
    coverage = dict(report.coverage_summary)
    quality = dict(report.quality_summary)

    pearson_ic = _scalar_float(quality.get("pearson_ic"))
    rank_ic = _scalar_float(quality.get("rank_ic"))
    usable_pair_count = _scalar_int(coverage.get("usable_pair_count"))
    total_observations = _scalar_int(coverage.get("input_count"), default=len(materialized_rows))
    coverage_ratio = _scalar_float(coverage.get("coverage_ratio"))
    bucket_count = _scalar_int(quality.get("bucket_count"))
    bucket_populated_count = _scalar_int(quality.get("bucket_populated_count"))
    bucket_is_monotonic = bool(quality.get("bucket_is_monotonic"))
    bucket_direction = str(quality.get("bucket_direction") or "insufficient")
    rejection_reason_codes = tuple(
        reason.code for reason in report.rejection_reasons
    )

    # N_eff is computed over the usable IC pairs (the actual sample the IC was
    # measured on), discounted by the caller-supplied horizon-overlap metadata.
    n_eff_estimate = estimate_n_eff(
        usable_pair_count,
        horizon_overlap_metadata,
        purge_gap=purge_gap,
        embargo_gap=embargo_gap,
    )
    n_eff = n_eff_estimate.n_eff
    power_statement = build_ic_power_statement(
        n_eff=n_eff,
        scope="stacked",
        factor_id=factor_id,
    )
    se_ic = _scalar_float(power_statement.get("se_ic"))
    mde_abs_ic = _scalar_float(power_statement.get("mde_abs_ic"))
    if mde_abs_ic is None:
        mde_abs_ic = minimum_detectable_abs_ic(n_eff)

    primary_state, reason_code = map_runtime_state_to_primary_state(
        runtime_state,
        n_eff=n_eff,
        pearson_ic=pearson_ic,
        rank_ic=rank_ic,
        mde_abs_ic=mde_abs_ic,
        bucket_is_monotonic=bucket_is_monotonic,
        rejection_reason_codes=rejection_reason_codes,
    )

    return MechanismDiagnostics(
        mechanism_id=mechanism_id,
        factor_id=factor_id,
        runtime_state=runtime_state,
        primary_state=primary_state,
        pearson_ic=pearson_ic,
        rank_ic=rank_ic,
        usable_pair_count=usable_pair_count,
        total_observations=total_observations,
        coverage_ratio=coverage_ratio,
        bucket_count=bucket_count,
        bucket_populated_count=bucket_populated_count,
        bucket_is_monotonic=bucket_is_monotonic,
        bucket_direction=bucket_direction,
        n_eff=n_eff,
        se_ic=se_ic,
        mde_abs_ic=mde_abs_ic,
        ic_power_statement=power_statement,
        n_eff_report=n_eff_estimate.to_dict(),
        reason_code=reason_code,
        rejection_reason_codes=rejection_reason_codes,
        caveats=tuple(caveats),
        diagnostics_quality_summary=quality,
    )


__all__ = [
    "CLOSED_TAXONOMY_PRIMARY_STATES",
    "MechanismDiagnostics",
    "PRIMARY_STATE_CANDIDATE_RESEARCH",
    "PRIMARY_STATE_INCONCLUSIVE",
    "PRIMARY_STATE_REJECT",
    "PRIMARY_STATE_WATCH",
    "TRACK_A_SCORER_SCHEMA",
    "TrackAScorerError",
    "map_runtime_state_to_primary_state",
    "score_mechanism",
]
