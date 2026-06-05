"""Tiny deterministic Feature/Label fixtures for fail-closed tests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetPartitionPlan,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.features.consumption import AcceptedDatasetVersion
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.registry import (
    LabelExposureReport,
    LabelRegistryLifecycleState,
    LabelRegistryRecord,
)
from alpha_system.labels.version import (
    LabelContractSpec,
    LabelFamily,
    LabelInputSpec,
    LabelLineageRecord,
    LabelValueRecord,
)

DATASET_ID = "dsv_feature_label_synthetic_fixture_v1"
SOURCE_ID = "dsrc_synthetic_fixture"
ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


class EmptyRegistryReader:
    """Read-only empty exposure registry used by request-gate fixtures."""

    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def fixture_payload() -> dict[str, Any]:
    """Return a deep copy of the JSON row fixture payload."""

    path = Path(__file__).with_name("canonical_rows.json")
    return deepcopy(json.loads(path.read_text(encoding="utf-8")))


def partition_payload() -> dict[str, Any]:
    """Return a deep copy of the JSON partition fixture payload."""

    path = Path(__file__).with_name("partition_metadata.json")
    return deepcopy(json.loads(path.read_text(encoding="utf-8")))


def ohlcv_rows() -> tuple[dict[str, object], ...]:
    return tuple(dict(row) for row in fixture_payload()["ohlcv_rows"])


def bbo_rows() -> tuple[dict[str, object], ...]:
    return tuple(dict(row) for row in fixture_payload()["bbo_rows"])


def dense_grid_rows() -> tuple[dict[str, object], ...]:
    return tuple(dict(row) for row in fixture_payload()["dense_grid_rows"])


def locked_partition_governance_metadata() -> dict[str, object]:
    payload = partition_payload()
    return dict(payload["locked_test_candidate"]["governance_metadata"])


def accepted_version(
    dataset_id: str = DATASET_ID,
    *,
    lifecycle_state: str = "VERSIONED",
) -> AcceptedDatasetVersion:
    quality_report = quality_report_for(dataset_id)
    return AcceptedDatasetVersion(
        registry_path="synthetic_registry.sqlite",
        dataset_version=dataset_version_for(dataset_id, quality_report=quality_report),
        lifecycle_state=lifecycle_state,
        quality_report=quality_report,
        coverage_report=coverage_report_for(dataset_id),
    )


def dataset_version_for(
    dataset_id: str,
    *,
    quality_report: DataQualityReport,
) -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=dataset_id,
        source=SOURCE_ID,
        symbol_universe=("ES",),
        bar_size="1 min",
        what_to_show="TRADES",
        start_ts=dt("2024-01-02T14:30:00+00:00"),
        end_ts=dt("2024-01-02T14:33:00+00:00"),
        contract_universe=("ESM4",),
        roll_policy_id="roll_policy_fixture",
        manifest_hash=HASH_0,
        code_hash=HASH_1,
        config_hash=HASH_2,
        quality_report_hash=compute_quality_report_hash(quality_report),
        created_at=dt("2024-01-02T15:00:00+00:00"),
    )


def quality_report_for(dataset_id: str = DATASET_ID) -> DataQualityReport:
    return DataQualityReport(
        quality_report_id=f"qr_{dataset_id}",
        dataset_version_id=dataset_id,
        gap_summary=_passing_summary(),
        duplicate_summary=_passing_summary(),
        non_monotonic_summary=_passing_summary(),
        ohlc_errors=_passing_summary(),
        zero_negative_price_errors=_passing_summary(),
        zero_volume_anomalies=_passing_summary(),
        dst_anomalies=_passing_summary(),
        session_coverage=_passing_summary(),
        roll_discontinuities=_passing_summary(),
        provider_error_summary=_passing_summary(),
        bbo_missing_metric=_passing_summary(),
        abnormal_spread_summary=_passing_summary(),
        status=ReportStatus.PASSING,
    )


def coverage_report_for(dataset_id: str = DATASET_ID) -> CoverageReport:
    return CoverageReport(
        coverage_report_id=f"cr_{dataset_id}",
        dataset_version_id=dataset_id,
        symbol_coverage=_coverage_summary(),
        contract_coverage=_coverage_summary(),
        session_coverage=_coverage_summary(),
        partition_coverage=_coverage_summary(include_partition_counts=True),
        missing_intervals=(),
        incomplete_chunks=(),
    )


def canonical_partition_plan() -> DatasetPartitionPlan:
    return DatasetPartitionPlan.canonical()


def approved_feature_request(
    name: str = "synthetic_close_return_1m",
    *,
    approval_status: FeatureRequestApprovalStatus = FeatureRequestApprovalStatus.APPROVED,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[name],
        formula_sketch={
            "exposure_family": name,
            "inputs": ["synthetic_close"],
            "operation": "pct_change",
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic fixture rows expose explicit available_ts"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["synthetic_close", "available_ts"],
            "source": "tiny synthetic Feature/Label fixture only",
        },
        approval_status=approval_status,
    )


def governed_label_spec() -> LabelSpec:
    return create_label_spec(
        horizon="1m",
        path_rules={
            "path": "trade_price_forward_return",
            "horizon_minutes": 1,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_flf_p25_fixture",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_fixture",
            "stop_rule": "not_used_for_fixed_horizon_fixture",
        },
        availability_time="2024-01-02T14:33:00+00:00",
        forbidden_feature_overlap={
            "label_ids": ["fwd_ret_1m"],
            "aliases": ["forward_return_1m"],
            "transforms": ["label(fwd_ret_1m)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def label_contract(dataset_id: str = DATASET_ID) -> LabelContractSpec:
    return LabelContractSpec.from_label_spec(
        label_id="fwd_ret_1m",
        family=LabelFamily.FIXED_HORIZON,
        governance_label_spec=governed_label_spec(),
        inputs=LabelInputSpec(
            input_views=("canonical_ohlcv",),
            fields=("close",),
            dataset_version_ids=(dataset_id,),
        ),
        contract_metadata={"fixture": "FLF-P25 synthetic fail-closed tests"},
    )


def registered_label_record(tmp_path: Path, dataset_id: str = DATASET_ID) -> LabelRegistryRecord:
    contract = label_contract(dataset_id)
    version = contract.derive_label_version()
    lineage = LabelLineageRecord(
        label_version=version,
        label_contract=contract,
        label_spec_id=contract.label_spec_id,
        contract_provenance={"fixture": "FLF-P25 synthetic fail-closed tests"},
    )
    return LabelRegistryRecord(
        label_version=version,
        label_contract=contract,
        lineage=lineage,
        exposure_report=LabelExposureReport(registry_entries_checked=0),
        materialization_plan_id="lmat_flf_p25_synthetic_label",
        dataset_version_id=dataset_id,
        partition_id="development_partition",
        materialization_output_path=(tmp_path / "labels.jsonl").as_posix(),
        value_record_count=1,
        first_event_ts=dt("2024-01-02T14:31:00+00:00"),
        last_event_ts=dt("2024-01-02T14:31:00+00:00"),
        first_label_available_ts=dt("2024-01-02T14:33:01+00:00"),
        last_label_available_ts=dt("2024-01-02T14:33:01+00:00"),
        registered_at=dt("2024-01-02T15:00:00+00:00"),
        lifecycle_state=LabelRegistryLifecycleState.REGISTERED,
    )


def label_values(record: LabelRegistryRecord) -> tuple[LabelValueRecord, ...]:
    return (
        LabelValueRecord(
            label_version_id=record.label_version_id,
            entity_id="ES",
            event_ts=dt("2024-01-02T14:31:00+00:00"),
            horizon_end_ts=dt("2024-01-02T14:32:00+00:00"),
            label_available_ts=dt("2024-01-02T14:33:01+00:00"),
            value=0.001,
            label_contract=record.label_contract,
        ),
    )


def label_value_payload(record: LabelRegistryRecord) -> dict[str, object]:
    return label_values(record)[0].to_dict()


def clean_live_feature_references() -> tuple[Mapping[str, str], ...]:
    return (
        {
            "feature_id": "base_ohlcv_returns",
            "information_time": "2024-01-02T14:32:59+00:00",
        },
    )


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _passing_summary() -> dict[str, object]:
    return {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}


def _coverage_summary(*, include_partition_counts: bool = False) -> dict[str, object]:
    summary: dict[str, object] = {
        "status": ReportStatus.PASSING.value,
        "blocking": False,
        "expected_count": 1,
        "observed_count": 1,
        "missing_count": 0,
    }
    if include_partition_counts:
        summary["missing_interval_count"] = 0
        summary["incomplete_chunk_count"] = 0
    return summary

