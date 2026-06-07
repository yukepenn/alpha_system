from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from alpha_system.features.families.bbo import (
    BBOFeatureName,
    build_bbo_feature_definition,
    compute_bbo_feature,
)
from alpha_system.features.families.cross_market import (
    CrossMarketFeatureName,
    align_cross_market_rows,
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
    StructureInputBundle,
    build_structure_feature_definition,
    compute_structure_feature,
)
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.governance.feature_request import FeatureRequest


DATASET_VERSION_ID = "dsv_databento_ohlcv_05404069799decb0"
RESEARCH_ROOT = (
    Path(__file__).resolve().parents[3] / "research/futures_core_alpha_pilot_v1"
)


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_p15_feature_requests_validate_and_cover_gap_ids() -> None:
    records = {
        path.name: FeatureRequest.from_mapping(json.loads(path.read_text()))
        for path in sorted((RESEARCH_ROOT / "feature_requests").glob("p15_g*.json"))
    }

    assert set(records) == {
        "p15_g2_vwap_session.json",
        "p15_g3_cross_market_derived_state.json",
        "p15_g4_causal_ohlcv_derived.json",
        "p15_g5_bbo_top_book_confirmation.json",
    }
    assert {
        record.formula_sketch["gap_id"]
        for record in records.values()
    } == {"P15-G2", "P15-G3", "P15-G4", "P15-G5"}
    assert all(record.approval_status == "APPROVED" for record in records.values())


def test_p15_g2_vwap_session_request_is_point_in_time() -> None:
    request = _feature_request("p15_g2_vwap_session.json")
    base = _ohlcv_view(late_close=Decimal("103"))
    changed_future = _ohlcv_view(late_close=Decimal("999"))
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.VWAP,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
    )

    base_records = compute_ohlcv_feature(definition, base)
    changed_records = compute_ohlcv_feature(definition, changed_future)

    assert [record.available_ts for record in base_records] == [
        row.available_ts for row in base.rows
    ]
    assert base_records[1].value == changed_records[1].value
    assert base_records[1].available_ts < changed_future.rows[2].available_ts
    assert (
        definition.spec.inputs.input_metadata.to_dict()["field_roles"]["session_label"]
        == "SESSION_METADATA"
    )


def test_p15_g3_cross_market_request_preserves_asof_alignment() -> None:
    request = _feature_request("p15_g3_cross_market_derived_state.json")
    base = _cross_market_views(late_nq_close=Decimal("207"))
    changed_future = _cross_market_views(late_nq_close=Decimal("999"))
    definition = build_cross_market_feature_definition(
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
        reset_on_session=False,
    )

    snapshots = align_cross_market_rows(base, reset_on_session=False)
    base_records = compute_cross_market_feature(definition, base)
    changed_records = compute_cross_market_feature(definition, changed_future)

    assert [record.available_ts for record in base_records] == [
        snapshot.available_ts for snapshot in snapshots
    ]
    assert all(
        source_ts <= snapshot.available_ts
        for snapshot in snapshots
        for timestamps in snapshot.source_available_ts.values()
        for source_ts in timestamps
    )
    assert base_records[1].value == changed_records[1].value


def test_p15_g4_derived_ohlcv_request_uses_current_available_ts() -> None:
    request = _feature_request("p15_g4_causal_ohlcv_derived.json")
    base = StructureInputBundle(_structure_view(late_high=Decimal("104")))
    changed_future = StructureInputBundle(_structure_view(late_high=Decimal("999")))
    definition = build_structure_feature_definition(
        StructureFeatureName.PRIOR_HIGH_DISTANCE,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
        window_length=2,
        reset_on_session=False,
    )

    base_records = compute_structure_feature(definition, base)
    changed_records = compute_structure_feature(definition, changed_future)

    assert [record.available_ts for record in base_records] == [
        row.available_ts for row in base.ohlcv.rows
    ]
    assert base_records[2].value == changed_records[2].value
    assert base_records[2].available_ts < changed_future.ohlcv.rows[3].available_ts


def test_p15_g5_bbo_request_flags_exact_time_missingness() -> None:
    request = _feature_request("p15_g5_bbo_top_book_confirmation.json")
    view = BBOInputView(
        (
            _bbo_row(_dt("2024-01-02T14:30:00+00:00")),
            _bbo_row(_dt("2024-01-02T14:31:00+00:00"), quality_flags=("missing_bbo",)),
            _bbo_row(_dt("2024-01-02T14:32:00+00:00")),
        )
    )
    missing_definition = build_bbo_feature_definition(
        BBOFeatureName.MISSING_BBO_FLAG,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
    )
    spread_definition = build_bbo_feature_definition(
        BBOFeatureName.SPREAD,
        request,
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
    )

    missing_records = compute_bbo_feature(missing_definition, view)
    spread_records = compute_bbo_feature(spread_definition, view)

    assert [record.available_ts for record in missing_records] == [
        row.available_ts for row in view.rows
    ]
    assert [record.value for record in missing_records] == [0, 1, 0]
    assert spread_records[1].value is None
    assert "missing_bbo" in spread_records[1].quality_flags
    assert "missing_bbo" not in spread_records[2].quality_flags


def _feature_request(file_name: str) -> FeatureRequest:
    return FeatureRequest.from_mapping(
        json.loads((RESEARCH_ROOT / "feature_requests" / file_name).read_text())
    )


def _ohlcv_view(*, late_close: Decimal) -> OHLCVInputView:
    start = _dt("2024-01-02T14:30:00+00:00")
    return OHLCVInputView(
        (
            _ohlcv_row(start, close=Decimal("100")),
            _ohlcv_row(start + timedelta(minutes=1), close=Decimal("101")),
            _ohlcv_row(
                start + timedelta(minutes=2),
                close=late_close,
                available_ts=_dt("2024-01-02T14:40:00+00:00"),
            ),
        )
    )


def _structure_view(*, late_high: Decimal) -> OHLCVInputView:
    start = _dt("2024-01-02T14:30:00+00:00")
    return OHLCVInputView(
        (
            _ohlcv_row(start, high=Decimal("101"), low=Decimal("99"), close=Decimal("100")),
            _ohlcv_row(
                start + timedelta(minutes=1),
                high=Decimal("102"),
                low=Decimal("100"),
                close=Decimal("101"),
            ),
            _ohlcv_row(
                start + timedelta(minutes=2),
                high=Decimal("103"),
                low=Decimal("101"),
                close=Decimal("102"),
            ),
            _ohlcv_row(
                start + timedelta(minutes=3),
                high=late_high,
                low=Decimal("98"),
                close=Decimal("103"),
                available_ts=_dt("2024-01-02T14:40:00+00:00"),
            ),
        )
    )


def _cross_market_views(*, late_nq_close: Decimal) -> dict[str, OHLCVInputView]:
    start = _dt("2024-01-02T14:30:00+00:00")
    return {
        "ES": OHLCVInputView(
            (
                _ohlcv_row(start, instrument="ES", close=Decimal("100")),
                _ohlcv_row(start + timedelta(minutes=1), instrument="ES", close=Decimal("102")),
            )
        ),
        "NQ": OHLCVInputView(
            (
                _ohlcv_row(start, instrument="NQ", close=Decimal("200")),
                _ohlcv_row(start + timedelta(minutes=1), instrument="NQ", close=Decimal("206")),
                _ohlcv_row(
                    start + timedelta(minutes=2),
                    instrument="NQ",
                    close=late_nq_close,
                    available_ts=_dt("2024-01-02T14:40:00+00:00"),
                ),
            )
        ),
        "RTY": OHLCVInputView(
            (
                _ohlcv_row(start, instrument="RTY", close=Decimal("50")),
                _ohlcv_row(start + timedelta(minutes=1), instrument="RTY", close=Decimal("51")),
            )
        ),
    }


def _ohlcv_row(
    bar_start_ts: datetime,
    *,
    instrument: str = "ES",
    high: Decimal | None = None,
    low: Decimal | None = None,
    close: Decimal,
    available_ts: datetime | None = None,
) -> OHLCVInputRow:
    high = close + Decimal("1") if high is None else high
    low = close - Decimal("1") if low is None else low
    return OHLCVInputRow(
        instrument_id=instrument,
        contract_id=f"{instrument}M4",
        series_id=f"{instrument}.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=available_ts or bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=(available_ts or bar_start_ts + timedelta(minutes=1, seconds=1))
        + timedelta(seconds=1),
        open=close,
        high=high,
        low=low,
        close=close,
        volume=Decimal("100"),
        data_version=DATASET_VERSION_ID,
        quality_flags=(),
        session_label="RTH",
    )


def _bbo_row(
    bar_start_ts: datetime,
    *,
    quality_flags: tuple[str, ...] = (),
) -> BBOInputRow:
    bid = Decimal("99")
    ask = Decimal("101")
    bid_size = Decimal("10")
    ask_size = Decimal("20")
    mid = (bid + ask) / Decimal("2")
    spread = ask - bid
    return BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        bid=bid,
        ask=ask,
        bid_size=bid_size,
        ask_size=ask_size,
        mid=mid,
        spread=spread,
        spread_ticks=Decimal("8"),
        microprice=(ask * bid_size + bid * ask_size) / (bid_size + ask_size),
        data_version=DATASET_VERSION_ID,
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    return parsed.astimezone(UTC)
