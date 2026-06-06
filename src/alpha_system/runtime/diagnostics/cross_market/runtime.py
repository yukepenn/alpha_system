"""Cross-market diagnostics runtime orchestration.

This module assembles a descriptive ES/NQ/RTY diagnostics report from resolved
runtime inputs and a caller-supplied in-memory diagnostics view. Correlation
summaries are delegated to :mod:`alpha_system.research.correlation`; the runtime
does not read provider files, materialize stores, or create strategy objects.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations, permutations
from pathlib import Path
from typing import Any

from alpha_system.data.foundation.datasets import DatasetVersion
from alpha_system.data.foundation.version_registry import resolve_dataset_version
from alpha_system.research import correlation as research_correlation
from alpha_system.runtime.contracts.run_record import RunRejectionReason, StudyRunResultState
from alpha_system.runtime.diagnostics.contracts import (
    DiagnosticsFamily,
    DiagnosticsRunRecord,
    DiagnosticsRunSpec,
    DiagnosticsRunSpecRef,
)
from alpha_system.runtime.diagnostics.report import (
    DiagnosticsQualityGate,
    DiagnosticsQualityGateStatus,
    DiagnosticsReport,
)
from alpha_system.runtime.entry_contract import ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES
from alpha_system.runtime.input_resolver import LOCKED_PARTITION_IDS, RuntimeInputPack

JsonScalar = None | bool | int | float | str
DatasetVersionResolver = Callable[[str | Path, object], DatasetVersion | None]

CROSS_MARKET_DIAGNOSTICS_REPORT_KIND = "cross_market_diagnostics_summary"
CROSS_MARKET_DIAGNOSTICS_THRESHOLD_PROFILE = "cross_market_diagnostics_default_v1"
DEFAULT_REQUIRED_SYMBOLS = ("ES", "NQ", "RTY")
DEFAULT_VALUE_FIELDS = ("cross_market_metric", "feature_value", "close", "mid", "value")
DEFAULT_LIMITATIONS = (
    "Cross-market diagnostics are descriptive Tier 0 summaries; "
    "a complete diagnostic is not alpha validation.",
    "The report stores scalar summaries only and does not embed market observations "
    "or feature and label payloads.",
    "Correlation summaries are delegated to alpha_system.research.correlation.",
    "Lead/lag summaries compare prior synchronized snapshots to current synchronized "
    "snapshots under available_ts discipline.",
    "Spread and residual proxies are arithmetic descriptors only; no hedge model, "
    "strategy, or portfolio object is created.",
)
LABEL_ONLY_FIELDS = frozenset(
    {
        "label",
        "label_outcome",
        "label_value",
        "target",
        "horizon_end_ts",
    }
)
MIXED_SOURCE_MARKERS = ("databento+ibkr", "databento,ibkr", "ibkr+databento", "ibkr,databento")


class CrossMarketDiagnosticsError(ValueError):
    """Raised when cross-market diagnostics cannot be assembled safely."""


@dataclass(frozen=True, slots=True)
class CrossMarketDiagnosticsConfig:
    """Scalar thresholds for the descriptive cross-market diagnostics report."""

    required_symbols: tuple[str, ...] = DEFAULT_REQUIRED_SYMBOLS
    min_aligned_snapshots: int = 3
    min_symbol_coverage_ratio: float = 0.80
    max_missingness_rate: float = 0.20
    max_timestamp_skew_seconds: float = 5.0
    lead_lag_steps: tuple[int, ...] = (1,)
    regime_field: str = "regime_label"
    value_fields: tuple[str, ...] = DEFAULT_VALUE_FIELDS
    limitations: tuple[str, ...] = DEFAULT_LIMITATIONS

    def __post_init__(self) -> None:
        symbols = tuple(
            _required_text(symbol, "required_symbols").upper() for symbol in self.required_symbols
        )
        if len(symbols) < 2:
            raise CrossMarketDiagnosticsError("required_symbols must contain at least two symbols")
        if len(set(symbols)) != len(symbols):
            raise CrossMarketDiagnosticsError("required_symbols must not contain duplicates")
        _positive_int(self.min_aligned_snapshots, "min_aligned_snapshots")
        _ratio(self.min_symbol_coverage_ratio, "min_symbol_coverage_ratio")
        _ratio(self.max_missingness_rate, "max_missingness_rate")
        _non_negative_float(self.max_timestamp_skew_seconds, "max_timestamp_skew_seconds")
        steps = tuple(int(step) for step in self.lead_lag_steps)
        if not steps:
            raise CrossMarketDiagnosticsError("lead_lag_steps must not be empty")
        if any(step < 0 for step in steps):
            raise CrossMarketDiagnosticsError("lead_lag_steps must be non-negative")
        if len(set(steps)) != len(steps):
            raise CrossMarketDiagnosticsError("lead_lag_steps must not contain duplicates")
        value_fields = tuple(_required_text(field, "value_fields") for field in self.value_fields)
        if not value_fields:
            raise CrossMarketDiagnosticsError("value_fields must not be empty")
        object.__setattr__(self, "required_symbols", symbols)
        object.__setattr__(self, "lead_lag_steps", tuple(sorted(steps)))
        object.__setattr__(self, "regime_field", _required_text(self.regime_field, "regime_field"))
        object.__setattr__(self, "value_fields", value_fields)
        object.__setattr__(
            self,
            "limitations",
            tuple(_required_text(item, "limitations") for item in self.limitations),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> CrossMarketDiagnosticsConfig:
        """Build config from a JSON-compatible mapping."""

        allowed = {
            "required_symbols",
            "min_aligned_snapshots",
            "min_symbol_coverage_ratio",
            "max_missingness_rate",
            "max_timestamp_skew_seconds",
            "lead_lag_steps",
            "regime_field",
            "value_fields",
            "limitations",
        }
        extra = set(value) - allowed
        if extra:
            raise CrossMarketDiagnosticsError(
                f"unsupported cross-market diagnostics config fields: {', '.join(sorted(extra))}"
            )
        defaults = cls()
        return cls(
            required_symbols=tuple(value.get("required_symbols", defaults.required_symbols)),
            min_aligned_snapshots=int(
                value.get("min_aligned_snapshots", defaults.min_aligned_snapshots)
            ),
            min_symbol_coverage_ratio=float(
                value.get("min_symbol_coverage_ratio", defaults.min_symbol_coverage_ratio)
            ),
            max_missingness_rate=float(
                value.get("max_missingness_rate", defaults.max_missingness_rate)
            ),
            max_timestamp_skew_seconds=float(
                value.get("max_timestamp_skew_seconds", defaults.max_timestamp_skew_seconds)
            ),
            lead_lag_steps=tuple(value.get("lead_lag_steps", defaults.lead_lag_steps)),
            regime_field=str(value.get("regime_field", defaults.regime_field)),
            value_fields=tuple(value.get("value_fields", defaults.value_fields)),
            limitations=tuple(value.get("limitations", defaults.limitations)),
        )


@dataclass(frozen=True, slots=True)
class SymbolAlignmentSummary:
    """Scalar alignment and coverage summary for one required symbol."""

    symbol: str
    input_count: int
    aligned_snapshot_count: int
    missing_timestamp_count: int
    unavailable_timestamp_count: int
    coverage_ratio: float | None
    missingness_rate: float | None
    first_event_ts: str | None
    last_event_ts: str | None

    def to_dict(self) -> dict[str, JsonScalar]:
        return {
            "symbol": self.symbol,
            "input_count": self.input_count,
            "aligned_snapshot_count": self.aligned_snapshot_count,
            "missing_timestamp_count": self.missing_timestamp_count,
            "unavailable_timestamp_count": self.unavailable_timestamp_count,
            "coverage_ratio": self.coverage_ratio,
            "missingness_rate": self.missingness_rate,
            "first_event_ts": self.first_event_ts,
            "last_event_ts": self.last_event_ts,
        }


@dataclass(frozen=True, slots=True)
class PairRelationshipSummary:
    """Scalar zero-lag pair relationship and spread/residual proxy summary."""

    pair_id: str
    anchor_symbol: str
    peer_symbol: str
    aligned_snapshot_count: int
    zero_lag_pearson: float | None
    zero_lag_rank: float | None
    spread_proxy_mean: float | None
    spread_proxy_abs_mean: float | None
    spread_proxy_min: float | None
    spread_proxy_max: float | None
    residual_proxy_mean: float | None
    residual_proxy_abs_mean: float | None

    def to_dict(self) -> dict[str, JsonScalar]:
        return {
            "pair_id": self.pair_id,
            "anchor_symbol": self.anchor_symbol,
            "peer_symbol": self.peer_symbol,
            "aligned_snapshot_count": self.aligned_snapshot_count,
            "zero_lag_pearson": self.zero_lag_pearson,
            "zero_lag_rank": self.zero_lag_rank,
            "spread_proxy_mean": self.spread_proxy_mean,
            "spread_proxy_abs_mean": self.spread_proxy_abs_mean,
            "spread_proxy_min": self.spread_proxy_min,
            "spread_proxy_max": self.spread_proxy_max,
            "residual_proxy_mean": self.residual_proxy_mean,
            "residual_proxy_abs_mean": self.residual_proxy_abs_mean,
        }


@dataclass(frozen=True, slots=True)
class LeadLagSummary:
    """Scalar ordered-pair lead/lag summary."""

    pair_id: str
    leader_symbol: str
    target_symbol: str
    lag_steps: int
    mean_lag_seconds: float | None
    sample_count: int
    pearson: float | None
    rank: float | None

    def to_dict(self) -> dict[str, JsonScalar]:
        return {
            "pair_id": self.pair_id,
            "leader_symbol": self.leader_symbol,
            "target_symbol": self.target_symbol,
            "lag_steps": self.lag_steps,
            "mean_lag_seconds": self.mean_lag_seconds,
            "sample_count": self.sample_count,
            "pearson": self.pearson,
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class RegimeCorrelationSummary:
    """Scalar regime-conditioned pair-correlation summary."""

    regime: str
    pair_id: str
    anchor_symbol: str
    peer_symbol: str
    sample_count: int
    pearson: float | None
    rank: float | None

    def to_dict(self) -> dict[str, JsonScalar]:
        return {
            "regime": self.regime,
            "pair_id": self.pair_id,
            "anchor_symbol": self.anchor_symbol,
            "peer_symbol": self.peer_symbol,
            "sample_count": self.sample_count,
            "pearson": self.pearson,
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class CrossMarketDiagnosticsReport:
    """Cross-market specialization of the shared diagnostics report contract."""

    diagnostics_report: DiagnosticsReport
    diagnostics_run_record: DiagnosticsRunRecord
    symbol_summaries: tuple[SymbolAlignmentSummary, ...]
    pair_summaries: tuple[PairRelationshipSummary, ...]
    lead_lag_summaries: tuple[LeadLagSummary, ...]
    regime_summaries: tuple[RegimeCorrelationSummary, ...]
    sync_summary_items: tuple[tuple[str, JsonScalar], ...]

    @property
    def status(self) -> StudyRunResultState:
        return self.diagnostics_report.status

    @property
    def coverage_summary(self) -> dict[str, JsonScalar]:
        return self.diagnostics_report.coverage_summary

    @property
    def quality_summary(self) -> dict[str, JsonScalar]:
        return self.diagnostics_report.quality_summary

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.diagnostics_report.limitations

    @property
    def rejection_reasons(self) -> tuple[RunRejectionReason, ...]:
        return self.diagnostics_report.rejection_reasons

    @property
    def timestamp_sync_summary(self) -> dict[str, JsonScalar]:
        return dict(self.sync_summary_items)

    def to_ref(self):
        """Return the shared diagnostics report reference."""

        return self.diagnostics_report.to_ref()

    def to_dict(self) -> dict[str, object]:
        """Return the shared report payload plus scalar cross-market sections."""

        payload = self.diagnostics_report.to_dict()
        payload.update(
            {
                "report_type": "CrossMarketDiagnosticsReport",
                "cross_market_timestamp_sync": self.timestamp_sync_summary,
                "cross_market_symbol_summaries": [
                    summary.to_dict() for summary in self.symbol_summaries
                ],
                "cross_market_pair_summaries": [
                    summary.to_dict() for summary in self.pair_summaries
                ],
                "cross_market_lead_lag_summaries": [
                    summary.to_dict() for summary in self.lead_lag_summaries
                ],
                "cross_market_regime_summaries": [
                    summary.to_dict() for summary in self.regime_summaries
                ],
                "diagnostics_run_record": self.diagnostics_run_record.to_dict(),
            }
        )
        return payload


@dataclass(frozen=True, slots=True)
class CrossMarketDiagnosticsRunResult:
    """Cross-market diagnostics report plus the visible diagnostics run record."""

    report: CrossMarketDiagnosticsReport
    record: DiagnosticsRunRecord

    def to_dict(self) -> dict[str, object]:
        return {
            "report": self.report.to_dict(),
            "record": self.record.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class _RuntimeInputSummary:
    dataset_version_id: str
    lifecycle_state: str
    dataset_source: str
    alpha_spec_ref: str
    study_spec_ref: str
    feature_packs: tuple[Mapping[str, Any], ...]
    label_packs: tuple[Mapping[str, Any], ...]
    canonical_input_views: tuple[Mapping[str, Any], ...]
    dataset_scope: Mapping[str, Any]
    partition_scope: Mapping[str, Any]
    governance_metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class _Observation:
    symbol: str
    event_ts: datetime
    available_ts: datetime
    decision_ts: datetime | None
    metric: float
    data_version: str | None
    regime: str | None


@dataclass(frozen=True, slots=True)
class _SynchronizedSnapshot:
    event_ts: datetime
    decision_ts: datetime
    availability_skew_seconds: float
    observations: Mapping[str, _Observation]
    regime: str | None


@dataclass(frozen=True, slots=True)
class _PreparedInputs:
    observations: tuple[_Observation, ...]
    input_count: int
    missing_available_ts_count: int
    unavailable_at_decision_count: int
    missing_metric_count: int
    label_only_field_count: int
    reasons_rejected: tuple[RunRejectionReason, ...]
    reasons_failed: tuple[RunRejectionReason, ...]
    reasons_inconclusive: tuple[RunRejectionReason, ...]


@dataclass(frozen=True, slots=True)
class _AlignmentResult:
    snapshots: tuple[_SynchronizedSnapshot, ...]
    timestamp_count: int
    input_counts_by_symbol: Mapping[str, int]
    missing_counts_by_symbol: Mapping[str, int]
    unavailable_counts_by_symbol: Mapping[str, int]
    first_event_by_symbol: Mapping[str, datetime]
    last_event_by_symbol: Mapping[str, datetime]
    duplicate_aligned_count: int
    reasons_rejected: tuple[RunRejectionReason, ...]
    reasons_failed: tuple[RunRejectionReason, ...]
    reasons_inconclusive: tuple[RunRejectionReason, ...]


@dataclass(frozen=True, slots=True)
class _Evaluation:
    status: StudyRunResultState
    quality_gates: tuple[DiagnosticsQualityGate, ...]
    rejection_reasons: tuple[RunRejectionReason, ...]


def resolve_cross_market_dataset_version(
    registry_path: str | Path,
    dataset_version_id: object,
    *,
    required_symbols: Sequence[str] = DEFAULT_REQUIRED_SYMBOLS,
    resolver: DatasetVersionResolver = resolve_dataset_version,
) -> DatasetVersion:
    """Resolve a DatasetVersion through the official registry adapter."""

    record = resolver(registry_path, dataset_version_id)
    if record is None:
        raise CrossMarketDiagnosticsError("DatasetVersion was not found in the version registry")
    required = {str(symbol).upper() for symbol in required_symbols}
    present = {symbol.upper() for symbol in record.symbol_universe}
    missing = sorted(required - present)
    if missing:
        raise CrossMarketDiagnosticsError(
            "DatasetVersion symbol_universe is missing required cross-market symbols: "
            + ", ".join(missing)
        )
    return record


def build_cross_market_diagnostics_run(
    *,
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    config: CrossMarketDiagnosticsConfig | Mapping[str, Any] | None = None,
) -> CrossMarketDiagnosticsRunResult:
    """Build a cross-market diagnostics report plus visible diagnostics record."""

    report = build_cross_market_diagnostics_report(
        diagnostics_run_spec=diagnostics_run_spec,
        runtime_input_pack=runtime_input_pack,
        observations=observations,
        config=config,
    )
    return CrossMarketDiagnosticsRunResult(report=report, record=report.diagnostics_run_record)


def build_cross_market_diagnostics_report(
    *,
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    runtime_input_pack: RuntimeInputPack | Mapping[str, Any],
    observations: Iterable[Mapping[str, Any]],
    config: CrossMarketDiagnosticsConfig | Mapping[str, Any] | None = None,
) -> CrossMarketDiagnosticsReport:
    """Build a descriptive cross-market diagnostics report from resolved inputs."""

    _require_cross_market_family(diagnostics_run_spec)
    active_config = _coerce_config(config)
    runtime_summary = _runtime_input_summary(runtime_input_pack)
    runtime_reasons = _runtime_input_reasons(runtime_summary, active_config)
    prepared = _prepare_observations(
        observations=observations,
        runtime_summary=runtime_summary,
        config=active_config,
    )
    alignment = _align_observations(prepared.observations, active_config)
    symbol_summaries = _symbol_summaries(alignment, active_config)
    pair_summaries = _pair_summaries(alignment.snapshots, active_config)
    lead_lag_summaries = _lead_lag_summaries(alignment.snapshots, active_config)
    regime_summaries = _regime_summaries(alignment.snapshots, active_config)
    sync_summary = _sync_summary(alignment, active_config)

    evaluation = _evaluate(
        runtime_reasons=runtime_reasons,
        prepared=prepared,
        alignment=alignment,
        symbol_summaries=symbol_summaries,
        pair_summaries=pair_summaries,
        lead_lag_summaries=lead_lag_summaries,
        regime_summaries=regime_summaries,
        sync_summary=sync_summary,
        config=active_config,
    )
    common_report = DiagnosticsReport(
        report_kind=CROSS_MARKET_DIAGNOSTICS_REPORT_KIND,
        diagnostics_family=DiagnosticsFamily.CROSS_MARKET,
        diagnostics_run_spec_ref=diagnostics_run_spec,
        status=evaluation.status,
        lineage_refs=_lineage_refs(diagnostics_run_spec, runtime_summary),
        coverage_summary=_coverage_summary(
            prepared=prepared,
            alignment=alignment,
            symbol_summaries=symbol_summaries,
            runtime_summary=runtime_summary,
            config=active_config,
        ),
        quality_summary=_quality_summary(
            evaluation=evaluation,
            pair_summaries=pair_summaries,
            lead_lag_summaries=lead_lag_summaries,
            regime_summaries=regime_summaries,
            sync_summary=sync_summary,
        ),
        limitations=_limitations(regime_summaries, active_config),
        quality_gates=evaluation.quality_gates,
        rejection_reasons=evaluation.rejection_reasons,
        report_metadata={
            "threshold_profile": CROSS_MARKET_DIAGNOSTICS_THRESHOLD_PROFILE,
            "descriptive_tier": "tier_0_cross_market_diagnostics",
            "orchestrated_research_primitives": "alpha_system.research.correlation",
            "required_symbols": ";".join(active_config.required_symbols),
        },
    )
    record = DiagnosticsRunRecord(
        diagnostics_run_spec_ref=diagnostics_run_spec,
        status=common_report.status,
        report_ref=common_report.to_ref(),
        rejection_reasons=common_report.rejection_reasons,
    )
    return CrossMarketDiagnosticsReport(
        diagnostics_report=common_report,
        diagnostics_run_record=record,
        symbol_summaries=symbol_summaries,
        pair_summaries=pair_summaries,
        lead_lag_summaries=lead_lag_summaries,
        regime_summaries=regime_summaries,
        sync_summary_items=tuple(sync_summary.items()),
    )


def _runtime_input_summary(value: RuntimeInputPack | Mapping[str, Any]) -> _RuntimeInputSummary:
    if isinstance(value, RuntimeInputPack):
        return _RuntimeInputSummary(
            dataset_version_id=value.dataset_version_id,
            lifecycle_state=value.dataset_lifecycle_state,
            dataset_source=value.dataset_source,
            alpha_spec_ref=value.alpha_spec_ref,
            study_spec_ref=value.study_spec_ref,
            feature_packs=tuple(pack.to_dict() for pack in value.feature_packs),
            label_packs=tuple(pack.to_dict() for pack in value.label_packs),
            canonical_input_views=tuple(view.to_dict() for view in value.canonical_input_views),
            dataset_scope=value.dataset_scope,
            partition_scope=value.partition_scope,
            governance_metadata=value.governance_metadata,
        )
    if not isinstance(value, Mapping):
        raise CrossMarketDiagnosticsError(
            f"runtime_input_pack must be RuntimeInputPack or mapping, got {type(value).__name__}"
        )
    dataset_version = value.get("dataset_version")
    if isinstance(dataset_version, Mapping):
        dataset_version_id = dataset_version.get("dataset_version_id")
        lifecycle_state = dataset_version.get("lifecycle_state")
        dataset_source = dataset_version.get("source")
    else:
        dataset_version_id = value.get("dataset_version_id")
        lifecycle_state = value.get("dataset_lifecycle_state", value.get("lifecycle_state"))
        dataset_source = value.get("dataset_source", value.get("source"))
    return _RuntimeInputSummary(
        dataset_version_id=_optional_text(dataset_version_id),
        lifecycle_state=_optional_text(lifecycle_state),
        dataset_source=_optional_text(dataset_source),
        alpha_spec_ref=_optional_text(value.get("alpha_spec_ref")),
        study_spec_ref=_optional_text(value.get("study_spec_ref")),
        feature_packs=_mapping_sequence(value.get("feature_packs", ()), "feature_packs"),
        label_packs=_mapping_sequence(value.get("label_packs", ()), "label_packs"),
        canonical_input_views=_mapping_sequence(
            value.get("canonical_input_views", ()),
            "canonical_input_views",
        ),
        dataset_scope=_mapping(value.get("dataset_scope", {}), "dataset_scope"),
        partition_scope=_mapping(value.get("partition_scope", {}), "partition_scope"),
        governance_metadata=_mapping(value.get("governance_metadata", {}), "governance_metadata"),
    )


def _runtime_input_reasons(
    runtime_summary: _RuntimeInputSummary,
    config: CrossMarketDiagnosticsConfig,
) -> tuple[RunRejectionReason, ...]:
    reasons: list[RunRejectionReason] = []
    if not runtime_summary.alpha_spec_ref or not runtime_summary.study_spec_ref:
        reasons.append(
            RunRejectionReason(
                code="governance_input_missing",
                message=(
                    "Cross-market diagnostics require approved AlphaSpec and StudySpec references."
                ),
            )
        )
    if runtime_summary.lifecycle_state not in ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES:
        reasons.append(
            RunRejectionReason(
                code="data_unavailable",
                message=(
                    "DatasetVersion lifecycle state is not accepted for research "
                    "runtime diagnostics."
                ),
            )
        )
    lowered_source = runtime_summary.dataset_source.lower()
    if any(marker in lowered_source for marker in MIXED_SOURCE_MARKERS):
        reasons.append(
            RunRejectionReason(
                code="data_unavailable",
                message=(
                    "Cross-market diagnostics require one DatasetVersion family and "
                    "reject mixed Databento plus IBKR sources."
                ),
            )
        )
    expected_dataset_id = runtime_summary.dataset_version_id
    for pack in (*runtime_summary.feature_packs, *runtime_summary.label_packs):
        pack_dataset_id = _nested_text(pack, "dataset_version_id")
        if pack_dataset_id and pack_dataset_id != expected_dataset_id:
            reasons.append(
                RunRejectionReason(
                    code="data_unavailable",
                    message=(
                        "Feature and label packs must be bound to the same accepted DatasetVersion."
                    ),
                )
            )
            break
    for index, pack in enumerate(runtime_summary.feature_packs):
        available_ts = pack.get("available_ts")
        if (
            not isinstance(available_ts, Mapping)
            or not available_ts.get("first")
            or not available_ts.get("last")
        ):
            reasons.append(
                RunRejectionReason(
                    code="leakage_risk",
                    message=f"Feature pack {index} does not carry an available_ts window.",
                )
            )
            break
    for index, pack in enumerate(runtime_summary.label_packs):
        label_available_ts = pack.get("label_available_ts")
        if (
            not isinstance(label_available_ts, Mapping)
            or not label_available_ts.get("first")
            or not label_available_ts.get("last")
        ):
            reasons.append(
                RunRejectionReason(
                    code="leakage_risk",
                    message=f"Label pack {index} does not carry a label_available_ts window.",
                )
            )
            break
    partition_id = _nested_text(runtime_summary.partition_scope, "partition_id")
    if partition_id in LOCKED_PARTITION_IDS and not runtime_summary.governance_metadata:
        reasons.append(
            RunRejectionReason(
                code="leakage_risk",
                message=(
                    "Locked-test partition diagnostics require governance contamination metadata."
                ),
            )
        )
    scoped_symbols = _symbols_from_scope(runtime_summary.dataset_scope)
    if scoped_symbols:
        missing = sorted(set(config.required_symbols) - scoped_symbols)
        if missing:
            reasons.append(
                RunRejectionReason(
                    code="data_unavailable",
                    message="Dataset scope is missing required cross-market symbols: "
                    + ", ".join(missing),
                )
            )
    return _unique_reasons(reasons)


def _prepare_observations(
    *,
    observations: Iterable[Mapping[str, Any]],
    runtime_summary: _RuntimeInputSummary,
    config: CrossMarketDiagnosticsConfig,
) -> _PreparedInputs:
    parsed: list[_Observation] = []
    rejected: list[RunRejectionReason] = []
    failed: list[RunRejectionReason] = []
    inconclusive: list[RunRejectionReason] = []
    input_count = 0
    missing_available_ts_count = 0
    unavailable_at_decision_count = 0
    missing_metric_count = 0
    label_only_field_count = 0

    for row_number, row in enumerate(observations):
        if not isinstance(row, Mapping):
            raise CrossMarketDiagnosticsError(
                f"cross-market diagnostics observations must be mappings, got {type(row).__name__}"
            )
        input_count += 1
        label_fields = sorted(LABEL_ONLY_FIELDS.intersection(row))
        if label_fields:
            label_only_field_count += 1
            continue
        symbol = _symbol(row)
        if symbol not in config.required_symbols:
            continue
        data_version = (
            _optional_text(row.get("data_version", row.get("dataset_version_id"))) or None
        )
        if data_version is not None and data_version != runtime_summary.dataset_version_id:
            rejected.append(
                RunRejectionReason(
                    code="data_unavailable",
                    message=(
                        "Observation DatasetVersion does not match the resolved runtime input pack."
                    ),
                )
            )
            continue
        event_ts = _datetime_or_none(
            _first_present(row, ("event_ts", "bar_end_ts")), f"row {row_number} event_ts"
        )
        available_ts = _datetime_or_none(row.get("available_ts"), f"row {row_number} available_ts")
        decision_ts = _datetime_or_none(
            row.get("decision_ts"), f"row {row_number} decision_ts", optional=True
        )
        metric = _metric(row, config.value_fields)
        if event_ts is None:
            failed.append(
                RunRejectionReason(
                    code="data_unavailable",
                    message="One or more cross-market observations omitted event_ts.",
                )
            )
            continue
        if available_ts is None:
            missing_available_ts_count += 1
            continue
        if decision_ts is not None and available_ts > decision_ts:
            unavailable_at_decision_count += 1
            continue
        if metric is None:
            missing_metric_count += 1
            continue
        parsed.append(
            _Observation(
                symbol=symbol,
                event_ts=event_ts,
                available_ts=available_ts,
                decision_ts=decision_ts,
                metric=metric,
                data_version=data_version,
                regime=_optional_text(row.get(config.regime_field, row.get("regime"))) or None,
            )
        )

    if input_count == 0:
        inconclusive.append(
            RunRejectionReason(
                code="inconclusive",
                message="Cross-market diagnostics received no observations to summarize.",
            )
        )
    if missing_available_ts_count:
        rejected.append(
            RunRejectionReason(
                code="leakage_risk",
                message="One or more cross-market observations omitted available_ts.",
            )
        )
    if unavailable_at_decision_count:
        rejected.append(
            RunRejectionReason(
                code="leakage_risk",
                message=(
                    "One or more cross-market observations were unavailable at the "
                    "supplied decision_ts."
                ),
            )
        )
    if missing_metric_count:
        failed.append(
            RunRejectionReason(
                code="data_unavailable",
                message=(
                    "One or more cross-market observations omitted a configured diagnostic metric."
                ),
            )
        )
    if label_only_field_count:
        rejected.append(
            RunRejectionReason(
                code="leakage_risk",
                message="Cross-market diagnostics observations must not expose label-only fields.",
            )
        )
    observed_symbols = {row.symbol for row in parsed}
    missing_symbols = sorted(set(config.required_symbols) - observed_symbols)
    if input_count and missing_symbols:
        rejected.append(
            RunRejectionReason(
                code="data_unavailable",
                message="No diagnostics observations were supplied for required symbols: "
                + ", ".join(missing_symbols),
            )
        )
    return _PreparedInputs(
        observations=tuple(parsed),
        input_count=input_count,
        missing_available_ts_count=missing_available_ts_count,
        unavailable_at_decision_count=unavailable_at_decision_count,
        missing_metric_count=missing_metric_count,
        label_only_field_count=label_only_field_count,
        reasons_rejected=_unique_reasons(rejected),
        reasons_failed=_unique_reasons(failed),
        reasons_inconclusive=_unique_reasons(inconclusive),
    )


def _align_observations(
    observations: Sequence[_Observation],
    config: CrossMarketDiagnosticsConfig,
) -> _AlignmentResult:
    required = set(config.required_symbols)
    grouped: dict[datetime, list[_Observation]] = defaultdict(list)
    input_counts: Counter[str] = Counter()
    first_event: dict[str, datetime] = {}
    last_event: dict[str, datetime] = {}
    for observation in observations:
        grouped[observation.event_ts].append(observation)
        input_counts[observation.symbol] += 1
        first_event[observation.symbol] = min(
            first_event.get(observation.symbol, observation.event_ts), observation.event_ts
        )
        last_event[observation.symbol] = max(
            last_event.get(observation.symbol, observation.event_ts), observation.event_ts
        )

    missing_counts: Counter[str] = Counter()
    unavailable_counts: Counter[str] = Counter()
    duplicate_aligned_count = 0
    rejected: list[RunRejectionReason] = []
    snapshots: list[_SynchronizedSnapshot] = []

    for event_ts, rows in sorted(grouped.items()):
        by_symbol: dict[str, _Observation] = {}
        duplicate_symbols: set[str] = set()
        for row in rows:
            if row.symbol not in required:
                continue
            if row.symbol in by_symbol:
                duplicate_symbols.add(row.symbol)
                continue
            by_symbol[row.symbol] = row
        if duplicate_symbols:
            duplicate_aligned_count += len(duplicate_symbols)
            continue
        for symbol in config.required_symbols:
            if symbol not in by_symbol:
                missing_counts[symbol] += 1
        if set(by_symbol) != required:
            continue
        decision_candidates = {
            row.decision_ts for row in by_symbol.values() if row.decision_ts is not None
        }
        if len(decision_candidates) > 1:
            rejected.append(
                RunRejectionReason(
                    code="leakage_risk",
                    message=(
                        "Aligned cross-market observations for one timestamp disagree "
                        "on decision_ts."
                    ),
                )
            )
            continue
        decision_ts = (
            next(iter(decision_candidates))
            if decision_candidates
            else max(row.available_ts for row in by_symbol.values())
        )
        assert decision_ts is not None
        late_symbols = [
            symbol for symbol, row in by_symbol.items() if row.available_ts > decision_ts
        ]
        if late_symbols:
            for symbol in late_symbols:
                unavailable_counts[symbol] += 1
            continue
        available_times = [row.available_ts for row in by_symbol.values()]
        availability_skew = (max(available_times) - min(available_times)).total_seconds()
        regimes = {row.regime for row in by_symbol.values() if row.regime}
        snapshots.append(
            _SynchronizedSnapshot(
                event_ts=event_ts,
                decision_ts=decision_ts,
                availability_skew_seconds=availability_skew,
                observations=by_symbol,
                regime=next(iter(regimes)) if len(regimes) == 1 else ("mixed" if regimes else None),
            )
        )

    if duplicate_aligned_count:
        rejected.append(
            RunRejectionReason(
                code="data_unavailable",
                message=(
                    "Duplicate symbol observations were found at one or more "
                    "cross-market timestamps."
                ),
            )
        )

    timestamp_count = len(grouped)
    return _AlignmentResult(
        snapshots=tuple(snapshots),
        timestamp_count=timestamp_count,
        input_counts_by_symbol=dict(input_counts),
        missing_counts_by_symbol=dict(missing_counts),
        unavailable_counts_by_symbol=dict(unavailable_counts),
        first_event_by_symbol=first_event,
        last_event_by_symbol=last_event,
        duplicate_aligned_count=duplicate_aligned_count,
        reasons_rejected=_unique_reasons(rejected),
        reasons_failed=(),
        reasons_inconclusive=(),
    )


def _symbol_summaries(
    alignment: _AlignmentResult,
    config: CrossMarketDiagnosticsConfig,
) -> tuple[SymbolAlignmentSummary, ...]:
    summaries: list[SymbolAlignmentSummary] = []
    timestamp_count = alignment.timestamp_count
    aligned_count = len(alignment.snapshots)
    for symbol in config.required_symbols:
        missing_count = int(alignment.missing_counts_by_symbol.get(symbol, 0))
        unavailable_count = int(alignment.unavailable_counts_by_symbol.get(symbol, 0))
        coverage_ratio = None if timestamp_count == 0 else aligned_count / timestamp_count
        missingness_rate = (
            None if timestamp_count == 0 else (missing_count + unavailable_count) / timestamp_count
        )
        summaries.append(
            SymbolAlignmentSummary(
                symbol=symbol,
                input_count=int(alignment.input_counts_by_symbol.get(symbol, 0)),
                aligned_snapshot_count=aligned_count,
                missing_timestamp_count=missing_count,
                unavailable_timestamp_count=unavailable_count,
                coverage_ratio=coverage_ratio,
                missingness_rate=missingness_rate,
                first_event_ts=_iso_or_none(alignment.first_event_by_symbol.get(symbol)),
                last_event_ts=_iso_or_none(alignment.last_event_by_symbol.get(symbol)),
            )
        )
    return tuple(summaries)


def _pair_summaries(
    snapshots: Sequence[_SynchronizedSnapshot],
    config: CrossMarketDiagnosticsConfig,
) -> tuple[PairRelationshipSummary, ...]:
    summaries: list[PairRelationshipSummary] = []
    for anchor, peer in combinations(config.required_symbols, 2):
        anchor_metrics = [snapshot.observations[anchor].metric for snapshot in snapshots]
        peer_metrics = [snapshot.observations[peer].metric for snapshot in snapshots]
        corr = _correlation(anchor_metrics, {peer: peer_metrics}).get(peer, {})
        spreads = [
            peer_value - anchor_value
            for anchor_value, peer_value in zip(anchor_metrics, peer_metrics, strict=True)
        ]
        summaries.append(
            PairRelationshipSummary(
                pair_id=f"{anchor}_{peer}",
                anchor_symbol=anchor,
                peer_symbol=peer,
                aligned_snapshot_count=len(spreads),
                zero_lag_pearson=_scalar_float(corr.get("pearson")),
                zero_lag_rank=_scalar_float(corr.get("rank")),
                spread_proxy_mean=_mean(spreads),
                spread_proxy_abs_mean=_mean(abs(value) for value in spreads),
                spread_proxy_min=_min(spreads),
                spread_proxy_max=_max(spreads),
                residual_proxy_mean=_mean(spreads),
                residual_proxy_abs_mean=_mean(abs(value) for value in spreads),
            )
        )
    return tuple(summaries)


def _lead_lag_summaries(
    snapshots: Sequence[_SynchronizedSnapshot],
    config: CrossMarketDiagnosticsConfig,
) -> tuple[LeadLagSummary, ...]:
    summaries: list[LeadLagSummary] = []
    for leader, target in permutations(config.required_symbols, 2):
        for lag_steps in config.lead_lag_steps:
            if lag_steps == 0:
                continue
            leader_metrics: list[float] = []
            target_metrics: list[float] = []
            lag_seconds: list[float] = []
            for index in range(lag_steps, len(snapshots)):
                leader_snapshot = snapshots[index - lag_steps]
                target_snapshot = snapshots[index]
                leader_metrics.append(leader_snapshot.observations[leader].metric)
                target_metrics.append(target_snapshot.observations[target].metric)
                lag_seconds.append(
                    (target_snapshot.event_ts - leader_snapshot.event_ts).total_seconds()
                )
            corr = _correlation(leader_metrics, {target: target_metrics}).get(target, {})
            summaries.append(
                LeadLagSummary(
                    pair_id=f"{leader}_leads_{target}",
                    leader_symbol=leader,
                    target_symbol=target,
                    lag_steps=lag_steps,
                    mean_lag_seconds=_mean(lag_seconds),
                    sample_count=len(leader_metrics),
                    pearson=_scalar_float(corr.get("pearson")),
                    rank=_scalar_float(corr.get("rank")),
                )
            )
    return tuple(summaries)


def _regime_summaries(
    snapshots: Sequence[_SynchronizedSnapshot],
    config: CrossMarketDiagnosticsConfig,
) -> tuple[RegimeCorrelationSummary, ...]:
    by_regime: dict[str, list[_SynchronizedSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        if snapshot.regime:
            by_regime[snapshot.regime].append(snapshot)

    summaries: list[RegimeCorrelationSummary] = []
    for regime, regime_snapshots in sorted(by_regime.items()):
        for anchor, peer in combinations(config.required_symbols, 2):
            anchor_metrics = [snapshot.observations[anchor].metric for snapshot in regime_snapshots]
            peer_metrics = [snapshot.observations[peer].metric for snapshot in regime_snapshots]
            corr = _correlation(anchor_metrics, {peer: peer_metrics}).get(peer, {})
            summaries.append(
                RegimeCorrelationSummary(
                    regime=regime,
                    pair_id=f"{anchor}_{peer}",
                    anchor_symbol=anchor,
                    peer_symbol=peer,
                    sample_count=len(anchor_metrics),
                    pearson=_scalar_float(corr.get("pearson")),
                    rank=_scalar_float(corr.get("rank")),
                )
            )
    return tuple(summaries)


def _sync_summary(
    alignment: _AlignmentResult,
    config: CrossMarketDiagnosticsConfig,
) -> dict[str, JsonScalar]:
    skews = [snapshot.availability_skew_seconds for snapshot in alignment.snapshots]
    synchronized_count = sum(1 for skew in skews if skew <= config.max_timestamp_skew_seconds)
    aligned_count = len(alignment.snapshots)
    return {
        "timestamp_count": alignment.timestamp_count,
        "aligned_snapshot_count": aligned_count,
        "synchronized_snapshot_count": synchronized_count,
        "timestamp_sync_ratio": None if aligned_count == 0 else synchronized_count / aligned_count,
        "mean_timestamp_skew_seconds": _mean(skews),
        "max_timestamp_skew_seconds": _max(skews),
        "configured_max_timestamp_skew_seconds": config.max_timestamp_skew_seconds,
    }


def _evaluate(
    *,
    runtime_reasons: Sequence[RunRejectionReason],
    prepared: _PreparedInputs,
    alignment: _AlignmentResult,
    symbol_summaries: Sequence[SymbolAlignmentSummary],
    pair_summaries: Sequence[PairRelationshipSummary],
    lead_lag_summaries: Sequence[LeadLagSummary],
    regime_summaries: Sequence[RegimeCorrelationSummary],
    sync_summary: Mapping[str, JsonScalar],
    config: CrossMarketDiagnosticsConfig,
) -> _Evaluation:
    rejected = list(runtime_reasons)
    rejected.extend(prepared.reasons_rejected)
    rejected.extend(alignment.reasons_rejected)
    failed = list(prepared.reasons_failed)
    failed.extend(alignment.reasons_failed)
    inconclusive = list(prepared.reasons_inconclusive)
    inconclusive.extend(alignment.reasons_inconclusive)

    aligned_count = len(alignment.snapshots)
    if prepared.input_count and aligned_count < config.min_aligned_snapshots:
        inconclusive.append(
            RunRejectionReason(
                code="low_sample",
                message=(
                    "Aligned cross-market snapshots are below the configured descriptive minimum."
                ),
            )
        )
    for summary in symbol_summaries:
        if (
            summary.coverage_ratio is not None
            and summary.coverage_ratio < config.min_symbol_coverage_ratio
        ):
            failed.append(
                RunRejectionReason(
                    code="low_coverage",
                    message=(
                        "Per-symbol aligned coverage is below the configured "
                        "cross-market threshold."
                    ),
                )
            )
            break
    for summary in symbol_summaries:
        if (
            summary.missingness_rate is not None
            and summary.missingness_rate > config.max_missingness_rate
        ):
            failed.append(
                RunRejectionReason(
                    code="data_unavailable",
                    message="Per-symbol missingness exceeds the configured cross-market threshold.",
                )
            )
            break
    max_skew = sync_summary.get("max_timestamp_skew_seconds")
    if isinstance(max_skew, float | int) and max_skew > config.max_timestamp_skew_seconds:
        failed.append(
            RunRejectionReason(
                code="timestamp_sync_weak",
                message=(
                    "Cross-market availability skew exceeds the configured timestamp "
                    "synchronization threshold."
                ),
            )
        )
    if aligned_count >= config.min_aligned_snapshots and not any(
        summary.zero_lag_pearson is not None or summary.zero_lag_rank is not None
        for summary in pair_summaries
    ):
        inconclusive.append(
            RunRejectionReason(
                code="inconclusive",
                message=(
                    "Zero-lag cross-market correlation summaries were unavailable "
                    "from the aligned snapshots."
                ),
            )
        )

    rejected = list(_unique_reasons(rejected))
    failed = list(_unique_reasons(failed))
    inconclusive = list(_unique_reasons(inconclusive))
    if rejected:
        status = StudyRunResultState.REJECTED
    elif failed:
        status = StudyRunResultState.DIAGNOSTICS_FAILED
    elif inconclusive:
        status = StudyRunResultState.INCONCLUSIVE
    else:
        status = StudyRunResultState.DIAGNOSTICS_COMPLETE
    reasons = tuple(rejected + failed + inconclusive)
    gates = _quality_gates(
        status=status,
        symbol_summaries=symbol_summaries,
        pair_summaries=pair_summaries,
        lead_lag_summaries=lead_lag_summaries,
        regime_summaries=regime_summaries,
        sync_summary=sync_summary,
        config=config,
        rejected_count=len(rejected),
    )
    return _Evaluation(status=status, quality_gates=gates, rejection_reasons=reasons)


def _quality_gates(
    *,
    status: StudyRunResultState,
    symbol_summaries: Sequence[SymbolAlignmentSummary],
    pair_summaries: Sequence[PairRelationshipSummary],
    lead_lag_summaries: Sequence[LeadLagSummary],
    regime_summaries: Sequence[RegimeCorrelationSummary],
    sync_summary: Mapping[str, JsonScalar],
    config: CrossMarketDiagnosticsConfig,
    rejected_count: int,
) -> tuple[DiagnosticsQualityGate, ...]:
    min_coverage = min(
        (
            summary.coverage_ratio
            for summary in symbol_summaries
            if summary.coverage_ratio is not None
        ),
        default=None,
    )
    max_missingness = max(
        (
            summary.missingness_rate
            for summary in symbol_summaries
            if summary.missingness_rate is not None
        ),
        default=None,
    )
    aligned_count = int(sync_summary.get("aligned_snapshot_count") or 0)
    synchronized_count = int(sync_summary.get("synchronized_snapshot_count") or 0)
    pair_available = any(
        summary.zero_lag_pearson is not None or summary.zero_lag_rank is not None
        for summary in pair_summaries
    )
    lead_lag_available = any(
        summary.pearson is not None or summary.rank is not None for summary in lead_lag_summaries
    )
    regime_available = any(
        summary.pearson is not None or summary.rank is not None for summary in regime_summaries
    )
    timestamp_status = (
        DiagnosticsQualityGateStatus.PASS
        if synchronized_count == aligned_count and aligned_count > 0
        else DiagnosticsQualityGateStatus.FAIL
        if aligned_count > 0
        else DiagnosticsQualityGateStatus.INCONCLUSIVE
    )
    return (
        DiagnosticsQualityGate(
            gate_id="cross_market_input_gate",
            name="Input gate",
            status=DiagnosticsQualityGateStatus.FAIL
            if rejected_count
            else DiagnosticsQualityGateStatus.PASS,
            summary=(
                "Resolved governance, DatasetVersion, feature-pack, label-pack, "
                "and available_ts references are checked."
            ),
            metric_refs={"rejected_reason_count": rejected_count},
        ),
        DiagnosticsQualityGate(
            gate_id="cross_market_alignment_gate",
            name="Alignment gate",
            status=DiagnosticsQualityGateStatus.PASS
            if aligned_count >= config.min_aligned_snapshots
            else DiagnosticsQualityGateStatus.INCONCLUSIVE,
            summary=(
                "Exact-timestamp synchronized snapshots are summarized without forward filling."
            ),
            metric_refs={
                "aligned_snapshot_count": aligned_count,
                "min_aligned_snapshots": config.min_aligned_snapshots,
            },
        ),
        DiagnosticsQualityGate(
            gate_id="cross_market_coverage_gate",
            name="Coverage gate",
            status=DiagnosticsQualityGateStatus.PASS
            if (
                min_coverage is not None
                and min_coverage >= config.min_symbol_coverage_ratio
                and (max_missingness or 0.0) <= config.max_missingness_rate
            )
            else DiagnosticsQualityGateStatus.FAIL
            if min_coverage is not None
            else DiagnosticsQualityGateStatus.INCONCLUSIVE,
            summary=(
                "Per-symbol coverage and missingness are summarized for the required instruments."
            ),
            metric_refs={
                "min_symbol_coverage_ratio": min_coverage,
                "configured_min_symbol_coverage_ratio": config.min_symbol_coverage_ratio,
                "max_symbol_missingness_rate": max_missingness,
                "configured_max_missingness_rate": config.max_missingness_rate,
            },
        ),
        DiagnosticsQualityGate(
            gate_id="cross_market_timestamp_sync_gate",
            name="Timestamp sync gate",
            status=timestamp_status,
            summary=(
                "Availability skew across instruments is summarized at each synchronized timestamp."
            ),
            metric_refs={
                "synchronized_snapshot_count": synchronized_count,
                "aligned_snapshot_count": aligned_count,
                "max_timestamp_skew_seconds": sync_summary.get("max_timestamp_skew_seconds"),
                "configured_max_timestamp_skew_seconds": config.max_timestamp_skew_seconds,
            },
        ),
        DiagnosticsQualityGate(
            gate_id="cross_market_pair_correlation_gate",
            name="Pair correlation gate",
            status=DiagnosticsQualityGateStatus.PASS
            if pair_available
            else DiagnosticsQualityGateStatus.INCONCLUSIVE,
            summary="Zero-lag pair correlation summaries are delegated to research.correlation.",
            metric_refs={"pair_summary_count": len(pair_summaries)},
        ),
        DiagnosticsQualityGate(
            gate_id="cross_market_lead_lag_gate",
            name="Lead lag gate",
            status=DiagnosticsQualityGateStatus.PASS
            if lead_lag_available
            else DiagnosticsQualityGateStatus.INCONCLUSIVE,
            summary=(
                "Ordered lead/lag summaries use prior synchronized snapshots and "
                "delegate correlation to research.correlation."
            ),
            metric_refs={"lead_lag_summary_count": len(lead_lag_summaries)},
        ),
        DiagnosticsQualityGate(
            gate_id="cross_market_regime_gate",
            name="Regime gate",
            status=DiagnosticsQualityGateStatus.PASS
            if regime_available
            else DiagnosticsQualityGateStatus.WARN,
            summary=(
                "Regime-conditioned pair correlation is summarized when regime labels are supplied."
            ),
            metric_refs={"regime_summary_count": len(regime_summaries)},
            limitations=("Regime summaries depend on caller-supplied descriptive regime labels.",),
        ),
        DiagnosticsQualityGate(
            gate_id="cross_market_terminal_state_gate",
            name="Terminal state gate",
            status=DiagnosticsQualityGateStatus.PASS
            if status is StudyRunResultState.DIAGNOSTICS_COMPLETE
            else DiagnosticsQualityGateStatus.FAIL
            if status in {StudyRunResultState.REJECTED, StudyRunResultState.DIAGNOSTICS_FAILED}
            else DiagnosticsQualityGateStatus.INCONCLUSIVE,
            summary=(
                "The diagnostics terminal state and visible reasons are exposed "
                "through the shared report record."
            ),
            metric_refs={"terminal_state": status.value},
        ),
    )


def _coverage_summary(
    *,
    prepared: _PreparedInputs,
    alignment: _AlignmentResult,
    symbol_summaries: Sequence[SymbolAlignmentSummary],
    runtime_summary: _RuntimeInputSummary,
    config: CrossMarketDiagnosticsConfig,
) -> dict[str, JsonScalar]:
    observed_required_symbol_count = sum(
        1 for summary in symbol_summaries if summary.input_count > 0
    )
    min_coverage = min(
        (
            summary.coverage_ratio
            for summary in symbol_summaries
            if summary.coverage_ratio is not None
        ),
        default=None,
    )
    max_missingness = max(
        (
            summary.missingness_rate
            for summary in symbol_summaries
            if summary.missingness_rate is not None
        ),
        default=None,
    )
    return {
        "input_count": prepared.input_count,
        "required_symbol_count": len(config.required_symbols),
        "observed_required_symbol_count": observed_required_symbol_count,
        "timestamp_count": alignment.timestamp_count,
        "aligned_snapshot_count": len(alignment.snapshots),
        "missing_available_ts_count": prepared.missing_available_ts_count,
        "unavailable_at_decision_count": prepared.unavailable_at_decision_count,
        "missing_metric_count": prepared.missing_metric_count,
        "label_only_field_count": prepared.label_only_field_count,
        "duplicate_aligned_count": alignment.duplicate_aligned_count,
        "min_symbol_coverage_ratio": min_coverage,
        "max_symbol_missingness_rate": max_missingness,
        "dataset_lifecycle_accepted": runtime_summary.lifecycle_state
        in ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES,
        "feature_pack_count": len(runtime_summary.feature_packs),
        "label_pack_count": len(runtime_summary.label_packs),
        "canonical_input_view_count": len(runtime_summary.canonical_input_views),
    }


def _quality_summary(
    *,
    evaluation: _Evaluation,
    pair_summaries: Sequence[PairRelationshipSummary],
    lead_lag_summaries: Sequence[LeadLagSummary],
    regime_summaries: Sequence[RegimeCorrelationSummary],
    sync_summary: Mapping[str, JsonScalar],
) -> dict[str, JsonScalar]:
    gate_statuses = [gate.status for gate in evaluation.quality_gates]
    return {
        "diagnostic_complete": evaluation.status is StudyRunResultState.DIAGNOSTICS_COMPLETE,
        "quality_gate_count": len(evaluation.quality_gates),
        "failing_gate_count": sum(
            1 for status in gate_statuses if status is DiagnosticsQualityGateStatus.FAIL
        ),
        "inconclusive_gate_count": sum(
            1 for status in gate_statuses if status is DiagnosticsQualityGateStatus.INCONCLUSIVE
        ),
        "warning_gate_count": sum(
            1 for status in gate_statuses if status is DiagnosticsQualityGateStatus.WARN
        ),
        "pair_summary_count": len(pair_summaries),
        "lead_lag_summary_count": len(lead_lag_summaries),
        "regime_summary_count": len(regime_summaries),
        "max_zero_lag_abs_pearson": _max_abs(
            summary.zero_lag_pearson for summary in pair_summaries
        ),
        "max_lead_lag_abs_pearson": _max_abs(summary.pearson for summary in lead_lag_summaries),
        "max_regime_abs_pearson": _max_abs(summary.pearson for summary in regime_summaries),
        "mean_timestamp_skew_seconds": sync_summary.get("mean_timestamp_skew_seconds"),
        "max_timestamp_skew_seconds": sync_summary.get("max_timestamp_skew_seconds"),
        "residual_spread_pair_count": sum(
            1 for summary in pair_summaries if summary.residual_proxy_abs_mean is not None
        ),
        "rejection_reason_count": len(evaluation.rejection_reasons),
    }


def _limitations(
    regime_summaries: Sequence[RegimeCorrelationSummary],
    config: CrossMarketDiagnosticsConfig,
) -> tuple[str, ...]:
    limitations = list(config.limitations)
    if not regime_summaries:
        limitations.append(
            "Regime-conditioned correlation is limited because no descriptive regime "
            "labels were supplied."
        )
    return tuple(limitations)


def _lineage_refs(
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
    runtime_summary: _RuntimeInputSummary,
) -> dict[str, str]:
    spec_ref = _diagnostics_spec_ref(diagnostics_run_spec)
    refs = {
        "diagnostics_run_spec_id": spec_ref.diagnostics_run_spec_id,
        "dataset_version_id": runtime_summary.dataset_version_id,
        "alpha_spec_ref": runtime_summary.alpha_spec_ref,
        "study_spec_ref": runtime_summary.study_spec_ref,
    }
    if isinstance(diagnostics_run_spec, DiagnosticsRunSpec):
        refs.setdefault(
            "study_run_spec_id", diagnostics_run_spec.study_run_spec_ref.study_run_spec_id
        )
        refs.setdefault("runtime_plan_id", diagnostics_run_spec.runtime_plan_ref.plan_id)
    return {key: value for key, value in refs.items() if value}


def _correlation(
    candidate_metrics: Sequence[float],
    existing_metrics: Mapping[str, Sequence[float]],
) -> dict[str, dict[str, float | int | None]]:
    return research_correlation.correlations_to_existing_factors(
        candidate_metrics,
        existing_metrics,
    )


def _coerce_config(
    value: CrossMarketDiagnosticsConfig | Mapping[str, Any] | None,
) -> CrossMarketDiagnosticsConfig:
    if value is None:
        return CrossMarketDiagnosticsConfig()
    if isinstance(value, CrossMarketDiagnosticsConfig):
        return value
    if not isinstance(value, Mapping):
        raise CrossMarketDiagnosticsError(
            f"config must be CrossMarketDiagnosticsConfig or mapping, got {type(value).__name__}"
        )
    return CrossMarketDiagnosticsConfig.from_mapping(value)


def _diagnostics_spec_ref(
    value: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> DiagnosticsRunSpecRef:
    if isinstance(value, DiagnosticsRunSpec):
        return value.to_ref()
    if isinstance(value, DiagnosticsRunSpecRef):
        return value
    if not isinstance(value, Mapping):
        raise CrossMarketDiagnosticsError(
            "diagnostics_run_spec must be DiagnosticsRunSpec, DiagnosticsRunSpecRef, or mapping"
        )
    return DiagnosticsRunSpecRef(
        diagnostics_run_spec_id=value.get("diagnostics_run_spec_id"),
        content_hash=value.get("content_hash"),
    )


def _require_cross_market_family(
    diagnostics_run_spec: DiagnosticsRunSpec | DiagnosticsRunSpecRef | Mapping[str, Any],
) -> None:
    if (
        isinstance(diagnostics_run_spec, DiagnosticsRunSpec)
        and diagnostics_run_spec.diagnostics_family is not DiagnosticsFamily.CROSS_MARKET
    ):
        raise CrossMarketDiagnosticsError(
            "cross-market diagnostics require DiagnosticsFamily.CROSS_MARKET"
        )


def _symbols_from_scope(scope: Mapping[str, Any]) -> set[str]:
    for key in ("symbol_universe", "symbols", "required_symbols"):
        value = scope.get(key)
        if isinstance(value, Sequence) and not isinstance(value, str | bytes):
            return {str(item).upper() for item in value}
    universe = scope.get("universe")
    if isinstance(universe, Mapping):
        return _symbols_from_scope(universe)
    return set()


def _mapping_sequence(value: object, field: str) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise CrossMarketDiagnosticsError(f"{field} must be a sequence of mappings")
    return tuple(_mapping(item, f"{field}[]") for item in value)


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CrossMarketDiagnosticsError(f"{field} must be a mapping")
    return value


def _symbol(row: Mapping[str, Any]) -> str:
    value = _first_present(row, ("symbol", "instrument_id"))
    return _optional_text(value).upper()


def _metric(row: Mapping[str, Any], value_fields: Sequence[str]) -> float | None:
    value = _first_present(row, value_fields)
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _first_present(row: Mapping[str, Any], fields: Sequence[str]) -> Any:
    for field in fields:
        if field in row and row[field] is not None:
            return row[field]
    return None


def _datetime_or_none(value: object, field: str, *, optional: bool = False) -> datetime | None:
    if value is None:
        return None if optional else None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise CrossMarketDiagnosticsError(f"{field} must be an ISO datetime") from exc
    else:
        raise CrossMarketDiagnosticsError(f"{field} must be a datetime or ISO datetime string")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CrossMarketDiagnosticsError(f"{field} must be timezone-aware")
    return parsed.astimezone(UTC)


def _optional_text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value).strip()
    return value.strip()


def _nested_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    return _optional_text(value)


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CrossMarketDiagnosticsError(f"{field} must be a non-empty string")
    return value.strip()


def _positive_int(value: int, field: str) -> None:
    if isinstance(value, bool) or value < 1:
        raise CrossMarketDiagnosticsError(f"{field} must be a positive integer")


def _ratio(value: float, field: str) -> None:
    if isinstance(value, bool) or not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
        raise CrossMarketDiagnosticsError(f"{field} must be a finite ratio between 0 and 1")


def _non_negative_float(value: float, field: str) -> None:
    if isinstance(value, bool) or not math.isfinite(float(value)) or float(value) < 0.0:
        raise CrossMarketDiagnosticsError(f"{field} must be a non-negative finite float")


def _mean(values: Iterable[float]) -> float | None:
    active = [float(value) for value in values if math.isfinite(float(value))]
    if not active:
        return None
    return sum(active) / len(active)


def _min(values: Iterable[float]) -> float | None:
    active = [float(value) for value in values if math.isfinite(float(value))]
    return min(active) if active else None


def _max(values: Iterable[float]) -> float | None:
    active = [float(value) for value in values if math.isfinite(float(value))]
    return max(active) if active else None


def _max_abs(values: Iterable[float | None]) -> float | None:
    active = [
        abs(float(value)) for value in values if value is not None and math.isfinite(float(value))
    ]
    return max(active) if active else None


def _scalar_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _iso_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _unique_reasons(reasons: Iterable[RunRejectionReason]) -> tuple[RunRejectionReason, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[RunRejectionReason] = []
    for reason in reasons:
        key = (reason.code, reason.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(reason)
    return tuple(unique)


__all__ = [
    "CROSS_MARKET_DIAGNOSTICS_REPORT_KIND",
    "CROSS_MARKET_DIAGNOSTICS_THRESHOLD_PROFILE",
    "CrossMarketDiagnosticsConfig",
    "CrossMarketDiagnosticsError",
    "CrossMarketDiagnosticsReport",
    "CrossMarketDiagnosticsRunResult",
    "LeadLagSummary",
    "PairRelationshipSummary",
    "RegimeCorrelationSummary",
    "SymbolAlignmentSummary",
    "build_cross_market_diagnostics_report",
    "build_cross_market_diagnostics_run",
    "resolve_cross_market_dataset_version",
]
