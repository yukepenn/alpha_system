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
from alpha_system.features.families.session import (
    SESSION_FEATURE_FAMILY,
    SessionCalendarEntry,
    SessionCalendarMetadata,
    SessionFeatureError,
    SessionFeatureName,
    build_session_feature_definition,
    build_session_feature_set_spec,
    compute_session_feature,
    compute_session_features,
    supported_session_features,
)
from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
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


def test_all_session_features_are_gated_versioned_causal_and_available() -> None:
    view = _fixture_view()
    metadata = _calendar_metadata()
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

    results = compute_session_features(definitions, view, metadata)
    feature_set = build_session_feature_set_spec(definitions)

    assert SESSION_FEATURE_FAMILY is FeatureFamily.SESSION_CALENDAR_ROLL
    assert feature_set.metadata.to_dict()["family"] == FeatureFamily.SESSION_CALENDAR_ROLL.value
    assert set(results) == set(SessionFeatureName)
    for definition in definitions:
        assert definition.spec.family is FeatureFamily.SESSION_CALENDAR_ROLL
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

    assert {record.value for record in results[SessionFeatureName.SESSION_ID]} == {
        "ES-2024-01-02"
    }
    assert results[SessionFeatureName.MINUTES_FROM_RTH_OPEN][0].value == -2
    assert results[SessionFeatureName.MINUTES_FROM_RTH_OPEN][2].value == 0
    assert results[SessionFeatureName.MINUTES_TO_RTH_CLOSE][2].value == 390
    assert results[SessionFeatureName.RTH_SEGMENT_FLAG][2].value == 1
    assert results[SessionFeatureName.RTH_SEGMENT_FLAG][0].value == 0
    assert results[SessionFeatureName.ETH_SEGMENT_FLAG][0].value == 1
    assert results[SessionFeatureName.DAY_OF_WEEK][0].value == 1
    assert results[SessionFeatureName.ROLL_PROXIMITY_MINUTES][2].value == 10_080
    assert results[SessionFeatureName.EXPIRATION_PROXIMITY_MINUTES][2].value == 42_150
    assert results[SessionFeatureName.MARKET_STATUS][2].value == "open"
    assert results[SessionFeatureName.HALT_FLAG][2].value == 0


def test_minutes_to_close_is_schedule_derived_without_future_trade_rows() -> None:
    metadata = _calendar_metadata()
    registry = EmptyRegistryReader()
    definition = build_session_feature_definition(
        SessionFeatureName.MINUTES_TO_RTH_CLOSE,
        _approved_request(SessionFeatureName.MINUTES_TO_RTH_CLOSE),
        registry,
    )
    first_rth_only = OHLCVInputView((_fixture_view().rows[2],))

    records = compute_session_feature(definition, first_rth_only, metadata)

    assert len(records) == 1
    assert records[0].value == 390
    assert records[0].available_ts == first_rth_only.rows[0].available_ts


def test_unavailable_metadata_emits_flagged_values() -> None:
    view = _fixture_view()
    metadata = SessionCalendarMetadata(
        (
            SessionCalendarEntry(
                session_id="ES-2024-01-02",
                session_start_ts=_dt("2024-01-02T14:28:00+00:00"),
                rth_open_ts=_dt("2024-01-02T14:30:00+00:00"),
                rth_close_ts=_dt("2024-01-02T21:00:00+00:00"),
            ),
        )
    )
    registry = EmptyRegistryReader()

    for feature, expected_flag in (
        (SessionFeatureName.ROLL_PROXIMITY_MINUTES, "roll_metadata_unavailable"),
        (SessionFeatureName.EXPIRATION_PROXIMITY_MINUTES, "expiration_metadata_unavailable"),
        (SessionFeatureName.MARKET_STATUS, "status_unavailable"),
        (SessionFeatureName.HALT_FLAG, "halt_unavailable"),
    ):
        definition = build_session_feature_definition(
            feature,
            _approved_request(feature),
            registry,
        )
        records = compute_session_feature(definition, view, metadata)

        assert records[0].value is None
        assert expected_flag in records[0].quality_flags
        assert "session_context_unavailable" in records[0].quality_flags

    definition = build_session_feature_definition(
        SessionFeatureName.MINUTES_FROM_RTH_OPEN,
        _approved_request(SessionFeatureName.MINUTES_FROM_RTH_OPEN),
        registry,
    )
    records = compute_session_feature(definition, view, None)
    assert records[0].value is None
    assert "rth_schedule_unavailable" in records[0].quality_flags


def test_no_trade_rows_remain_flagged_but_do_not_change_calendar_values() -> None:
    view = _fixture_view()
    definition = build_session_feature_definition(
        SessionFeatureName.MINUTES_FROM_RTH_OPEN,
        _approved_request(SessionFeatureName.MINUTES_FROM_RTH_OPEN),
        EmptyRegistryReader(),
    )

    records = compute_session_feature(definition, view, _calendar_metadata())

    assert records[3].value == 1
    assert "no_trade" in records[3].quality_flags


def test_missing_available_ts_fails_closed() -> None:
    view = _fixture_view()
    corrupt_row = view.rows[0]
    object.__setattr__(corrupt_row, "available_ts", None)
    definition = build_session_feature_definition(
        SessionFeatureName.DAY_OF_WEEK,
        _approved_request(SessionFeatureName.DAY_OF_WEEK),
        EmptyRegistryReader(),
    )

    with pytest.raises(SessionFeatureError, match="available_ts"):
        compute_session_feature(definition, view, _calendar_metadata())


def test_feature_request_gate_is_required_and_fail_closed() -> None:
    registry = EmptyRegistryReader()

    with pytest.raises(FeatureRequestGateError):
        build_session_feature_definition(SessionFeatureName.DAY_OF_WEEK, None, registry)

    with pytest.raises(FeatureRequestGateError):
        build_session_feature_definition(
            SessionFeatureName.DAY_OF_WEEK,
            _request(SessionFeatureName.DAY_OF_WEEK, FeatureRequestApprovalStatus.PENDING),
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
            SessionFeatureName.MINUTES_TO_RTH_CLOSE,
            _approved_request(SessionFeatureName.MINUTES_TO_RTH_CLOSE),
            EmptyRegistryReader(),
            window=window,
        )


def _fixture_view() -> OHLCVInputView:
    rows = (
        _row(_dt("2024-01-02T14:28:00+00:00"), "ETH"),
        _row(_dt("2024-01-02T14:29:00+00:00"), "ETH"),
        _row(_dt("2024-01-02T14:30:00+00:00"), "RTH"),
        _row(
            _dt("2024-01-02T14:31:00+00:00"),
            "RTH",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _row(_dt("2024-01-02T20:59:00+00:00"), "RTH"),
    )
    return OHLCVInputView(rows)


def _row(
    bar_start_ts: datetime,
    session_label: str,
    *,
    volume: str = "100",
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
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal(volume),
        data_version="dsv_synthetic_session",
        quality_flags=quality_flags,
        session_label=session_label,
    )


def _calendar_metadata() -> SessionCalendarMetadata:
    return SessionCalendarMetadata(
        (
            SessionCalendarEntry(
                session_id="ES-2024-01-02",
                session_start_ts=_dt("2024-01-02T14:28:00+00:00"),
                rth_open_ts=_dt("2024-01-02T14:30:00+00:00"),
                rth_close_ts=_dt("2024-01-02T21:00:00+00:00"),
                roll_ts=_dt("2024-01-09T14:30:00+00:00"),
                expiration_ts=_dt("2024-01-31T21:00:00+00:00"),
                market_status="open",
                halt=False,
            ),
        )
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
            "inputs": ["canonical_ohlcv", "session_calendar_metadata"],
            "operation": feature.value,
            "window": 1,
        },
        availability_assumptions={
            "timing": "synthetic rows expose available_ts after bar end",
            "schedule": "session schedule metadata is deterministic context",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["bar_start_ts", "session_label", "available_ts"],
            "source": "tiny synthetic canonical session fixture only",
        },
        approval_status=approval_status,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
