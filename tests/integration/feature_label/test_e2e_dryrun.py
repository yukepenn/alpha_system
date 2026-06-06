from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from alpha_system.cli import feature as feature_cli
from alpha_system.cli import label as label_cli
from alpha_system.cli.main import build_parser
from alpha_system.data.foundation.datasets import (
    CoverageReport,
    DataQualityReport,
    DatasetVersion,
    ReportStatus,
    compute_quality_report_hash,
)
from alpha_system.data.foundation.version_registry import persist_dataset_version
from alpha_system.features import consumption
from alpha_system.features.contracts import FeatureLineageRecord, FeatureSetSpec, FeatureSpec
from alpha_system.features.engine.materialization import (
    FeatureMaterializationInputs,
    build_feature_materialization_plan,
    materialize_features,
)
from alpha_system.features.families.bbo import (
    BBOFeatureDefinition,
    BBOFeatureName,
    build_bbo_feature_definition,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureDefinition,
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.features.registry import (
    PROHIBITED_FEATURE_REGISTRY_STATES,
    FeatureRegistry,
    FeatureRegistryLifecycleState,
    FeatureRegistryRecord,
)
from alpha_system.features.reports import (
    build_feature_coverage_report,
    build_feature_quality_report,
)
from alpha_system.governance.alpha_spec import validate_alpha_spec
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.governance.label_leakage_guard import check_label_leakage
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.governance.study_input_pack import (
    create_study_input_pack,
    validate_study_input_pack_references,
)
from alpha_system.governance.study_spec import create_study_spec
from alpha_system.labels.engine import (
    LabelMaterializationInputs,
    build_label_materialization_plan,
    materialize_labels,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from alpha_system.labels.leakage_audit import LabelLeakageAuditStatus, audit_registered_label
from alpha_system.labels.registry import (
    PROHIBITED_LABEL_REGISTRY_STATES,
    LabelRegistry,
    LabelRegistryLifecycleState,
)
from alpha_system.labels.version import LabelLineageRecord

DATASET_ID = "dsv_databento_feature_label_e2e_dryrun_v1"
PARTITION_ID = "development_partition"
HASH_0 = "0" * 64
HASH_1 = "1" * 64
HASH_2 = "2" * 64


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_feature_label_e2e_dry_run_uses_cli_engines_and_governance(
    tmp_path: Path,
    capsys: Any,
) -> None:
    alpha_data_root = tmp_path / "alpha_data"
    dataset_registry_path = alpha_data_root / "registry" / "datasets.sqlite"
    feature_registry_path = alpha_data_root / "registry" / "features.sqlite"
    label_registry_path = alpha_data_root / "registry" / "labels.sqlite"
    quality_report = _quality_report(DATASET_ID)
    coverage_report = _coverage_report(DATASET_ID)
    dataset_version = _dataset_version(DATASET_ID, quality_report=quality_report)
    source_manifest = {"manifest_hash": dataset_version.manifest_hash}
    persist_dataset_version(
        dataset_registry_path,
        dataset_version,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=dataset_version.code_hash,
        config_hash=dataset_version.config_hash,
    )

    alpha_spec = validate_alpha_spec(
        json.loads(Path("tests/fixtures/governance/alpha_spec_valid.json").read_text())
    )
    feature_requests = _approved_feature_requests(alpha_spec.alpha_spec_id)
    feature_definitions = _feature_definitions(feature_requests)
    label_spec = _mid_label_spec(alpha_spec.alpha_spec_id)
    label_definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.MID_FWD_RET_1M,
        label_spec,
        dataset_version_ids=(DATASET_ID,),
    )
    accepted = consumption.resolve_accepted_dataset_version(
        dataset_registry_path,
        DATASET_ID,
        lifecycle_state="VERSIONED",
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        code_hash=dataset_version.code_hash,
        config_hash=dataset_version.config_hash,
    )

    bar_rows = _bar_rows(DATASET_ID, length=5)
    bbo_rows = _bbo_rows(DATASET_ID, length=5)
    dense_rows = (_dense_no_trade_row(DATASET_ID),)
    assert _feature_lifecycle_observed(feature_requests, feature_definitions) == (
        "REQUESTED",
        "SPEC_DRAFTED",
        "SPEC_VALIDATED",
        "IMPLEMENTATION_ALLOWED",
    )
    assert _label_lifecycle_observed(label_spec, label_definition) == (
        "LABEL_REQUESTED",
        "LABEL_SPEC_DRAFTED",
        "LABEL_SPEC_VALIDATED",
        "MATERIALIZATION_ALLOWED",
    )

    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_e2e_dryrun",
        feature_set_version="v1",
        features=tuple(_feature_spec(definition) for definition in feature_definitions),
        description="P30 local-only end-to-end dry-run feature set.",
        metadata={"phase": "FLF-P30", "dataset_version_id": DATASET_ID},
    )
    feature_plan = build_feature_materialization_plan(
        feature_set,
        accepted,
        partition_id=PARTITION_ID,
        alpha_data_root=alpha_data_root,
        output_namespace="features/dry_runs/e2e",
    )
    feature_result = materialize_features(
        feature_plan,
        FeatureMaterializationInputs(
            accepted_version=accepted,
            bar_rows=bar_rows,
            bbo_rows=bbo_rows,
            dense_grid_bar_rows=dense_rows,
        ),
        feature_definitions,
        dry_run=False,
    )

    assert feature_result.wrote_output is True
    assert feature_result.output_path is not None
    assert feature_result.output_path.is_relative_to(alpha_data_root)
    assert all(record.available_ts.tzinfo is not None for record in feature_result.records)
    assert all(record.available_ts >= record.event_ts for record in feature_result.records)
    missing_mid_records = [
        record
        for record in feature_result.records
        if record.feature_version_id
        == _definition_by_name(feature_definitions, BBOFeatureName.MID).feature_version_id
        and "missing_bbo" in record.quality_flags
    ]
    quarantined_mid_records = [
        record
        for record in feature_result.records
        if record.feature_version_id
        == _definition_by_name(feature_definitions, BBOFeatureName.MID).feature_version_id
        and "bbo_quarantined" in record.quality_flags
    ]
    assert missing_mid_records and all(record.value is None for record in missing_mid_records)
    assert quarantined_mid_records and all(
        record.value is None for record in quarantined_mid_records
    )
    missing_bbo_flag_version_id = _definition_by_name(
        feature_definitions,
        BBOFeatureName.MISSING_BBO_FLAG,
    ).feature_version_id
    assert missing_bbo_flag_version_id in {
        record.feature_version_id for record in feature_result.records
    }
    assert _synthetic_no_trade_rows(dense_rows) == 1
    assert len([record for record in feature_result.records if record.entity_id == "ES_c_0"]) > 0

    feature_registry = FeatureRegistry(feature_registry_path)
    feature_records = tuple(
        feature_registry.persist_feature(
            _feature_registry_record(
                definition,
                feature_result=feature_result,
                ordinal=ordinal,
            )
        )
        for ordinal, definition in enumerate(feature_definitions)
    )
    assert {record.lifecycle_state for record in feature_records} == {
        FeatureRegistryLifecycleState.REGISTERED
    }
    feature_quality_reports = tuple(
        build_feature_quality_report(record, alpha_data_root=alpha_data_root)
        for record in feature_records
    )
    feature_coverage_reports = tuple(
        build_feature_coverage_report(record, alpha_data_root=alpha_data_root)
        for record in feature_records
    )
    assert all(not report.blocking for report in feature_quality_reports)
    coverage_blocking_codes = {
        finding.code for report in feature_coverage_reports for finding in report.blocking
    }
    assert "SESSION_COVERAGE_UNRESOLVED" in coverage_blocking_codes
    assert all(report.record_count > 0 for report in feature_coverage_reports)
    assert any(report.missing_bbo_count >= 1 for report in feature_quality_reports)
    assert any(report.bbo_quarantined_count >= 1 for report in feature_quality_reports)
    assert PROHIBITED_FEATURE_REGISTRY_STATES.isdisjoint(
        {state.value for state in FeatureRegistryLifecycleState}
    )

    label_plan = build_label_materialization_plan(
        (label_definition,),
        accepted,
        partition_id=PARTITION_ID,
        instrument_ids=("ES",),
        alpha_data_root=alpha_data_root,
        dry_run=False,
        output_namespace="labels/dry_runs/e2e",
    )
    label_result = materialize_labels(
        label_plan,
        LabelMaterializationInputs(
            accepted_version=accepted,
            bar_rows=bar_rows,
            bbo_rows=bbo_rows,
            dense_grid_bar_rows=dense_rows,
        ),
        (label_definition,),
    )
    assert label_result.wrote_output is True
    assert label_result.output_path is not None
    assert label_result.output_path.is_relative_to(alpha_data_root)
    assert all(record.label_available_ts.tzinfo is not None for record in label_result.records)
    assert all(
        record.label_available_ts >= record.horizon_end_ts for record in label_result.records
    )
    assert all(record.label_spec_id == label_spec.label_spec_id for record in label_result.records)

    label_registry = LabelRegistry(label_registry_path)
    label_record = label_registry.register_materialized_label(
        label_result,
        label_contract=label_definition.contract,
        label_version=label_definition.version,
        lineage=LabelLineageRecord(
            label_version=label_definition.version,
            label_contract=label_definition.contract,
            label_spec_id=label_definition.label_spec_id,
            contract_provenance={"phase": "FLF-P30", "fixture": "e2e_dryrun"},
        ),
    )
    safe_feature_references = [
        {
            "feature_id": record.feature_spec.feature_id,
            "feature_version_id": record.feature_version_id,
            "available_at": "2024-01-02T13:59:00+00:00",
        }
        for record in feature_records
    ]
    governance_leakage = check_label_leakage(label_spec, safe_feature_references)
    audit = audit_registered_label(
        label_record,
        live_feature_references=safe_feature_references,
        label_value_records=label_result.records,
    )
    assert governance_leakage.clean is True
    assert audit.status is LabelLeakageAuditStatus.CLEAN
    assert audit.value_records_checked == len(label_result.records)
    ready_label_record = replace(
        label_record,
        lifecycle_state=LabelRegistryLifecycleState.READY_FOR_STUDY,
    )
    assert ready_label_record.lifecycle_state is LabelRegistryLifecycleState.READY_FOR_STUDY
    assert PROHIBITED_LABEL_REGISTRY_STATES.isdisjoint(
        {state.value for state in LabelRegistryLifecycleState}
    )

    dataset_scope = {
        "dataset_version_ids": [DATASET_ID],
        "partition_id": PARTITION_ID,
        "symbols": ["ES"],
        "source": "accepted synthetic Databento-shaped DatasetVersion fixture",
    }
    study_spec = create_study_spec(
        alpha_spec_id=alpha_spec.alpha_spec_id,
        label_spec_id=label_spec.label_spec_id,
        dataset_scope=dataset_scope,
        split_protocol={"development": "2024-01-02 synthetic fixture only"},
        metrics=["coverage", "leakage_audit_clean"],
        cost_assumptions={"scope": "not evaluated in dry-run substrate test"},
        variant_budget=1,
        locked_test_policy={
            "allowed_touch": "locked test is not used by this local dry-run fixture",
            "oos_reuse": "out-of-sample reuse is not performed in this substrate test",
        },
        negative_controls=["not run in substrate dry-run"],
        stopping_rules=["stop on leakage or missing availability timestamp"],
    )
    input_pack = create_study_input_pack(
        feature_request_ids=[request.feature_request_id for request in feature_requests],
        label_spec_ids=[label_spec.label_spec_id],
        alpha_spec_id=alpha_spec.alpha_spec_id,
        dataset_scope=dataset_scope,
    )
    validated_pack = validate_study_input_pack_references(
        input_pack,
        feature_requests=feature_requests,
        label_specs=[label_spec],
        alpha_spec=alpha_spec,
        study_spec=study_spec,
    )
    assert validated_pack.to_dict()["dataset_scope"] == dataset_scope
    assert _final_lifecycle_observed(feature_records, audit, validated_pack) == (
        "IMPLEMENTED",
        "MATERIALIZATION_PLANNED",
        "MATERIALIZED_DRAFT",
        "QUALITY_CHECKED",
        "REGISTERED",
        "LEAKAGE_AUDITED",
        "READY_FOR_STUDY",
    )

    paths = _write_cli_inputs(
        tmp_path,
        quality_report=quality_report,
        coverage_report=coverage_report,
        source_manifest=source_manifest,
        label_spec=label_spec,
        input_pack=validated_pack.to_dict(),
        feature_references=safe_feature_references,
        label_records=[record.to_dict() for record in label_result.records],
    )
    parser = build_parser()
    feature_args = parser.parse_args(
        [
            "feature",
            "materialize",
            "--registry-path",
            feature_registry_path.as_posix(),
            "--feature-set-id",
            feature_set.feature_set_id,
            "--feature-set-version",
            feature_set.feature_set_version,
            "--dataset-registry",
            dataset_registry_path.as_posix(),
            "--dataset-version-id",
            DATASET_ID,
            "--quality-report",
            paths["quality"].as_posix(),
            "--coverage-report",
            paths["coverage"].as_posix(),
            "--source-manifest",
            paths["manifest"].as_posix(),
            "--code-hash",
            HASH_1,
            "--config-hash",
            HASH_2,
            "--partition",
            PARTITION_ID,
            "--alpha-data-root",
            alpha_data_root.as_posix(),
            "--json",
        ]
    )
    assert feature_cli.run_materialize(feature_args) == 0
    feature_cli_payload = json.loads(capsys.readouterr().out)
    assert feature_cli_payload["command"] == "feature materialize"
    assert feature_cli_payload["dry_run"] is True
    assert feature_cli_payload["writes_values"] is False
    assert feature_cli_payload["plan"]["dataset_version_id"] == DATASET_ID

    label_args = parser.parse_args(
        [
            "label",
            "materialize",
            "--label-family",
            "fixed_horizon",
            "--label-name",
            FixedHorizonLabelName.MID_FWD_RET_1M.value,
            "--label-spec",
            paths["label_spec"].as_posix(),
            "--dataset-registry",
            dataset_registry_path.as_posix(),
            "--dataset-version-id",
            DATASET_ID,
            "--quality-report",
            paths["quality"].as_posix(),
            "--coverage-report",
            paths["coverage"].as_posix(),
            "--source-manifest",
            paths["manifest"].as_posix(),
            "--code-hash",
            HASH_1,
            "--config-hash",
            HASH_2,
            "--partition",
            PARTITION_ID,
            "--alpha-data-root",
            alpha_data_root.as_posix(),
            "--instrument",
            "ES",
            "--json",
        ]
    )
    assert label_cli.run_materialize(label_args) == 0
    label_cli_payload = json.loads(capsys.readouterr().out)
    assert label_cli_payload["command"] == "label materialize"
    assert label_cli_payload["dry_run"] is True
    assert label_cli_payload["writes_values"] is False
    assert label_cli_payload["plan"]["label_spec_ids"] == [label_spec.label_spec_id]

    input_pack_args = parser.parse_args(
        ["label", "input-pack", "--input-pack", paths["input_pack"].as_posix(), "--json"]
    )
    assert label_cli.run_input_pack(input_pack_args) == 0
    input_pack_payload = json.loads(capsys.readouterr().out)
    assert input_pack_payload["feature_request_count"] == len(feature_requests)
    assert input_pack_payload["label_spec_count"] == 1
    assert input_pack_payload["dataset_scope_keys"] == sorted(dataset_scope)

    audit_args = parser.parse_args(
        [
            "label",
            "leakage-audit",
            "--registry-path",
            label_registry_path.as_posix(),
            "--label-version-id",
            label_definition.label_version_id,
            "--live-feature-references",
            paths["feature_refs"].as_posix(),
            "--label-value-records",
            paths["label_records"].as_posix(),
            "--json",
        ]
    )
    assert label_cli.run_leakage_audit(audit_args) == 0
    audit_payload = json.loads(capsys.readouterr().out)
    assert audit_payload["report"]["status"] == LabelLeakageAuditStatus.CLEAN.value
    assert audit_payload["report"]["blocking_finding_count"] == 0

    assert feature_result.output_path.resolve(strict=False).is_relative_to(
        alpha_data_root.resolve(strict=False)
    )
    assert label_result.output_path.resolve(strict=False).is_relative_to(
        alpha_data_root.resolve(strict=False)
    )
    assert not any(
        Path.cwd().resolve(strict=False) in path.parents for path in alpha_data_root.rglob("*")
    )


def _feature_definitions(
    requests: tuple[FeatureRequest, FeatureRequest, FeatureRequest],
) -> tuple[OHLCVFeatureDefinition, BBOFeatureDefinition, BBOFeatureDefinition]:
    return (
        build_ohlcv_feature_definition(
            OHLCVFeatureName.RETURNS,
            requests[0],
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_ID,),
            reset_on_session=False,
        ),
        build_bbo_feature_definition(
            BBOFeatureName.MID,
            requests[1],
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_ID,),
        ),
        build_bbo_feature_definition(
            BBOFeatureName.MISSING_BBO_FLAG,
            requests[2],
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_ID,),
        ),
    )


def _feature_spec(definition: OHLCVFeatureDefinition | BBOFeatureDefinition) -> FeatureSpec:
    spec = definition.spec
    if isinstance(spec, FeatureSpec):
        return spec
    return spec.feature_spec


def _definition_by_name(
    definitions: tuple[OHLCVFeatureDefinition, BBOFeatureDefinition, BBOFeatureDefinition],
    name: BBOFeatureName,
) -> BBOFeatureDefinition:
    matches = [
        definition
        for definition in definitions
        if isinstance(definition, BBOFeatureDefinition) and definition.name is name
    ]
    assert len(matches) == 1
    return matches[0]


def _feature_registry_record(
    definition: OHLCVFeatureDefinition | BBOFeatureDefinition,
    *,
    feature_result: object,
    ordinal: int,
) -> FeatureRegistryRecord:
    spec = _feature_spec(definition)
    version = definition.version
    checked_request = definition.request_gate_decision.checked_feature_request
    duplicate_report = definition.request_gate_decision.duplicate_exposure_report
    assert checked_request is not None
    assert duplicate_report is not None
    records = tuple(
        record
        for record in feature_result.records
        if record.feature_version_id == version.feature_version_id
    )
    assert records
    assert feature_result.output_path is not None
    return FeatureRegistryRecord(
        feature_version=version,
        feature_spec=spec,
        lineage=FeatureLineageRecord(
            feature_version=version,
            feature_spec=spec,
            feature_request_id=spec.feature_request_id,
            contract_provenance={"phase": "FLF-P30", "fixture": "e2e_dryrun"},
        ),
        feature_request_payload=checked_request.to_dict(),
        duplicate_exposure_report=duplicate_report,
        feature_set_id=feature_result.plan.feature_set.feature_set_id,
        feature_set_version=feature_result.plan.feature_set.feature_set_version,
        feature_set_ordinal=ordinal,
        materialization_plan_id=feature_result.plan.plan_id,
        dataset_version_id=feature_result.plan.dataset_version_id,
        partition_id=feature_result.plan.partition_id,
        materialization_output_path=feature_result.output_path.as_posix(),
        value_record_count=len(records),
        first_event_ts=min(record.event_ts for record in records),
        last_event_ts=max(record.event_ts for record in records),
        first_available_ts=min(record.available_ts for record in records),
        last_available_ts=max(record.available_ts for record in records),
        registered_at=_dt("2024-01-02T15:10:00+00:00"),
        registry_metadata=_coverage_registry_metadata(),
    )


def _approved_feature_requests(
    alpha_spec_id: str,
) -> tuple[FeatureRequest, FeatureRequest, FeatureRequest]:
    return (
        _approved_feature_request(
            alpha_spec_id,
            "returns",
            ("canonical_ohlcv",),
            ("close",),
        ),
        _approved_feature_request(
            alpha_spec_id,
            "bbo_mid",
            ("canonical_bbo",),
            ("mid", "quality_flags"),
        ),
        _approved_feature_request(
            alpha_spec_id,
            "missing_bbo_flag",
            ("canonical_bbo",),
            ("quality_flags",),
        ),
    )


def _approved_feature_request(
    alpha_spec_id: str,
    token: str,
    input_views: tuple[str, ...],
    fields: tuple[str, ...],
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=alpha_spec_id,
        requested_inputs=[f"e2e_{token}"],
        formula_sketch={
            "exposure_family": f"e2e_{token}",
            "inputs": list(input_views),
            "operation": token,
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic canonical rows expose available_ts after bar end"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": list(fields),
            "source": "tiny synthetic canonical mappings only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _mid_label_spec(alpha_spec_id: str) -> LabelSpec:
    return create_label_spec(
        horizon="1m",
        path_rules={
            "path": "midprice_forward_return",
            "horizon_minutes": 1,
            "terminal_rule": "exact event_ts row at fixed forward horizon",
        },
        cost_model={
            "model": "gross_unadjusted_forward_return",
            "adjustment_scope": "not_applied_in_fixed_horizon_family",
        },
        target_stop_rules={
            "target_rule": "not_used_for_fixed_horizon_return",
            "stop_rule": "not_used_for_fixed_horizon_return",
        },
        availability_time="2024-01-02T14:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [FixedHorizonLabelName.MID_FWD_RET_1M.value],
            "aliases": ["mid_forward_return_1m"],
            "transforms": ["label(mid_fwd_ret_1m)"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
        alpha_spec_id=alpha_spec_id,
    )


def _dataset_version(dataset_id: str, *, quality_report: DataQualityReport) -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=dataset_id,
        source="dsrc_databento_historical",
        symbol_universe=("ES",),
        bar_size="1 min",
        what_to_show="TRADES_AND_BBO",
        start_ts=_dt("2024-01-02T14:30:00+00:00"),
        end_ts=_dt("2024-01-02T14:35:00+00:00"),
        contract_universe=("ESM4",),
        roll_policy_id="roll_policy_fixture",
        manifest_hash=HASH_0,
        code_hash=HASH_1,
        config_hash=HASH_2,
        quality_report_hash=compute_quality_report_hash(quality_report),
        created_at=_dt("2024-01-02T15:00:00+00:00"),
    )


def _quality_report(dataset_id: str) -> DataQualityReport:
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
        bbo_missing_metric=_metric_summary(count=1, status=ReportStatus.WARNING),
        abnormal_spread_summary=_metric_summary(count=1, status=ReportStatus.WARNING),
        status=ReportStatus.WARNING,
    )


def _coverage_report(dataset_id: str) -> CoverageReport:
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


def _passing_summary() -> dict[str, object]:
    return {"count": 0, "status": ReportStatus.PASSING.value, "blocking": False}


def _metric_summary(*, count: int, status: ReportStatus) -> dict[str, object]:
    return {"count": count, "status": status.value, "blocking": False}


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


def _bar_rows(dataset_id: str, *, length: int) -> tuple[dict[str, object], ...]:
    start = _dt("2024-01-02T14:30:00+00:00")
    return tuple(
        _bar_row(dataset_id, start + timedelta(minutes=index), close=Decimal("100") + index)
        for index in range(length)
    )


def _bar_row(dataset_id: str, start: datetime, *, close: Decimal) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_c_0",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": end.isoformat(),
        "event_ts": end.isoformat(),
        "available_ts": (end + timedelta(seconds=1)).isoformat(),
        "ingested_at": (end + timedelta(seconds=2)).isoformat(),
        "open": str(close - Decimal("0.25")),
        "high": str(close + Decimal("0.50")),
        "low": str(close - Decimal("0.50")),
        "close": str(close),
        "volume": "10",
        "source": "dsrc_databento_historical",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": (),
        "session_label": "RTH",
    }


def _bbo_rows(dataset_id: str, *, length: int) -> tuple[dict[str, object], ...]:
    start = _dt("2024-01-02T14:30:00+00:00")
    rows = []
    for index in range(length):
        if index == 1:
            rows.append(_missing_bbo_row(dataset_id, start + timedelta(minutes=index)))
        elif index == 2:
            rows.append(
                _bbo_row(
                    dataset_id,
                    start + timedelta(minutes=index),
                    mid=Decimal("102"),
                    quality_flags=("bbo_quarantined",),
                )
            )
        else:
            rows.append(
                _bbo_row(dataset_id, start + timedelta(minutes=index), mid=Decimal("100") + index)
            )
    return tuple(rows)


def _bbo_row(
    dataset_id: str,
    start: datetime,
    *,
    mid: Decimal,
    quality_flags: tuple[str, ...] = (),
) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    bid = mid - Decimal("0.25")
    ask = mid + Decimal("0.25")
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_c_0",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": end.isoformat(),
        "event_ts": end.isoformat(),
        "available_ts": (end + timedelta(seconds=1)).isoformat(),
        "ingested_at": (end + timedelta(seconds=2)).isoformat(),
        "bid": str(bid),
        "ask": str(ask),
        "bid_size": "10",
        "ask_size": "12",
        "mid": str(mid),
        "spread": str(ask - bid),
        "source": "dsrc_databento_historical",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": quality_flags,
        "session_label": "RTH",
        "spread_ticks": "2",
        "microprice": str(mid),
        "bid_order_count": 1,
        "ask_order_count": 1,
    }


def _missing_bbo_row(dataset_id: str, start: datetime) -> dict[str, object]:
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_c_0",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": end.isoformat(),
        "event_ts": end.isoformat(),
        "available_ts": (end + timedelta(seconds=1)).isoformat(),
        "ingested_at": (end + timedelta(seconds=2)).isoformat(),
        "bid": "0",
        "ask": "0",
        "bid_size": "0",
        "ask_size": "0",
        "mid": "0",
        "spread": "0",
        "source": "dsrc_databento_historical",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": ("missing_bbo",),
        "session_label": "RTH",
        "spread_ticks": "0",
        "microprice": "0",
        "bid_order_count": 0,
        "ask_order_count": 0,
    }


def _dense_no_trade_row(dataset_id: str) -> dict[str, object]:
    start = _dt("2024-01-02T14:35:00+00:00")
    end = start + timedelta(minutes=1)
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_c_0",
        "bar_start_ts": start.isoformat(),
        "bar_end_ts": end.isoformat(),
        "event_ts": end.isoformat(),
        "available_ts": (end + timedelta(seconds=1)).isoformat(),
        "ingested_at": (end + timedelta(seconds=2)).isoformat(),
        "open": "104",
        "high": "104",
        "low": "104",
        "close": "104",
        "volume": "0",
        "source": "dsrc_databento_historical",
        "source_request_id": "req_fixture_1",
        "data_version": dataset_id,
        "quality_flags": ("no_trade",),
        "session_label": "RTH",
        "has_trade": False,
        "synthetic": True,
        "fill_method": "previous_close",
        "provider_bar_ref": None,
    }


def _synthetic_no_trade_rows(rows: tuple[dict[str, object], ...]) -> int:
    return sum(
        1
        for row in rows
        if row["has_trade"] is False
        and row["synthetic"] is True
        and "no_trade" in row["quality_flags"]
        and row["volume"] == "0"
    )


def _coverage_registry_metadata() -> dict[str, object]:
    return {
        "coverage_expectations": {
            "symbols": ["ES"],
            "sessions": ["RTH"],
            "partitions": [PARTITION_ID],
        }
    }


def _feature_lifecycle_observed(
    requests: tuple[FeatureRequest, ...],
    definitions: tuple[OHLCVFeatureDefinition, BBOFeatureDefinition, BBOFeatureDefinition],
) -> tuple[str, ...]:
    assert all(
        request.approval_status == FeatureRequestApprovalStatus.APPROVED.value
        for request in requests
    )
    assert all(_feature_spec(definition).implementation_eligible for definition in definitions)
    assert all(
        definition.request_gate_decision.implementation_allowed for definition in definitions
    )
    return ("REQUESTED", "SPEC_DRAFTED", "SPEC_VALIDATED", "IMPLEMENTATION_ALLOWED")


def _label_lifecycle_observed(
    label_spec: LabelSpec,
    definition: FixedHorizonLabelDefinition,
) -> tuple[str, ...]:
    assert label_spec.label_spec_id == definition.label_spec_id
    assert definition.contract.availability_policy.future_data_legal_only_for_labels
    return (
        "LABEL_REQUESTED",
        "LABEL_SPEC_DRAFTED",
        "LABEL_SPEC_VALIDATED",
        "MATERIALIZATION_ALLOWED",
    )


def _final_lifecycle_observed(
    feature_records: tuple[object, ...],
    audit: object,
    input_pack: object,
) -> tuple[str, ...]:
    assert feature_records
    assert audit.status is LabelLeakageAuditStatus.CLEAN
    assert input_pack.feature_request_ids
    return (
        "IMPLEMENTED",
        "MATERIALIZATION_PLANNED",
        "MATERIALIZED_DRAFT",
        "QUALITY_CHECKED",
        "REGISTERED",
        "LEAKAGE_AUDITED",
        "READY_FOR_STUDY",
    )


def _write_cli_inputs(
    tmp_path: Path,
    *,
    quality_report: DataQualityReport,
    coverage_report: CoverageReport,
    source_manifest: dict[str, object],
    label_spec: LabelSpec,
    input_pack: dict[str, object],
    feature_references: list[dict[str, object]],
    label_records: list[dict[str, object]],
) -> dict[str, Path]:
    paths = {
        "quality": tmp_path / "quality.json",
        "coverage": tmp_path / "coverage.json",
        "manifest": tmp_path / "manifest.json",
        "label_spec": tmp_path / "label_spec.json",
        "input_pack": tmp_path / "input_pack.json",
        "feature_refs": tmp_path / "feature_refs.json",
        "label_records": tmp_path / "label_records.json",
    }
    _write_json(paths["quality"], _quality_report_dict(quality_report))
    _write_json(paths["coverage"], _coverage_report_dict(coverage_report))
    _write_json(paths["manifest"], source_manifest)
    _write_json(paths["label_spec"], label_spec.to_dict())
    _write_json(paths["input_pack"], input_pack)
    _write_json(paths["feature_refs"], feature_references)
    _write_json(paths["label_records"], label_records)
    return paths


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _quality_report_dict(report: DataQualityReport) -> dict[str, object]:
    return {
        "quality_report_id": report.quality_report_id,
        "dataset_version_id": report.dataset_version_id,
        "gap_summary": dict(report.gap_summary),
        "duplicate_summary": dict(report.duplicate_summary),
        "non_monotonic_summary": dict(report.non_monotonic_summary),
        "ohlc_errors": dict(report.ohlc_errors),
        "zero_negative_price_errors": dict(report.zero_negative_price_errors),
        "zero_volume_anomalies": dict(report.zero_volume_anomalies),
        "dst_anomalies": dict(report.dst_anomalies),
        "session_coverage": dict(report.session_coverage),
        "roll_discontinuities": dict(report.roll_discontinuities),
        "provider_error_summary": dict(report.provider_error_summary),
        "bbo_missing_metric": dict(report.bbo_missing_metric),
        "abnormal_spread_summary": dict(report.abnormal_spread_summary),
        "status": report.status.value,
    }


def _coverage_report_dict(report: CoverageReport) -> dict[str, object]:
    return {
        "coverage_report_id": report.coverage_report_id,
        "dataset_version_id": report.dataset_version_id,
        "symbol_coverage": dict(report.symbol_coverage),
        "contract_coverage": dict(report.contract_coverage),
        "session_coverage": dict(report.session_coverage),
        "partition_coverage": dict(report.partition_coverage),
        "missing_intervals": [dict(item) for item in report.missing_intervals],
        "incomplete_chunks": [dict(item) for item in report.incomplete_chunks],
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, ReportStatus):
        return value.value
    return value


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
