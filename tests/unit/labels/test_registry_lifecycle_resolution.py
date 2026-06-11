from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from alpha_system.data.foundation.datasets import DatasetVersion
from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.labels.registry import LabelRegistry, LabelRegistryLifecycleState
from alpha_system.labels.version import LabelContractSpec
from alpha_system.runtime.entry_contract import (
    RuntimeEntryRequest,
    RuntimeEntryStatus,
    evaluate_runtime_entry_request,
)
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    RuntimeInputResolutionResult,
    resolve_runtime_input_pack,
)
from tests.fixtures.feature_label.synthetic import (
    dataset_version_for,
    quality_report_for,
    registered_label_record,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
FEATURE_REQUEST_REF = "freq_eb180e1226ce34c048c7e6eb"
FEATURE_VERSION_ID = "fver_" + "a" * 64
BASE_TS = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)


def test_label_registry_keeps_raw_audit_access_and_registered_active_resolution(
    tmp_path: Path,
) -> None:
    """P151500 closes runtime deprecated-lock access while preserving audit reads."""

    registry = LabelRegistry(tmp_path / "labels.sqlite")
    deprecated, replacement = _registered_label_pair(tmp_path)
    registry._persist_label(deprecated)
    registry._persist_label(replacement)

    deprecation = registry.deprecate_label(
        deprecated.label_version_id,
        reason="P151500 synthetic deprecated lock",
        deprecated_by="P151500 unit test",
        replacement_label_version_id=replacement.label_version_id,
    )

    raw = registry.resolve_label(deprecated.label_version_id)
    assert raw is not None
    assert raw.lifecycle_state is LabelRegistryLifecycleState.DEPRECATED
    by_version = registry.resolve_label_by_version(deprecated.label_version_id)
    assert by_version is not None
    assert by_version.label_version_id == raw.label_version_id
    assert registry.resolve_active_label(deprecated.label_version_id) is None
    assert registry.resolve_registered_label(deprecated.label_version_id) is None
    active_replacement = registry.resolve_registered_label(replacement.label_version_id)
    assert active_replacement is not None
    assert active_replacement.label_version_id == replacement.label_version_id
    assert deprecation.replacement_label_version_id == replacement.label_version_id


def test_runtime_resolver_fails_closed_for_deprecated_label_with_replacement(
    tmp_path: Path,
) -> None:
    registry = LabelRegistry(tmp_path / "labels.sqlite")
    deprecated, replacement = _registered_label_pair(tmp_path)
    registry._persist_label(deprecated)
    registry._persist_label(replacement)
    registry.deprecate_label(
        deprecated.label_version_id,
        reason="P151500 synthetic deprecated lock",
        deprecated_by="P151500 unit test",
        replacement_label_version_id=replacement.label_version_id,
    )

    result = _resolve_label_lock(registry, deprecated.label_contract, deprecated.label_version_id)

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    reason = _only_reason(result)
    assert reason.code == "label_pack_deprecated"
    assert "replacement_label_version_id=" in reason.actual
    assert replacement.label_version_id in reason.actual
    assert registry.resolve_label(deprecated.label_version_id) is not None


def test_runtime_resolver_resolves_registered_label_pack(tmp_path: Path) -> None:
    registry = LabelRegistry(tmp_path / "labels.sqlite")
    record, _replacement = _registered_label_pair(tmp_path)
    registry._persist_label(record)

    result = _resolve_label_lock(registry, record.label_contract, record.label_version_id)

    assert result.status is RuntimeEntryStatus.INPUTS_RESOLVED
    assert result.input_pack is not None
    assert result.input_pack.label_packs[0].label_version_id == record.label_version_id
    assert result.input_pack.label_packs[0].lifecycle_state == "REGISTERED"


def _registered_label_pair(tmp_path: Path) -> tuple[Any, Any]:
    return (
        registered_label_record(tmp_path, dataset_id="dsv_p151500_deprecated_label_v1"),
        registered_label_record(tmp_path, dataset_id="dsv_p151500_replacement_label_v1"),
    )


def _resolve_label_lock(
    registry: LabelRegistry,
    label_contract: LabelContractSpec,
    label_version_id: str,
) -> RuntimeInputResolutionResult:
    dataset_id = label_contract.inputs.dataset_version_ids[0]
    entry_result = evaluate_runtime_entry_request(
        RuntimeEntryRequest(
            alpha_spec_ref=ALPHA_SPEC_REF,
            study_spec_ref=STUDY_SPEC_REF,
            study_input_pack=StudyInputPack(
                feature_request_ids=[FEATURE_REQUEST_REF],
                label_spec_ids=[label_contract.label_spec_id],
                alpha_spec_id=ALPHA_SPEC_REF,
                dataset_scope=_dataset_scope(dataset_id),
            ),
            target_dataset_version_id=dataset_id,
            dataset_scope=_dataset_scope(dataset_id),
            partition_scope={"partition_id": "development_partition"},
            expected_dataset_lifecycle_state="VERSIONED",
            dataset_version_source_family="synthetic",
        )
    )
    assert entry_result.status is RuntimeEntryStatus.INPUTS_RESOLVED

    return resolve_runtime_input_pack(
        entry_result,
        registry_path="/tmp/p151500_synthetic_datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(label_version_id,),
        partition_scope={"partition_id": "development_partition"},
        session_scope={"session": "synthetic_rth"},
        feature_label_resolver=FeatureLabelPackResolver(
            feature_store=_FeatureStore({FEATURE_VERSION_ID: _FeatureRecord(dataset_id)}),
            label_registry=registry,
        ),
        dataset_version_resolver=lambda _path, _id: _dataset_version(dataset_id),
    )


def _dataset_version(dataset_id: str) -> DatasetVersion:
    return dataset_version_for(dataset_id, quality_report=quality_report_for(dataset_id))


def _dataset_scope(dataset_id: str) -> dict[str, object]:
    return {
        "dataset_version_id": dataset_id,
        "source": "tiny synthetic P151500 lifecycle fixture",
    }


def _only_reason(result: RuntimeInputResolutionResult):
    assert len(result.reasons) == 1
    return result.reasons[0]


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    dataset_version_id: str
    feature_version_id: str = FEATURE_VERSION_ID
    feature_request_id: str = FEATURE_REQUEST_REF
    feature_set_id: str = "fset_p151500_lifecycle_fixture"
    feature_set_version: str = "1"
    partition_id: str = "development_partition"
    materialization_plan_id: str = "feature_plan_p151500_lifecycle_fixture"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=1)
    first_available_ts: datetime = BASE_TS
    last_available_ts: datetime = BASE_TS + timedelta(minutes=1)
    lifecycle_state: str = "REGISTERED"


class _FeatureStore:
    def __init__(self, records: dict[str, _FeatureRecord]) -> None:
        self.records = records

    def resolve_feature_by_version(self, feature_version_id: str) -> _FeatureRecord | None:
        return self.records.get(feature_version_id)
