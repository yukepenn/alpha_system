"""Small accepted-DatasetVersion feature/label dry-run orchestration.

The helper in this module stays at the canonical mapping boundary: it resolves
one accepted DatasetVersion, validates supplied canonical row mappings through
the canonical loaders, and delegates all value production to the existing
feature and label materialization engines. It does not read provider files,
call external providers, register values, or write inside the repository.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from alpha_system.data.foundation.datasets import CoverageReport, DataQualityReport
from alpha_system.data.foundation.grid import NO_TRADE_QUALITY_FLAG, DenseGridBarRecord
from alpha_system.data.foundation.quotes import (
    BBO_QUARANTINE_QUALITY_FLAG,
    MISSING_BBO_QUALITY_FLAG,
    CanonicalBBORecord,
)
from alpha_system.features import consumption
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.features.contracts import FeatureSetSpec, FeatureSpec
from alpha_system.features.engine.materialization import (
    FeatureMaterializationError,
    FeatureMaterializationInputs,
    SupportedFeatureDefinition,
    build_feature_materialization_plan,
    materialize_features,
)
from alpha_system.labels.engine import (
    LabelMaterializationInputs,
    SupportedLabelDefinition,
    build_label_materialization_plan,
    materialize_labels,
)
from alpha_system.labels.version import LabelContractSpec

SMALL_DATASET_VERSION_DRY_RUN_STATUS = "COMPLETED"
SMALL_DATASET_VERSION_DRY_RUN_WITH_WARNINGS = "PASS_WITH_WARNINGS"
SMALL_DATASET_VERSION_DRY_RUN_PURPOSE = "small_dataset_version_dry_run"
DEFAULT_MAX_INPUT_ROWS = 64


@dataclass(frozen=True, slots=True)
class SmallDatasetVersionDryRunSummary:
    """Row-free summary for one bounded accepted-DatasetVersion dry run."""

    status: str
    dataset_version_id: str
    source: str
    lifecycle_state: str
    partition_id: str
    symbols: tuple[str, ...]
    sessions: tuple[str, ...]
    counts_by_symbol: Mapping[str, int]
    counts_by_session: Mapping[str, int]
    canonical_bar_rows: int
    canonical_bbo_rows: int
    dense_grid_bar_rows: int
    synthetic_no_trade_rows: int
    missing_bbo_rows: int
    bbo_quarantined_rows: int
    feature_count: int
    feature_value_count: int
    label_count: int
    label_value_count: int
    quality_status: str
    coverage_status: str
    quality_blocking: bool
    coverage_blocking: bool
    feature_output_under_alpha_data_root: bool
    label_output_under_alpha_data_root: bool
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "counts_by_symbol",
            MappingProxyType(dict(self.counts_by_symbol)),
        )
        object.__setattr__(
            self,
            "counts_by_session",
            MappingProxyType(dict(self.counts_by_session)),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible row-free dry-run summary."""

        return {
            "status": self.status,
            "dataset_version_id": self.dataset_version_id,
            "source": self.source,
            "lifecycle_state": self.lifecycle_state,
            "partition_id": self.partition_id,
            "symbols": list(self.symbols),
            "sessions": list(self.sessions),
            "counts_by_symbol": dict(self.counts_by_symbol),
            "counts_by_session": dict(self.counts_by_session),
            "canonical_bar_rows": self.canonical_bar_rows,
            "canonical_bbo_rows": self.canonical_bbo_rows,
            "dense_grid_bar_rows": self.dense_grid_bar_rows,
            "synthetic_no_trade_rows": self.synthetic_no_trade_rows,
            "missing_bbo_rows": self.missing_bbo_rows,
            "bbo_quarantined_rows": self.bbo_quarantined_rows,
            "feature_count": self.feature_count,
            "feature_value_count": self.feature_value_count,
            "label_count": self.label_count,
            "label_value_count": self.label_value_count,
            "quality_status": self.quality_status,
            "coverage_status": self.coverage_status,
            "quality_blocking": self.quality_blocking,
            "coverage_blocking": self.coverage_blocking,
            "feature_output_under_alpha_data_root": self.feature_output_under_alpha_data_root,
            "label_output_under_alpha_data_root": self.label_output_under_alpha_data_root,
            "warnings": list(self.warnings),
        }


def run_small_dataset_version_dry_run(
    *,
    registry_path: str | Path,
    dataset_version_id: object,
    lifecycle_state: object,
    quality_report: DataQualityReport,
    coverage_report: CoverageReport,
    source_manifest: object,
    code_hash: object,
    config_hash: object,
    partition_id: object,
    alpha_data_root: str | Path | None,
    feature_definitions: Iterable[SupportedFeatureDefinition],
    label_definitions: Iterable[SupportedLabelDefinition],
    bar_rows: Iterable[Mapping[str, object]] = (),
    bbo_rows: Iterable[Mapping[str, object]] = (),
    dense_grid_bar_rows: Iterable[Mapping[str, object]] = (),
    instrument_ids: Sequence[str] = (),
    governance_metadata: Mapping[str, Any] | None = None,
    max_input_rows: int = DEFAULT_MAX_INPUT_ROWS,
) -> SmallDatasetVersionDryRunSummary:
    """Materialize a bounded local-only feature/label sample and summarize it.

    The result intentionally contains counts and status only. Feature and label
    values are written by the existing engines under ``alpha_data_root`` and are
    never returned in this summary.
    """

    limit = _positive_int(max_input_rows, "max_input_rows")
    feature_defs = _feature_definitions(feature_definitions)
    label_defs = _label_definitions(label_definitions)
    partition = _text(partition_id, "partition_id")
    metadata = dict(governance_metadata or {})

    accepted = _resolve_accepted_version(
        registry_path=registry_path,
        dataset_version_id=dataset_version_id,
        lifecycle_state=lifecycle_state,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=code_hash,
        config_hash=config_hash,
    )

    raw_bar_rows, bar_warning = _bounded_rows(bar_rows, "bar_rows", limit)
    raw_bbo_rows, bbo_warning = _bounded_rows(bbo_rows, "bbo_rows", limit)
    raw_dense_rows, dense_warning = _bounded_rows(
        dense_grid_bar_rows,
        "dense_grid_bar_rows",
        limit,
    )
    warnings = tuple(
        warning for warning in (bar_warning, bbo_warning, dense_warning) if warning is not None
    )
    if not raw_bar_rows and not raw_dense_rows:
        raise FeatureMaterializationError(
            "small DatasetVersion dry run requires canonical OHLCV or dense-grid mappings"
        )

    canonical_bars = accepted.canonical_bars_from_mappings(
        raw_bar_rows,
        partition_id=partition,
        purpose=SMALL_DATASET_VERSION_DRY_RUN_PURPOSE,
        governance_metadata=metadata,
    )
    canonical_bbos = accepted.canonical_bbos_from_mappings(
        raw_bbo_rows,
        partition_id=partition,
        purpose=SMALL_DATASET_VERSION_DRY_RUN_PURPOSE,
        governance_metadata=metadata,
    )
    dense_bars = accepted.dense_grid_bars_from_mappings(
        raw_dense_rows,
        partition_id=partition,
        purpose=SMALL_DATASET_VERSION_DRY_RUN_PURPOSE,
        governance_metadata=metadata,
    )

    feature_set = _feature_set_from_definitions(feature_defs)
    feature_plan = build_feature_materialization_plan(
        feature_set,
        accepted,
        partition_id=partition,
        alpha_data_root=alpha_data_root,
        governance_metadata=metadata,
        output_namespace="features/dry_runs/small_dataset_version",
    )
    feature_inputs = FeatureMaterializationInputs(
        accepted_version=accepted,
        bar_rows=raw_bar_rows,
        bbo_rows=raw_bbo_rows,
        dense_grid_bar_rows=raw_dense_rows,
        governance_metadata=metadata,
    )
    feature_result = materialize_features(
        feature_plan,
        feature_inputs,
        feature_defs,
        dry_run=False,
    )

    label_plan = build_label_materialization_plan(
        label_defs,
        accepted,
        partition_id=partition,
        instrument_ids=tuple(instrument_ids),
        alpha_data_root=alpha_data_root,
        governance_metadata=metadata,
        dry_run=False,
        output_namespace="labels/dry_runs/small_dataset_version",
    )
    label_inputs = LabelMaterializationInputs(
        accepted_version=accepted,
        bar_rows=raw_bar_rows,
        bbo_rows=raw_bbo_rows,
        dense_grid_bar_rows=raw_dense_rows,
        governance_metadata=metadata,
    )
    label_result = materialize_labels(label_plan, label_inputs, label_defs)

    counts = _coverage_counts(canonical_bars, canonical_bbos, dense_bars)
    warnings = warnings + _value_count_warnings(
        feature_result.record_count,
        label_result.record_count,
    )
    status = (
        SMALL_DATASET_VERSION_DRY_RUN_WITH_WARNINGS
        if warnings
        else SMALL_DATASET_VERSION_DRY_RUN_STATUS
    )
    return SmallDatasetVersionDryRunSummary(
        status=status,
        dataset_version_id=accepted.dataset_version_id,
        source=accepted.source,
        lifecycle_state=accepted.lifecycle_state,
        partition_id=partition,
        symbols=counts["symbols"],
        sessions=counts["sessions"],
        counts_by_symbol=counts["counts_by_symbol"],
        counts_by_session=counts["counts_by_session"],
        canonical_bar_rows=len(canonical_bars),
        canonical_bbo_rows=len(canonical_bbos),
        dense_grid_bar_rows=len(dense_bars),
        synthetic_no_trade_rows=_synthetic_no_trade_count(dense_bars),
        missing_bbo_rows=_bbo_flag_count(canonical_bbos, MISSING_BBO_QUALITY_FLAG),
        bbo_quarantined_rows=_bbo_flag_count(canonical_bbos, BBO_QUARANTINE_QUALITY_FLAG),
        feature_count=len(feature_defs),
        feature_value_count=feature_result.record_count,
        label_count=len(label_defs),
        label_value_count=label_result.record_count,
        quality_status=accepted.quality_report.status.value,
        coverage_status=accepted.coverage_report.coverage_status.value,
        quality_blocking=accepted.quality_report.blocks_versioning,
        coverage_blocking=accepted.coverage_report.blocks_versioning,
        feature_output_under_alpha_data_root=_is_under_root(
            feature_result.output_path,
            feature_plan.alpha_data_root,
        ),
        label_output_under_alpha_data_root=_is_under_root(
            label_result.output_path,
            label_plan.alpha_data_root,
        ),
        warnings=warnings,
    )


def _resolve_accepted_version(
    *,
    registry_path: str | Path,
    dataset_version_id: object,
    lifecycle_state: object,
    quality_report: DataQualityReport,
    coverage_report: CoverageReport,
    source_manifest: object,
    code_hash: object,
    config_hash: object,
) -> AcceptedDatasetVersion:
    return consumption.resolve_accepted_dataset_version(
        registry_path,
        dataset_version_id,
        lifecycle_state=lifecycle_state,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=code_hash,
        config_hash=config_hash,
    )


def _feature_set_from_definitions(
    definitions: tuple[SupportedFeatureDefinition, ...],
) -> FeatureSetSpec:
    return FeatureSetSpec(
        feature_set_id="feature_set_small_dataset_version_dry_run",
        feature_set_version="v1",
        features=tuple(_feature_spec(definition) for definition in definitions),
        description="Bounded local-only accepted DatasetVersion dry-run feature set.",
        metadata={"purpose": SMALL_DATASET_VERSION_DRY_RUN_PURPOSE},
    )


def _feature_spec(definition: SupportedFeatureDefinition) -> FeatureSpec:
    spec = definition.spec
    if isinstance(spec, FeatureSpec):
        return spec
    nested = getattr(spec, "feature_spec", None)
    if isinstance(nested, FeatureSpec):
        return nested
    raise FeatureMaterializationError("feature definition does not expose a FeatureSpec")


def _feature_definitions(
    definitions: Iterable[SupportedFeatureDefinition],
) -> tuple[SupportedFeatureDefinition, ...]:
    if isinstance(definitions, str):
        raise FeatureMaterializationError("feature_definitions must be an iterable")
    normalized = tuple(definitions)
    if not normalized:
        raise FeatureMaterializationError("at least one feature definition is required")
    return normalized


def _label_definitions(
    definitions: Iterable[SupportedLabelDefinition],
) -> tuple[SupportedLabelDefinition, ...]:
    if isinstance(definitions, str):
        raise FeatureMaterializationError("label_definitions must be an iterable")
    normalized = tuple(definitions)
    if not normalized:
        raise FeatureMaterializationError("at least one label definition is required")
    for definition in normalized:
        _label_contract(definition)
    return normalized


def _label_contract(definition: SupportedLabelDefinition) -> LabelContractSpec:
    contract = getattr(definition, "contract", None)
    if isinstance(contract, LabelContractSpec):
        return contract
    spec = getattr(definition, "spec", None)
    nested = getattr(spec, "label_contract", None)
    if isinstance(nested, LabelContractSpec):
        return nested
    raise FeatureMaterializationError("label definition does not expose a LabelContractSpec")


def _bounded_rows(
    rows: Iterable[Mapping[str, object]],
    field_name: str,
    max_rows: int,
) -> tuple[tuple[Mapping[str, object], ...], str | None]:
    if isinstance(rows, str):
        raise FeatureMaterializationError(f"{field_name} must be an iterable of mappings")
    normalized = tuple(rows)
    for row in normalized:
        if isinstance(row, str) or not isinstance(row, Mapping):
            raise FeatureMaterializationError(f"{field_name} must contain mappings")
    if len(normalized) > max_rows:
        return normalized[:max_rows], f"{field_name} truncated from {len(normalized)} to {max_rows}"
    return normalized, None


def _coverage_counts(
    bars: Sequence[object],
    bbos: Sequence[object],
    dense_bars: Sequence[object],
) -> dict[str, object]:
    symbol_counts: Counter[str] = Counter()
    session_counts: Counter[str] = Counter()
    for record in (*bars, *bbos, *dense_bars):
        symbol_counts[str(getattr(record, "instrument_id"))] += 1
        session_counts[str(getattr(record, "session_label"))] += 1
    return {
        "symbols": tuple(sorted(symbol_counts)),
        "sessions": tuple(sorted(session_counts)),
        "counts_by_symbol": dict(sorted(symbol_counts.items())),
        "counts_by_session": dict(sorted(session_counts.items())),
    }


def _synthetic_no_trade_count(records: Sequence[DenseGridBarRecord]) -> int:
    return sum(
        1
        for record in records
        if not record.has_trade
        and record.synthetic
        and NO_TRADE_QUALITY_FLAG in {flag.lower() for flag in record.quality_flags}
    )


def _bbo_flag_count(records: Sequence[CanonicalBBORecord], flag: str) -> int:
    return sum(1 for record in records if flag in {token.lower() for token in record.quality_flags})


def _value_count_warnings(feature_count: int, label_count: int) -> tuple[str, ...]:
    warnings: list[str] = []
    if feature_count == 0:
        warnings.append("feature engine produced zero values")
    if label_count == 0:
        warnings.append("label engine produced zero values")
    return tuple(warnings)


def _is_under_root(path: Path | None, root: Path) -> bool:
    if path is None:
        return False
    resolved_path = path.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    return resolved_path == resolved_root or resolved_path.is_relative_to(resolved_root)


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise FeatureMaterializationError(f"{field_name} must be a positive integer")
    return value


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise FeatureMaterializationError(f"{field_name} must be a non-empty string")
    text = value.strip()
    if not text or "\n" in text or "\r" in text:
        raise FeatureMaterializationError(f"{field_name} must be a non-empty single-line string")
    return text


__all__ = [
    "DEFAULT_MAX_INPUT_ROWS",
    "SMALL_DATASET_VERSION_DRY_RUN_PURPOSE",
    "SMALL_DATASET_VERSION_DRY_RUN_STATUS",
    "SMALL_DATASET_VERSION_DRY_RUN_WITH_WARNINGS",
    "SmallDatasetVersionDryRunSummary",
    "run_small_dataset_version_dry_run",
]
