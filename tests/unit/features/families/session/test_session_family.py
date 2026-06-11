from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.data.foundation.grid import (
    NO_TRADE_QUALITY_FLAG,
    PREVIOUS_CLOSE_FILL_METHOD,
    DenseGridBarRecord,
)
from alpha_system.features.contracts import (
    FeatureContractError,
    FeatureFamily,
    WindowCausality,
    WindowKind,
    WindowSpec,
)
from alpha_system.features.families.session import (
    CalendarFeatureSpec,
    ExpirationFeatureSpec,
    RollFeatureSpec,
    SessionCalendarRollMetadata,
    SessionFeatureError,
    SessionFeatureName,
    SessionPositionFeatureSpec,
    StatusFeatureSpec,
    build_session_feature_definition,
    compute_session_feature,
    compute_session_features,
    row_key,
    supported_session_features,
)
from alpha_system.features.input_views import OHLCVInputRow
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


def test_all_session_features_are_gated_versioned_and_available() -> None:
    rows = _fixture_rows()
    metadata = _fixture_metadata(rows)
    registry = EmptyRegistryReader()
    definitions = tuple(
        build_session_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            dataset_version_ids=("dsv_synthetic_session",),
        )
        for feature in supported_session_features()
    )

    results = compute_session_features(definitions, rows, metadata)

    assert set(results) == set(SessionFeatureName)
    for definition in definitions:
        assert definition.spec.family is FeatureFamily.SESSION_CALENDAR_ROLL
        assert definition.spec.feature_request_id.startswith("freq_")
        assert definition.request_gate_decision.duplicate_exposure_report is not None
        assert definition.version == definition.spec.derive_feature_version()
        if definition.name in {
            SessionFeatureName.BARS_TO_ROLL,
            SessionFeatureName.MINUTES_TO_ROLL,
        }:
            assert definition.spec.live is False
            assert definition.spec.implementation_eligible is True
            assert definition.spec.window.kind is WindowKind.FUTURE
            assert definition.spec.window.causality is WindowCausality.FUTURE
            assert definition.spec.window.offline_only is True
        else:
            assert definition.spec.live is True
            assert definition.spec.implementation_eligible is True
            assert definition.spec.window.is_live_compatible is True
        records = results[definition.name]
        assert len(records) == len(rows)
        assert all(record.feature_version_id == definition.feature_version_id for record in records)
        assert [record.available_ts for record in records] == [row.available_ts for row in rows]
        parameters = definition.spec.transform.parameters.to_dict()
        assert parameters["session_template_id"] == "session_cme_index_futures_eth"
        assert parameters["session_timezone"] == "America/Chicago"
        assert parameters["rth_open_time_local"] == "08:30"
        assert parameters["rth_close_time_local"] == "15:00"
        assert "rth_open_time_utc" not in parameters
        assert "rth_close_time_utc" not in parameters

    assert isinstance(
        _definition(definitions, SessionFeatureName.SESSION_ID).spec,
        SessionPositionFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, SessionFeatureName.DAY_OF_WEEK).spec,
        CalendarFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, SessionFeatureName.BARS_TO_ROLL).spec,
        RollFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, SessionFeatureName.MINUTES_TO_EXPIRATION).spec,
        ExpirationFeatureSpec,
    )
    assert isinstance(
        _definition(definitions, SessionFeatureName.HALT_STATUS_FLAG).spec,
        StatusFeatureSpec,
    )

    assert results[SessionFeatureName.SESSION_ID][1].value == "ES_c_0:2024-01-02:RTH"
    assert results[SessionFeatureName.MINUTES_FROM_RTH_OPEN][0].value is None
    assert "outside_rth" in results[SessionFeatureName.MINUTES_FROM_RTH_OPEN][0].quality_flags
    assert results[SessionFeatureName.MINUTES_FROM_RTH_OPEN][1].value == 0
    assert results[SessionFeatureName.MINUTES_FROM_RTH_OPEN][2].value == 1
    assert results[SessionFeatureName.MINUTES_TO_RTH_CLOSE][1].value == 390
    assert results[SessionFeatureName.RTH_SEGMENT_FLAG][0].value == 0
    assert results[SessionFeatureName.RTH_SEGMENT_FLAG][1].value == 1
    assert results[SessionFeatureName.ETH_SEGMENT_FLAG][0].value == 1
    assert results[SessionFeatureName.DAY_OF_WEEK][1].value == 1
    assert results[SessionFeatureName.BARS_TO_ROLL][0].value == 3
    assert results[SessionFeatureName.BARS_TO_ROLL][2].value == 1
    assert results[SessionFeatureName.BARS_TO_ROLL][3].value is None
    assert "roll_transition_absent" in results[SessionFeatureName.BARS_TO_ROLL][3].quality_flags
    assert results[SessionFeatureName.MINUTES_TO_ROLL][1].value == 2
    assert results[SessionFeatureName.MINUTES_TO_EXPIRATION][1].value == 390
    assert results[SessionFeatureName.MINUTES_TO_EXPIRATION][3].value is None
    assert (
        "expiration_metadata_absent"
        in results[SessionFeatureName.MINUTES_TO_EXPIRATION][3].quality_flags
    )
    assert results[SessionFeatureName.HALT_STATUS_FLAG][1].value == 0
    assert "status_trading" in results[SessionFeatureName.HALT_STATUS_FLAG][1].quality_flags
    assert results[SessionFeatureName.HALT_STATUS_FLAG][3].value == 1
    assert "status_halted" in results[SessionFeatureName.HALT_STATUS_FLAG][3].quality_flags


def test_synthetic_no_trade_rows_retain_session_position_but_are_flagged() -> None:
    rows = _fixture_rows()
    definition = build_session_feature_definition(
        SessionFeatureName.SESSION_ID,
        _approved_request(SessionFeatureName.SESSION_ID),
        EmptyRegistryReader(),
    )

    records = compute_session_feature(definition, rows)
    synthetic_record = records[4]

    assert synthetic_record.value == "ES_c_0:2024-01-02:RTH"
    assert NO_TRADE_QUALITY_FLAG in synthetic_record.quality_flags
    assert "synthetic_no_trade_position_only" in synthetic_record.quality_flags


def test_session_position_features_ignore_static_session_label_for_rth_truth() -> None:
    # P183000 repair provenance: canonical session_label is a coverage descriptor;
    # RTH/ETH truth comes from bar_start_ts converted through the session template.
    rows = (
        _ohlcv_row(_dt("2024-01-10T14:29:00+00:00"), "ETH", contract_id="ESM4"),
        _ohlcv_row(_dt("2024-01-10T14:30:00+00:00"), "ETH", contract_id="ESM4"),
        _ohlcv_row(_dt("2024-01-10T20:59:00+00:00"), "ETH", contract_id="ESM4"),
        _ohlcv_row(_dt("2024-01-10T21:00:00+00:00"), "ETH", contract_id="ESM4"),
        _ohlcv_row(_dt("2024-07-10T13:30:00+00:00"), "ETH", contract_id="ESU4"),
        _ohlcv_row(_dt("2024-07-10T20:00:00+00:00"), "ETH", contract_id="ESU4"),
    )
    registry = EmptyRegistryReader()
    definitions = {
        feature: build_session_feature_definition(
            feature,
            _approved_request(feature),
            registry,
            dataset_version_ids=("dsv_synthetic_session",),
        )
        for feature in (
            SessionFeatureName.SESSION_ID,
            SessionFeatureName.MINUTES_FROM_RTH_OPEN,
            SessionFeatureName.MINUTES_TO_RTH_CLOSE,
            SessionFeatureName.RTH_SEGMENT_FLAG,
            SessionFeatureName.ETH_SEGMENT_FLAG,
        )
    }

    records = {
        feature: compute_session_feature(definition, rows)
        for feature, definition in definitions.items()
    }

    assert [record.value for record in records[SessionFeatureName.RTH_SEGMENT_FLAG]] == [
        0,
        1,
        1,
        0,
        1,
        0,
    ]
    assert [record.value for record in records[SessionFeatureName.ETH_SEGMENT_FLAG]] == [
        1,
        0,
        0,
        1,
        0,
        1,
    ]
    assert [record.value for record in records[SessionFeatureName.MINUTES_FROM_RTH_OPEN]] == [
        None,
        0,
        389,
        None,
        0,
        None,
    ]
    assert [record.value for record in records[SessionFeatureName.MINUTES_TO_RTH_CLOSE]] == [
        None,
        390,
        1,
        None,
        390,
        None,
    ]
    assert records[SessionFeatureName.SESSION_ID][1].value == "ES_c_0:2024-01-10:RTH"
    assert records[SessionFeatureName.SESSION_ID][3].value == "ES_c_0:2024-01-10:ETH"
    assert records[SessionFeatureName.SESSION_ID][4].value == "ES_c_0:2024-07-10:RTH"
    assert "outside_rth" in records[SessionFeatureName.MINUTES_FROM_RTH_OPEN][0].quality_flags
    assert "before_rth_open" in records[SessionFeatureName.MINUTES_FROM_RTH_OPEN][0].quality_flags
    assert "after_rth_close" in records[SessionFeatureName.MINUTES_TO_RTH_CLOSE][3].quality_flags


def test_missing_optional_metadata_is_flagged_not_fabricated() -> None:
    rows = _fixture_rows()
    expiration_definition = build_session_feature_definition(
        SessionFeatureName.MINUTES_TO_EXPIRATION,
        _approved_request(SessionFeatureName.MINUTES_TO_EXPIRATION),
        EmptyRegistryReader(),
    )
    status_definition = build_session_feature_definition(
        SessionFeatureName.HALT_STATUS_FLAG,
        _approved_request(SessionFeatureName.HALT_STATUS_FLAG),
        EmptyRegistryReader(),
    )

    expiration = compute_session_feature(expiration_definition, rows)
    status = compute_session_feature(status_definition, rows)

    assert all(record.value is None for record in expiration)
    assert all("expiration_metadata_absent" in record.quality_flags for record in expiration)
    assert all(record.value is None for record in status)
    assert all("status_metadata_absent" in record.quality_flags for record in status)


def test_missing_available_ts_fails_closed() -> None:
    rows = list(_fixture_rows())
    object.__setattr__(rows[0], "available_ts", None)
    definition = build_session_feature_definition(
        SessionFeatureName.DAY_OF_WEEK,
        _approved_request(SessionFeatureName.DAY_OF_WEEK),
        EmptyRegistryReader(),
    )

    with pytest.raises(SessionFeatureError, match="available_ts"):
        compute_session_feature(definition, rows)


def test_feature_request_gate_is_required_and_fail_closed() -> None:
    registry = EmptyRegistryReader()

    with pytest.raises(FeatureRequestGateError):
        build_session_feature_definition(SessionFeatureName.SESSION_ID, None, registry)

    with pytest.raises(FeatureRequestGateError):
        build_session_feature_definition(
            SessionFeatureName.SESSION_ID,
            _request(SessionFeatureName.SESSION_ID, FeatureRequestApprovalStatus.PENDING),
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
        build_session_feature_definition(
            SessionFeatureName.SESSION_ID,
            _approved_request(SessionFeatureName.SESSION_ID),
            EmptyRegistryReader(),
            window=window,
        )


def _definition(
    definitions: tuple[object, ...],
    name: SessionFeatureName,
) -> object:
    for definition in definitions:
        if getattr(definition, "name") is name:
            return definition
    raise AssertionError(f"missing definition for {name}")


def _fixture_rows() -> tuple[OHLCVInputRow | DenseGridBarRecord, ...]:
    eth = _dt("2024-01-02T13:59:00+00:00")
    rth = _dt("2024-01-02T14:30:00+00:00")
    return (
        _ohlcv_row(eth, "ETH", contract_id="ESM4"),
        _ohlcv_row(rth, "RTH", contract_id="ESM4"),
        _ohlcv_row(rth + timedelta(minutes=1), "RTH", contract_id="ESM4"),
        _ohlcv_row(rth + timedelta(minutes=2), "RTH", contract_id="ESU4"),
        _dense_no_trade_row(rth + timedelta(minutes=3), contract_id="ESU4"),
    )


def _fixture_metadata(
    rows: tuple[OHLCVInputRow | DenseGridBarRecord, ...],
) -> SessionCalendarRollMetadata:
    return SessionCalendarRollMetadata(
        expiration_ts_by_contract_id={"ESM4": _dt("2024-01-02T21:00:00+00:00")},
        status_by_row_key={
            row_key(rows[1]): "trading",
            row_key(rows[3]): "halted",
        },
    )


def _ohlcv_row(
    bar_start_ts: datetime,
    session_label: str,
    *,
    contract_id: str,
) -> OHLCVInputRow:
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id=contract_id,
        series_id="ES_c_0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal("10"),
        data_version="dsv_synthetic_session",
        quality_flags=(),
        session_label=session_label,
    )


def _dense_no_trade_row(bar_start_ts: datetime, *, contract_id: str) -> DenseGridBarRecord:
    return DenseGridBarRecord(
        instrument_id="ES",
        contract_id=contract_id,
        series_id="ES_c_0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("0"),
        source="dsrc_synthetic",
        source_request_id="req_synthetic",
        data_version="dsv_synthetic_session_dense",
        quality_flags=(NO_TRADE_QUALITY_FLAG,),
        session_label="RTH",
        has_trade=False,
        synthetic=True,
        fill_method=PREVIOUS_CLOSE_FILL_METHOD,
        provider_bar_ref=None,
    )


def _approved_request(feature: SessionFeatureName) -> FeatureRequest:
    return _request(feature, FeatureRequestApprovalStatus.APPROVED)


def _request(
    feature: SessionFeatureName,
    approval_status: FeatureRequestApprovalStatus,
) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"session_calendar_roll_{feature.value}"],
        formula_sketch={
            "exposure_family": f"session_calendar_roll_{feature.value}",
            "inputs": ["canonical_ohlcv"],
            "operation": feature.value,
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic session fixture rows expose available_ts after bar end"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": [
                "contract_id",
                "series_id",
                "session_label",
                "bar_start_ts",
                "available_ts",
            ],
            "source": "tiny synthetic canonical OHLCV and dense-grid fixture only",
        },
        approval_status=approval_status,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
