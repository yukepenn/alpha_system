from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alpha_system.features.contracts import (
    FeatureFamily,
    FeatureInputSpec,
    FeatureLineageRecord,
    FeatureSpec,
    NormalizationSpec,
    TransformSpec,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.registry import FeatureRegistryRecord
from alpha_system.features.reports import (
    FeatureCoverageReport,
    FeaturePartitionRole,
    FeatureQualityReport,
)
from alpha_system.features.request_gate import (
    DuplicateExposureReport,
    EquivalentFeatureGroup,
    evaluate_feature_request_gate,
)
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureFindingKind,
    ExposureFindingSeverity,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
DATASET_VERSION_ID = "dsv_synthetic_feature_reports_v1"
PLAN_ID = "fmat_feature_report_fixture"
PARTITION_ID = "development_partition"
MISSING = object()


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_quality_report_fails_closed_on_missing_available_ts_and_surfaces_bbo(
    tmp_path: Path,
) -> None:
    record = _registry_record(
        tmp_path,
        rows=(
            _row(
                "2024-01-02T14:31:00+00:00",
                "2024-01-02T14:31:05+00:00",
                {"metric": 1.0, "session_label": "RTH"},
                quality_flags=("missing_bbo",),
            ),
            _row(
                "2024-01-02T14:32:00+00:00",
                MISSING,
                {"metric": 1.0, "session_label": "RTH"},
                quality_flags=("bbo_quarantined",),
            ),
        ),
        duplicate_report=_equivalent_exposure_report(),
    )

    report = FeatureQualityReport.from_registry_record(record, alpha_data_root=tmp_path)

    assert report.available_ts_missing_count == 1
    assert report.missing_bbo_count == 1
    assert report.bbo_quarantined_count == 1
    assert report.constant_feature is True
    assert report.duplicate_exposure_status == "EQUIVALENCE_RECORDED"
    assert len(report.equivalent_feature_groups) == 1
    assert _codes(report.blocking) == {"FEATURE_VALUE_AVAILABLE_TS_MISSING"}
    assert {
        "MISSING_BBO_EXPOSURE_RECORDED",
        "CONSTANT_FEATURE_DETECTED",
        "EQUIVALENT_EXPOSURE_RECORDED",
    }.issubset(_codes(report.non_blocking))
    assert all(finding.severity.value == "blocking" for finding in report.blocking)
    assert all(finding.severity.value == "non_blocking" for finding in report.non_blocking)


def test_coverage_report_blocks_undocumented_gaps_and_records_documented_gaps(
    tmp_path: Path,
) -> None:
    record = _registry_record(
        tmp_path,
        rows=(
            _row(
                "2024-01-02T14:31:00+00:00",
                "2024-01-02T14:31:05+00:00",
                {"metric": 1.0, "session_label": "RTH"},
            ),
        ),
        registry_metadata={
            "coverage_expectations": {
                "symbols": ["ES", "NQ"],
                "sessions": ["ETH", "RTH"],
                "partitions": [PARTITION_ID],
                "documented_gaps": {"sessions": ["ETH"]},
            }
        },
    )

    report = FeatureCoverageReport.from_registry_record(record, alpha_data_root=tmp_path)

    assert report.partition_role is FeaturePartitionRole.DEVELOPMENT
    assert report.symbol_coverage[0].key == "ES"
    assert report.session_coverage[0].key == "RTH"
    assert report.partition_coverage[0].key == PARTITION_ID
    assert "UNDOCUMENTED_SYMBOL_COVERAGE_GAP" in _codes(report.blocking)
    assert "DOCUMENTED_SESSION_COVERAGE_GAP" in _codes(report.non_blocking)


def test_coverage_report_fails_closed_without_documented_symbol_or_session_scope(
    tmp_path: Path,
) -> None:
    record = _registry_record(
        tmp_path,
        rows=(
            _row(
                "2024-01-02T14:31:00+00:00",
                "2024-01-02T14:31:05+00:00",
                1.0,
            ),
        ),
        registry_metadata={},
    )

    report = FeatureCoverageReport.from_registry_record(record, alpha_data_root=tmp_path)

    assert {
        "SYMBOL_COVERAGE_EXPECTATIONS_MISSING",
        "SESSION_COVERAGE_EXPECTATIONS_MISSING",
        "SESSION_COVERAGE_UNRESOLVED",
    }.issubset(_codes(report.blocking))


def _registry_record(
    tmp_path: Path,
    *,
    rows: tuple[dict[str, object], ...],
    registry_metadata: dict[str, object] | None = None,
    duplicate_report: DuplicateExposureReport | None = None,
) -> FeatureRegistryRecord:
    spec, request_payload = _feature_spec()
    version = spec.derive_feature_version()
    output_path = tmp_path / "features" / "materialized" / "values.jsonl"
    _write_values(output_path, version.feature_version_id, rows)
    event_ts = tuple(_dt(str(row["event_ts"])) for row in rows)
    available_ts = tuple(
        _dt(str(row["available_ts"]))
        for row in rows
        if row.get("available_ts", MISSING) is not MISSING
    )
    first_available = min(available_ts) if available_ts else min(event_ts)
    last_available = max(available_ts) if available_ts else max(event_ts)
    return FeatureRegistryRecord(
        feature_version=version,
        feature_spec=spec,
        lineage=FeatureLineageRecord(
            feature_version=version,
            feature_spec=spec,
            feature_request_id=spec.feature_request_id,
            contract_provenance={"test": "feature_reports"},
        ),
        feature_request_payload=request_payload,
        duplicate_exposure_report=duplicate_report or _empty_duplicate_report(),
        feature_set_id="feature_set_report_fixture",
        feature_set_version="v1",
        feature_set_ordinal=0,
        materialization_plan_id=PLAN_ID,
        dataset_version_id=DATASET_VERSION_ID,
        partition_id=PARTITION_ID,
        materialization_output_path=output_path.as_posix(),
        value_record_count=len(rows),
        first_event_ts=min(event_ts),
        last_event_ts=max(event_ts),
        first_available_ts=first_available,
        last_available_ts=last_available,
        registered_at=_dt("2024-01-02T15:00:00+00:00"),
        registry_metadata=registry_metadata
        if registry_metadata is not None
        else {
            "coverage_expectations": {
                "symbols": ["ES"],
                "sessions": ["RTH"],
                "partitions": [PARTITION_ID],
            }
        },
    )


def _feature_spec() -> tuple[FeatureSpec, dict[str, object]]:
    request = create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=["synthetic_close"],
        formula_sketch={
            "exposure_family": "feature_report_fixture",
            "inputs": ["synthetic_close"],
            "operation": "pct_change",
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic fixture available_ts follows event_ts"
        },
        duplicate_or_equivalent_exposure_notes=ExposureCheckResult(
            (),
            ExposureRegistryStatus.EMPTY,
            0,
        ).to_notes(),
        data_requirements={
            "fields": ["synthetic_close"],
            "source": "tiny synthetic fixture fields only",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )
    decision = evaluate_feature_request_gate(request, EmptyRegistryReader())
    assert decision.implementation_allowed is True
    assert decision.feature_request_id is not None
    assert decision.checked_feature_request is not None
    spec = FeatureSpec(
        feature_id="base_ohlcv_feature_report_fixture",
        family=FeatureFamily.BASE_OHLCV,
        feature_request_id=decision.feature_request_id,
        inputs=FeatureInputSpec(
            input_views=("canonical_ohlcv",),
            fields=("synthetic_close", "available_ts"),
            dataset_version_ids=(DATASET_VERSION_ID,),
        ),
        transform=TransformSpec(
            transform_id="pct_change",
            parameters={
                "operation": "pct_change",
                "inputs": ["synthetic_close"],
                "window": 1,
            },
        ),
        window=WindowSpec(
            kind=WindowKind.ROLLING,
            length=1,
            causality=WindowCausality.CAUSAL,
            offline_only=False,
        ),
        normalization=NormalizationSpec(normalization_id="identity"),
        availability_assumptions={
            "timing": "synthetic fixture available_ts follows event_ts"
        },
        available_ts_derivation_rule="feature.available_ts = input available_ts",
        implementation_eligible=True,
        request_gate_decision=decision,
    )
    return spec, decision.checked_feature_request.to_dict()


def _row(
    event_ts: str,
    available_ts: str | object,
    value: object,
    *,
    entity_id: str = "ES",
    quality_flags: tuple[str, ...] = (),
) -> dict[str, object]:
    payload: dict[str, object] = {
        "entity_id": entity_id,
        "event_ts": event_ts,
        "value": value,
        "quality_flags": list(quality_flags),
    }
    if available_ts is not MISSING:
        payload["available_ts"] = available_ts
    return payload


def _write_values(
    path: Path,
    feature_version_id: str,
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "record_type": "feature_materialization_plan",
                "plan": {"plan_id": PLAN_ID},
            },
            sort_keys=True,
        )
    ]
    for row in rows:
        value = dict(row)
        value["feature_version_id"] = feature_version_id
        lines.append(
            json.dumps(
                {
                    "record_type": "feature_value",
                    "plan_id": PLAN_ID,
                    "dataset_version_id": DATASET_VERSION_ID,
                    "partition_id": PARTITION_ID,
                    "value": value,
                },
                sort_keys=True,
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _empty_duplicate_report() -> DuplicateExposureReport:
    return DuplicateExposureReport(
        registry_status=ExposureRegistryStatus.EMPTY,
        registry_entries_checked=0,
        registry_error="",
        equivalent_feature_groups=(),
    )


def _equivalent_exposure_report() -> DuplicateExposureReport:
    return DuplicateExposureReport(
        registry_status=ExposureRegistryStatus.CHECKED,
        registry_entries_checked=1,
        registry_error="",
        equivalent_feature_groups=(
            EquivalentFeatureGroup(
                kind=ExposureFindingKind.EQUIVALENT,
                severity=ExposureFindingSeverity.WARNING,
                matched_registry_reference={"feature_version_id": "fver_existing_fixture"},
                rationale="synthetic fixture equivalent exposure visibility",
            ),
        ),
    )


def _codes(findings: tuple[Any, ...]) -> set[str]:
    return {finding.code for finding in findings}


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
