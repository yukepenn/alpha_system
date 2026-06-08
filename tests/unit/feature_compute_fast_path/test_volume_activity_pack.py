from __future__ import annotations

from collections import defaultdict
from typing import Any

import pytest

from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import (
    VOLUME_ACTIVITY_FEATURE_IDS,
    PackMaterializer,
    build_fast_feature_pack,
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
from tests.fixtures.feature_compute_fast_path.volume_activity import (
    DATASET_ID,
    FIRST_VALID_INDEX,
    INPUT_GAP_INDEX,
    PARTITION_ID,
    SECOND_SESSION_VALID_INDEX,
    SESSION_RESET_INDEX,
    STRUCTURE_WINDOW_LENGTH,
    WINDOW_LENGTH,
    ZERO_RANGE_INDEX,
    volume_activity_rows,
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

PACK_OHLCV_FEATURES = (
    OHLCVFeatureName.ROLLING_VOLUME,
    OHLCVFeatureName.VOLUME_ZSCORE,
    OHLCVFeatureName.SESSION_MINUTE,
    OHLCVFeatureName.ROLLING_RANGE,
    OHLCVFeatureName.RANGE_POSITION,
    OHLCVFeatureName.TRENDINESS,
)
PACK_STRUCTURE_FEATURES = (
    StructureFeatureName.CLOSE_LOCATION_VALUE,
    StructureFeatureName.WICK_REJECTION_SCORE,
)
FLOAT_REDUCTION_TOLERANCE = FeatureParityTolerance(
    abs=1e-12,
    rel=1e-12,
    reason=(
        "Volume z-score, rolling OHLC ranges, and structure ratios are finite "
        "floating-point reductions; the Polars expression path can evaluate "
        "equivalent operations in a different binary order."
    ),
)


def test_volume_activity_pack_matches_reference_on_synthetic_fixture() -> None:
    pytest.importorskip("polars")
    rows = volume_activity_rows()
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _volume_activity_pack_contracts()
    reference_view = build_ohlcv_input_view(
        accepted,
        rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_volume_activity_parity",
    )
    reference_records = _reference_records(definitions, reference_view)
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(rows), pack)
    )

    assert tuple(feature.feature_id for feature in pack.feature_set.features) == (
        VOLUME_ACTIVITY_FEATURE_IDS
    )
    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == tuple(
        definition.feature_version_id for definition in definitions
    )
    _assert_fixture_coverage(reference_records)
    for definition in definitions:
        tolerance = (
            FeatureParityTolerance()
            if definition.feature_id
            in {"base_ohlcv_rolling_volume", "base_ohlcv_session_minute"}
            else FLOAT_REDUCTION_TOLERANCE
        )
        assert_feature_records_match(
            reference_records[definition.feature_id],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
            tolerance=tolerance,
        )


def _volume_activity_pack_contracts() -> tuple[
    tuple[OHLCVFeatureDefinition | StructureFeatureDefinition, ...],
    FeatureSetSpec,
]:
    registry_reader = EmptyRegistryReader()
    requests = {
        feature_name: approved_feature_request(f"fast_path_volume_activity_{feature_name.value}")
        for feature_name in (*PACK_OHLCV_FEATURES, *PACK_STRUCTURE_FEATURES)
    }
    ohlcv_definitions = tuple(
        build_ohlcv_feature_definition(
            feature_name,
            requests[feature_name],
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            window_length=1
            if feature_name is OHLCVFeatureName.SESSION_MINUTE
            else WINDOW_LENGTH,
            horizon=1,
            reset_on_session=True,
        )
        for feature_name in PACK_OHLCV_FEATURES
    )
    structure_definitions = tuple(
        build_structure_feature_definition(
            feature_name,
            requests[feature_name],
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            window_length=STRUCTURE_WINDOW_LENGTH,
            reset_on_session=True,
        )
        for feature_name in PACK_STRUCTURE_FEATURES
    )
    definitions = (*ohlcv_definitions, *structure_definitions)
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_volume_activity_v1",
        feature_set_version="v1",
        features=(
            *tuple(definition.spec for definition in ohlcv_definitions),
            *tuple(definition.spec.feature_spec for definition in structure_definitions),
        ),
        description="V1 volume / activity fast pack parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FCFP-P07"},
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
    rolling_volume = reference_records["base_ohlcv_rolling_volume"]
    volume_zscore = reference_records["base_ohlcv_volume_zscore"]
    session_minute = reference_records["base_ohlcv_session_minute"]
    trendiness = reference_records["base_ohlcv_trendiness"]
    close_location = reference_records["liquidity_structure_close_location_value"]
    wick = reference_records["liquidity_structure_wick_rejection_score"]

    assert rolling_volume[0].quality_flags == ("insufficient_window", "ohlcv_gap")
    assert rolling_volume[FIRST_VALID_INDEX].value is not None
    assert rolling_volume[INPUT_GAP_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "ohlcv_gap",
    )
    assert rolling_volume[SESSION_RESET_INDEX].quality_flags == (
        "insufficient_window",
        "ohlcv_gap",
    )
    assert rolling_volume[SECOND_SESSION_VALID_INDEX].value is not None

    assert volume_zscore[FIRST_VALID_INDEX].value is not None
    assert volume_zscore[INPUT_GAP_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "primitive_gap",
    )
    assert volume_zscore[SESSION_RESET_INDEX].quality_flags == (
        "insufficient_window",
        "primitive_gap",
    )

    assert session_minute[0].value == 0
    assert session_minute[SESSION_RESET_INDEX].value == 0
    assert session_minute[SESSION_RESET_INDEX].quality_flags == ()
    assert trendiness[SECOND_SESSION_VALID_INDEX].value is not None

    assert close_location[INPUT_GAP_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "structure_gap",
    )
    assert wick[INPUT_GAP_INDEX].quality_flags == (
        "input_gap",
        "no_trade",
        "structure_gap",
    )
    assert close_location[ZERO_RANGE_INDEX].quality_flags == (
        "structure_gap",
        "zero_range",
    )
    assert wick[ZERO_RANGE_INDEX].quality_flags == ("structure_gap", "zero_range")


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}
