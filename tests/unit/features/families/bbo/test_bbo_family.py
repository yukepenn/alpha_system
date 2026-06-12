from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from alpha_system.features.contracts import (
    FeatureContractError,
    FeatureFamily,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.families.bbo import (
    BBOFeatureError,
    BBOFeatureName,
    LiquidityQualityFeatureSpec,
    MicropriceFeatureSpec,
    SpreadFeatureSpec,
    TopBookImbalanceFeatureSpec,
    build_bbo_feature_definition,
    compute_bbo_feature,
    compute_bbo_features,
    supported_bbo_features,
)
from alpha_system.features.input_views import BBOInputRow, BBOInputView
from alpha_system.features.request_gate import FeatureRequestGateError
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.runtime.input_resolver import _reject_label_as_live_feature

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_all_bbo_features_are_gated_versioned_causal_and_available() -> None:
    view = _fixture_view()
    registry = EmptyRegistryReader()
    definitions = tuple(
        build_bbo_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            dataset_version_ids=("dsv_synthetic_bbo",),
            window_length=2,
            wide_spread_bps_threshold=300.0,
            low_depth_threshold=1.0,
            reset_on_session=False,
        )
        for feature in supported_bbo_features()
    )

    results = compute_bbo_features(definitions, view)

    assert any(row.event_ts != row.bar_end_ts for row in view.rows)
    assert set(results) == set(BBOFeatureName)
    for definition in definitions:
        assert definition.spec.family is FeatureFamily.BBO_TRADABILITY
        assert definition.spec.implementation_eligible is True
        assert definition.spec.feature_request_id.startswith("freq_")
        assert definition.version == definition.spec.derive_feature_version()
        assert definition.spec.window.is_live_compatible is True
        records = results[definition.name]
        assert len(records) == len(view.rows)
        assert all(record.feature_version_id == definition.feature_version_id for record in records)
        assert [record.event_ts for record in records] == [row.bar_end_ts for row in view.rows]
        assert [record.available_ts for record in records] == [
            row.available_ts for row in view.rows
        ]

    assert isinstance(_definition(definitions, BBOFeatureName.SPREAD).spec, SpreadFeatureSpec)
    assert isinstance(
        _definition(definitions, BBOFeatureName.MICROPRICE).spec,
        MicropriceFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, BBOFeatureName.TOP_BOOK_IMBALANCE).spec,
        TopBookImbalanceFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, BBOFeatureName.BAD_QUOTE_FLAG).spec,
        LiquidityQualityFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, BBOFeatureName.WIDE_SPREAD_FLAG).spec,
        LiquidityQualityFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, BBOFeatureName.LOW_DEPTH_FLAG).spec,
        LiquidityQualityFeatureSpec,
    )

    assert results[BBOFeatureName.MID][0].value == pytest.approx(100.0)
    assert results[BBOFeatureName.SPREAD][2].value == pytest.approx(4.0)
    assert results[BBOFeatureName.SPREAD_TICKS][2].value == pytest.approx(16.0)
    assert results[BBOFeatureName.SPREAD_BPS][0].value == pytest.approx(200.0)
    assert results[BBOFeatureName.SPREAD_BPS][2].value == pytest.approx(4 / 102 * 10_000)
    assert results[BBOFeatureName.SPREAD_ZSCORE][2].value == pytest.approx(1.0)
    assert results[BBOFeatureName.BID_SIZE][1].value == pytest.approx(30.0)
    assert results[BBOFeatureName.ASK_SIZE][1].value == pytest.approx(10.0)
    assert results[BBOFeatureName.TOP_BOOK_DEPTH][0].value == pytest.approx(40.0)
    assert results[BBOFeatureName.TOP_BOOK_IMBALANCE][0].value == pytest.approx(-0.5)
    assert results[BBOFeatureName.MICROPRICE][0].value == pytest.approx(99.5)
    assert results[BBOFeatureName.MICROPRICE_MINUS_MID][1].value == pytest.approx(0.5)
    assert results[BBOFeatureName.WIDE_SPREAD_FLAG][0].value == 0
    assert results[BBOFeatureName.WIDE_SPREAD_FLAG][2].value == 1
    assert results[BBOFeatureName.TOP_BOOK_DEPTH][5].value == pytest.approx(0.0)
    assert results[BBOFeatureName.LOW_DEPTH_FLAG][5].value == 1


def test_missing_and_quarantined_bbo_are_not_filled_or_used_as_quotes() -> None:
    view = _fixture_view()
    registry = EmptyRegistryReader()
    checked_features = (
        BBOFeatureName.MID,
        BBOFeatureName.SPREAD,
        BBOFeatureName.SPREAD_BPS,
        BBOFeatureName.SPREAD_ZSCORE,
        BBOFeatureName.MICROPRICE,
        BBOFeatureName.TOP_BOOK_IMBALANCE,
        BBOFeatureName.WIDE_SPREAD_FLAG,
    )

    for feature in checked_features:
        definition = build_bbo_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            window_length=2,
            wide_spread_bps_threshold=300.0,
            reset_on_session=False,
        )
        records = compute_bbo_feature(definition, view)

        assert records[3].value is None
        assert "missing_bbo" in records[3].quality_flags
        assert records[4].value is None
        assert "bbo_quarantined" in records[4].quality_flags

    spread_zscore = compute_bbo_feature(
        build_bbo_feature_definition(
            BBOFeatureName.SPREAD_ZSCORE,
            _approved_request(BBOFeatureName.SPREAD_ZSCORE),
            registry,
            window_length=2,
            reset_on_session=False,
        ),
        view,
    )
    assert spread_zscore[5].value is None
    assert "input_gap" in spread_zscore[5].quality_flags
    assert "bbo_quarantined" in spread_zscore[5].quality_flags


def test_bbo_quality_flags_are_derived_from_canonical_tokens_only() -> None:
    view = _fixture_view()
    registry = EmptyRegistryReader()
    missing_definition = build_bbo_feature_definition(
        BBOFeatureName.MISSING_BBO_FLAG,
        _approved_request(BBOFeatureName.MISSING_BBO_FLAG),
        registry,
    )
    bad_definition = build_bbo_feature_definition(
        BBOFeatureName.BAD_QUOTE_FLAG,
        _approved_request(BBOFeatureName.BAD_QUOTE_FLAG),
        registry,
    )

    missing = compute_bbo_feature(missing_definition, view)
    bad = compute_bbo_feature(bad_definition, view)

    assert "bad_quote_flag" not in bad_definition.spec.inputs.fields
    assert missing[3].value == 1
    assert missing[4].value == 0
    assert bad[3].value == 1
    assert bad[4].value == 1
    assert bad[5].value == 0


def test_microprice_requires_valid_bid_and_ask_sizes() -> None:
    view = _fixture_view()
    definition = build_bbo_feature_definition(
        BBOFeatureName.MICROPRICE,
        _approved_request(BBOFeatureName.MICROPRICE),
        EmptyRegistryReader(),
    )

    records = compute_bbo_feature(definition, view)

    assert records[5].value is None
    assert "invalid_bbo_size" in records[5].quality_flags


def test_spread_zscore_contract_declares_session_metadata_and_truth() -> None:
    definition = build_bbo_feature_definition(
        BBOFeatureName.SPREAD_ZSCORE,
        _approved_request(BBOFeatureName.SPREAD_ZSCORE),
        EmptyRegistryReader(),
        window_length=2,
        reset_on_session=True,
    )

    metadata = definition.spec.inputs.input_metadata.to_dict()
    parameters = definition.spec.transform.parameters.to_dict()

    assert metadata["field_roles"]["session_label"] == "SESSION_METADATA"
    assert parameters["session_template_id"] == "session_cme_index_futures_eth"
    assert parameters["session_timezone"] == "America/Chicago"
    assert parameters["rth_open_time_local"] == "08:30"
    assert parameters["rth_close_time_local"] == "15:00"
    assert parameters["session_truth_source"] == "alpha_system.data.foundation.sessions"

    _reject_label_as_live_feature(
        SimpleNamespace(feature_spec=definition.spec.feature_spec),
        field="feature_pack_refs[0]",
    )


def test_spread_zscore_reset_uses_timestamp_truth_when_session_label_is_static() -> None:
    rows = (
        _row(
            _dt("2024-01-02T20:58:00+00:00"),
            bid="99",
            ask="101",
            bid_size="10",
            ask_size="10",
        ),
        _row(
            _dt("2024-01-02T20:59:00+00:00"),
            bid="98",
            ask="102",
            bid_size="10",
            ask_size="10",
        ),
        _row(
            _dt("2024-01-02T21:00:00+00:00"),
            bid="97",
            ask="103",
            bid_size="10",
            ask_size="10",
        ),
    )
    view = BBOInputView(tuple(_replace_session_label(row, "RTH") for row in rows))
    definition = build_bbo_feature_definition(
        BBOFeatureName.SPREAD_ZSCORE,
        _approved_request(BBOFeatureName.SPREAD_ZSCORE),
        EmptyRegistryReader(),
        window_length=2,
        reset_on_session=True,
    )

    records = compute_bbo_feature(definition, view)

    assert records[1].value is not None
    assert records[2].value is None
    assert records[2].quality_flags == ("insufficient_window", "primitive_gap")


def test_missing_available_ts_fails_closed() -> None:
    view = _fixture_view()
    corrupt_row = view.rows[0]
    object.__setattr__(corrupt_row, "available_ts", None)
    definition = build_bbo_feature_definition(
        BBOFeatureName.SPREAD,
        _approved_request(BBOFeatureName.SPREAD),
        EmptyRegistryReader(),
    )

    with pytest.raises(BBOFeatureError, match="available_ts"):
        compute_bbo_feature(definition, view)


def test_feature_request_gate_is_required_and_fail_closed() -> None:
    registry = EmptyRegistryReader()

    with pytest.raises(FeatureRequestGateError):
        build_bbo_feature_definition(BBOFeatureName.SPREAD, None, registry)

    with pytest.raises(FeatureRequestGateError):
        build_bbo_feature_definition(
            BBOFeatureName.SPREAD,
            _request(BBOFeatureName.SPREAD, FeatureRequestApprovalStatus.PENDING),
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
        build_bbo_feature_definition(
            BBOFeatureName.SPREAD_ZSCORE,
            _approved_request(BBOFeatureName.SPREAD_ZSCORE),
            EmptyRegistryReader(),
            window=window,
        )


def _definition(definitions: tuple[object, ...], name: BBOFeatureName) -> object:
    for definition in definitions:
        if getattr(definition, "name") is name:
            return definition
    raise AssertionError(f"missing definition for {name}")


def _fixture_view() -> BBOInputView:
    start = _dt("2024-01-02T14:30:00+00:00")
    rows = (
        _row(start, bid="99", ask="101", bid_size="10", ask_size="30", spread_ticks="8"),
        _row(
            start + timedelta(minutes=1),
            bid="100",
            ask="102",
            bid_size="30",
            ask_size="10",
            spread_ticks="8",
        ),
        _row(
            start + timedelta(minutes=2),
            bid="100",
            ask="104",
            bid_size="20",
            ask_size="20",
            spread_ticks="16",
        ),
        _row(
            start + timedelta(minutes=3),
            bid="0",
            ask="0",
            bid_size="0",
            ask_size="0",
            quality_flags=("missing_bbo",),
        ),
        _row(
            start + timedelta(minutes=4),
            bid="105",
            ask="104",
            bid_size="10",
            ask_size="10",
            mid="104.5",
            spread="-1",
            quality_flags=("bbo_quarantined",),
        ),
        _row(
            start + timedelta(minutes=5),
            bid="101",
            ask="102",
            bid_size="0",
            ask_size="0",
            spread_ticks="4",
        ),
    )
    return BBOInputView(rows)


def _row(
    bar_start_ts: datetime,
    *,
    bid: str,
    ask: str,
    bid_size: str,
    ask_size: str,
    mid: str | None = None,
    spread: str | None = None,
    spread_ticks: str | None = None,
    quality_flags: tuple[str, ...] = (),
) -> BBOInputRow:
    bid_decimal = Decimal(bid)
    ask_decimal = Decimal(ask)
    bid_size_decimal = Decimal(bid_size)
    ask_size_decimal = Decimal(ask_size)
    mid_decimal = Decimal(mid) if mid is not None else (bid_decimal + ask_decimal) / Decimal("2")
    spread_decimal = Decimal(spread) if spread is not None else ask_decimal - bid_decimal
    microprice = None
    if bid_size_decimal > 0 and ask_size_decimal > 0 and ask_decimal >= bid_decimal:
        microprice = (
            ask_decimal * bid_size_decimal + bid_decimal * ask_size_decimal
        ) / (bid_size_decimal + ask_size_decimal)
    return BBOInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(seconds=59, milliseconds=800),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        bid=bid_decimal,
        ask=ask_decimal,
        bid_size=bid_size_decimal,
        ask_size=ask_size_decimal,
        mid=mid_decimal,
        spread=spread_decimal,
        data_version="dsv_synthetic_bbo",
        quality_flags=quality_flags,
        session_label="RTH",
        spread_ticks=Decimal(spread_ticks) if spread_ticks is not None else None,
        microprice=microprice,
    )


def _replace_session_label(row: BBOInputRow, session_label: str) -> BBOInputRow:
    return BBOInputRow(
        instrument_id=row.instrument_id,
        contract_id=row.contract_id,
        series_id=row.series_id,
        bar_start_ts=row.bar_start_ts,
        bar_end_ts=row.bar_end_ts,
        event_ts=row.event_ts,
        available_ts=row.available_ts,
        ingested_at=row.ingested_at,
        bid=row.bid,
        ask=row.ask,
        bid_size=row.bid_size,
        ask_size=row.ask_size,
        mid=row.mid,
        spread=row.spread,
        data_version=row.data_version,
        quality_flags=row.quality_flags,
        session_label=session_label,
        spread_ticks=row.spread_ticks,
        microprice=row.microprice,
        bid_order_count=row.bid_order_count,
        ask_order_count=row.ask_order_count,
    )


def _approved_request(feature: BBOFeatureName) -> FeatureRequest:
    return _request(feature, FeatureRequestApprovalStatus.APPROVED)


def _request(
    feature: BBOFeatureName,
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"bbo_tradability_{feature.value}"],
        formula_sketch={
            "exposure_family": f"bbo_tradability_{feature.value}",
            "inputs": ["canonical_bbo"],
            "operation": feature.value,
            "window": 2,
        },
        availability_assumptions={
            "timing": "synthetic BBO fixture rows expose available_ts after bar end"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["bid", "ask", "bid_size", "ask_size", "quality_flags", "available_ts"],
            "source": "tiny synthetic canonical BBO fixture only",
        },
        approval_status=approval_status,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
