from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any

from alpha_system.data.foundation.datasets import DatasetVersion
from alpha_system.governance.study_input_pack import StudyInputPack
from alpha_system.runtime.entry_contract import (
    RuntimeEntryRequest,
    RuntimeEntryStatus,
    evaluate_runtime_entry_request,
)
from alpha_system.runtime.input_resolver import (
    FeatureLabelPackResolver,
    resolve_runtime_input_pack,
)

ALPHA_SPEC_REF = "aspec_af848bc999a4c4b11a421bd0"
STUDY_SPEC_REF = "sspec_438ceffd40855205de5497f0"
FEATURE_REQUEST_REF = "freq_eb180e1226ce34c048c7e6eb"
LABEL_SPEC_REF = "lspec_8663589ca7a9f1e5859289c7"
DATASET_VERSION_ID = "dsv_synthetic_feature_label_fixture_v1"
FEATURE_VERSION_ID = "fver_" + "c" * 64
LABEL_VERSION_ID = "lver_" + "d" * 64
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
PARTITION_SCOPE = {"partition_id": "development_partition"}
SESSION_SCOPE = {"session": "rth_and_eth"}


def test_feature_available_ts_must_not_precede_feature_event_ts() -> None:
    feature = replace(_feature_record(), first_available_ts=BASE_TS - timedelta(minutes=1))

    result = _resolve(feature_record=feature)

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "feature_available_ts_precedes_event_ts" in _reason_codes(result)


def test_label_available_ts_must_not_precede_label_event_ts() -> None:
    label = replace(_label_record(), first_label_available_ts=BASE_TS - timedelta(minutes=1))

    result = _resolve(label_record=label)

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "label_available_ts_precedes_event_ts" in _reason_codes(result)


def test_missing_feature_or_label_availability_timestamp_blocks() -> None:
    feature = replace(_feature_record(), first_available_ts=None)
    label = replace(_label_record(), first_label_available_ts=None)

    feature_result = _resolve(feature_record=feature)
    label_result = _resolve(label_record=label)

    assert feature_result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert label_result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "feature_available_ts_missing" in _reason_codes(feature_result)
    assert "label_available_ts_missing" in _reason_codes(label_result)


def test_label_version_ref_cannot_be_exposed_as_live_feature_input() -> None:
    result = resolve_runtime_input_pack(
        _entry_result(),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        feature_pack_refs=(LABEL_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=PARTITION_SCOPE,
        session_scope=SESSION_SCOPE,
        feature_label_resolver=_resolver(),
        dataset_version_resolver=lambda _path, _id: _dataset_version(),
    )

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "label_as_feature_input" in _reason_codes(result)


def test_live_feature_contract_cannot_reference_label_fields() -> None:
    feature = replace(
        _feature_record(),
        feature_spec=_FeatureSpec(inputs=_Inputs(fields=("close", "label_value"))),
    )

    result = _resolve(feature_record=feature)

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "label_as_feature_input" in _reason_codes(result)


def _resolve(
    *,
    feature_record: Any | None = None,
    label_record: Any | None = None,
) -> Any:
    return resolve_runtime_input_pack(
        _entry_result(),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=PARTITION_SCOPE,
        session_scope=SESSION_SCOPE,
        feature_label_resolver=FeatureLabelPackResolver(
            feature_store=_FeatureStore({FEATURE_VERSION_ID: feature_record or _feature_record()}),
            label_registry=_LabelRegistry({LABEL_VERSION_ID: label_record or _label_record()}),
        ),
        dataset_version_resolver=lambda _path, _id: _dataset_version(),
    )


def _entry_result() -> Any:
    dataset_scope = {
        "instrument_universe": "synthetic fixture universe only",
        "source": "synthetic fixture metadata, not market data",
    }
    result = evaluate_runtime_entry_request(
        RuntimeEntryRequest(
            alpha_spec_ref=ALPHA_SPEC_REF,
            study_spec_ref=STUDY_SPEC_REF,
            study_input_pack=StudyInputPack(
                feature_request_ids=[FEATURE_REQUEST_REF],
                label_spec_ids=[LABEL_SPEC_REF],
                alpha_spec_id=ALPHA_SPEC_REF,
                dataset_scope=dataset_scope,
            ),
            target_dataset_version_id=DATASET_VERSION_ID,
            dataset_scope=dataset_scope,
            partition_scope=PARTITION_SCOPE,
            expected_dataset_lifecycle_state="VERSIONED",
            dataset_version_source_family="databento",
        )
    )
    assert result.resolved
    return result


def _dataset_version() -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=DATASET_VERSION_ID,
        source="databento",
        symbol_universe=("ES",),
        bar_size="1m",
        what_to_show="TRADES",
        start_ts=datetime(2018, 1, 1, tzinfo=UTC),
        end_ts=datetime(2026, 1, 31, tzinfo=UTC),
        contract_universe=("ESM6",),
        roll_policy_id="synthetic_roll_policy_v1",
        manifest_hash="0" * 64,
        code_hash="1" * 64,
        config_hash="2" * 64,
        quality_report_hash="3" * 64,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


@dataclass(frozen=True, slots=True)
class _Inputs:
    fields: tuple[str, ...] = ("close", "volume")
    input_views: tuple[str, ...] = ("canonical_ohlcv",)


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    feature_request_id: str = FEATURE_REQUEST_REF
    live: bool = True
    inputs: _Inputs = _Inputs()


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_version_id: str = FEATURE_VERSION_ID
    feature_request_id: str = FEATURE_REQUEST_REF
    feature_set_id: str = "fset_synthetic_runtime"
    feature_set_version: str = "1"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = "development_partition"
    materialization_plan_id: str = "feature_plan_synthetic"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=2)
    first_available_ts: datetime | None = BASE_TS
    last_available_ts: datetime | None = BASE_TS + timedelta(minutes=2)
    lifecycle_state: str = "REGISTERED"
    feature_spec: _FeatureSpec = _FeatureSpec()


@dataclass(frozen=True, slots=True)
class _LabelRecord:
    label_version_id: str = LABEL_VERSION_ID
    label_spec_id: str = LABEL_SPEC_REF
    label_id: str = "forward_return_5m"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = "development_partition"
    materialization_plan_id: str = "label_plan_synthetic"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=2)
    first_label_available_ts: datetime | None = BASE_TS + timedelta(minutes=5)
    last_label_available_ts: datetime | None = BASE_TS + timedelta(minutes=7)
    lifecycle_state: str = "REGISTERED"


class _FeatureStore:
    def __init__(self, records: dict[str, _FeatureRecord]) -> None:
        self.records = records

    def resolve_feature_by_version(self, feature_version_id: str) -> _FeatureRecord | None:
        return self.records.get(feature_version_id)


class _LabelRegistry:
    def __init__(self, records: dict[str, _LabelRecord]) -> None:
        self.records = records

    def resolve_label_by_version(self, label_version_id: str) -> _LabelRecord | None:
        return self.records.get(label_version_id)


def _feature_record() -> _FeatureRecord:
    return _FeatureRecord()


def _label_record() -> _LabelRecord:
    return _LabelRecord()


def _resolver() -> FeatureLabelPackResolver:
    return FeatureLabelPackResolver(
        feature_store=_FeatureStore({FEATURE_VERSION_ID: _feature_record()}),
        label_registry=_LabelRegistry({LABEL_VERSION_ID: _label_record()}),
    )


def _reason_codes(result: Any) -> set[str]:
    return {reason.code for reason in result.reasons}
