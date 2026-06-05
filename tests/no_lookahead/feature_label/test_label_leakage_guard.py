from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.leakage_audit import (
    LabelLeakageAuditStatus,
    audit_registered_label,
)
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


def test_clean_live_feature_references_pass_label_leakage_audit(tmp_path: Path) -> None:
    record = _registered_label(tmp_path)

    report = audit_registered_label(
        record,
        live_feature_references=[
            {
                "feature_id": "midprice_last_trade_return",
                "information_time": "2024-01-02T14:31:59+00:00",
            }
        ],
        label_value_records=_label_values(record),
    )

    assert report.status is LabelLeakageAuditStatus.CLEAN
    assert report.clean is True
    assert report.blocking_findings == ()
    assert report.governance_result.clean is True


def test_registered_label_version_reused_as_live_feature_is_blocked(
    tmp_path: Path,
) -> None:
    record = _registered_label(tmp_path)

    report = audit_registered_label(
        record,
        live_feature_references=[
            {
                "feature_id": record.label_version_id,
                "information_time": "2024-01-02T14:31:59+00:00",
            }
        ],
        label_value_records=_label_values(record),
    )

    assert report.blocked is True
    assert any(
        finding.check == "label_identity_as_feature"
        and finding.label_version_id == record.label_version_id
        for finding in report.blocking_findings
    )


def test_forbidden_feature_overlap_is_blocked_by_governance_guard(
    tmp_path: Path,
) -> None:
    record = _registered_label(tmp_path)

    report = audit_registered_label(
        record,
        live_feature_references=[
            {
                "feature_id": "forward_return_1m",
                "information_time": "2024-01-02T14:31:59+00:00",
            }
        ],
        label_value_records=_label_values(record),
    )

    assert report.blocked is True
    assert report.governance_result.blocked is True
    assert any(finding.check == "label_as_feature" for finding in report.blocking_findings)


def test_feature_reaching_label_availability_time_is_blocked(
    tmp_path: Path,
) -> None:
    record = _registered_label(tmp_path)

    report = audit_registered_label(
        record,
        live_feature_references=[
            {
                "feature_id": "midprice_last_trade_return",
                "information_time": "2024-01-02T14:32:00+00:00",
            }
        ],
        label_value_records=_label_values(record),
    )

    assert report.blocked is True
    assert report.governance_result.blocked is True
    assert any(finding.check == "availability_time" for finding in report.blocking_findings)


def _registered_label(tmp_path: Path) -> LabelRegistryRecord:
    contract = _label_contract()
    version = contract.derive_label_version()
    lineage = LabelLineageRecord(
        label_version=version,
        label_contract=contract,
        label_spec_id=contract.label_spec_id,
        contract_provenance={"fixture": "FLF-P23 no-lookahead"},
    )
    return LabelRegistryRecord(
        label_version=version,
        label_contract=contract,
        lineage=lineage,
        exposure_report=LabelExposureReport(registry_entries_checked=0),
        materialization_plan_id="lmat_synthetic_label_leakage_audit",
        dataset_version_id="dsv_synthetic_label_leakage_audit",
        partition_id="development_partition",
        materialization_output_path=(tmp_path / "values.jsonl").as_posix(),
        value_record_count=1,
        first_event_ts=_dt("2024-01-02T14:30:00+00:00"),
        last_event_ts=_dt("2024-01-02T14:30:00+00:00"),
        first_label_available_ts=_dt("2024-01-02T14:32:01+00:00"),
        last_label_available_ts=_dt("2024-01-02T14:32:01+00:00"),
        registered_at=_dt("2024-01-02T15:00:00+00:00"),
        lifecycle_state=LabelRegistryLifecycleState.REGISTERED,
    )


def _label_values(record: LabelRegistryRecord) -> tuple[LabelValueRecord, ...]:
    return (
        LabelValueRecord(
            label_version_id=record.label_version_id,
            entity_id="ES",
            event_ts=_dt("2024-01-02T14:30:00+00:00"),
            horizon_end_ts=_dt("2024-01-02T14:31:00+00:00"),
            label_available_ts=_dt("2024-01-02T14:32:01+00:00"),
            value=0.001,
            label_contract=record.label_contract,
        ),
    )


def _label_contract() -> LabelContractSpec:
    label_spec = _label_spec()
    return LabelContractSpec.from_label_spec(
        label_id="fwd_ret_1m",
        family=LabelFamily.FIXED_HORIZON,
        governance_label_spec=label_spec,
        inputs=LabelInputSpec(
            input_views=("canonical_ohlcv",),
            fields=("close",),
            dataset_version_ids=("dsv_synthetic_label_leakage_audit",),
        ),
        contract_metadata={"fixture": "FLF-P23 no-lookahead"},
    )


def _label_spec() -> LabelSpec:
    return create_label_spec(
        horizon="1m",
        path_rules={
            "path": "trade_price_forward_return",
            "horizon_minutes": 1,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_leakage_audit_fixture",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_return",
            "stop_rule": "not_used_for_fixed_horizon_return",
        },
        availability_time="2024-01-02T14:32:00+00:00",
        forbidden_feature_overlap={
            "label_ids": ["fwd_ret_1m"],
            "aliases": ["forward_return_1m"],
            "transforms": ["label(fwd_ret_1m)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
