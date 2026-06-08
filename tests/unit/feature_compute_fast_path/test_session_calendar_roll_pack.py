from __future__ import annotations

from collections import defaultdict

import pytest

from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import (
    SESSION_CALENDAR_ROLL_FEATURE_IDS,
    PackMaterializer,
    build_fast_feature_pack,
)
from alpha_system.features.families.session import (
    SessionFeatureDefinition,
    SessionFeatureName,
    build_session_feature_definition,
    compute_session_feature,
)
from tests.fixtures.feature_compute_fast_path.session_calendar_roll import (
    DATASET_ID,
    PARTITION_ID,
    SYNTHETIC_NO_TRADE_INDEX,
    session_calendar_roll_pack_records,
    session_calendar_roll_pack_rows,
)
from tests.fixtures.feature_label.synthetic import (
    EmptyRegistryReader,
    approved_feature_request,
)
from tests.unit.feature_compute_fast_path.parity_harness import (
    assert_feature_records_match,
)

PACK_FEATURES = tuple(SessionFeatureName)


def test_session_calendar_roll_pack_matches_reference_on_synthetic_fixture() -> None:
    pytest.importorskip("polars")
    rows = session_calendar_roll_pack_records()
    frame_rows = session_calendar_roll_pack_rows()
    definitions, feature_set = _session_pack_contracts()
    reference_records = {
        definition.name: compute_session_feature(definition, rows)
        for definition in definitions
    }
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(frame_rows), pack)
    )

    assert (
        tuple(feature.feature_id for feature in pack.feature_set.features)
        == SESSION_CALENDAR_ROLL_FEATURE_IDS
    )
    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == tuple(
        definition.feature_version_id for definition in definitions
    )
    _assert_fixture_coverage(reference_records)
    for definition in definitions:
        assert_feature_records_match(
            reference_records[definition.name],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
        )


def _session_pack_contracts() -> tuple[tuple[SessionFeatureDefinition, ...], FeatureSetSpec]:
    registry_reader = EmptyRegistryReader()
    requests = {
        feature_name: approved_feature_request(
            f"fast_path_session_calendar_roll_{feature_name.value}"
        )
        for feature_name in PACK_FEATURES
    }
    definitions = tuple(
        build_session_feature_definition(
            feature_name,
            requests[feature_name],
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            input_view_name="dense_grid_ohlcv",
        )
        for feature_name in PACK_FEATURES
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_session_calendar_roll_v1",
        feature_set_version="v1",
        features=tuple(definition.spec.feature_spec for definition in definitions),
        description="V1 Session / Calendar / Roll fast pack parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FCFP-P03"},
    )
    return definitions, feature_set


def _assert_fixture_coverage(
    reference_records: dict[SessionFeatureName, tuple[FeatureValueRecord, ...]],
) -> None:
    assert any(
        "outside_rth" in record.quality_flags
        for record in reference_records[SessionFeatureName.MINUTES_FROM_RTH_OPEN]
    )
    assert any(
        "before_rth_open" in record.quality_flags
        for record in reference_records[SessionFeatureName.MINUTES_FROM_RTH_OPEN]
    )
    assert any(
        "after_rth_close" in record.quality_flags
        for record in reference_records[SessionFeatureName.MINUTES_TO_RTH_CLOSE]
    )
    assert any(
        record.value is None and "roll_transition_absent" in record.quality_flags
        for record in reference_records[SessionFeatureName.BARS_TO_ROLL]
    )
    assert (
        "synthetic_no_trade_position_only"
        in reference_records[SessionFeatureName.SESSION_ID][
            SYNTHETIC_NO_TRADE_INDEX
        ].quality_flags
    )
    assert all(
        record.value is None and "expiration_metadata_absent" in record.quality_flags
        for record in reference_records[SessionFeatureName.MINUTES_TO_EXPIRATION]
    )
    assert all(
        record.value is None and "status_metadata_absent" in record.quality_flags
        for record in reference_records[SessionFeatureName.HALT_STATUS_FLAG]
    )


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}
