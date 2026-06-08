from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import (
    BASE_OHLCV_FEATURE_IDS,
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    PackMaterializer,
    build_fast_feature_pack,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureDefinition,
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
from alpha_system.features.input_views import build_ohlcv_input_view
from tests.fixtures.feature_compute_fast_path.base_ohlcv import (
    DATASET_ID,
    PARTITION_ID,
    base_ohlcv_pack_rows,
)
from tests.fixtures.feature_label.synthetic import (
    EmptyRegistryReader,
    accepted_version,
    approved_feature_request,
)
from tests.unit.feature_compute_fast_path.parity_harness import (
    FeatureParityTolerance,
    assert_feature_records_match,
)

PACK_FEATURES = (
    OHLCVFeatureName.RETURNS,
    OHLCVFeatureName.LOG_RETURNS,
    OHLCVFeatureName.ROLLING_VOLATILITY,
    OHLCVFeatureName.ROLLING_RANGE,
    OHLCVFeatureName.RANGE_POSITION,
    OHLCVFeatureName.VOLUME_ZSCORE,
)
VOLUME_ZSCORE_TOLERANCE = FeatureParityTolerance(
    abs=5e-8,
    rel=0.0,
    reason=(
        "Polars and the reference primitive may sum rolling variance terms in a "
        "different order; the full-year proof observed max diff around 3.3e-8."
    ),
)
EXPECTED_GAP_COUNTS = {
    OHLCVFeatureName.RETURNS: 3,
    OHLCVFeatureName.LOG_RETURNS: 3,
    OHLCVFeatureName.ROLLING_VOLATILITY: 26,
    OHLCVFeatureName.ROLLING_RANGE: 25,
    OHLCVFeatureName.RANGE_POSITION: 25,
    OHLCVFeatureName.VOLUME_ZSCORE: 25,
}
GAP_FLAGS = frozenset(
    {
        "insufficient_window",
        "input_gap",
        "session_reset",
        "primitive_gap",
        "ohlcv_gap",
        "no_trade",
    }
)


def test_base_ohlcv_pack_matches_reference_on_synthetic_fixture() -> None:
    pytest.importorskip("polars")
    rows = base_ohlcv_pack_rows()
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set, _ = _base_pack_contracts()
    reference_view = build_ohlcv_input_view(
        accepted,
        rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_base_ohlcv_parity",
    )
    reference_records = {
        definition.name: compute_ohlcv_feature(definition, reference_view)
        for definition in definitions
    }
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(rows), pack)
    )

    assert (
        tuple(feature.feature_id for feature in pack.feature_set.features)
        == BASE_OHLCV_FEATURE_IDS
    )
    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == tuple(
        definition.feature_version_id for definition in definitions
    )
    for definition in definitions:
        tolerance = (
            VOLUME_ZSCORE_TOLERANCE
            if definition.name is OHLCVFeatureName.VOLUME_ZSCORE
            else FeatureParityTolerance()
        )
        assert _gap_count(reference_records[definition.name]) == EXPECTED_GAP_COUNTS[
            definition.name
        ]
        assert_feature_records_match(
            reference_records[definition.name],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
            tolerance=tolerance,
        )


def test_base_ohlcv_pack_materialization_records_fast_provenance(tmp_path: Path) -> None:
    pytest.importorskip("polars")
    rows = base_ohlcv_pack_rows()
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set, _ = _base_pack_contracts()
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    result = materializer.materialize_pack(
        pack,
        accepted,
        partition_id=PARTITION_ID,
        canonical_frame=materializer.frame_from_rows(rows),
        alpha_data_root=tmp_path,
        value_store_format=ValueStoreFormat.DUAL,
    )

    assert result.value_store_handle is not None
    assert result.value_store_handle.schema_version == FAST_VALUE_SCHEMA_VERSION
    assert Path(result.value_store_handle.jsonl_path or "").exists()
    assert Path(result.value_store_handle.parquet_path or "").exists()
    assert result.value_store_handle.format is ValueStoreFormat.DUAL
    assert {record.feature_version_id for record in result.records} == {
        definition.feature_version_id for definition in definitions
    }
    payloads = [
        json.loads(line)
        for line in Path(result.value_store_handle.jsonl_path or "").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert {payload["record_type"] for payload in payloads} == {
        "fast_feature_materialization_plan",
        "fast_feature_value",
    }
    assert {
        payload["producer_engine_id"]
        for payload in payloads
    } == {FAST_PRODUCER_ENGINE_ID}
    assert {
        payload["value_schema_version"]
        for payload in payloads
    } == {FAST_VALUE_SCHEMA_VERSION}


def _base_pack_contracts() -> tuple[
    tuple[OHLCVFeatureDefinition, ...],
    FeatureSetSpec,
    dict[str, object],
]:
    registry_reader = EmptyRegistryReader()
    requests = {
        feature_name: approved_feature_request(f"fast_path_base_ohlcv_{feature_name.value}")
        for feature_name in PACK_FEATURES
    }
    definitions = tuple(
        build_ohlcv_feature_definition(
            feature_name,
            requests[feature_name],
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            window_length=20,
            horizon=1,
            reset_on_session=False,
            ddof=0,
        )
        for feature_name in PACK_FEATURES
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_base_ohlcv_v1",
        feature_set_version="v1",
        features=tuple(definition.spec for definition in definitions),
        description="V1 Base OHLCV fast pack parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FCFP-P02"},
    )
    feature_requests = {
        definition.spec.feature_id: (
            definition.request_gate_decision.checked_feature_request or requests[definition.name]
        )
        for definition in definitions
    }
    return definitions, feature_set, feature_requests


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}


def _gap_count(records: tuple[FeatureValueRecord, ...]) -> int:
    return sum(
        1
        for record in records
        if record.value is None or bool(GAP_FLAGS.intersection(record.quality_flags))
    )
