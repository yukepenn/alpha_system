from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import pytest

from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    VWAP_SESSION_AUCTION_FEATURE_IDS,
    PackMaterializer,
    build_fast_feature_pack,
    build_vwap_session_auction_pack,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureDefinition,
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from tests.fixtures.feature_compute_fast_path.vwap_session_auction import (
    DATASET_ID,
    FIRST_RTH_NO_TRADE_INDEX,
    LEADING_NO_TRADE_INDEX,
    NEXT_RTH_OPEN_INDEX,
    PARTITION_ID,
    RTH_ZERO_VOLUME_INDEX,
    ZERO_VWAP_INDEX,
    vwap_session_auction_frame_rows,
    vwap_session_auction_input_rows,
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
    OHLCVFeatureName.VWAP,
    OHLCVFeatureName.ANCHORED_VWAP,
    OHLCVFeatureName.DISTANCE_TO_VWAP,
    OHLCVFeatureName.OPENING_RANGE,
    OHLCVFeatureName.OVERNIGHT_RANGE,
)
VWAP_TOLERANCE = FeatureParityTolerance(
    abs=1e-12,
    rel=1e-12,
    reason=(
        "VWAP, anchored VWAP, and distance-to-VWAP are cumulative floating-point "
        "calculations; Polars and the reference may sum equivalent terms with "
        "minor binary-rounding differences."
    ),
)


def test_vwap_session_auction_pack_matches_reference_on_synthetic_fixture() -> None:
    pytest.importorskip("polars")
    # P194500 repair provenance: canonical session_label can be static metadata;
    # both engines must derive RTH/ETH membership from bar_start_ts.
    reference_rows = _static_session_input_rows()
    frame_rows = _static_session_frame_rows()
    definitions, feature_set = _vwap_pack_contracts()
    reference_view = OHLCVInputView(reference_rows)
    reference_records = {
        definition.name: compute_ohlcv_feature(definition, reference_view)
        for definition in definitions
    }
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(frame_rows), pack)
    )

    assert (
        tuple(feature.feature_id for feature in pack.feature_set.features)
        == VWAP_SESSION_AUCTION_FEATURE_IDS
    )
    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == tuple(
        definition.feature_version_id for definition in definitions
    )
    _assert_fixture_coverage(reference_records)
    for definition in definitions:
        tolerance = (
            VWAP_TOLERANCE
            if definition.name
            in {
                OHLCVFeatureName.VWAP,
                OHLCVFeatureName.ANCHORED_VWAP,
                OHLCVFeatureName.DISTANCE_TO_VWAP,
            }
            else FeatureParityTolerance()
        )
        assert_feature_records_match(
            reference_records[definition.name],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
            tolerance=tolerance,
        )


def test_vwap_session_minute_binding_matches_reference_on_multi_session_fixture() -> None:
    pytest.importorskip("polars")
    reference_rows = _static_session_input_rows()
    frame_rows = _static_session_frame_rows()
    definition, feature_set = _vwap_session_minute_contracts()
    reference_records = compute_ohlcv_feature(definition, OHLCVInputView(reference_rows))
    materializer = PackMaterializer()
    pack = build_vwap_session_auction_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(frame_rows), pack)
    )

    assert reference_records[NEXT_RTH_OPEN_INDEX].value == 0
    assert_feature_records_match(
        reference_records,
        fast_records[definition.feature_version_id],
        expected_feature_version_id=definition.feature_version_id,
    )


def test_vwap_opening_range_uses_timestamp_rth_when_session_label_is_static_eth() -> None:
    pytest.importorskip("polars")
    frame_rows = tuple(
        {**row, "session_label": "ETH"} for row in vwap_session_auction_frame_rows()
    )
    definitions, feature_set = _vwap_pack_contracts()
    opening_definition = next(
        definition
        for definition in definitions
        if definition.name is OHLCVFeatureName.OPENING_RANGE
    )
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(frame_rows), pack)
    )
    opening_records = fast_records[opening_definition.feature_version_id]

    assert opening_records[FIRST_RTH_NO_TRADE_INDEX].value is None
    assert opening_records[5].value is not None
    assert opening_records[RTH_ZERO_VOLUME_INDEX].value is not None
    assert "outside_rth" in opening_records[0].quality_flags


def test_vwap_session_auction_pack_materialization_records_fast_provenance(
    tmp_path: Path,
) -> None:
    pytest.importorskip("polars")
    rows = vwap_session_auction_frame_rows()
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _vwap_pack_contracts()
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


def _vwap_pack_contracts() -> tuple[tuple[OHLCVFeatureDefinition, ...], FeatureSetSpec]:
    registry_reader = EmptyRegistryReader()
    requests = {
        feature_name: approved_feature_request(
            f"fast_path_vwap_session_auction_{feature_name.value}"
        )
        for feature_name in PACK_FEATURES
    }
    definitions = tuple(
        build_ohlcv_feature_definition(
            feature_name,
            requests[feature_name],
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            opening_range_minutes=2,
            anchor_session_label="RTH",
            reset_on_session=True,
        )
        for feature_name in PACK_FEATURES
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_vwap_session_auction_v1",
        feature_set_version="v1",
        features=tuple(definition.spec for definition in definitions),
        description="V1 VWAP / session-auction fast pack parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FCFP-P04"},
    )
    return definitions, feature_set


def _vwap_session_minute_contracts() -> tuple[OHLCVFeatureDefinition, FeatureSetSpec]:
    registry_reader = EmptyRegistryReader()
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.SESSION_MINUTE,
        approved_feature_request("fast_path_vwap_session_auction_session_minute"),
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        reset_on_session=True,
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_vwap_session_minute_v1",
        feature_set_version="v1",
        features=(definition.spec,),
        description="V1 VWAP/session-auction session-minute parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FUTSUB-P14"},
    )
    return definition, feature_set


def _assert_fixture_coverage(
    reference_records: dict[OHLCVFeatureName, tuple[FeatureValueRecord, ...]],
) -> None:
    assert reference_records[OHLCVFeatureName.VWAP][
        LEADING_NO_TRADE_INDEX
    ].quality_flags == ("no_trade", "ohlcv_gap")
    assert reference_records[OHLCVFeatureName.VWAP][
        RTH_ZERO_VOLUME_INDEX
    ].quality_flags == ("ohlcv_gap", "zero_volume")
    assert reference_records[OHLCVFeatureName.ANCHORED_VWAP][
        LEADING_NO_TRADE_INDEX
    ].quality_flags == ("before_anchor", "ohlcv_gap")
    assert reference_records[OHLCVFeatureName.ANCHORED_VWAP][
        RTH_ZERO_VOLUME_INDEX
    ].quality_flags == ("ohlcv_gap", "zero_volume")
    assert reference_records[OHLCVFeatureName.DISTANCE_TO_VWAP][
        ZERO_VWAP_INDEX
    ].quality_flags == ("ohlcv_gap", "zero_vwap")
    assert reference_records[OHLCVFeatureName.OPENING_RANGE][0].quality_flags == (
        "ohlcv_gap",
        "outside_rth",
    )
    assert reference_records[OHLCVFeatureName.OPENING_RANGE][
        FIRST_RTH_NO_TRADE_INDEX
    ].quality_flags == (
        "no_opening_trade",
        "no_trade",
        "ohlcv_gap",
    )
    assert reference_records[OHLCVFeatureName.OPENING_RANGE][
        RTH_ZERO_VOLUME_INDEX
    ].value is not None
    assert reference_records[OHLCVFeatureName.OVERNIGHT_RANGE][0].quality_flags == (
        "no_overnight_trade",
        "no_trade",
        "ohlcv_gap",
    )
    assert reference_records[OHLCVFeatureName.OVERNIGHT_RANGE][1].quality_flags == (
        "no_overnight_trade",
        "no_trade",
        "ohlcv_gap",
    )
    assert reference_records[OHLCVFeatureName.OVERNIGHT_RANGE][
        FIRST_RTH_NO_TRADE_INDEX
    ].value is not None
    assert reference_records[OHLCVFeatureName.OVERNIGHT_RANGE][
        NEXT_RTH_OPEN_INDEX
    ].value is not None


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}


def _static_session_input_rows() -> tuple[OHLCVInputRow, ...]:
    return tuple(replace(row, session_label="ETH") for row in vwap_session_auction_input_rows())


def _static_session_frame_rows() -> tuple[dict[str, object], ...]:
    return tuple({**row, "session_label": "ETH"} for row in vwap_session_auction_frame_rows())
