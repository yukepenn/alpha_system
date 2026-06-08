from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.data.foundation.grid import (
    NO_TRADE_QUALITY_FLAG,
    PREVIOUS_CLOSE_FILL_METHOD,
    DenseGridBarRecord,
)
from alpha_system.features.families.session import (
    SessionCalendarRollMetadata,
    SessionFeatureError,
    SessionFeatureName,
    build_session_feature_definition,
    compute_session_feature,
    row_key,
)
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


def test_dense_grid_session_definition_preserves_identity_and_available_ts() -> None:
    rows = _dense_rows()
    definition = build_session_feature_definition(
        SessionFeatureName.MINUTES_TO_RTH_CLOSE,
        _approved_request(SessionFeatureName.MINUTES_TO_RTH_CLOSE),
        EmptyRegistryReader(),
        dataset_version_ids=(
            "dsv_databento_ohlcv_05404069799decb0",
            "dsv_databento_ohlcv_dense_2024_v1",
        ),
        input_view_name="dense_grid_ohlcv",
    )

    records = compute_session_feature(definition, rows)

    assert definition.spec.inputs.input_views == ("dense_grid_ohlcv",)
    assert definition.spec.inputs.dataset_version_ids == (
        "dsv_databento_ohlcv_05404069799decb0",
        "dsv_databento_ohlcv_dense_2024_v1",
    )
    assert definition.feature_version_id.startswith("fver_")
    assert [record.available_ts for record in records] == [row.available_ts for row in rows]
    assert records[0].value == 390
    assert records[1].value == 389
    assert NO_TRADE_QUALITY_FLAG in records[1].quality_flags
    assert "synthetic_no_trade_position_only" in records[1].quality_flags


def test_session_metadata_available_after_row_available_ts_fails_closed() -> None:
    rows = _dense_rows()
    definition = build_session_feature_definition(
        SessionFeatureName.HALT_STATUS_FLAG,
        _approved_request(SessionFeatureName.HALT_STATUS_FLAG),
        EmptyRegistryReader(),
        input_view_name="dense_grid_ohlcv",
    )
    key = row_key(rows[0])
    metadata = SessionCalendarRollMetadata(
        status_by_row_key={key: "halted"},
        status_available_ts_by_row_key={key: rows[0].available_ts + timedelta(minutes=1)},
    )

    with pytest.raises(SessionFeatureError, match="status metadata available_ts"):
        compute_session_feature(definition, rows, metadata)


def test_session_metadata_available_at_row_available_ts_is_allowed() -> None:
    rows = _dense_rows()
    definition = build_session_feature_definition(
        SessionFeatureName.HALT_STATUS_FLAG,
        _approved_request(SessionFeatureName.HALT_STATUS_FLAG),
        EmptyRegistryReader(),
        input_view_name="dense_grid_ohlcv",
    )
    key = row_key(rows[0])
    metadata = SessionCalendarRollMetadata(
        status_by_row_key={key: "halted"},
        status_available_ts_by_row_key={key: rows[0].available_ts},
    )

    records = compute_session_feature(definition, rows, metadata)

    assert records[0].value == 1
    assert records[0].available_ts == rows[0].available_ts
    assert "status_halted" in records[0].quality_flags
    assert records[1].value is None
    assert "status_metadata_absent" in records[1].quality_flags


def _dense_rows() -> tuple[DenseGridBarRecord, ...]:
    first = _dt("2024-01-02T14:30:00+00:00")
    second = first + timedelta(minutes=1)
    return (
        _dense_row(first, has_trade=True),
        _dense_row(second, has_trade=False),
    )


def _dense_row(bar_start_ts: datetime, *, has_trade: bool) -> DenseGridBarRecord:
    price = Decimal("100")
    return DenseGridBarRecord(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES_c_0",
        bar_start_ts=bar_start_ts,
        bar_end_ts=bar_start_ts + timedelta(minutes=1),
        event_ts=bar_start_ts + timedelta(minutes=1),
        available_ts=bar_start_ts + timedelta(minutes=1, seconds=1),
        ingested_at=bar_start_ts + timedelta(minutes=1, seconds=2),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal("10") if has_trade else Decimal("0"),
        source="dsrc_synthetic",
        source_request_id="req_synthetic",
        data_version="dsv_databento_ohlcv_dense_2024_v1",
        quality_flags=() if has_trade else (NO_TRADE_QUALITY_FLAG,),
        session_label="RTH",
        has_trade=has_trade,
        synthetic=not has_trade,
        fill_method=None if has_trade else PREVIOUS_CLOSE_FILL_METHOD,
        provider_bar_ref="provider_bar_1" if has_trade else None,
    )


def _approved_request(feature: SessionFeatureName) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"session_calendar_maintenance_{feature.value}"],
        formula_sketch={
            "exposure_family": f"session_calendar_maintenance_{feature.value}",
            "inputs": ["ohlcv_dense_research_grid"],
            "operation": feature.value,
            "window": 1,
        },
        availability_assumptions={
            "timing": "metadata availability must not exceed row available_ts"
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["session_label", "bar_start_ts", "available_ts"],
            "source": "tiny synthetic dense-grid fixture",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
