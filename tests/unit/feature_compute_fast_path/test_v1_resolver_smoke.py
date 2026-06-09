from __future__ import annotations

from pathlib import Path

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.fast import PackMaterializer, build_fast_feature_pack
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
)
from alpha_system.features.store import FeatureStore
from alpha_system.governance.feature_lock_validation import (
    FeatureLockValidationError,
    validate_feature_locks,
)
from alpha_system.labels.fast import FastLabelMaterializer, build_fixed_horizon_label_pack
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
)
from alpha_system.labels.registry import LabelRegistry
from alpha_system.runtime.entry_contract import RuntimeEntryStatus
from tests.unit.futures_substrate_scaleout.test_keystone_identity import (
    _accepted_version,
    _approved_request,
    _bar_rows,
    _fixed_label_spec,
    _reason_codes,
    _resolve_runtime,
)


DATASET_ID = "dsv_synthetic_v1_resolver_smoke"
PARTITION_ID = "development_partition"


class _EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_v1_feature_and_label_outputs_resolve_and_stale_locks_fail_closed(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    accepted = _accepted_version(DATASET_ID)
    rows = _bar_rows(DATASET_ID, length=4)

    feature_definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        _approved_request(OHLCVFeatureName.RETURNS),
        _EmptyRegistryReader(),
        dataset_version_ids=(DATASET_ID,),
        reset_on_session=False,
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_v1_resolver_smoke",
        feature_set_version="v1",
        features=(feature_definition.spec,),
    )
    feature_materializer = PackMaterializer()
    feature_store = FeatureStore.from_alpha_data_root(tmp_path)
    feature_pack = build_fast_feature_pack(feature_set)
    feature_result = feature_materializer.materialize_pack(
        feature_pack,
        accepted,
        partition_id=PARTITION_ID,
        canonical_frame=feature_materializer.frame_from_rows(rows),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    feature_record = feature_materializer.register_pack(
        feature_result,
        feature_pack,
        feature_requests={
            feature_definition.spec.feature_id: (
                feature_definition.request_gate_decision.checked_feature_request
            )
        },
        store=feature_store,
    )[0]

    label_definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_1M,
        _fixed_label_spec(),
        dataset_version_ids=(DATASET_ID,),
    )
    label_pack = build_fixed_horizon_label_pack((label_definition,))
    label_materializer = FastLabelMaterializer()
    label_registry = LabelRegistry.from_alpha_data_root(tmp_path)
    price_frame = label_materializer.frame_from_rows(ohlcv_rows=rows, bbo_rows=())
    label_result = label_materializer.materialize_pack(
        label_pack,
        accepted,
        partition_id=PARTITION_ID,
        price_frame=price_frame,
        instrument_ids=("ES",),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.PARQUET,
    )
    label_record = label_materializer.register_pack(
        label_result,
        label_pack,
        store=label_registry,
    )[0]

    assert feature_record.producer_engine_id == (
        "alpha_system.features.fast.pack_materializer.v1"
    )
    assert label_record.registry_metadata.to_dict()["producer_engine_id"] == (
        "alpha_system.labels.fast.pack_materializer.v1"
    )

    resolved = _resolve_runtime(
        feature_record.feature_version_id,
        label_record.label_version_id,
        dataset_version=accepted.dataset_version,
        feature_store=feature_store,
        label_registry=label_registry,
        expected_feature_request_id=feature_record.feature_request_id,
        expected_label_spec_id=label_record.label_spec_id,
    )
    assert resolved.status is RuntimeEntryStatus.INPUTS_RESOLVED
    assert resolved.input_pack is not None
    assert resolved.input_pack.feature_packs[0].feature_version_id == (
        feature_record.feature_version_id
    )
    assert resolved.input_pack.label_packs[0].label_version_id == label_record.label_version_id

    stale_feature_id = "fver_" + "f" * 64
    with pytest.raises(FeatureLockValidationError, match="stale feature-pack lock"):
        validate_feature_locks(
            ({"feature_version_id": stale_feature_id},),
            registry_path=feature_store.registry.registry_path,
        )
    stale_feature = _resolve_runtime(
        stale_feature_id,
        label_record.label_version_id,
        dataset_version=accepted.dataset_version,
        feature_store=feature_store,
        label_registry=label_registry,
        expected_feature_request_id=feature_record.feature_request_id,
        expected_label_spec_id=label_record.label_spec_id,
    )
    assert stale_feature.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "feature_pack_not_found" in _reason_codes(stale_feature)

    fuzzy_label = _resolve_runtime(
        feature_record.feature_version_id,
        "fwd_ret_1m",
        dataset_version=accepted.dataset_version,
        feature_store=feature_store,
        label_registry=label_registry,
        expected_feature_request_id=feature_record.feature_request_id,
        expected_label_spec_id=label_record.label_spec_id,
    )
    assert fuzzy_label.status is RuntimeEntryStatus.INPUTS_BLOCKED
    assert "invalid_label_pack_ref" in _reason_codes(fuzzy_label)
