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
    CompressionFeatureSpec,
    OpeningRangeFeatureSpec,
    PriorExtremeFeatureSpec,
    StructureFeatureError,
    StructureFeatureName,
    StructureInputBundle,
    SweepFeatureSpec,
    WickFeatureSpec,
    build_structure_feature_definition,
    compute_structure_feature,
    compute_structure_features,
    supported_structure_features,
)
from alpha_system.features.input_views import (
    BBOInputRow,
    BBOInputView,
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
    bundle = _fixture_bundle()
    registry = EmptyRegistryReader()
    definitions = tuple(
        build_structure_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            dataset_version_ids=("dsv_synthetic_structure",),
            window_length=2,
            opening_range_minutes=2,
            reset_on_session=False,
        )
        for feature in supported_structure_features()
    )

    results = compute_structure_features(definitions, bundle)

    assert set(results) == set(StructureFeatureName)
    for definition in definitions:
        assert definition.spec.family is FeatureFamily.LIQUIDITY_STRUCTURE
        assert definition.spec.implementation_eligible is True
        assert definition.spec.feature_request_id.startswith("freq_")
        assert definition.version == definition.spec.derive_feature_version()
        assert definition.spec.window.is_live_compatible is True
        records = results[definition.name]
        assert len(records) == len(bundle.ohlcv.rows)
        assert all(record.feature_version_id == definition.feature_version_id for record in records)
        assert [record.available_ts for record in records] == [
            row.available_ts for row in bundle.ohlcv.rows
        ]

    assert isinstance(
        _definition(definitions, StructureFeatureName.PRIOR_HIGH_DISTANCE).spec,
        PriorExtremeFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE).spec,
        OpeningRangeFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, StructureFeatureName.SWEEP_HIGH_FLAG).spec,
        SweepFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, StructureFeatureName.CLOSE_LOCATION_VALUE).spec,
        WickFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, StructureFeatureName.RANGE_CONTRACTION).spec,
        CompressionFeatureSpec,
    )

    assert results[StructureFeatureName.PRIOR_HIGH_DISTANCE][2].value == pytest.approx(-1.0)
    assert results[StructureFeatureName.PRIOR_LOW_DISTANCE][2].value == pytest.approx(2.0)
    assert results[StructureFeatureName.OPENING_RANGE_HIGH_DISTANCE][1].value == pytest.approx(
        -0.5
    )
    assert results[StructureFeatureName.OPENING_RANGE_LOW_DISTANCE][2].value == pytest.approx(2.0)
    assert results[StructureFeatureName.SWEEP_HIGH_FLAG][3].value == 1
    assert results[StructureFeatureName.SWEEP_LOW_FLAG][4].value == 1
    assert results[StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG][3].value == 1
    assert results[StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG][4].value == 1
    assert results[StructureFeatureName.CLOSE_LOCATION_VALUE][3].value == pytest.approx(0.5)
    assert results[StructureFeatureName.WICK_REJECTION_SCORE][4].value == pytest.approx(0.5)
    assert results[StructureFeatureName.RANGE_CONTRACTION][5].value == pytest.approx(
        1.0 - 1.0 / 3.5
    )


def test_late_available_row_cannot_change_prior_structure_output() -> None:
    base = StructureInputBundle(OHLCVInputView(_late_available_rows(late_close="100")))
    changed_future = StructureInputBundle(OHLCVInputView(_late_available_rows(late_close="999")))
    definition = build_structure_feature_definition(
        StructureFeatureName.PRIOR_HIGH_DISTANCE,
        _approved_request(StructureFeatureName.PRIOR_HIGH_DISTANCE),
        EmptyRegistryReader(),
        window_length=2,
        reset_on_session=False,
    )

    base_records = compute_structure_feature(definition, base)
    changed_records = compute_structure_feature(definition, changed_future)

    assert base_records[2].available_ts == _dt("2024-01-02T14:34:01+00:00")
    assert base_records[2].value == changed_records[2].value
    assert base_records[2].value == pytest.approx(102 - 101)


def test_no_trade_rows_are_not_treated_as_trade_bars() -> None:
    bundle = _fixture_bundle()
    checked_features = (
        StructureFeatureName.PRIOR_HIGH_DISTANCE,
        StructureFeatureName.SWEEP_HIGH_FLAG,
        StructureFeatureName.CLOSE_LOCATION_VALUE,
        StructureFeatureName.RANGE_CONTRACTION,
    )

    for feature in checked_features:
        definition = build_structure_feature_definition(
            feature,
            _approved_request(feature),
            EmptyRegistryReader(),
            window_length=2,
            reset_on_session=False,
        )
        records = compute_structure_feature(definition, bundle)

        assert records[6].value is None
        assert "no_trade" in records[6].quality_flags
        if feature is not StructureFeatureName.CLOSE_LOCATION_VALUE:
            assert records[7].value is None
            assert "input_gap" in records[7].quality_flags
            assert "no_trade" in records[7].quality_flags


def test_exact_time_bbo_missingness_is_flagged_without_forward_fill() -> None:
    bundle = _fixture_bundle()
    definition = build_structure_feature_definition(
        StructureFeatureName.SWEEP_HIGH_FLAG,
        _approved_request(StructureFeatureName.SWEEP_HIGH_FLAG),
        EmptyRegistryReader(),
        window_length=2,
        reset_on_session=False,
    )

    records = compute_structure_feature(definition, bundle)

    assert records[3].value == 1
    assert "missing_bbo" in records[3].quality_flags
    assert "bbo_gap" in records[3].quality_flags
    assert records[4].value == 0
    assert "bbo_quarantined" in records[4].quality_flags
    assert "bbo_gap" not in records[5].quality_flags
    assert "missing_bbo" not in records[5].quality_flags
    assert "bbo_quarantined" not in records[5].quality_flags


def test_missing_available_ts_fails_closed() -> None:
    bundle = _fixture_bundle()
    corrupt_row = bundle.ohlcv.rows[0]
    object.__setattr__(corrupt_row, "available_ts", None)
    definition = build_structure_feature_definition(
        StructureFeatureName.CLOSE_LOCATION_VALUE,
        _approved_request(StructureFeatureName.CLOSE_LOCATION_VALUE),
        EmptyRegistryReader(),
    )

    with pytest.raises(StructureFeatureError, match="available_ts"):
        compute_structure_feature(definition, bundle)


def test_feature_request_gate_is_required_and_fail_closed() -> None:
    registry = EmptyRegistryReader()

    with pytest.raises(FeatureRequestGateError):
        build_structure_feature_definition(
            StructureFeatureName.PRIOR_HIGH_DISTANCE,
            None,
            registry,
        )

    with pytest.raises(FeatureRequestGateError):
        build_structure_feature_definition(
            StructureFeatureName.PRIOR_HIGH_DISTANCE,
            _request(
                StructureFeatureName.PRIOR_HIGH_DISTANCE,
                FeatureRequestApprovalStatus.PENDING,
            ),
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
            StructureFeatureName.SWEEP_HIGH_FLAG,
            _approved_request(StructureFeatureName.SWEEP_HIGH_FLAG),
            EmptyRegistryReader(),
            window=window,
        )


def _definition(
    definitions: tuple[object, ...],
    name: StructureFeatureName,
) -> object:
    for definition in definitions:
        if getattr(definition, "name") is name:
            return definition
    raise AssertionError(f"missing definition for {name}")


def _fixture_bundle() -> StructureInputBundle:
    start = _dt("2024-01-02T14:30:00+00:00")
    ohlcv_rows = (
        _ohlcv_row(start, open_="100", high="101", low="99", close="100"),
        _ohlcv_row(start + timedelta(minutes=1), open_="100", high="102", low="100", close="101.5"),
        _ohlcv_row(
            start + timedelta(minutes=2),
            open_="101.5",
            high="101.8",
            low="100.5",
            close="101",
        ),
        _ohlcv_row(start + timedelta(minutes=3), open_="101", high="103", low="100", close="101.5"),
        _ohlcv_row(
            start + timedelta(minutes=4),
            open_="101.5",
            high="102",
            low="98",
            close="100.5",
        ),
        _ohlcv_row(
            start + timedelta(minutes=5),
            open_="100.5",
            high="101.5",
            low="100.5",
            close="101",
        ),
        _ohlcv_row(
            start + timedelta(minutes=6),
            open_="101",
            high="101",
            low="101",
            close="101",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _ohlcv_row(start + timedelta(minutes=7), open_="101", high="102", low="100", close="101"),
    )
    bbo_rows = (
        _bbo_row(start + timedelta(minutes=3), quality_flags=("missing_bbo",)),
        _bbo_row(
            start + timedelta(minutes=4),
            bid="102",
            ask="101",
            quality_flags=("bbo_quarantined",),
        ),
    )
    return StructureInputBundle(OHLCVInputView(ohlcv_rows), BBOInputView(bbo_rows))


def _late_available_rows(*, late_close: str) -> tuple[OHLCVInputRow, ...]:
    start = _dt("2024-01-02T14:30:00+00:00")
    return (
        _ohlcv_row(start, high="100", low="99", close="99.5"),
        _ohlcv_row(start + timedelta(minutes=1), high="101", low="100", close="100.5"),
        _ohlcv_row(start + timedelta(minutes=3), high="103", low="101", close="102"),
        _ohlcv_row(
            start + timedelta(minutes=2),
            high="1000",
            low="98",
            close=late_close,
            available_ts=_dt("2024-01-02T14:40:00+00:00"),
        ),
    )


def _ohlcv_row(
    bar_start_ts: datetime,
    *,
    open_: str | None = None,
    high: str,
    low: str,
    close: str,
    volume: str = "10",
    quality_flags: tuple[str, ...] = (),
    available_ts: datetime | None = None,
) -> OHLCVInputRow:
    close_decimal = Decimal(close)
    high_decimal = Decimal(high)
    low_decimal = Decimal(low)
    open_decimal = Decimal(open_) if open_ is not None else close_decimal
    available = available_ts or bar_start_ts + timedelta(minutes=1, seconds=1)
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=available,
        ingested_at=available + timedelta(seconds=1),
        open=open_decimal,
        high=high_decimal,
        low=low_decimal,
        close=close_decimal,
        volume=Decimal(volume),
        data_version="dsv_synthetic_structure",
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _bbo_row(
    matching_bar_start_ts: datetime,
    *,
    bid: str = "99",
    ask: str = "101",
    quality_flags: tuple[str, ...] = (),
) -> BBOInputRow:
    bid_decimal = Decimal(bid)
    ask_decimal = Decimal(ask)
    mid = (bid_decimal + ask_decimal) / Decimal("2")
    available_ts = matching_bar_start_ts + timedelta(minutes=1, seconds=1)
    return BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=matching_bar_start_ts,
        bar_end_ts=matching_bar_start_ts + timedelta(minutes=1),
        event_ts=matching_bar_start_ts + timedelta(minutes=1),
        available_ts=available_ts,
        ingested_at=available_ts + timedelta(seconds=1),
        bid=bid_decimal,
        ask=ask_decimal,
        bid_size=Decimal("0") if quality_flags else Decimal("10"),
        ask_size=Decimal("0") if quality_flags else Decimal("10"),
        mid=mid,
        spread=ask_decimal - bid_decimal,
        data_version="dsv_synthetic_structure",
        quality_flags=quality_flags,
        session_label="RTH",
        spread_ticks=None,
        microprice=None,
    )


def _approved_request(feature: StructureFeatureName) -> FeatureRequest:
    return _request(feature, FeatureRequestApprovalStatus.APPROVED)


def _request(
    feature: StructureFeatureName,
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"liquidity_structure_{feature.value}"],
        formula_sketch={
            "exposure_family": f"liquidity_structure_{feature.value}",
            "inputs": ["canonical_ohlcv", "canonical_bbo"],
            "operation": feature.value,
            "window": 2,
        },
        availability_assumptions={
            "timing": "synthetic structure fixture rows expose available_ts after bar end"
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
