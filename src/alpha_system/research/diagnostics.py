"""Top-level intraday factor diagnostics orchestration."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alpha_system.core.git_info import capture_git_info
from alpha_system.core.hashing import hash_config
from alpha_system.core.registry import connect_registry, init_registry
from alpha_system.core.run_ids import generate_run_id
from alpha_system.data.fixture_policy import FixturePolicyError, assert_registry_path_allowed
from alpha_system.data.paths import assert_local_wsl_path
from alpha_system.experiments.registry import RunRecord, insert_run_record
from alpha_system.factors.io import read_factor_value_dicts
from alpha_system.labels.spec import LabelSpec
from alpha_system.labels.validation import LabelValidationError, validate_label_record
from alpha_system.research.buckets import (
    bucket_forward_returns,
    bucket_monotonicity,
    extreme_bucket_hit_rate,
    mfe_mae_by_bucket,
    tail_expectancy,
    u_shape_profile,
)
from alpha_system.research.events import (
    conditional_forward_returns,
    event_study,
    false_breakout_rate,
    post_event_mfe_mae,
    sample_size,
    target_before_stop_probability,
)
from alpha_system.research.execution_filters import execution_filter_summary
from alpha_system.research.ic import (
    ic_by_calendar_period,
    ic_by_horizon,
    ic_decay,
    icir_from_calendar_periods,
    pearson_ic,
    rank_ic,
)
from alpha_system.research.management_features import management_feature_summary
from alpha_system.research.regimes import (
    conditional_strategy_improvement,
    false_rejection_rate,
    regime_filter_coverage,
    regime_filter_uplift,
)
from alpha_system.research.stability import (
    monthly_stability,
    regime_stability,
    session_segment_stability,
    time_of_day_stability,
)
from alpha_system.research.study_config import DEFAULT_DIAGNOSTIC_TYPES, StudyConfig
from alpha_system.research.study_outputs import (
    DiagnosticSummary,
    StudyRunResult,
    write_study_outputs,
)


SUPPORTED_DIAGNOSTIC_TYPES: frozenset[str] = frozenset(DEFAULT_DIAGNOSTIC_TYPES)


class DiagnosticsError(ValueError):
    """Raised when diagnostics cannot be computed safely."""


@dataclass(frozen=True, slots=True)
class AlignmentResult:
    observations: tuple[dict[str, Any], ...]
    missing_label_count: int
    missing_factor_count: int
    warnings: tuple[str, ...]


def run_study(config: StudyConfig) -> StudyRunResult:
    """Run diagnostics, write local artifacts, and optionally record registry rows."""
    config_payload = config.to_dict()
    config_hash = hash_config(config_payload)
    summary = compute_diagnostic_summary(
        config,
        run_id=generate_run_id(
            "study",
            seed=config.study_id,
            components={
                "factor_id": config.factor_id,
                "factor_version": config.factor_version,
                "label_id": config.label_id,
                "label_version": config.label_version,
                "data_version": config.data_version,
                "config_hash": config_hash,
            },
        ),
    )
    output_paths = write_study_outputs(
        summary,
        output_dir=config.output_dir,
        manifest_path=config.manifest_path,
        config_hash=config_hash,
        config_payload=config_payload,
    )
    registry_written = False
    registry_path = None
    if config.registry_path:
        registry_path = _record_registry_entries(
            config,
            summary,
            config_hash=config_hash,
            artifact_paths=output_paths.to_dict(),
        )
        registry_written = True
    return StudyRunResult(
        summary=summary,
        output_paths=output_paths,
        registry_path=registry_path,
        registry_written=registry_written,
    )


def compute_diagnostic_summary(config: StudyConfig, *, run_id: str | None = None) -> DiagnosticSummary:
    """Compute a deterministic diagnostic summary from versioned factor and label inputs."""
    factor_values = read_factor_value_dicts(config.factor_values_path)
    labels = read_label_dicts(config.labels_path)
    alignment = align_factor_values_to_labels(factor_values, labels, config)
    observations = alignment.observations
    warnings = list(alignment.warnings)
    diagnostics = _diagnostics_for_observations(observations, config, warnings)
    warnings.extend(_sample_warnings(config, alignment))
    return DiagnosticSummary(
        run_id=run_id or generate_run_id("study", seed=config.study_id),
        study_id=config.study_id,
        factor_id=config.factor_id,
        factor_version=config.factor_version,
        label_id=config.label_id,
        label_version=config.label_version,
        data_version=config.data_version,
        engine_version=config.engine_version,
        sample_size=len(observations),
        missing_label_count=alignment.missing_label_count,
        missing_factor_count=alignment.missing_factor_count,
        warnings=tuple(dict.fromkeys(warnings)),
        diagnostics=diagnostics,
    )


def read_label_dicts(path: str | Path) -> tuple[dict[str, Any], ...]:
    """Read label JSONL records and return normalized dictionaries."""
    input_path = assert_local_wsl_path(path)
    lines = input_path.read_text(encoding="utf-8").splitlines()
    labels: list[dict[str, Any]] = []
    for line in lines:
        if line.strip():
            labels.append(validate_label_record(json.loads(line)).to_dict())
    return tuple(labels)


def align_factor_values_to_labels(
    factor_values: Iterable[Mapping[str, Any]],
    labels: Iterable[Mapping[str, Any] | LabelSpec],
    config: StudyConfig,
) -> AlignmentResult:
    """Validate versioned factor/label alignment and return joined observations."""
    normalized_labels = tuple(_label(label) for label in labels)
    primary_labels = tuple(label for label in normalized_labels if label.label_id == config.label_id)
    optional_labels = tuple(label for label in normalized_labels if label.label_id != config.label_id)
    _assert_label_versions(primary_labels, config)
    primary_index = _primary_label_index(primary_labels, config)
    optional_index = _optional_label_index(optional_labels, config)

    selected_factors: list[Mapping[str, Any]] = []
    mismatched_factor_versions = 0
    missing_factor_count = 0
    for factor in factor_values:
        if str(factor.get("factor_id", "")) != config.factor_id:
            continue
        if str(factor.get("factor_version", "")) != config.factor_version:
            mismatched_factor_versions += 1
            continue
        if str(factor.get("data_version", "")) != config.data_version:
            mismatched_factor_versions += 1
            continue
        if not _selector_allows(factor, config):
            continue
        selected_factors.append(factor)
        if _numeric_factor_value(factor) is None:
            missing_factor_count += 1

    if not selected_factors:
        msg = "factor version reference produced no matching factor values"
        raise DiagnosticsError(msg)
    if not primary_index:
        msg = "label version reference produced no matching labels"
        raise DiagnosticsError(msg)

    observations: list[dict[str, Any]] = []
    missing_label_count = 0
    for factor in selected_factors:
        key = (
            str(factor["instrument_id"]),
            _datetime(factor["event_ts"]),
            str(factor["session_id"]),
            config.data_version,
            config.label_version,
        )
        labels_for_factor = primary_index.get(key, ())
        if not labels_for_factor:
            missing_label_count += 1
            continue
        for label in labels_for_factor:
            _assert_label_available_after_factor(factor, label)
            observation = _observation_from_pair(factor, label)
            observation.update(optional_index.get(_optional_key(label), {}))
            observations.append(observation)

    warnings: list[str] = []
    if mismatched_factor_versions:
        warnings.append("invalid version references ignored for non-matching factor/data versions")
    return AlignmentResult(
        observations=tuple(observations),
        missing_label_count=missing_label_count,
        missing_factor_count=missing_factor_count,
        warnings=tuple(warnings),
    )


def _diagnostics_for_observations(
    observations: tuple[dict[str, Any], ...],
    config: StudyConfig,
    warnings: list[str],
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    unsupported = tuple(
        item for item in config.diagnostic_types if item not in SUPPORTED_DIAGNOSTIC_TYPES
    )
    for item in unsupported:
        warnings.append(f"unsupported diagnostic type: {item}")
    requested = tuple(item for item in config.diagnostic_types if item in SUPPORTED_DIAGNOSTIC_TYPES)

    if "directional" in requested:
        diagnostics["directional"] = {
            "pearson_ic": pearson_ic(
                (row["factor_value"] for row in observations),
                (row["label_value"] for row in observations),
            ),
            "rank_ic": rank_ic(
                (row["factor_value"] for row in observations),
                (row["label_value"] for row in observations),
            ),
            "ic_by_horizon": ic_by_horizon(observations),
            "ic_decay": ic_decay(observations),
            "ic_by_day": ic_by_calendar_period(observations, period="day"),
            "ic_by_week": ic_by_calendar_period(observations, period="week"),
            "ic_by_month": ic_by_calendar_period(observations, period="month"),
            "icir": icir_from_calendar_periods(observations, period="day"),
        }

    if "buckets" in requested:
        bucket_summary = bucket_forward_returns(observations, bucket_count=config.bucket_count)
        diagnostics["buckets"] = {
            "bucket_forward_returns": bucket_summary,
            "bucket_monotonicity": bucket_monotonicity(bucket_summary),
            "tail_expectancy": tail_expectancy(bucket_summary),
            "u_shape_profile": u_shape_profile(bucket_summary),
            "extreme_bucket_hit_rate": extreme_bucket_hit_rate(
                observations,
                bucket_count=config.bucket_count,
            ),
            "mfe_mae_by_bucket": mfe_mae_by_bucket(
                observations,
                bucket_count=config.bucket_count,
            ),
        }

    if "events" in requested:
        diagnostics["events"] = {
            "event_study": event_study(observations),
            "conditional_forward_returns": conditional_forward_returns(observations),
            "sample_size": sample_size(observations),
            "false_breakout_rate": false_breakout_rate(observations),
            "target_before_stop_probability": target_before_stop_probability(observations),
            "post_event_mfe_mae": post_event_mfe_mae(observations),
        }

    if "regimes" in requested:
        diagnostics["regimes"] = {
            "with_filter_vs_without_filter_uplift": regime_filter_uplift(observations),
            "coverage": regime_filter_coverage(observations),
            "false_rejection_rate": false_rejection_rate(observations),
            "conditional_strategy_improvement": conditional_strategy_improvement(observations),
        }

    if "execution_filters" in requested:
        diagnostics["execution_filters"] = execution_filter_summary(observations)

    if "management_features" in requested:
        diagnostics["management_features"] = management_feature_summary(observations)

    diagnostics["stability"] = {
        "time_of_day": time_of_day_stability(observations),
        "session_segment": session_segment_stability(observations),
        "monthly": monthly_stability(observations),
        "regime": regime_stability(observations),
    }
    return diagnostics


def _sample_warnings(config: StudyConfig, alignment: AlignmentResult) -> tuple[str, ...]:
    warnings: list[str] = []
    total_factor_rows = len(alignment.observations) + alignment.missing_label_count
    thresholds = config.sample_size_thresholds
    if len(alignment.observations) < thresholds.min_total:
        warnings.append("insufficient sample size for requested diagnostics")
    if total_factor_rows:
        missing_label_rate = alignment.missing_label_count / total_factor_rows
        missing_factor_rate = alignment.missing_factor_count / total_factor_rows
        if missing_label_rate > thresholds.max_missing_label_rate:
            warnings.append("missing label coverage exceeds configured threshold")
        if missing_factor_rate > thresholds.max_missing_factor_rate:
            warnings.append("high missing-factor rate exceeds configured threshold")
    horizon_counts = Counter(row["horizon_seconds"] for row in alignment.observations)
    if len(horizon_counts) > 1 and (min(horizon_counts.values()) / max(horizon_counts.values())) < 0.8:
        warnings.append("unstable horizon coverage across selected labels")
    return tuple(warnings)


def _record_registry_entries(
    config: StudyConfig,
    summary: DiagnosticSummary,
    *,
    config_hash: str,
    artifact_paths: Mapping[str, str],
) -> str:
    try:
        registry_path = assert_registry_path_allowed(config.registry_path or "")
    except FixturePolicyError as exc:
        raise DiagnosticsError(str(exc)) from exc
    status = init_registry(registry_path)
    if not status.valid:
        msg = f"registry is not valid: {status.status_message}"
        raise DiagnosticsError(msg)
    git_info = capture_git_info(Path.cwd())
    record = RunRecord(
        run_id=summary.run_id,
        timestamp=datetime.now(timezone.utc),
        git_commit=git_info.commit,
        git_dirty=git_info.dirty,
        code_hash=hash_config({"engine_version": config.engine_version, "module": __name__}),
        config_hash=config_hash,
        data_version=config.data_version,
        factor_versions={config.factor_id: config.factor_version},
        label_versions={config.label_id: config.label_version},
        engine_version=config.engine_version,
        parameters=config.to_dict(),
        artifact_paths=artifact_paths,
        decision_status="diagnostic_recorded",
        warnings=summary.warnings,
        status_message="Tier 0 diagnostics record; no candidate promotion.",
    )
    with connect_registry(registry_path) as connection:
        insert_run_record(connection, "study_runs", record)
        insert_run_record(connection, "factor_validation_runs", record)
    return registry_path.as_posix()


def _assert_label_versions(labels: tuple[LabelSpec, ...], config: StudyConfig) -> None:
    mismatched = [
        label
        for label in labels
        if str(label.path_metadata.get("label_version", "")) != config.label_version
        or label.data_version != config.data_version
    ]
    if mismatched:
        msg = "primary labels contain records with misaligned data or label version"
        raise DiagnosticsError(msg)


def _primary_label_index(
    labels: tuple[LabelSpec, ...],
    config: StudyConfig,
) -> dict[tuple[str, datetime, str, str, str], tuple[LabelSpec, ...]]:
    buckets: dict[tuple[str, datetime, str, str, str], list[LabelSpec]] = defaultdict(list)
    for label in labels:
        if str(label.path_metadata.get("label_version", "")) != config.label_version:
            continue
        if label.data_version != config.data_version:
            continue
        if not _selector_allows_label(label, config):
            continue
        buckets[
            (
                label.instrument_id,
                label.event_ts,
                str(label.path_metadata["session_id"]),
                label.data_version,
                str(label.path_metadata["label_version"]),
            )
        ].append(label)
    return {key: tuple(value) for key, value in buckets.items()}


def _optional_label_index(
    labels: tuple[LabelSpec, ...],
    config: StudyConfig,
) -> dict[tuple[str, datetime, str, int, str, str], dict[str, Any]]:
    output: dict[tuple[str, datetime, str, int, str, str], dict[str, Any]] = {}
    for label in labels:
        if str(label.path_metadata.get("label_version", "")) != config.label_version:
            continue
        if label.data_version != config.data_version:
            continue
        if not _selector_allows_label(label, config):
            continue
        bucket = output.setdefault(_optional_key(label), {})
        label_type = label.label_type.value
        if label_type == "mfe_by_horizon":
            bucket["mfe"] = _float(label.value)
        elif label_type == "mae_by_horizon":
            bucket["mae"] = _float(label.value)
        elif label_type == "target_before_stop":
            bucket["target_before_stop"] = None if label.value is None else bool(label.value)
            bucket["time_to_target"] = _time_delta_bars(label)
        elif label_type == "stop_before_target":
            bucket["stop_before_target"] = None if label.value is None else bool(label.value)
            bucket["time_to_stop"] = _time_delta_bars(label)
        elif label_type == "future_spread_liquidity":
            metadata = dict(label.path_metadata)
            bucket["spread"] = _float(metadata.get("average_spread", label.value))
            bucket["liquidity"] = _float(metadata.get("total_volume"))
            bucket["volume_participation"] = _float(metadata.get("average_trade_count"))
            bucket["slippage"] = _float(metadata.get("average_spread", label.value))
    return output


def _observation_from_pair(factor: Mapping[str, Any], label: LabelSpec) -> dict[str, Any]:
    value = _numeric_factor_value(factor)
    label_value = _float(label.value)
    metadata = dict(label.path_metadata)
    return {
        "factor_value": value,
        "label_value": label_value,
        "forward_return": label_value,
        "instrument_id": str(factor["instrument_id"]),
        "event_ts": _datetime(factor["event_ts"]),
        "session_id": str(factor["session_id"]),
        "bar_index": int(factor["bar_index"]),
        "horizon_seconds": int(label.horizon.total_seconds()),
        "regime_filter": False if value is None else value > 0,
        "event_trigger": False if value is None else value > 0,
        "regime": metadata.get("regime", "all"),
    }


def _selector_allows(factor: Mapping[str, Any], config: StudyConfig) -> bool:
    if config.instruments and str(factor.get("instrument_id", "")) not in config.instruments:
        return False
    if config.sessions and str(factor.get("session_id", "")) not in config.sessions:
        return False
    event_ts = _datetime(factor["event_ts"])
    if config.start_ts is not None and event_ts < config.start_ts:
        return False
    if config.end_ts is not None and event_ts > config.end_ts:
        return False
    return True


def _selector_allows_label(label: LabelSpec, config: StudyConfig) -> bool:
    if config.instruments and label.instrument_id not in config.instruments:
        return False
    session_id = str(label.path_metadata["session_id"])
    if config.sessions and session_id not in config.sessions:
        return False
    if config.start_ts is not None and label.event_ts < config.start_ts:
        return False
    if config.end_ts is not None and label.event_ts > config.end_ts:
        return False
    if config.horizon_seconds is not None and int(label.horizon.total_seconds()) != config.horizon_seconds:
        return False
    return True


def _assert_label_available_after_factor(factor: Mapping[str, Any], label: LabelSpec) -> None:
    factor_available_ts = _datetime(factor["available_ts"])
    if label.label_available_ts < factor_available_ts:
        msg = "label_available_ts precedes factor available_ts for aligned row"
        raise DiagnosticsError(msg)


def _label(label: Mapping[str, Any] | LabelSpec) -> LabelSpec:
    try:
        return validate_label_record(label)
    except LabelValidationError as exc:
        raise DiagnosticsError(str(exc)) from exc


def _optional_key(label: LabelSpec) -> tuple[str, datetime, str, int, str, str]:
    return (
        label.instrument_id,
        label.event_ts,
        str(label.path_metadata["session_id"]),
        int(label.horizon.total_seconds()),
        label.data_version,
        str(label.path_metadata["label_version"]),
    )


def _numeric_factor_value(factor: Mapping[str, Any]) -> float | None:
    for field in ("normalized_value", "value"):
        value = _float(factor.get(field))
        if value is not None:
            return value
    return None


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        active = value
    else:
        active = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if active.tzinfo is None:
        active = active.replace(tzinfo=timezone.utc)
    return active.astimezone(timezone.utc)


def _time_delta_bars(label: LabelSpec) -> int | None:
    metadata = dict(label.path_metadata)
    key = "target_hit_bar_index" if "target_hit_bar_index" in metadata else "stop_hit_bar_index"
    if key not in metadata or "entry_bar_index" not in metadata:
        return None
    try:
        return int(metadata[key]) - int(metadata["entry_bar_index"])
    except (TypeError, ValueError):
        return None
