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
FEATURE_VERSION_ID = "fver_" + "a" * 64
LABEL_VERSION_ID = "lver_" + "b" * 64
DATASET_SCOPE = {
    "instrument_universe": "SYNTH_US_EQUITY_LARGE_CAP fixture universe only",
    "source": "tiny synthetic governance fixture metadata, not real market data",
    "time_range": "2026-01-01 through 2026-01-31 synthetic timestamps",
}
PARTITION_SCOPE = {"partition_id": "development_partition"}
SESSION_SCOPE = {"session": "rth_and_eth"}
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def test_resolves_value_free_runtime_input_pack_through_sanctioned_resolver() -> None:
    entry_result = _entry_result()
    feature_store = _FeatureStore({_feature_record().feature_version_id: _feature_record()})
    label_registry = _LabelRegistry({_label_record().label_version_id: _label_record()})
    calls: list[tuple[object, object]] = []

    def resolver(registry_path: object, dataset_version_id: object) -> DatasetVersion:
        calls.append((registry_path, dataset_version_id))
        return _dataset_version()

    result = resolve_runtime_input_pack(
        entry_result,
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=PARTITION_SCOPE,
        session_scope=SESSION_SCOPE,
        feature_label_resolver=FeatureLabelPackResolver(
            feature_store=feature_store,
            label_registry=label_registry,
        ),
        dataset_version_resolver=resolver,
    )

    assert result.status is RuntimeEntryStatus.INPUTS_RESOLVED
    assert result.input_pack is not None
    assert calls == [("/tmp/alpha_registry/datasets.sqlite", DATASET_VERSION_ID)]
    assert feature_store.calls == [FEATURE_VERSION_ID]
    assert label_registry.calls == [LABEL_VERSION_ID]
    assert hash(result.input_pack)

    payload = result.input_pack.to_dict()
    assert payload["value_free"] is True
    assert payload["dataset_version"]["dataset_version_id"] == DATASET_VERSION_ID
    assert payload["canonical_input_views"][0]["record_type"].endswith("CanonicalBarRecord")
    assert payload["feature_packs"][0]["available_ts"]["first"] == BASE_TS.isoformat()
    assert (
        payload["label_packs"][0]["label_available_ts"]["first"]
        == (BASE_TS + timedelta(minutes=5)).isoformat()
    )
    assert "materialization_output_path" not in str(payload)
    assert "label_value" not in str(payload)


def test_refuses_blocked_entry_result_without_touching_registry_or_stores() -> None:
    blocked_entry = evaluate_runtime_entry_request(
        replace(_entry_request(), raw_provider_source="databento")
    )
    calls: list[object] = []

    def resolver(registry_path: object, dataset_version_id: object) -> None:
        calls.append((registry_path, dataset_version_id))
        return None

    result = resolve_runtime_input_pack(
        blocked_entry,
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        partition_scope=PARTITION_SCOPE,
        session_scope=SESSION_SCOPE,
        dataset_version_resolver=resolver,
    )

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "runtime_entry_blocked" in _reason_codes(result)
    assert calls == []


def test_missing_dataset_version_blocks_resolution() -> None:
    result = resolve_runtime_input_pack(
        _entry_result(),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=PARTITION_SCOPE,
        session_scope=SESSION_SCOPE,
        feature_label_resolver=_resolver(),
        dataset_version_resolver=lambda _path, _id: None,
    )

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "dataset_version_not_found" in _reason_codes(result)


def test_inadmissible_dataset_lifecycle_state_blocks_resolution() -> None:
    result = resolve_runtime_input_pack(
        _entry_result(),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="DRAFT",
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=PARTITION_SCOPE,
        session_scope=SESSION_SCOPE,
        feature_label_resolver=_resolver(),
        dataset_version_resolver=lambda _path, _id: _dataset_version(),
    )

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "inadmissible_dataset_lifecycle_state" in _reason_codes(result)


def test_raw_provider_or_provider_reader_metadata_blocks_resolution() -> None:
    result = resolve_runtime_input_pack(
        _entry_result(),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        feature_pack_refs=("raw/databento/es.dbn.zst",),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=PARTITION_SCOPE,
        session_scope={"provider_reader_import": "alpha_system.data.databento.client"},
        feature_label_resolver=_resolver(),
        dataset_version_resolver=lambda _path, _id: _dataset_version(),
    )

    codes = _reason_codes(result)
    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "raw_provider_file_requested" in codes
    assert "provider_metadata_requested" in codes


def test_pack_dataset_mismatch_blocks_databento_ibkr_merge_path() -> None:
    ibkr_feature = replace(_feature_record(), dataset_version_id="dsv_ibkr_recent_fixture_v1")

    result = resolve_runtime_input_pack(
        _entry_result(),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="READY_FOR_RESEARCH",
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=PARTITION_SCOPE,
        session_scope=SESSION_SCOPE,
        feature_label_resolver=FeatureLabelPackResolver(
            feature_store=_FeatureStore({FEATURE_VERSION_ID: ibkr_feature}),
            label_registry=_LabelRegistry({LABEL_VERSION_ID: _label_record()}),
        ),
        dataset_version_resolver=lambda _path, _id: _dataset_version(source="databento"),
    )

    assert result.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "feature_pack_dataset_version_mismatch" in _reason_codes(result)


def test_locked_partition_requires_metadata_and_refuses_selection() -> None:
    locked_scope = {"partition_id": "locked_test_candidate"}

    missing_metadata = resolve_runtime_input_pack(
        _entry_result(),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=locked_scope,
        session_scope=SESSION_SCOPE,
        feature_label_resolver=_resolver(),
        dataset_version_resolver=lambda _path, _id: _dataset_version(),
    )

    assert missing_metadata.status is RuntimeEntryStatus.INPUTS_INCONCLUSIVE
    assert "locked_partition_governance_metadata_missing" in _reason_codes(missing_metadata)

    selection = resolve_runtime_input_pack(
        _entry_result(),
        registry_path="/tmp/alpha_registry/datasets.sqlite",
        dataset_lifecycle_state="VERSIONED",
        feature_pack_refs=(FEATURE_VERSION_ID,),
        label_pack_refs=(LABEL_VERSION_ID,),
        partition_scope=locked_scope,
        session_scope=SESSION_SCOPE,
        governance_metadata={
            "contamination_review_id": "synthetic_review_001",
            "rationale": "fixture metadata only",
        },
        partition_purpose="locked_test_selection",
        feature_label_resolver=_resolver(),
        dataset_version_resolver=lambda _path, _id: _dataset_version(),
    )

    assert selection.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "locked_test_selection_forbidden" in _reason_codes(selection)


def _entry_result() -> Any:
    result = evaluate_runtime_entry_request(_entry_request())
    assert result.resolved
    return result


def _entry_request() -> RuntimeEntryRequest:
    return RuntimeEntryRequest(
        alpha_spec_ref=ALPHA_SPEC_REF,
        study_spec_ref=STUDY_SPEC_REF,
        study_input_pack=StudyInputPack(
            feature_request_ids=[FEATURE_REQUEST_REF],
            label_spec_ids=[LABEL_SPEC_REF],
            alpha_spec_id=ALPHA_SPEC_REF,
            dataset_scope=DATASET_SCOPE,
        ),
        target_dataset_version_id=DATASET_VERSION_ID,
        dataset_scope=DATASET_SCOPE,
        partition_scope=PARTITION_SCOPE,
        expected_dataset_lifecycle_state="VERSIONED",
        dataset_version_source_family="databento",
    )


def _resolver() -> FeatureLabelPackResolver:
    return FeatureLabelPackResolver(
        feature_store=_FeatureStore({FEATURE_VERSION_ID: _feature_record()}),
        label_registry=_LabelRegistry({LABEL_VERSION_ID: _label_record()}),
    )


def _dataset_version(source: str = "databento") -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=DATASET_VERSION_ID,
        source=source,
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
    first_available_ts: datetime = BASE_TS
    last_available_ts: datetime = BASE_TS + timedelta(minutes=2)
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
    first_label_available_ts: datetime = BASE_TS + timedelta(minutes=5)
    last_label_available_ts: datetime = BASE_TS + timedelta(minutes=7)
    lifecycle_state: str = "READY_FOR_STUDY"


class _FeatureStore:
    def __init__(self, records: dict[str, _FeatureRecord]) -> None:
        self.records = records
        self.calls: list[str] = []

    def resolve_feature_by_version(self, feature_version_id: str) -> _FeatureRecord | None:
        self.calls.append(feature_version_id)
        return self.records.get(feature_version_id)


class _LabelRegistry:
    def __init__(self, records: dict[str, _LabelRecord]) -> None:
        self.records = records
        self.calls: list[str] = []

    def resolve_label_by_version(self, label_version_id: str) -> _LabelRecord | None:
        self.calls.append(label_version_id)
        return self.records.get(label_version_id)


def _feature_record() -> _FeatureRecord:
    return _FeatureRecord()


def _label_record() -> _LabelRecord:
    return _LabelRecord()


def _reason_codes(result: Any) -> set[str]:
    return {reason.code for reason in result.reasons}
