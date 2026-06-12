from __future__ import annotations

from collections import defaultdict
from datetime import UTC, timedelta
from typing import Any

import pytest

from alpha_system.data.foundation.sessions import (
    SESSION_TYPE_ETH,
    SESSION_TYPE_RTH,
    classify_session_timestamp,
)
from alpha_system.features.contracts import FeatureSetSpec, FeatureValueRecord
from alpha_system.features.fast import PackMaterializer, build_fast_feature_pack
from alpha_system.features.families.bbo import (
    BBOFeatureName,
    build_bbo_feature_definition,
    compute_bbo_feature,
)
from alpha_system.features.families.cross_market import (
    CrossMarketFeatureName,
    build_cross_market_feature_definition,
    compute_cross_market_feature,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
from alpha_system.features.families.structure import (
    StructureFeatureName,
    build_structure_feature_definition,
    compute_structure_feature,
)
from alpha_system.features.input_views import build_bbo_input_view, build_ohlcv_input_view
from tests.fixtures.feature_compute_fast_path.dst_session_boundary import (
    DATASET_ID,
    PARTITION_ID,
    POST_DST_RTH_OPEN_TS,
    PRE_DST_RTH_OPEN_TS,
    SUMMER_RTH_OPEN_TS,
    VOLUME_WINDOW_LENGTH,
    WINDOW_LENGTH,
    dst_bbo_rows,
    dst_cross_market_ohlcv_rows,
    dst_ohlcv_rows,
    dst_rth_open_event_timestamps,
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

FLOAT_TOLERANCE = FeatureParityTolerance(
    abs=1e-12,
    rel=1e-12,
    reason="DST fixture parity allows equivalent floating-point reduction order.",
)


def test_dst_fixture_session_classification_flips_utc_open_edges() -> None:
    assert _segment(PRE_DST_RTH_OPEN_TS - timedelta(minutes=1)) == SESSION_TYPE_ETH
    assert _segment(PRE_DST_RTH_OPEN_TS) == SESSION_TYPE_RTH
    assert _segment(POST_DST_RTH_OPEN_TS - timedelta(minutes=1)) == SESSION_TYPE_ETH
    assert _segment(POST_DST_RTH_OPEN_TS) == SESSION_TYPE_RTH
    assert _segment(SUMMER_RTH_OPEN_TS - timedelta(minutes=1)) == SESSION_TYPE_ETH
    assert _segment(SUMMER_RTH_OPEN_TS) == SESSION_TYPE_RTH

    assert _rth_open_utc(PRE_DST_RTH_OPEN_TS) == PRE_DST_RTH_OPEN_TS
    assert _rth_open_utc(POST_DST_RTH_OPEN_TS) == POST_DST_RTH_OPEN_TS
    assert _rth_open_utc(SUMMER_RTH_OPEN_TS) == SUMMER_RTH_OPEN_TS


def test_repointed_fast_packs_match_reference_on_dst_boundary_fixture() -> None:
    pytest.importorskip("polars")
    registry_reader = EmptyRegistryReader()
    accepted = accepted_version(DATASET_ID)
    materializer = PackMaterializer()

    ohlcv_rows = dst_ohlcv_rows()
    ohlcv_view = build_ohlcv_input_view(
        accepted,
        ohlcv_rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_dst_session_boundary_ohlcv",
    )
    bbo_rows = dst_bbo_rows()
    bbo_view = build_bbo_input_view(
        accepted,
        bbo_rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_dst_session_boundary_bbo",
    )
    cross_rows = dst_cross_market_ohlcv_rows()
    cross_view = build_ohlcv_input_view(
        accepted,
        cross_rows,
        partition_id=PARTITION_ID,
        purpose="feature_fast_path_dst_session_boundary_cross_market",
    )

    structure_definition = build_structure_feature_definition(
        StructureFeatureName.RANGE_CONTRACTION,
        approved_feature_request("dst_liquidity_structure_range_contraction"),
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        window_length=WINDOW_LENGTH,
        reset_on_session=True,
    )
    _assert_fast_parity(
        structure_definition,
        _feature_set(
            "feature_set_fast_path_dst_liquidity_structure_v1",
            structure_definition,
        ),
        ohlcv_rows,
        compute_structure_feature(structure_definition, ohlcv_view),
        materializer=materializer,
        tolerance=FLOAT_TOLERANCE,
    )

    bbo_definition = build_bbo_feature_definition(
        BBOFeatureName.SPREAD_ZSCORE,
        approved_feature_request("dst_bbo_tradability_spread_zscore"),
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        window_length=WINDOW_LENGTH,
        reset_on_session=True,
        ddof=0,
    )
    _assert_fast_parity(
        bbo_definition,
        _feature_set("feature_set_fast_path_dst_bbo_tradability_v1", bbo_definition),
        bbo_rows,
        compute_bbo_feature(bbo_definition, bbo_view),
        materializer=materializer,
        tolerance=FLOAT_TOLERANCE,
    )

    regime_definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.ATR,
        approved_feature_request("dst_regime_ohlcv_atr"),
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        window_length=WINDOW_LENGTH,
        reset_on_session=True,
        ddof=0,
    )
    _assert_fast_parity(
        regime_definition,
        _feature_set("feature_set_fast_path_dst_regime_vol_compression_v1", regime_definition),
        ohlcv_rows,
        compute_ohlcv_feature(regime_definition, ohlcv_view),
        materializer=materializer,
        tolerance=FLOAT_TOLERANCE,
    )

    volume_definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.VOLUME_ZSCORE,
        approved_feature_request("dst_volume_activity_volume_zscore"),
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        window_length=VOLUME_WINDOW_LENGTH,
        reset_on_session=True,
        ddof=0,
    )
    _assert_fast_parity(
        volume_definition,
        _feature_set("feature_set_fast_path_dst_volume_activity_v1", volume_definition),
        ohlcv_rows,
        compute_ohlcv_feature(volume_definition, ohlcv_view),
        materializer=materializer,
        tolerance=FLOAT_TOLERANCE,
    )

    cross_definition = build_cross_market_feature_definition(
        CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
        approved_feature_request("dst_cross_market_synchronized_returns"),
        registry_reader,
        dataset_version_ids=(DATASET_ID,),
        window_length=WINDOW_LENGTH,
        horizon=1,
        reset_on_session=True,
        ddof=0,
        alignment_policy="strict_intersection",
    )
    _assert_fast_parity(
        cross_definition,
        _feature_set(
            "feature_set_fast_path_dst_cross_market_v1",
            cross_definition,
            metadata={"family": "cross_market_alignment"},
        ),
        cross_rows,
        compute_cross_market_feature(cross_definition, cross_view),
        materializer=materializer,
        tolerance=FLOAT_TOLERANCE,
    )


def _segment(timestamp: object) -> str:
    return classify_session_timestamp(timestamp).segment_label


def _rth_open_utc(timestamp: object) -> object:
    return classify_session_timestamp(timestamp).rth_open_ts.astimezone(UTC)


def _feature_set(
    feature_set_id: str,
    definition: object,
    *,
    metadata: dict[str, object] | None = None,
) -> FeatureSetSpec:
    return FeatureSetSpec(
        feature_set_id=feature_set_id,
        feature_set_version="v1",
        features=(_feature_spec(definition),),
        description="DST session-boundary fast-path parity fixture.",
        metadata={
            "campaign": "ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1",
            "phase": "P036000_IDENTITY_PINS_DST_FIXTURE",
            **(metadata or {}),
        },
    )


def _feature_spec(definition: object) -> Any:
    bound_spec = getattr(definition, "spec")
    return getattr(bound_spec, "feature_spec", bound_spec)


def _assert_fast_parity(
    definition: object,
    feature_set: FeatureSetSpec,
    rows: tuple[dict[str, object], ...],
    reference_records: tuple[FeatureValueRecord, ...],
    *,
    materializer: PackMaterializer,
    tolerance: FeatureParityTolerance,
) -> None:
    pack = build_fast_feature_pack(feature_set)
    fast_records = _records_by_feature_version(
        materializer.compute_values(materializer.frame_from_rows(rows), pack)
    )
    feature_version_id = getattr(definition, "feature_version_id")
    _assert_records_cover_dst_boundaries(reference_records)
    assert_feature_records_match(
        reference_records,
        fast_records[feature_version_id],
        expected_feature_version_id=feature_version_id,
        tolerance=tolerance,
    )


def _assert_records_cover_dst_boundaries(records: tuple[FeatureValueRecord, ...]) -> None:
    expected_events = set(dst_rth_open_event_timestamps())
    actual_events = {record.event_ts for record in records}
    assert expected_events.issubset(actual_events)


def _records_by_feature_version(
    records: tuple[FeatureValueRecord, ...],
) -> dict[str, tuple[FeatureValueRecord, ...]]:
    grouped: dict[str, list[FeatureValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.feature_version_id].append(record)
    return {feature_version_id: tuple(values) for feature_version_id, values in grouped.items()}
