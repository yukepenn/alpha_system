from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from alpha_system.data.foundation.datasets import DatasetVersion
from alpha_system.runtime.input_resolver import FeatureLabelPackResolver
from alpha_system.runtime.smoke import (
    RuntimeSmokeStatus,
    SmokeConfig,
    run_real_dataset_version_smoke,
)

DATASET_VERSION_ID = "dsv_rt_p21_local_fixture_v1"
FEATURE_VERSION_ID = "fver_" + "a" * 64
LABEL_VERSION_ID = "lver_" + "b" * 64
FEATURE_REQUEST_ID = "freq_" + "1" * 24
LABEL_SPEC_ID = "lspec_" + "2" * 24
BASE_TS = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)


def test_smoke_is_pass_with_warnings_when_local_data_root_absent() -> None:
    result = run_real_dataset_version_smoke(SmokeConfig(alpha_data_root=None))
    payload = result.to_dict()

    assert result.status is RuntimeSmokeStatus.PASS_WITH_WARNINGS
    assert payload["real_dataset_version_smoke_ran"] is False
    assert payload["warning_reason"] == "ALPHA_DATA_ROOT is not set"
    assert payload["external_provider_call"] is False
    assert payload["raw_file_read"] is False
    assert payload["emitted_paths"] == []


def test_smoke_resolves_dataset_version_and_builds_value_free_runtime_summary(
    tmp_path: Path,
) -> None:
    root = _local_root(tmp_path)
    resolver_calls: list[tuple[Path, object]] = []

    def dataset_resolver(registry_path: str | Path, dataset_version_id: object) -> DatasetVersion:
        resolver_calls.append((Path(registry_path), dataset_version_id))
        return _dataset_version()

    result = run_real_dataset_version_smoke(
        SmokeConfig(
            alpha_data_root=root,
            dataset_version_id=DATASET_VERSION_ID,
            feature_pack_refs=(FEATURE_VERSION_ID,),
            label_pack_refs=(LABEL_VERSION_ID,),
            feature_request_ids=(FEATURE_REQUEST_ID,),
            label_spec_ids=(LABEL_SPEC_ID,),
            partition_scope={"partition_id": "development_partition"},
        ),
        dataset_version_resolver=dataset_resolver,
        feature_label_resolver=_resolver(),
    )
    payload = result.to_dict()

    assert result.status is RuntimeSmokeStatus.PASS
    assert payload["real_dataset_version_smoke_ran"] is True
    assert resolver_calls
    assert resolver_calls[0][1] == DATASET_VERSION_ID
    assert payload["input_resolution_status"] == "INPUTS_RESOLVED"
    assert payload["diagnostics_statuses"]["no_lookahead_audit"] == "POINT_IN_TIME_SAFE"
    assert "double_cost" in payload["cost_profiles"]
    assert payload["evidence_draft_ref"]["descriptive_only"] is True
    assert payload["evidence_draft_ref"]["not_a_candidate"] is True
    assert payload["evidence_draft_ref"]["not_reference_truth"] is True
    assert payload["tool_result"]["status"] == "EVIDENCE_DRAFT_READY"
    assert payload["run_summary"]["next_required_gate"] == "fresh_yellow_lane_review_before_merge"

    serialized = json.dumps(payload, sort_keys=True)
    assert ".dbn" not in serialized
    assert ".zst" not in serialized
    assert ".parquet" not in serialized
    assert ".arrow" not in serialized
    assert ".feather" not in serialized
    assert "data/raw/" not in serialized
    assert "artifacts/" not in serialized


def test_smoke_module_has_no_provider_import_or_raw_file_reader() -> None:
    source = Path("src/alpha_system/runtime/smoke.py").read_text(encoding="utf-8")

    assert "alpha_system.data.databento" not in source
    assert "alpha_system.data.ibkr" not in source
    assert ".dbn" not in source
    assert ".zst" not in source
    assert ".parquet" not in source
    assert ".arrow" not in source
    assert ".feather" not in source


def _local_root(tmp_path: Path) -> Path:
    root = tmp_path / "alpha-data"
    registry = root / "registry"
    registry.mkdir(parents=True)
    for name in ("datasets.sqlite", "features.sqlite", "labels.sqlite"):
        (registry / name).touch()
    return root


def _dataset_version() -> DatasetVersion:
    return DatasetVersion(
        dataset_version_id=DATASET_VERSION_ID,
        source="databento",
        symbol_universe=("ES",),
        bar_size="1m",
        what_to_show="TRADES",
        start_ts=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        end_ts=datetime(2026, 1, 2, 15, 30, tzinfo=UTC),
        contract_universe=("ESH6",),
        roll_policy_id="rt_p21_smoke_roll_policy",
        manifest_hash="0" * 64,
        code_hash="1" * 64,
        config_hash="2" * 64,
        quality_report_hash="3" * 64,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )


@dataclass(frozen=True, slots=True)
class _Inputs:
    fields: tuple[str, ...] = ("close", "volume")
    input_views: tuple[str, ...] = ("canonical_ohlcv",)


@dataclass(frozen=True, slots=True)
class _FeatureSpec:
    feature_request_id: str = FEATURE_REQUEST_ID
    live: bool = True
    inputs: _Inputs = _Inputs()


@dataclass(frozen=True, slots=True)
class _FeatureRecord:
    feature_version_id: str = FEATURE_VERSION_ID
    feature_request_id: str = FEATURE_REQUEST_ID
    feature_set_id: str = "fset_rt_p21_smoke"
    feature_set_version: str = "1"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = "development_partition"
    materialization_plan_id: str = "rt_p21_feature_plan"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=4)
    first_available_ts: datetime = BASE_TS + timedelta(seconds=1)
    last_available_ts: datetime = BASE_TS + timedelta(minutes=4, seconds=1)
    lifecycle_state: str = "REGISTERED"
    feature_spec: _FeatureSpec = _FeatureSpec()


@dataclass(frozen=True, slots=True)
class _LabelRecord:
    label_version_id: str = LABEL_VERSION_ID
    label_spec_id: str = LABEL_SPEC_ID
    label_id: str = "rt_p21_forward_return_5m"
    dataset_version_id: str = DATASET_VERSION_ID
    partition_id: str = "development_partition"
    materialization_plan_id: str = "rt_p21_label_plan"
    first_event_ts: datetime = BASE_TS
    last_event_ts: datetime = BASE_TS + timedelta(minutes=4)
    first_label_available_ts: datetime = BASE_TS + timedelta(minutes=5)
    last_label_available_ts: datetime = BASE_TS + timedelta(minutes=10)
    lifecycle_state: str = "READY_FOR_STUDY"


class _FeatureStore:
    def resolve_feature_by_version(self, feature_version_id: str) -> _FeatureRecord | None:
        if feature_version_id == FEATURE_VERSION_ID:
            return _FeatureRecord()
        return None


class _LabelRegistry:
    def resolve_label_by_version(self, label_version_id: str) -> _LabelRecord | None:
        if label_version_id == LABEL_VERSION_ID:
            return _LabelRecord()
        return None


def _resolver() -> FeatureLabelPackResolver:
    return FeatureLabelPackResolver(
        feature_store=_FeatureStore(),
        label_registry=_LabelRegistry(),
    )
