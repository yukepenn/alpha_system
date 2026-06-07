from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from alpha_system.features.contracts import (
    FeatureContractError,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.families.ohlcv import (
    OHLCVFeatureError,
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
    compute_ohlcv_features,
    supported_ohlcv_features,
)
from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.features.request_gate import FeatureRequestGateError
from alpha_system.governance.duplicate_exposure import ExposureCheckResult, ExposureRegistryStatus
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)
from alpha_system.runtime.input_resolver import (
    RuntimeInputResolverError,
    _reject_label_as_live_feature,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_all_base_ohlcv_features_are_gated_versioned_and_causal() -> None:
    view = _fixture_view()
    registry = EmptyRegistryReader()
    definitions = tuple(
        build_ohlcv_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            dataset_version_ids=("dsv_synthetic_ohlcv",),
            window_length=2,
            opening_range_minutes=2,
            reset_on_session=False,
        )
        for feature in supported_ohlcv_features()
    )

    results = compute_ohlcv_features(definitions, view)

    assert set(results) == set(OHLCVFeatureName)
    for definition in definitions:
        assert definition.spec.implementation_eligible is True
        assert definition.spec.feature_request_id.startswith("freq_")
        assert definition.version == definition.spec.derive_feature_version()
        assert definition.spec.window.is_live_compatible is True
        records = results[definition.name]
        assert len(records) == len(view.rows)
        assert all(record.feature_version_id == definition.feature_version_id for record in records)
        assert [record.available_ts for record in records] == [
            row.available_ts for row in view.rows
        ]

    assert results[OHLCVFeatureName.RETURNS][1].value == pytest.approx(100 / 99 - 1)
    assert results[OHLCVFeatureName.LOG_RETURNS][1].value == pytest.approx(math.log(100 / 99))
    assert results[OHLCVFeatureName.ROLLING_VOLATILITY][3].value == pytest.approx(
        _std((101 / 100 - 1, 102 / 101 - 1))
    )
    assert results[OHLCVFeatureName.ROLLING_RANGE][2].value == pytest.approx(5.0)
    assert results[OHLCVFeatureName.ATR][1].value == pytest.approx(3.0)
    assert results[OHLCVFeatureName.VOLUME_ZSCORE][1].value == pytest.approx(1.0)
    assert results[OHLCVFeatureName.ROLLING_VOLUME][1].value == pytest.approx(30.0)
    assert results[OHLCVFeatureName.SESSION_MINUTE][0].value == 0
    assert results[OHLCVFeatureName.SESSION_MINUTE][2].value == 0
    assert results[OHLCVFeatureName.RTH_FLAG][2].value == 1
    assert results[OHLCVFeatureName.ETH_FLAG][0].value == 1
    assert results[OHLCVFeatureName.OPENING_RANGE][3].value == pytest.approx(4.0)
    assert results[OHLCVFeatureName.OVERNIGHT_RANGE][2].value == pytest.approx(4.0)
    assert results[OHLCVFeatureName.VWAP][2].value == pytest.approx((102 + 99 + 101) / 3)
    assert results[OHLCVFeatureName.ANCHORED_VWAP][0].value is None
    assert results[OHLCVFeatureName.ANCHORED_VWAP][2].value == pytest.approx(
        (102 + 99 + 101) / 3
    )
    assert results[OHLCVFeatureName.DISTANCE_TO_VWAP][2].value == pytest.approx(
        (101 - ((102 + 99 + 101) / 3)) / ((102 + 99 + 101) / 3)
    )
    assert results[OHLCVFeatureName.RANGE_POSITION][2].value == pytest.approx(0.8)
    assert results[OHLCVFeatureName.TRENDINESS][2].value == pytest.approx(1.0)


def test_no_trade_rows_are_not_treated_as_trade_bars() -> None:
    view = _fixture_view()
    registry = EmptyRegistryReader()
    checked_features = (
        OHLCVFeatureName.RETURNS,
        OHLCVFeatureName.ROLLING_RANGE,
        OHLCVFeatureName.VOLUME_ZSCORE,
        OHLCVFeatureName.ROLLING_VOLUME,
        OHLCVFeatureName.VWAP,
    )

    for feature in checked_features:
        definition = build_ohlcv_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            window_length=2,
            reset_on_session=False,
        )
        records = compute_ohlcv_feature(definition, view)

        assert records[4].value is None
        assert "no_trade" in records[4].quality_flags


def test_missing_available_ts_fails_closed() -> None:
    view = _fixture_view()
    corrupt_row = view.rows[0]
    object.__setattr__(corrupt_row, "available_ts", None)
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        _approved_request(OHLCVFeatureName.RETURNS),
        EmptyRegistryReader(),
    )

    with pytest.raises(OHLCVFeatureError, match="available_ts"):
        compute_ohlcv_feature(definition, view)


def test_feature_request_gate_is_required_and_fail_closed() -> None:
    registry = EmptyRegistryReader()

    with pytest.raises(FeatureRequestGateError):
        build_ohlcv_feature_definition(OHLCVFeatureName.RETURNS, None, registry)

    with pytest.raises(FeatureRequestGateError):
        build_ohlcv_feature_definition(
            OHLCVFeatureName.RETURNS,
            _request(OHLCVFeatureName.RETURNS, FeatureRequestApprovalStatus.PENDING),
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
        build_ohlcv_feature_definition(
            OHLCVFeatureName.ROLLING_RANGE,
            _approved_request(OHLCVFeatureName.ROLLING_RANGE),
            EmptyRegistryReader(),
            window=window,
        )


@pytest.mark.parametrize(
    "feature_name",
    (
        OHLCVFeatureName.RTH_FLAG,
        OHLCVFeatureName.ETH_FLAG,
        OHLCVFeatureName.SESSION_MINUTE,
    ),
)
def test_session_context_features_declare_session_label_as_metadata(
    feature_name: OHLCVFeatureName,
) -> None:
    definition = build_ohlcv_feature_definition(
        feature_name,
        _approved_request(feature_name),
        EmptyRegistryReader(),
    )

    field_roles = definition.spec.inputs.input_metadata.to_dict()["field_roles"]

    assert field_roles["session_label"] == "SESSION_METADATA"
    assert set(field_roles) == {"session_label"}


def test_non_session_feature_metadata_has_no_field_roles() -> None:
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RETURNS,
        _approved_request(OHLCVFeatureName.RETURNS),
        EmptyRegistryReader(),
    )

    input_metadata = definition.spec.inputs.input_metadata.to_dict()

    assert "field_roles" not in input_metadata
    assert (
        input_metadata["consumption_surface"]
        == "alpha_system.features.input_views.OHLCVInputView"
    )
    assert (
        input_metadata["trade_semantics"]
        == "FLF-P04 no_trade rows are gaps for trade logic"
    )


def test_built_session_context_feature_passes_runtime_label_guard() -> None:
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.RTH_FLAG,
        _approved_request(OHLCVFeatureName.RTH_FLAG),
        EmptyRegistryReader(),
    )

    _reject_label_as_live_feature(
        SimpleNamespace(feature_spec=definition.spec),
        field="feature_pack_refs[0]",
    )

    forbidden_spec = SimpleNamespace(
        live=True,
        inputs=SimpleNamespace(
            fields=("fwd_ret_5m",),
            input_views=("canonical_ohlcv",),
            input_metadata={"field_roles": {"fwd_ret_5m": "SESSION_METADATA"}},
        ),
    )
    with pytest.raises(RuntimeInputResolverError) as exc_info:
        _reject_label_as_live_feature(
            SimpleNamespace(feature_spec=forbidden_spec),
            field="feature_pack_refs[1]",
        )

    assert exc_info.value.reason.code == "label_as_feature_input"


def _fixture_view() -> OHLCVInputView:
    start = _dt("2024-01-02T13:58:00+00:00")
    rows = (
        _row(start, "ETH", open_="99", high="100", low="98", close="99", volume="10"),
        _row(
            start + timedelta(minutes=1),
            "ETH",
            open_="99",
            high="101",
            low="97",
            close="100",
            volume="20",
        ),
        _row(
            _dt("2024-01-02T14:30:00+00:00"),
            "RTH",
            open_="100",
            high="102",
            low="99",
            close="101",
            volume="100",
        ),
        _row(
            _dt("2024-01-02T14:31:00+00:00"),
            "RTH",
            open_="101",
            high="103",
            low="100",
            close="102",
            volume="200",
        ),
        _row(
            _dt("2024-01-02T14:32:00+00:00"),
            "RTH",
            open_="102",
            high="102",
            low="102",
            close="102",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _row(
            _dt("2024-01-02T14:33:00+00:00"),
            "RTH",
            open_="102",
            high="105",
            low="101",
            close="104",
            volume="300",
        ),
    )
    return OHLCVInputView(rows)


def _row(
    bar_start_ts: datetime,
    session_label: str,
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
        data_version="dsv_synthetic_ohlcv",
        quality_flags=quality_flags,
        session_label=session_label,
    )


def _approved_request(feature: OHLCVFeatureName) -> FeatureRequest:
    return _request(feature, FeatureRequestApprovalStatus.APPROVED)


def _request(
    feature: OHLCVFeatureName,
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"base_ohlcv_{feature.value}"],
        formula_sketch={
            "exposure_family": f"base_ohlcv_{feature.value}",
            "inputs": ["canonical_ohlcv"],
            "operation": feature.value,
            "window": 2,
        },
        availability_assumptions={
            "timing": "synthetic OHLCV fixture rows expose available_ts after bar end"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["open", "high", "low", "close", "volume", "available_ts"],
            "source": "tiny synthetic canonical OHLCV fixture only",
        },
        approval_status=approval_status,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _std(values: tuple[float, ...]) -> float:
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))
