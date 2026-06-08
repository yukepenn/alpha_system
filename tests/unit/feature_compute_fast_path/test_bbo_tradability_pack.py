from __future__ import annotations

from collections import defaultdict

import pytest

from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import (
    BBO_TRADABILITY_FEATURE_IDS,
    PackMaterializer,
    build_fast_feature_pack,
)
from alpha_system.features.families.bbo import (
    BBOFeatureDefinition,
    BBOFeatureName,
    build_bbo_feature_definition,
    compute_bbo_feature,
)
from alpha_system.features.input_views import build_bbo_input_view
from tests.fixtures.feature_compute_fast_path.bbo_tradability import (
    DATASET_ID,
    FIRST_ZSCORE_VALID_INDEX,
    MISSING_BBO_INDEX,
    MISSING_SPREAD_TICKS_INDEX,
    PARTITION_ID,
    QUARANTINED_BBO_INDEX,
    SECOND_SESSION_VALID_INDEX,
    SESSION_RESET_INDEX,
    WIDE_LOW_DEPTH_INDEX,
    WINDOW_LENGTH,
    bbo_tradability_rows,
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

PACK_FEATURES = tuple(BBOFeatureName)
SPREAD_ZSCORE_TOLERANCE = FeatureParityTolerance(
    abs=1e-12,
    rel=1e-12,
    reason=(
        "Spread z-score is a rolling floating-point variance reduction; the Polars "
        "expression path may sum equivalent terms in a different binary order."
    ),
)


def test_bbo_tradability_pack_matches_reference_on_synthetic_fixture() -> None:
    pytest.importorskip("polars")
    rows = bbo_tradability_rows()
    accepted = accepted_version(DATASET_ID)
    definitions, feature_set = _bbo_pack_contracts()
    reference_view = build_bbo_input_view(
        accepted,
        rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_bbo_tradability_parity",
    )
    reference_records = {
        definition.name: compute_bbo_feature(definition, reference_view)
        for definition in definitions
    }
    materializer = PackMaterializer()
    pack = build_fast_feature_pack(feature_set)

    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(rows), pack)
    )

    assert (
        tuple(feature.feature_id for feature in pack.feature_set.features)
        == BBO_TRADABILITY_FEATURE_IDS
    )
    assert tuple(declaration.feature_version_id for declaration in pack.declarations) == tuple(
        definition.feature_version_id for definition in definitions
    )
    _assert_fixture_coverage(reference_records)
    for definition in definitions:
        tolerance = (
            SPREAD_ZSCORE_TOLERANCE
            if definition.name is BBOFeatureName.SPREAD_ZSCORE
            else FeatureParityTolerance()
        )
        assert_feature_records_match(
            reference_records[definition.name],
            fast_records[definition.feature_version_id],
            expected_feature_version_id=definition.feature_version_id,
            tolerance=tolerance,
        )


def _bbo_pack_contracts() -> tuple[tuple[BBOFeatureDefinition, ...], FeatureSetSpec]:
    registry_reader = EmptyRegistryReader()
    requests = {
        feature_name: approved_feature_request(f"fast_path_bbo_tradability_{feature_name.value}")
        for feature_name in PACK_FEATURES
    }
    definitions = tuple(
        build_bbo_feature_definition(
            feature_name,
            requests[feature_name],
            registry_reader,
            dataset_version_ids=(DATASET_ID,),
            window_length=WINDOW_LENGTH,
            reset_on_session=True,
            ddof=0,
        )
        for feature_name in PACK_FEATURES
    )
    feature_set = FeatureSetSpec(
        feature_set_id="feature_set_fast_path_bbo_tradability_v1",
        feature_set_version="v1",
        features=tuple(definition.spec.feature_spec for definition in definitions),
        description="V1 BBO tradability fast pack parity fixture.",
        metadata={"campaign": "FEATURE_COMPUTE_FAST_PATH_V1", "phase": "FCFP-P08"},
    )
    return definitions, feature_set


def _assert_fixture_coverage(
    reference_records: dict[BBOFeatureName, tuple[FeatureValueRecord, ...]],
) -> None:
    spread = reference_records[BBOFeatureName.SPREAD]
    spread_ticks = reference_records[BBOFeatureName.SPREAD_TICKS]
    spread_zscore = reference_records[BBOFeatureName.SPREAD_ZSCORE]
    missing_bbo = reference_records[BBOFeatureName.MISSING_BBO_FLAG]
    bad_quote = reference_records[BBOFeatureName.BAD_QUOTE_FLAG]
    wide_spread = reference_records[BBOFeatureName.WIDE_SPREAD_FLAG]
    low_depth = reference_records[BBOFeatureName.LOW_DEPTH_FLAG]
    imbalance = reference_records[BBOFeatureName.TOP_BOOK_IMBALANCE]
    microprice = reference_records[BBOFeatureName.MICROPRICE]

    assert spread_zscore[0].quality_flags == ("insufficient_window", "primitive_gap")
    assert spread_zscore[1].quality_flags == ("insufficient_window", "primitive_gap")
    assert spread_zscore[FIRST_ZSCORE_VALID_INDEX].value is not None
    assert spread_zscore[MISSING_BBO_INDEX].quality_flags == (
        "bbo_gap",
        "input_gap",
        "missing_bbo",
        "primitive_gap",
    )
    assert spread_zscore[QUARANTINED_BBO_INDEX].quality_flags == (
        "bbo_gap",
        "bbo_quarantined",
        "input_gap",
        "missing_bbo",
        "primitive_gap",
    )
    assert spread_zscore[SESSION_RESET_INDEX].quality_flags == (
        "insufficient_window",
        "primitive_gap",
    )
    assert spread_zscore[SECOND_SESSION_VALID_INDEX].value is not None

    assert spread[MISSING_BBO_INDEX].quality_flags == ("bbo_gap", "missing_bbo")
    assert spread[QUARANTINED_BBO_INDEX].quality_flags == (
        "bbo_gap",
        "bbo_quarantined",
    )
    assert missing_bbo[MISSING_BBO_INDEX].value == 1
    assert missing_bbo[MISSING_BBO_INDEX].quality_flags == ("missing_bbo",)
    assert bad_quote[MISSING_BBO_INDEX].value == 1
    assert bad_quote[MISSING_BBO_INDEX].quality_flags == ("missing_bbo",)
    assert bad_quote[QUARANTINED_BBO_INDEX].value == 1
    assert bad_quote[QUARANTINED_BBO_INDEX].quality_flags == ("bbo_quarantined",)

    assert wide_spread[WIDE_LOW_DEPTH_INDEX].value == 1
    assert low_depth[WIDE_LOW_DEPTH_INDEX].value == 1
    assert imbalance[WIDE_LOW_DEPTH_INDEX].value == 0.0
    assert microprice[WIDE_LOW_DEPTH_INDEX].value is not None
    assert spread_ticks[MISSING_SPREAD_TICKS_INDEX].quality_flags == (
        "bbo_gap",
        "missing_spread_ticks",
    )


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}
