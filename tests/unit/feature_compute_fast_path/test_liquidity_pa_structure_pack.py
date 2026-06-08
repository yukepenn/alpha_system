from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    LIQUIDITY_PA_STRUCTURE_FEATURE_IDS,
    PackMaterializer,
    build_fast_feature_pack,
)
from alpha_system.features.families.structure import (
    StructureFeatureDefinition,
    StructureFeatureName,
    build_structure_feature_definition,
    compute_structure_feature,
)
from alpha_system.features.input_views import build_ohlcv_input_view
from tests.fixtures.feature_compute_fast_path.liquidity_pa_structure import (
    DATASET_ID,
    HIGH_SWEEP_INDEX,
    LOW_SWEEP_INDEX,
    NO_TRADE_INDEX,
    OPENING_RANGE_FROZEN_INDEX,
    OPENING_RANGE_MINUTES,
    OUTSIDE_OPENING_SESSION_INDEX,
    PARTITION_ID,
    PRIOR_GAP_INDEX,
    RANGE_CONTRACTION_VALID_INDEX,
    SESSION_RESET_INDEX,
    WINDOW_LENGTH,
    ZERO_RANGE_INDEX,
    liquidity_pa_structure_rows,
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

PACK_FEATURES = tuple(StructureFeatureName)
RATIO_TOLERANCE = FeatureParityTolerance(
    abs=1e-12,
    rel=1e-12,
    reason=(
        "Structure ratio features divide finite OHLC ranges; Polars and the "
        "reference can produce equivalent binary floating-point results with "
        "minor rounding differences."
    ),
)


def test_liquidity_pa_structure_pack_matches_reference_on_synthetic_fixture() -> None:
    pytest.importorskip("polars")
    rows = liquidity_pa_structure_rows()
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _structure_pack_contracts()
    reference_view = build_ohlcv_input_view(
        accepted,
        rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_liquidity_pa_structure_parity",
    )
    reference_records = {
        definition.name: compute_structure_feature(definition, reference_view)
        for definition in definitions
    }
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(rows), pack)
    )

    assert (
        tuple(feature.feature_id for feature in pack.feature_set.features)
        == LIQUIDITY_PA_STRUCTURE_FEATURE_IDS
    )
    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == tuple(
        definition.feature_version_id for definition in definitions
    )
    _assert_fixture_coverage(reference_records)
    for definition in definitions:
        tolerance = (
            RATIO_TOLERANCE
            if definition.name
            in {
                StructureFeatureName.CLOSE_LOCATION_VALUE,
                StructureFeatureName.WICK_REJECTION_SCORE,
                StructureFeatureName.RANGE_CONTRACTION,
            }
            else FeatureParityTolerance()
        )
        assert_feature_records_match(
            reference_records[definition.name],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
            tolerance=tolerance,
        )


def test_liquidity_pa_structure_pack_materialization_records_fast_provenance(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    rows = liquidity_pa_structure_rows()
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _structure_pack_contracts()
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


def _structure_pack_contracts() -> tuple[tuple[StructureFeatureDefinition, ...], FeatureSetSpec]:
    registry_reader = EmptyRegistryReader()
    requests = {
        feature_name: approved_feature_request(
            f"fast_path_liquidity_pa_structure_{feature_name.value}"
        )
        for feature_name in PACK_FEATURES
    }
    definitions = tuple(
        build_structure_feature_definition(
            feature_name,
            requests[feature_name],
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            window_length=WINDOW_LENGTH,
            opening_range_minutes=OPENING_RANGE_MINUTES,
            opening_session_label="RTH",
            reset_on_session=True,
        )
        for feature_name in PACK_FEATURES
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_liquidity_pa_structure_v1",
        feature_set_version="v1",
        features=tuple(definition.spec.feature_spec for definition in definitions),
        description="V1 liquidity sweep / PA-structure fast pack parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FCFP-P06"},
    )
    return definitions, feature_set


def _assert_fixture_coverage(
    reference_records: dict[StructureFeatureName, tuple[FeatureValueRecord, ...]],
) -> None:
    prior_high = reference_records[StructureFeatureName.PRIOR_HIGH_DISTANCE]
    opening_high = reference_records[StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE]
    opening_low = reference_records[StructureFeatureName.OPENING_RANGE_LOW_DISTANCE]
    sweep_high = reference_records[StructureFeatureName.SWEEP_HIGH_FLAG]
    sweep_low = reference_records[StructureFeatureName.SWEEP_LOW_FLAG]
    failed_high = reference_records[StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG]
    failed_low = reference_records[StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG]
    close_location = reference_records[StructureFeatureName.CLOSE_LOCATION_VALUE]
    wick = reference_records[StructureFeatureName.WICK_REJECTION_SCORE]
    range_contraction = reference_records[StructureFeatureName.RANGE_CONTRACTION]

    assert prior_high[0].quality_flags == (
        "input_gap",
        "insufficient_window",
        "structure_gap",
    )
    assert prior_high[NO_TRADE_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "structure_gap",
    )
    assert prior_high[PRIOR_GAP_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "structure_gap",
    )
    assert prior_high[SESSION_RESET_INDEX].quality_flags == (
        "input_gap",
        "insufficient_window",
        "structure_gap",
    )
    assert opening_high[OUTSIDE_OPENING_SESSION_INDEX].quality_flags == (
        "outside_opening_session",
        "structure_gap",
    )
    assert opening_high[NO_TRADE_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "structure_gap",
    )
    assert opening_high[OPENING_RANGE_FROZEN_INDEX].value is not None
    assert opening_low[OPENING_RANGE_FROZEN_INDEX].value is not None
    assert sweep_high[HIGH_SWEEP_INDEX].value == 1
    assert failed_high[HIGH_SWEEP_INDEX].value == 1
    assert sweep_low[LOW_SWEEP_INDEX].value == 1
    assert failed_low[LOW_SWEEP_INDEX].value == 1
    assert close_location[ZERO_RANGE_INDEX].quality_flags == (
        "structure_gap",
        "zero_range",
    )
    assert wick[ZERO_RANGE_INDEX].quality_flags == ("structure_gap", "zero_range")
    assert range_contraction[ZERO_RANGE_INDEX].quality_flags == (
        "structure_gap",
        "zero_range",
    )
    assert range_contraction[RANGE_CONTRACTION_VALID_INDEX].value is not None


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}
