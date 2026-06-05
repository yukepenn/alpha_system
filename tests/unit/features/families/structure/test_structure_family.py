from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.contracts import (
    FeatureContractError,
    FeatureFamily,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.families.structure import (
    StructureFeatureError,
    StructureFeatureName,
    build_structure_feature_definition,
    compute_structure_feature,
    compute_structure_features,
    supported_structure_features,
)
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
    CanonicalInputViews,
    OHLCVInputRow,
    OHLCVInputView,
)
from alpha_system.features.request_gate import FeatureRequestGateError
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_all_structure_features_are_gated_versioned_causal_and_available() -> None:
    views = _fixture_views()
    registry = EmptyRegistryReader()
    definitions = tuple(
        build_structure_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            dataset_version_ids=("dsv_synthetic_structure",),
            window_length=2,
            opening_range_minutes=2,
            failure_window=2,
            reset_on_session=False,
        )
        for feature in supported_structure_features()
    )

    results = compute_structure_features(definitions, views)

    assert set(results) == set(StructureFeatureName)
    for definition in definitions:
        assert definition.spec.family is FeatureFamily.LIQUIDITY_STRUCTURE
        assert definition.spec.implementation_eligible is True
        assert definition.spec.feature_request_id.startswith("freq_")
        assert definition.version == definition.spec.derive_feature_version()
        assert definition.spec.window.is_live_compatible is True
        records = results[definition.name]
        assert len(records) == len(views.ohlcv.rows)
        assert all(record.feature_version_id == definition.feature_version_id for record in records)
        assert [record.available_ts for record in records] == [
            row.available_ts for row in views.ohlcv.rows
        ]

    assert results[StructureFeatureName.PRIOR_HIGH_DISTANCE][2].value == pytest.approx(
        (102.5 - 102.0) / 102.0
    )
    assert results[StructureFeatureName.PRIOR_LOW_DISTANCE][2].value == pytest.approx(
        (102.5 - 99.0) / 99.0
    )
    assert results[StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE][2].value == pytest.approx(
        (102.5 - 102.0) / 102.0
    )
    assert results[StructureFeatureName.OPENING_RANGE_LOW_DISTANCE][2].value == pytest.approx(
        (102.5 - 99.0) / 99.0
    )
    assert results[StructureFeatureName.SWEEP_HIGH_FLAG][3].value == 1
    assert results[StructureFeatureName.SWEEP_LOW_FLAG][4].value == 1
    assert results[StructureFeatureName.FAILED_BREAKOUT_HIGH_FLAG][3].value == 1
    assert results[StructureFeatureName.FAILED_BREAKOUT_HIGH_FLAG][6].value == 1
    assert results[StructureFeatureName.FAILED_BREAKOUT_LOW_FLAG][9].value == 1
    assert results[StructureFeatureName.CLOSE_LOCATION_VALUE][0].value == pytest.approx(0.0)
    assert results[StructureFeatureName.WICK_REJECTION_SCORE][3].value == pytest.approx(-1 / 3)
    assert results[StructureFeatureName.RANGE_CONTRACTION][2].value == pytest.approx(3.0 / 2.5)
    assert results[StructureFeatureName.BBO_MID_DISTANCE][0].value == pytest.approx(0.0)
    assert results[StructureFeatureName.BBO_MID_DISTANCE][2].value == pytest.approx(
        (102.5 - 102.0) / 102.0
    )


def test_no_trade_rows_are_not_treated_as_trade_bars() -> None:
    views = _fixture_views()
    registry = EmptyRegistryReader()
    checked_features = (
        StructureFeatureName.PRIOR_HIGH_DISTANCE,
        StructureFeatureName.SWEEP_HIGH_FLAG,
        StructureFeatureName.CLOSE_LOCATION_VALUE,
        StructureFeatureName.WICK_REJECTION_SCORE,
        StructureFeatureName.RANGE_CONTRACTION,
        StructureFeatureName.BBO_MID_DISTANCE,
    )

    for feature in checked_features:
        definition = build_structure_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            window_length=2,
            reset_on_session=False,
        )
        records = compute_structure_feature(definition, views)

        assert records[7].value is None
        assert "no_trade" in records[7].quality_flags

    range_contraction = compute_structure_feature(
        build_structure_feature_definition(
            StructureFeatureName.RANGE_CONTRACTION,
            _approved_request(StructureFeatureName.RANGE_CONTRACTION),
            registry,
            window_length=2,
            reset_on_session=False,
        ),
        views,
    )
    assert range_contraction[8].value is None
    assert "input_gap" in range_contraction[8].quality_flags
    assert "no_trade" in range_contraction[8].quality_flags


def test_missing_and_quarantined_bbo_are_not_filled_for_structure_values() -> None:
    views = _fixture_views()
    definition = build_structure_feature_definition(
        StructureFeatureName.BBO_MID_DISTANCE,
        _approved_request(StructureFeatureName.BBO_MID_DISTANCE),
        EmptyRegistryReader(),
    )

    records = compute_structure_feature(definition, views)

    assert records[4].value is None
    assert "bbo_quarantined" in records[4].quality_flags
    assert records[8].value is None
    assert "missing_bbo" in records[8].quality_flags
    assert records[9].value == pytest.approx((99.5 - 99.0) / 99.0)


def test_bbo_derived_feature_requires_canonical_input_views() -> None:
    definition = build_structure_feature_definition(
        StructureFeatureName.BBO_MID_DISTANCE,
        _approved_request(StructureFeatureName.BBO_MID_DISTANCE),
        EmptyRegistryReader(),
    )

    with pytest.raises(StructureFeatureError, match="CanonicalInputViews"):
        compute_structure_feature(definition, _fixture_views().ohlcv)


def test_missing_available_ts_fails_closed() -> None:
    views = _fixture_views()
    corrupt_row = views.ohlcv.rows[0]
    object.__setattr__(corrupt_row, "available_ts", None)
    definition = build_structure_feature_definition(
        StructureFeatureName.CLOSE_LOCATION_VALUE,
        _approved_request(StructureFeatureName.CLOSE_LOCATION_VALUE),
        EmptyRegistryReader(),
    )

    with pytest.raises(StructureFeatureError, match="available_ts"):
        compute_structure_feature(definition, views)


def test_feature_request_gate_is_required_and_fail_closed() -> None:
    registry = EmptyRegistryReader()

    with pytest.raises(FeatureRequestGateError):
        build_structure_feature_definition(
            StructureFeatureName.SWEEP_HIGH_FLAG,
            None,
            registry,
        )

    with pytest.raises(FeatureRequestGateError):
        build_structure_feature_definition(
            StructureFeatureName.SWEEP_HIGH_FLAG,
            _request(StructureFeatureName.SWEEP_HIGH_FLAG, FeatureRequestApprovalStatus.PENDING),
            registry,
        )


@pytest.mark.parametrize(
    "window",
    [
        WindowSpec(
            kind=WindowKind.CENTERED,
            length=3,
            causality=WindowCausality.CENTERED,
            offline_only=True,
        ),
        WindowSpec(
            kind=WindowKind.FUTURE,
            length=2,
            causality=WindowCausality.FUTURE,
            offline_only=True,
        ),
    ],
)
def test_future_and_centered_live_windows_fail_closed(window: WindowSpec) -> None:
    with pytest.raises(FeatureContractError, match="live FeatureSpec"):
        build_structure_feature_definition(
            StructureFeatureName.RANGE_CONTRACTION,
            _approved_request(StructureFeatureName.RANGE_CONTRACTION),
            EmptyRegistryReader(),
            window=window,
        )


def _fixture_views() -> CanonicalInputViews:
    start = _dt("2024-01-02T14:30:00+00:00")
    ohlcv_rows = (
        _ohlcv_row(start, open_="100", high="101", low="99", close="100", volume="10"),
        _ohlcv_row(
            start + timedelta(minutes=1),
            open_="100",
            high="102",
            low="100",
            close="101",
            volume="10",
        ),
        _ohlcv_row(
            start + timedelta(minutes=2),
            open_="101",
            high="103",
            low="100",
            close="102.5",
            volume="10",
        ),
        _ohlcv_row(
            start + timedelta(minutes=3),
            open_="102.5",
            high="104",
            low="101",
            close="101.5",
            volume="10",
        ),
        _ohlcv_row(
            start + timedelta(minutes=4),
            open_="101.5",
            high="102",
            low="98",
            close="100",
            volume="10",
        ),
        _ohlcv_row(
            start + timedelta(minutes=5),
            open_="100",
            high="105",
            low="99",
            close="104.5",
            volume="10",
        ),
        _ohlcv_row(
            start + timedelta(minutes=6),
            open_="104.5",
            high="105",
            low="100",
            close="103",
            volume="10",
        ),
        _ohlcv_row(
            start + timedelta(minutes=7),
            open_="103",
            high="103",
            low="103",
            close="103",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _ohlcv_row(
            start + timedelta(minutes=8),
            open_="103",
            high="104",
            low="97",
            close="98.5",
            volume="10",
        ),
        _ohlcv_row(
            start + timedelta(minutes=9),
            open_="98.5",
            high="100",
            low="98",
            close="99.5",
            volume="10",
        ),
    )
    bbo_rows = (
        _bbo_row(start, bid="99", ask="101"),
        _bbo_row(start + timedelta(minutes=1), bid="100", ask="102"),
        _bbo_row(start + timedelta(minutes=2), bid="101", ask="103"),
        _bbo_row(start + timedelta(minutes=3), bid="101", ask="103"),
        _bbo_row(
            start + timedelta(minutes=4),
            bid="105",
            ask="104",
            mid="104.5",
            spread="-1",
            quality_flags=("bbo_quarantined",),
        ),
        _bbo_row(start + timedelta(minutes=5), bid="103", ask="105"),
        _bbo_row(start + timedelta(minutes=6), bid="103", ask="105"),
        _bbo_row(start + timedelta(minutes=7), bid="102", ask="104"),
        _bbo_row(
            start + timedelta(minutes=8),
            bid="0",
            ask="0",
            quality_flags=("missing_bbo",),
        ),
        _bbo_row(start + timedelta(minutes=9), bid="98", ask="100"),
    )
    return CanonicalInputViews(ohlcv=OHLCVInputView(ohlcv_rows), bbo=BBOInputView(bbo_rows))


def _ohlcv_row(
    bar_start_ts: datetime,
    *,
    open_: str,
    high: str,
    low: str,
    close: str,
    volume: str,
    quality_flags: tuple[str, ...] = (),
) -> OHLCVInputRow:
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        data_version="dsv_synthetic_structure",
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _bbo_row(
    bar_start_ts: datetime,
    *,
    bid: str,
    ask: str,
    mid: str | None = None,
    spread: str | None = None,
    quality_flags: tuple[str, ...] = (),
) -> BBOInputRow:
    bid_decimal = Decimal(bid)
    ask_decimal = Decimal(ask)
    mid_decimal = Decimal(mid) if mid is not None else (bid_decimal + ask_decimal) / Decimal("2")
    spread_decimal = Decimal(spread) if spread is not None else ask_decimal - bid_decimal
    return BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, microseconds=500_000),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        bid=bid_decimal,
        ask=ask_decimal,
        bid_size=Decimal("10"),
        ask_size=Decimal("10"),
        mid=mid_decimal,
        spread=spread_decimal,
        data_version="dsv_synthetic_structure",
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _approved_request(feature: StructureFeatureName) -> FeatureRequest:
    return _request(feature, FeatureRequestApprovalStatus.APPROVED)


def _request(
    feature: StructureFeatureName,
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    input_views = ["canonical_ohlcv"]
    if feature is StructureFeatureName.BBO_MID_DISTANCE:
        input_views.append("canonical_bbo")
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"liquidity_structure_{feature.value}"],
        formula_sketch={
            "exposure_family": f"liquidity_structure_{feature.value}",
            "inputs": input_views,
            "operation": feature.value,
            "window": 2,
        },
        availability_assumptions={
            "timing": "synthetic OHLCV/BBO fixture rows expose available_ts after bar end"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["open", "high", "low", "close", "quality_flags", "available_ts"],
            "source": "tiny synthetic canonical OHLCV/BBO fixture only",
        },
        approval_status=approval_status,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
