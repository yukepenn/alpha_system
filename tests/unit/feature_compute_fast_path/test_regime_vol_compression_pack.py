from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    REGIME_VOL_COMPRESSION_FEATURE_IDS,
    PackMaterializer,
    build_fast_feature_pack,
    build_regime_vol_compression_pack,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureDefinition,
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
from alpha_system.features.families.structure import (
    StructureFeatureDefinition,
    StructureFeatureName,
    build_structure_feature_definition,
    compute_structure_feature,
)
from alpha_system.features.input_views import build_ohlcv_input_view
from tests.fixtures.feature_compute_fast_path.regime_vol_compression import (
    DATASET_ID,
    FIRST_SESSION_ZERO_MOVEMENT_INDEX,
    NO_TRADE_INDEX,
    PARTITION_ID,
    RANGE_CONTRACTION_VALID_INDEX,
    SECOND_SESSION_ZERO_MOVEMENT_INDEX,
    SESSION_RESET_INDEX,
    WINDOW_LENGTH,
    regime_vol_compression_rows,
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
    OHLCVFeatureName.ATR,
    OHLCVFeatureName.TRENDINESS,
    StructureFeatureName.RANGE_CONTRACTION,
)
ROLLING_FLOAT_TOLERANCE = FeatureParityTolerance(
    abs=1e-12,
    rel=1e-12,
    reason=(
        "ATR rolling means and trendiness ratios are floating-point reductions; "
        "the Polars expression path may evaluate equivalent terms in a different "
        "binary operation order."
    ),
)


def test_regime_vol_compression_pack_matches_reference_on_synthetic_fixture() -> None:
    pytest.importorskip("polars")
    # P235500 repair provenance: canonical session_label can be static metadata;
    # reset-scoped OHLCV/structure truth comes from bar_start_ts.
    rows = _static_session_rows(regime_vol_compression_rows())
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _regime_pack_contracts()
    reference_view = build_ohlcv_input_view(
        accepted,
        rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_regime_vol_compression_parity",
    )
    reference_records = _reference_records(definitions, reference_view)
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(rows), pack)
    )

    assert (
        tuple(feature.feature_id for feature in pack.feature_set.features)
        == REGIME_VOL_COMPRESSION_FEATURE_IDS
    )
    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == tuple(
        definition.feature_version_id for definition in definitions
    )
    _assert_fixture_coverage(reference_records)
    for definition in definitions:
        tolerance = (
            ROLLING_FLOAT_TOLERANCE
            if definition.feature_id in {"base_ohlcv_atr", "base_ohlcv_trendiness"}
            else FeatureParityTolerance()
        )
        assert_feature_records_match(
            reference_records[definition.feature_id],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
            tolerance=tolerance,
        )


def test_regime_ohlcv_bindings_match_reference_with_session_reset() -> None:
    pytest.importorskip("polars")
    rows = _static_session_rows(regime_vol_compression_rows())
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _regime_ohlcv_binding_contracts()
    reference_view = build_ohlcv_input_view(
        accepted,
        rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_regime_ohlcv_binding_parity",
    )
    reference_records = {
        definition.feature_id: compute_ohlcv_feature(definition, reference_view)
        for definition in definitions
    }
    materializer = PackMaterializer()
    pack = build_regime_vol_compression_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(rows), pack)
    )

    returns = reference_records["base_ohlcv_returns"]
    assert returns[SESSION_RESET_INDEX].quality_flags == (
        "primitive_gap",
        "session_reset",
    )
    for definition in definitions:
        assert_feature_records_match(
            reference_records[definition.feature_id],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
        )


def test_regime_vol_compression_pack_materialization_records_fast_provenance(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    rows = _static_session_rows(regime_vol_compression_rows())
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _regime_pack_contracts()
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
    assert {payload["producer_engine_id"] for payload in payloads} == {
        FAST_PRODUCER_ENGINE_ID
    }
    assert {payload["value_schema_version"] for payload in payloads} == {
        FAST_VALUE_SCHEMA_VERSION
    }


def _regime_pack_contracts() -> tuple[
    tuple[OHLCVFeatureDefinition | StructureFeatureDefinition, ...],
    FeatureSetSpec,
]:
    registry_reader = EmptyRegistryReader()
    atr_request = approved_feature_request("fast_path_regime_vol_compression_atr")
    trendiness_request = approved_feature_request(
        "fast_path_regime_vol_compression_trendiness"
    )
    range_contraction_request = approved_feature_request(
        "fast_path_regime_vol_compression_range_contraction"
    )
    atr_definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.ATR,
        atr_request,
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        window_length=WINDOW_LENGTH,
        reset_on_session=True,
    )
    trendiness_definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.TRENDINESS,
        trendiness_request,
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        window_length=WINDOW_LENGTH,
        reset_on_session=True,
    )
    range_contraction_definition = build_structure_feature_definition(
        StructureFeatureName.RANGE_CONTRACTION,
        range_contraction_request,
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        window_length=WINDOW_LENGTH,
        reset_on_session=True,
    )
    definitions = (
        atr_definition,
        trendiness_definition,
        range_contraction_definition,
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_regime_vol_compression_v1",
        feature_set_version="v1",
        features=(
            atr_definition.spec,
            trendiness_definition.spec,
            range_contraction_definition.spec.feature_spec,
        ),
        description="V1 regime / volatility / compression fast pack parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FCFP-P05"},
    )
    return definitions, feature_set


def _regime_ohlcv_binding_contracts() -> tuple[
    tuple[OHLCVFeatureDefinition, ...],
    FeatureSetSpec,
]:
    registry_reader = EmptyRegistryReader()
    requests = {
        OHLCVFeatureName.RETURNS: approved_feature_request(
            "fast_path_regime_vol_compression_returns"
        ),
        OHLCVFeatureName.ROLLING_RANGE: approved_feature_request(
            "fast_path_regime_vol_compression_rolling_range"
        ),
    }
    definitions = tuple(
        build_ohlcv_feature_definition(
            feature_name,
            requests[feature_name],
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            window_length=WINDOW_LENGTH,
            horizon=1,
            reset_on_session=True,
        )
        for feature_name in (OHLCVFeatureName.RETURNS, OHLCVFeatureName.ROLLING_RANGE)
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_regime_ohlcv_bindings_v1",
        feature_set_version="v1",
        features=tuple(definition.spec for definition in definitions),
        description="V1 regime pack OHLCV binding parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FUTSUB-P14"},
    )
    return definitions, feature_set


def _reference_records(
    definitions: tuple[OHLCVFeatureDefinition | StructureFeatureDefinition, ...],
    reference_view: Any,
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    records: dict[str, tuple[FeatureValueRecord, ...]] = {}
    for definition in definitions:
        if isinstance(definition, OHLCVFeatureDefinition):
            records[definition.feature_id] = compute_ohlcv_feature(definition, reference_view)
        else:
            records[definition.feature_id] = compute_structure_feature(definition, reference_view)
    return records


def _assert_fixture_coverage(
    reference_records: dict[str, tuple[FeatureValueRecord, ...]],
) -> None:
    atr = reference_records["base_ohlcv_atr"]
    trendiness = reference_records["base_ohlcv_trendiness"]
    range_contraction = reference_records["liquidity_structure_range_contraction"]

    assert atr[SESSION_RESET_INDEX].quality_flags == (
        "insufficient_window",
        "primitive_gap",
    )
    assert atr[NO_TRADE_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "primitive_gap",
    )
    assert trendiness[FIRST_SESSION_ZERO_MOVEMENT_INDEX].quality_flags == (
        "ohlcv_gap",
        "zero_movement",
    )
    assert trendiness[NO_TRADE_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "ohlcv_gap",
    )
    assert trendiness[SESSION_RESET_INDEX].quality_flags == (
        "insufficient_window",
        "ohlcv_gap",
    )
    assert trendiness[SECOND_SESSION_ZERO_MOVEMENT_INDEX].quality_flags == (
        "ohlcv_gap",
        "zero_movement",
    )
    assert range_contraction[NO_TRADE_INDEX].quality_flags == (
        "no_trade",
        "structure_gap",
    )
    assert range_contraction[SESSION_RESET_INDEX].quality_flags == (
        "input_gap",
        "insufficient_window",
        "structure_gap",
    )
    assert range_contraction[RANGE_CONTRACTION_VALID_INDEX].value is not None


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}


def _static_session_rows(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple({**row, "session_label": "ETH"} for row in rows)
