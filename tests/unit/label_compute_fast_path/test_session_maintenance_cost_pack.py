from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.input_views import build_bbo_input_view, build_ohlcv_input_view
from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.fast import (
    COST_ADJUSTED_LABEL_IDS,
    SESSION_MAINTENANCE_LABEL_IDS,
    FastLabelMaterializer,
    build_cost_adjusted_label_pack,
    build_session_maintenance_label_pack,
    cost_adjusted_pack_coverage,
    session_maintenance_pack_coverage,
)
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelDefinition,
    CostAdjustedLabelName,
    build_cost_adjusted_label_definition,
    compute_cost_adjusted_labels,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelDefinition,
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_labels,
)
from alpha_system.labels.version import LabelValueRecord
from tests.fixtures.feature_label.synthetic import accepted_version
from tests.fixtures.label_compute_fast_path.session_cost_labels import (
    COST_MISSING_SOURCE_TS,
    COST_NORMAL_SOURCE_TS,
    COST_TERMINAL_GAP_SOURCE_TS,
    DATASET_ID,
    MAINTENANCE_NORMAL_SOURCE_TS,
    PARTITION_ID,
    ROLL_SOURCE_TS,
    SESSION_GAP_SOURCE_TS,
    SESSION_NORMAL_SOURCE_TS,
    cost_adjusted_bbo_rows,
    cost_adjusted_label_specs,
    cost_adjusted_ohlcv_rows,
    session_maintenance_label_specs,
    session_maintenance_ohlcv_rows,
)
from tests.unit.feature_compute_fast_path.parity_harness import (
    LabelParityTolerance,
    assert_label_records_match,
)


def test_session_maintenance_pack_matches_reference_close_out_cases() -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definitions = _session_maintenance_definitions()
    ohlcv_rows = session_maintenance_ohlcv_rows()
    reference_records = compute_fixed_horizon_labels(
        definitions,
        build_ohlcv_input_view(
            accepted,
            ohlcv_rows,
            partition_id=PARTITION_ID,
            purpose="lcfp_p04_session_maintenance_reference",
        ),
    )

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=()),
        build_session_maintenance_label_pack(definitions),
    )
    fast_records = _records_by_label_version(computation.records)

    assert SESSION_MAINTENANCE_LABEL_IDS == ("session_close", "maintenance_flat")
    assert session_maintenance_pack_coverage().label_ids == SESSION_MAINTENANCE_LABEL_IDS
    for definition in definitions:
        assert_label_records_match(
            reference_records[definition.name],
            fast_records[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
        )

    session_records = reference_records[FixedHorizonLabelName.SESSION_CLOSE]
    maintenance_records = reference_records[FixedHorizonLabelName.MAINTENANCE_FLAT]
    _assert_has_event(session_records, SESSION_NORMAL_SOURCE_TS)
    _assert_missing_event(session_records, SESSION_GAP_SOURCE_TS)
    _assert_missing_event(session_records, ROLL_SOURCE_TS)
    _assert_has_event(maintenance_records, MAINTENANCE_NORMAL_SOURCE_TS)
    _assert_missing_event(maintenance_records, ROLL_SOURCE_TS)


def test_cost_adjusted_pack_matches_reference_and_preserves_bbo_gap_flags() -> None:
    pytest.importorskip("polars")
    accepted = accepted_version(DATASET_ID)
    definitions = _cost_adjusted_definitions()
    ohlcv_rows = cost_adjusted_ohlcv_rows()
    bbo_rows = cost_adjusted_bbo_rows()
    ohlcv_view = build_ohlcv_input_view(
        accepted,
        ohlcv_rows,
        partition_id=PARTITION_ID,
        purpose="lcfp_p04_cost_adjusted_reference",
    )
    bbo_view = build_bbo_input_view(
        accepted,
        bbo_rows,
        partition_id=PARTITION_ID,
        purpose="lcfp_p04_cost_adjusted_reference",
    )
    reference_records = compute_cost_adjusted_labels(
        definitions,
        bbo_view,
        trade_rows=ohlcv_view.rows,
    )

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=bbo_rows),
        build_cost_adjusted_label_pack(definitions),
    )
    fast_records = _records_by_label_version(computation.records)

    assert COST_ADJUSTED_LABEL_IDS == (
        "cost_adjusted_fwd_ret",
        "spread_adjusted_fwd_ret",
    )
    assert cost_adjusted_pack_coverage().cost_profile_source == "alpha_system.backtest.costs"
    tolerance = LabelParityTolerance(
        abs=1e-12,
        rel=1e-12,
        reason="Decimal reference arithmetic is reconstructed from a float Polars panel",
    )
    for definition in definitions:
        assert_label_records_match(
            reference_records[definition.name],
            fast_records[definition.label_version_id],
            expected_label_version_id=definition.label_version_id,
            tolerance=tolerance,
        )

    spread_records = reference_records[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET]
    normal = _record_by_event(spread_records, COST_NORMAL_SOURCE_TS)
    terminal_gap = _record_by_event(spread_records, COST_TERMINAL_GAP_SOURCE_TS)
    entry_gap = _record_by_event(spread_records, COST_MISSING_SOURCE_TS)
    assert normal.value is not None
    assert terminal_gap.value is None
    assert terminal_gap.quality_flags == (
        "label_gap",
        "terminal_bbo_gap",
        "bbo_gap",
        "missing_bbo",
    )
    assert entry_gap.value is None
    assert entry_gap.quality_flags == (
        "label_gap",
        "entry_bbo_gap",
        "bbo_gap",
        "missing_bbo",
    )


def test_cost_adjusted_maintenance_crossing_window_matches_reference_behavior() -> None:
    pytest.importorskip("polars")
    source_ts = datetime(2024, 1, 2, 21, 45, tzinfo=UTC)
    terminal_ts = source_ts + timedelta(minutes=30)
    accepted = accepted_version(DATASET_ID)
    ohlcv_rows = (
        _ohlcv_mapping(source_ts, close=Decimal("100")),
        _ohlcv_mapping(terminal_ts, close=Decimal("101")),
    )
    bbo_rows = (
        _bbo_mapping(source_ts, bid=Decimal("99"), ask=Decimal("101")),
        _bbo_mapping(terminal_ts, bid=Decimal("100"), ask=Decimal("102")),
    )
    definition = build_cost_adjusted_label_definition(
        CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
        _cost_label_spec(
            CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
            horizon="30m",
            availability_time="2024-01-02T22:16:00+00:00",
        ),
        dataset_version_ids=(DATASET_ID,),
    )
    ohlcv_view = build_ohlcv_input_view(
        accepted,
        ohlcv_rows,
        partition_id=PARTITION_ID,
        purpose="lcfp_p04_cost_maintenance_reference",
    )
    bbo_view = build_bbo_input_view(
        accepted,
        bbo_rows,
        partition_id=PARTITION_ID,
        purpose="lcfp_p04_cost_maintenance_reference",
    )
    reference_records = compute_cost_adjusted_labels(
        (definition,),
        bbo_view,
        trade_rows=ohlcv_view.rows,
    )

    materializer = FastLabelMaterializer()
    computation = materializer.compute_values_with_metadata(
        materializer.frame_from_rows(ohlcv_rows=ohlcv_rows, bbo_rows=bbo_rows),
        build_cost_adjusted_label_pack((definition,)),
    )
    fast_records = _records_by_label_version(computation.records)

    assert _record_by_event(
        reference_records[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET],
        source_ts,
    ).value is not None
    assert_label_records_match(
        reference_records[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET],
        fast_records[definition.label_version_id],
        expected_label_version_id=definition.label_version_id,
        tolerance=LabelParityTolerance(
            abs=1e-12,
            rel=1e-12,
            reason="Decimal reference arithmetic is reconstructed from a float Polars panel",
        ),
    )


def _session_maintenance_definitions() -> tuple[FixedHorizonLabelDefinition, ...]:
    specs = session_maintenance_label_specs()
    return tuple(
        build_fixed_horizon_label_definition(
            label_name,
            specs[label_name],
            dataset_version_ids=(DATASET_ID,),
        )
        for label_name in (
            FixedHorizonLabelName.SESSION_CLOSE,
            FixedHorizonLabelName.MAINTENANCE_FLAT,
        )
    )


def _cost_adjusted_definitions() -> tuple[CostAdjustedLabelDefinition, ...]:
    specs = cost_adjusted_label_specs()
    return tuple(
        build_cost_adjusted_label_definition(
            label_name,
            specs[label_name],
            dataset_version_ids=(DATASET_ID,),
        )
        for label_name in (
            CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
            CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET,
        )
    )


def _records_by_label_version(
    records: tuple[LabelValueRecord, ...],
) -> dict[str, tuple[LabelValueRecord, ...]]:
    grouped: dict[str, list[LabelValueRecord]] = defaultdict(list)
    for record in records:
        grouped[record.label_version_id].append(record)
    return {label_version_id: tuple(values) for label_version_id, values in grouped.items()}


def _assert_has_event(records: tuple[LabelValueRecord, ...], event_ts: datetime) -> None:
    assert any(record.event_ts == event_ts for record in records)


def _assert_missing_event(records: tuple[LabelValueRecord, ...], event_ts: datetime) -> None:
    assert all(record.event_ts != event_ts for record in records)


def _record_by_event(
    records: tuple[LabelValueRecord, ...],
    event_ts: datetime,
) -> LabelValueRecord:
    matches = tuple(record for record in records if record.event_ts == event_ts)
    assert len(matches) == 1
    return matches[0]


def _ohlcv_mapping(event_ts: datetime, *, close: Decimal) -> dict[str, object]:
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_COST_MAINT",
        "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
        "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
        "open": str(close),
        "high": str(close + Decimal("0.25")),
        "low": str(close - Decimal("0.25")),
        "close": str(close),
        "volume": "10",
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_lcfp_p04_cost_maintenance",
        "data_version": DATASET_ID,
        "quality_flags": [],
        "session_label": "RTH",
    }


def _bbo_mapping(event_ts: datetime, *, bid: Decimal, ask: Decimal) -> dict[str, object]:
    mid = (bid + ask) / Decimal("2")
    spread = ask - bid
    return {
        "instrument_id": "ES",
        "contract_id": "ESM4",
        "series_id": "ES_COST_MAINT",
        "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
        "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
        "bid": str(bid),
        "ask": str(ask),
        "bid_size": "10",
        "ask_size": "10",
        "mid": str(mid),
        "spread": str(spread),
        "source": "dsrc_synthetic_fixture",
        "source_request_id": "synthetic_lcfp_p04_cost_maintenance",
        "data_version": DATASET_ID,
        "quality_flags": [],
        "session_label": "RTH",
        "spread_ticks": None,
        "microprice": None,
        "bid_order_count": None,
        "ask_order_count": None,
    }


def _cost_label_spec(
    label_name: CostAdjustedLabelName,
    *,
    horizon: str,
    availability_time: str,
):
    return create_label_spec(
        horizon=horizon,
        path_rules={
            "path": "bbo_mid_forward_return",
            "terminal_rule": "exact event_ts match with valid BBO only",
            "horizon_steps": int(horizon.removesuffix("m")),
        },
        cost_model={
            "model": "spread_adjusted",
            "spread_adjustment": "half_spread_round_trip",
        },
        target_stop_rules={
            "target_rule": "disabled_for_lcfp_p04_cost_maintenance_fixture",
            "stop_rule": "disabled_for_lcfp_p04_cost_maintenance_fixture",
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": [label_name.value],
            "aliases": [f"synthetic_{label_name.value}_maintenance"],
            "transforms": [f"label({label_name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )
