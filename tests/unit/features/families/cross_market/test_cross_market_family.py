from __future__ import annotations

import math
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
from alpha_system.features.families.cross_market import (
    CrossMarketFeatureError,
    CrossMarketFeatureName,
    CrossMarketFlagFeatureSpec,
    CrossMarketInputBundle,
    CrossMarketReturnFeatureSpec,
    CrossMarketRollingFeatureSpec,
    CrossMarketRotationFeatureSpec,
    align_cross_market_rows,
    build_cross_market_feature_definition,
    compute_cross_market_feature,
    compute_cross_market_features,
    supported_cross_market_features,
)
from alpha_system.features.input_views import BBOInputRow, BBOInputView, OHLCVInputRow, OHLCVInputView
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


def test_all_cross_market_features_are_gated_versioned_causal_and_available() -> None:
    bundle = _fixture_bundle()
    registry = EmptyRegistryReader()
    definitions = tuple(
        build_cross_market_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            dataset_version_ids=(
                "dsv_synthetic_es",
                "dsv_synthetic_nq",
                "dsv_synthetic_rty",
            ),
            window_length=2,
            reset_on_session=False,
        )
        for feature in supported_cross_market_features()
    )

    results = compute_cross_market_features(definitions, bundle)
    snapshots = align_cross_market_rows(bundle, reset_on_session=False)

    assert set(results) == set(CrossMarketFeatureName)
    for definition in definitions:
        assert definition.spec.family is FeatureFamily.CROSS_MARKET
        assert definition.spec.implementation_eligible is True
        assert definition.spec.feature_request_id.startswith("freq_")
        assert definition.version == definition.spec.derive_feature_version()
        assert definition.spec.window.is_live_compatible is True
        records = results[definition.name]
        assert len(records) == len(snapshots)
        assert all(record.feature_version_id == definition.feature_version_id for record in records)
        assert [record.available_ts for record in records] == [
            snapshot.available_ts for snapshot in snapshots
        ]

    assert isinstance(
        _definition(definitions, CrossMarketFeatureName.SYNCHRONIZED_RETURNS).spec,
        CrossMarketReturnFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION).spec,
        CrossMarketRollingFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, CrossMarketFeatureName.CONFIRMATION_FLAG).spec,
        CrossMarketFlagFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, CrossMarketFeatureName.RISK_ON_ROTATION_PROXY).spec,
        CrossMarketRotationFeatureSpec,
    )

    synchronized = results[CrossMarketFeatureName.SYNCHRONIZED_RETURNS]
    assert synchronized[1].to_dict()["value"] == pytest.approx(
        {"ES": 0.02, "NQ": 0.03, "RTY": 0.02}
    )
    assert results[CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD][1].value == pytest.approx(
        0.01
    )
    assert results[CrossMarketFeatureName.RTY_MINUS_ES_RETURN_SPREAD][1].value == pytest.approx(
        0.0
    )
    assert results[CrossMarketFeatureName.CONFIRMATION_FLAG][1].value == 1
    assert results[CrossMarketFeatureName.DIVERGENCE_FLAG][1].value == 0
    assert results[CrossMarketFeatureName.RISK_ON_ROTATION_PROXY][1].value == pytest.approx(
        0.005
    )
    assert results[CrossMarketFeatureName.RISK_OFF_ROTATION_PROXY][1].value == pytest.approx(
        -0.005
    )
    assert results[CrossMarketFeatureName.DIVERGENCE_FLAG][2].value == 1
    assert results[CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION][2].value == pytest.approx(
        1.0
    )
    assert results[CrossMarketFeatureName.NQ_ES_ROLLING_BETA_RESIDUAL][2].value is not None


def test_late_available_instrument_row_cannot_change_prior_cross_market_output() -> None:
    base_bundle = _late_nq_bundle(late_nq_close="206")
    changed_future_bundle = _late_nq_bundle(late_nq_close="999")
    target_available_ts = _dt("2024-01-02T14:32:01+00:00")

    base_snapshot = _snapshot_at(
        align_cross_market_rows(base_bundle, reset_on_session=False),
        target_available_ts,
    )
    changed_snapshot = _snapshot_at(
        align_cross_market_rows(changed_future_bundle, reset_on_session=False),
        target_available_ts,
    )

    assert base_snapshot.returns["NQ"] == changed_snapshot.returns["NQ"]
    assert base_snapshot.returns["NQ"] == pytest.approx(201 / 200 - 1)
    assert all(
        source_ts <= base_snapshot.available_ts
        for timestamps in base_snapshot.source_available_ts.values()
        for source_ts in timestamps
    )


def test_no_trade_rows_are_not_treated_as_trade_bars() -> None:
    bundle = _fixture_bundle()
    definition = build_cross_market_feature_definition(
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        _approved_request(CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD),
        EmptyRegistryReader(),
        reset_on_session=False,
    )

    records = compute_cross_market_feature(definition, bundle)

    assert records[-1].value is None
    assert "no_trade" in records[-1].quality_flags
    assert "es_return_gap" in records[-1].quality_flags


def test_exact_time_missing_bbo_is_flagged_without_forward_fill() -> None:
    bundle = _fixture_bundle(
        bbo_by_instrument={
            "ES": BBOInputView((_bbo_row("ES", _dt("2024-01-02T14:32:01+00:00")),)),
            "NQ": BBOInputView(
                (
                    _bbo_row(
                        "NQ",
                        _dt("2024-01-02T14:32:01+00:00"),
                        quality_flags=("missing_bbo",),
                    ),
                )
            ),
            "RTY": BBOInputView((_bbo_row("RTY", _dt("2024-01-02T14:32:01+00:00")),)),
        }
    )
    definition = build_cross_market_feature_definition(
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        _approved_request(CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD),
        EmptyRegistryReader(),
        reset_on_session=False,
    )

    records = compute_cross_market_feature(definition, bundle)

    assert records[1].value == pytest.approx(0.01)
    assert "missing_bbo" in records[1].quality_flags
    assert "nq_bbo_gap" in records[1].quality_flags
    assert "missing_bbo" not in records[2].quality_flags


def test_cross_market_contract_declares_session_metadata_and_truth() -> None:
    definition = build_cross_market_feature_definition(
        CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD,
        _approved_request(CrossMarketFeatureName.NQ_MINUS_ES_RETURN_SPREAD),
        EmptyRegistryReader(),
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


def test_cross_market_return_reset_uses_timestamp_truth_when_session_label_is_static() -> None:
    start = _dt("2024-01-02T20:58:00+00:00")
    bundle = CrossMarketInputBundle(
        {
            market: OHLCVInputView(
                (
                    _ohlcv_row(market, start, close=base),
                    _ohlcv_row(market, start + timedelta(minutes=1), close=str(int(base) + 1)),
                    _ohlcv_row(market, start + timedelta(minutes=2), close=str(int(base) + 2)),
                )
            )
            for market, base in {"ES": "100", "NQ": "200", "RTY": "50"}.items()
        }
    )
    definition = build_cross_market_feature_definition(
        CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
        _approved_request(CrossMarketFeatureName.SYNCHRONIZED_RETURNS),
        EmptyRegistryReader(),
        reset_on_session=True,
    )

    snapshots = align_cross_market_rows(bundle, reset_on_session=True)
    records = compute_cross_market_feature(definition, bundle)

    assert [snapshot.session_label for snapshot in snapshots] == ["RTH", "RTH", "ETH"]
    assert records[1].value is not None
    assert records[2].value is None
    assert "session_reset" in records[2].quality_flags


def test_mixed_dataset_version_families_fail_closed() -> None:
    with pytest.raises(CrossMarketFeatureError, match="DatasetVersion families"):
        _fixture_bundle(
            data_versions={
                "ES": "family_a:es",
                "NQ": "family_b:nq",
                "RTY": "family_a:rty",
            }
        )


def test_missing_available_ts_fails_closed() -> None:
    bundle = _fixture_bundle()
    corrupt_row = bundle.ohlcv_by_instrument["ES"].rows[0]
    object.__setattr__(corrupt_row, "available_ts", None)

    with pytest.raises(CrossMarketFeatureError, match="available_ts"):
        align_cross_market_rows(bundle)


def test_feature_request_gate_is_required_and_fail_closed() -> None:
    registry = EmptyRegistryReader()

    with pytest.raises(FeatureRequestGateError):
        build_cross_market_feature_definition(
            CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
            None,
            registry,
        )

    with pytest.raises(FeatureRequestGateError):
        build_cross_market_feature_definition(
            CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
            _request(
                CrossMarketFeatureName.SYNCHRONIZED_RETURNS,
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
        build_cross_market_feature_definition(
            CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION,
            _approved_request(CrossMarketFeatureName.NQ_ES_ROLLING_CORRELATION),
            EmptyRegistryReader(),
            window=window,
        )


def _definition(
    definitions: tuple[object, ...],
    name: CrossMarketFeatureName,
) -> object:
    for definition in definitions:
        if getattr(definition, "name") is name:
            return definition
    raise AssertionError(f"missing definition for {name}")


def _fixture_bundle(
    *,
    bbo_by_instrument: dict[str, BBOInputView] | None = None,
    data_versions: dict[str, str] | None = None,
) -> CrossMarketInputBundle:
    data_versions = data_versions or {}
    start = _dt("2024-01-02T14:30:00+00:00")
    rows = {
        "ES": (
            _ohlcv_row("ES", start, close="100", data_version=data_versions.get("ES")),
            _ohlcv_row("ES", start + timedelta(minutes=1), close="102", data_version=data_versions.get("ES")),
            _ohlcv_row("ES", start + timedelta(minutes=2), close="101", data_version=data_versions.get("ES")),
            _ohlcv_row("ES", start + timedelta(minutes=3), close="104", data_version=data_versions.get("ES")),
            _ohlcv_row(
                "ES",
                start + timedelta(minutes=4),
                close="104",
                quality_flags=("no_trade",),
                data_version=data_versions.get("ES"),
            ),
        ),
        "NQ": (
            _ohlcv_row("NQ", start, close="200", data_version=data_versions.get("NQ")),
            _ohlcv_row("NQ", start + timedelta(minutes=1), close="206", data_version=data_versions.get("NQ")),
            _ohlcv_row("NQ", start + timedelta(minutes=2), close="203", data_version=data_versions.get("NQ")),
            _ohlcv_row("NQ", start + timedelta(minutes=3), close="209", data_version=data_versions.get("NQ")),
            _ohlcv_row("NQ", start + timedelta(minutes=4), close="211", data_version=data_versions.get("NQ")),
        ),
        "RTY": (
            _ohlcv_row("RTY", start, close="50", data_version=data_versions.get("RTY")),
            _ohlcv_row("RTY", start + timedelta(minutes=1), close="51", data_version=data_versions.get("RTY")),
            _ohlcv_row("RTY", start + timedelta(minutes=2), close="52", data_version=data_versions.get("RTY")),
            _ohlcv_row("RTY", start + timedelta(minutes=3), close="51", data_version=data_versions.get("RTY")),
            _ohlcv_row("RTY", start + timedelta(minutes=4), close="53", data_version=data_versions.get("RTY")),
        ),
    }
    return CrossMarketInputBundle(
        {market: OHLCVInputView(market_rows) for market, market_rows in rows.items()},
        bbo_by_instrument,
    )


def _late_nq_bundle(*, late_nq_close: str) -> CrossMarketInputBundle:
    start = _dt("2024-01-02T14:30:00+00:00")
    return CrossMarketInputBundle(
        {
            "ES": OHLCVInputView(
                (
                    _ohlcv_row("ES", start, close="100"),
                    _ohlcv_row("ES", start + timedelta(minutes=1), close="102"),
                )
            ),
            "NQ": OHLCVInputView(
                (
                    _ohlcv_row("NQ", start, close="200"),
                    _ohlcv_row(
                        "NQ",
                        start + timedelta(seconds=29),
                        close="201",
                        available_ts=_dt("2024-01-02T14:31:30+00:00"),
                    ),
                    _ohlcv_row(
                        "NQ",
                        start + timedelta(minutes=1),
                        close=late_nq_close,
                        available_ts=_dt("2024-01-02T14:40:00+00:00"),
                    ),
                )
            ),
            "RTY": OHLCVInputView(
                (
                    _ohlcv_row("RTY", start, close="50"),
                    _ohlcv_row("RTY", start + timedelta(minutes=1), close="51"),
                )
            ),
        }
    )


def _snapshot_at(
    snapshots: tuple[object, ...],
    available_ts: datetime,
) -> object:
    for snapshot in snapshots:
        if getattr(snapshot, "available_ts") == available_ts:
            return snapshot
    raise AssertionError(f"missing snapshot at {available_ts.isoformat()}")


def _ohlcv_row(
    market: str,
    bar_start_ts: datetime,
    *,
    close: str,
    available_ts: datetime | None = None,
    quality_flags: tuple[str, ...] = (),
    data_version: str | None = None,
) -> OHLCVInputRow:
    close_decimal = Decimal(close)
    available = available_ts or bar_start_ts + timedelta(minutes=1, seconds=1)
    return OHLCVInputRow(
        instrument_id=market,
        contract_id=f"{market}M4",
        series_id=f"{market}.c.0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=available,
        ingested_at=available + timedelta(seconds=1),
        open=close_decimal,
        high=close_decimal,
        low=close_decimal,
        close=close_decimal,
        volume=Decimal("0") if "no_trade" in quality_flags else Decimal("10"),
        data_version=data_version or "dsv_synthetic_cross_market",
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _bbo_row(
    market: str,
    available_ts: datetime,
    *,
    quality_flags: tuple[str, ...] = (),
) -> BBOInputRow:
    bid = Decimal("0") if quality_flags else Decimal("99")
    ask = Decimal("0") if quality_flags else Decimal("101")
    mid = (bid + ask) / Decimal("2")
    spread = ask - bid
    return BBOInputRow(
        instrument_id=market,
        contract_id=f"{market}M4",
        series_id=f"{market}.c.0",
        bar_start_ts=available_ts - timedelta(minutes=1, seconds=1),
        bar_end_ts=available_ts - timedelta(seconds=1),
        event_ts=available_ts - timedelta(seconds=1),
        available_ts=available_ts,
        ingested_at=available_ts + timedelta(seconds=1),
        bid=bid,
        ask=ask,
        bid_size=Decimal("0") if quality_flags else Decimal("10"),
        ask_size=Decimal("0") if quality_flags else Decimal("10"),
        mid=mid,
        spread=spread,
        data_version="dsv_synthetic_cross_market",
        quality_flags=quality_flags,
        session_label="RTH",
        spread_ticks=None,
        microprice=None,
    )


def _approved_request(feature: CrossMarketFeatureName) -> FeatureRequest:
    return _request(feature, FeatureRequestApprovalStatus.APPROVED)


def _request(
    feature: CrossMarketFeatureName,
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"cross_market_{feature.value}"],
        formula_sketch={
            "exposure_family": f"cross_market_{feature.value}",
            "inputs": ["canonical_ohlcv"],
            "markets": ["ES", "NQ", "RTY"],
            "operation": feature.value,
            "window": 2,
        },
        availability_assumptions={
            "timing": (
                "synthetic ES/NQ/RTY fixture rows expose per-instrument available_ts "
                "after bar end"
            )
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["close", "quality_flags", "available_ts"],
            "source": "tiny synthetic canonical ES/NQ/RTY fixture only",
        },
        approval_status=approval_status,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
