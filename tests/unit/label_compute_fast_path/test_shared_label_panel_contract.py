from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.labels.fast import (
    LabelAvailabilityFamily,
    QUALITY_FLAG_INSUFFICIENT_WINDOW,
    QUALITY_FLAG_MAINTENANCE_CROSSING,
    QUALITY_FLAG_SESSION_RESET,
    TerminalGuardDisposition,
    TerminalKind,
    TerminalRequest,
    build_shared_label_panel,
    derive_label_available_ts,
    quality_metadata_for_resolution,
    resolve_terminal_indices,
)
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_label,
)
from alpha_system.labels.roll_guard import RollCrossPolicy, evaluate_roll_guard
from tests.fixtures.label_compute_fast_path.synthetic_panel import (
    DATASET_ID,
    bbo_rows_for_ohlcv,
    fixed_horizon_label_spec,
    minute_ohlcv_rows,
)


def test_shared_panel_builder_carries_wide_price_bbo_session_roll_and_maintenance_contract() -> None:
    rows = minute_ohlcv_rows(
        _dt("2024-01-02T14:30:00+00:00"),
        count=4,
        no_trade_indices=frozenset({2}),
    )
    bbo_rows = bbo_rows_for_ohlcv(
        rows,
        missing_bbo_indices=frozenset({1}),
        quarantined_indices=frozenset({3}),
    )

    panel = build_shared_label_panel(
        symbol="ES",
        year=2024,
        ohlcv_rows=rows,
        bbo_rows=bbo_rows,
    )

    assert len(panel.rows) == 4
    assert panel.rows[0].trade_price == pytest.approx(100.0)
    assert panel.rows[0].high > panel.rows[0].low
    assert panel.rows[0].mid == pytest.approx(100.0)
    assert panel.rows[0].spread == pytest.approx(0.25)
    assert panel.rows[0].bbo_present is True
    assert panel.rows[1].bbo_present is False
    assert panel.rows[1].bbo_missing is True
    assert panel.rows[3].bbo_quarantined is True
    assert "no_trade" in panel.rows[2].quality_flags
    assert panel.rows[0].session_segment_id.startswith("ES_CONTINUOUS:rth:")
    assert panel.roll_calendar
    assert panel.maintenance_windows
    assert panel.metadata["bbo_semantics"].endswith("presence flagged")


def test_roll_cross_policy_dispositions_match_roll_guard_actions() -> None:
    source_ts = _dt("2024-03-06T23:45:00+00:00")
    roll_boundary_ts = _dt("2024-03-07T00:00:00+00:00")
    requested_terminal_ts = _dt("2024-03-07T00:15:00+00:00")
    horizon_minutes = int((requested_terminal_ts - source_ts).total_seconds() // 60)
    panel = build_shared_label_panel(
        symbol="ES",
        year=2024,
        ohlcv_rows=(
            _ohlcv_mapping(source_ts, close=Decimal("100"), contract_id="ESH4"),
            _ohlcv_mapping(roll_boundary_ts, close=Decimal("100.5"), contract_id="ESH4"),
            _ohlcv_mapping(requested_terminal_ts, close=Decimal("101"), contract_id="ESH4"),
        ),
    )
    source = panel.rows[0]
    terminal = panel.rows[2]

    for policy in RollCrossPolicy:
        model = resolve_terminal_indices(
            panel,
            TerminalRequest(
                kind=TerminalKind.FIXED_HORIZON,
                horizon_minutes=horizon_minutes,
                roll_policy=policy,
            ),
        )
        resolution = model.resolutions[0]
        verdict = evaluate_roll_guard(
            entry_ts=source.event_ts,
            label_horizon_ts=terminal.event_ts,
            calendar=panel.roll_calendar,
            policy=policy,
            root_symbol="ES",
        )

        assert resolution.reason == verdict.reason
        if policy is RollCrossPolicy.TRUNCATE:
            assert resolution.disposition is TerminalGuardDisposition.TRUNCATE
            assert resolution.terminal_index == 1
            assert resolution.effective_terminal_ts == roll_boundary_ts
        elif policy is RollCrossPolicy.FLAG:
            assert resolution.disposition is TerminalGuardDisposition.FLAG
            assert resolution.terminal_index == 2
            assert "roll_splice_flag" in resolution.quality_flags
        elif policy is RollCrossPolicy.INVALID:
            assert resolution.disposition is TerminalGuardDisposition.INVALID
            assert resolution.terminal_index is None
        else:
            assert resolution.disposition is TerminalGuardDisposition.DROP
            assert resolution.terminal_index is None


def test_roll_truncation_terminal_kind_uses_exact_boundary_terminal() -> None:
    source_ts = _dt("2024-03-06T23:45:00+00:00")
    roll_boundary_ts = _dt("2024-03-07T00:00:00+00:00")
    requested_terminal_ts = _dt("2024-03-07T00:15:00+00:00")
    horizon_minutes = int((requested_terminal_ts - source_ts).total_seconds() // 60)
    panel = build_shared_label_panel(
        symbol="ES",
        year=2024,
        ohlcv_rows=(
            _ohlcv_mapping(source_ts, close=Decimal("100"), contract_id="ESH4"),
            _ohlcv_mapping(roll_boundary_ts, close=Decimal("100.5"), contract_id="ESH4"),
            _ohlcv_mapping(requested_terminal_ts, close=Decimal("101"), contract_id="ESH4"),
        ),
    )

    model = resolve_terminal_indices(
        panel,
        TerminalRequest(
            kind=TerminalKind.ROLL_TRUNCATION,
            horizon_minutes=horizon_minutes,
            roll_policy=RollCrossPolicy.TRUNCATE,
        ),
    )

    assert model.resolutions[0].kind is TerminalKind.ROLL_TRUNCATION
    assert model.resolutions[0].disposition is TerminalGuardDisposition.TRUNCATE
    assert model.resolutions[0].terminal_index == 1


def test_maintenance_crossing_terminal_semantics_match_reference_drop() -> None:
    source_ts = _dt("2024-01-02T21:45:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=30)
    ohlcv_rows = (
        _ohlcv_mapping(source_ts, close=Decimal("100"), contract_id="ESH4"),
        _ohlcv_mapping(terminal_ts, close=Decimal("101"), contract_id="ESH4"),
    )
    panel = build_shared_label_panel(symbol="ES", year=2024, ohlcv_rows=ohlcv_rows)

    resolution = resolve_terminal_indices(
        panel,
        TerminalRequest(kind=TerminalKind.FIXED_HORIZON, horizon_minutes=30),
    ).resolutions[0]
    metadata = quality_metadata_for_resolution(panel, resolution)

    assert resolution.disposition is TerminalGuardDisposition.DROP
    assert resolution.reason == QUALITY_FLAG_MAINTENANCE_CROSSING
    assert QUALITY_FLAG_SESSION_RESET in metadata.gap_reasons

    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_30M,
        fixed_horizon_label_spec(),
        dataset_version_ids=(DATASET_ID,),
    )
    assert compute_fixed_horizon_label(definition, _ohlcv_input_view(ohlcv_rows)) == ()


def test_close_out_terminal_kinds_use_reference_scope_boundaries() -> None:
    ohlcv_rows = (
        _ohlcv_mapping(_dt("2024-01-02T20:58:00+00:00"), close=Decimal("100")),
        _ohlcv_mapping(_dt("2024-01-02T20:59:00+00:00"), close=Decimal("101")),
        _ohlcv_mapping(_dt("2024-01-02T21:00:00+00:00"), close=Decimal("102")),
        _ohlcv_mapping(_dt("2024-01-02T21:30:00+00:00"), close=Decimal("103")),
        _ohlcv_mapping(_dt("2024-01-02T22:00:00+00:00"), close=Decimal("104")),
    )
    panel = build_shared_label_panel(symbol="ES", year=2024, ohlcv_rows=ohlcv_rows)

    session_model = resolve_terminal_indices(
        panel,
        TerminalRequest(kind=TerminalKind.SESSION_CLOSE),
    )
    maintenance_model = resolve_terminal_indices(
        panel,
        TerminalRequest(kind=TerminalKind.MAINTENANCE_FLAT),
    )

    assert session_model.resolutions[0].terminal_index == 2
    assert session_model.resolutions[2].disposition is TerminalGuardDisposition.DROP
    assert maintenance_model.resolutions[3].terminal_index == 4
    assert maintenance_model.resolutions[3].disposition is TerminalGuardDisposition.PASS


def test_session_gap_without_exact_terminal_is_insufficient_window_metadata() -> None:
    rows = minute_ohlcv_rows(
        _dt("2024-01-02T14:30:00+00:00"),
        count=3,
    )
    panel = build_shared_label_panel(symbol="ES", year=2024, ohlcv_rows=rows)

    resolution = resolve_terminal_indices(
        panel,
        TerminalRequest(kind=TerminalKind.FIXED_HORIZON, horizon_minutes=5),
    ).resolutions[0]
    metadata = quality_metadata_for_resolution(panel, resolution)

    assert resolution.disposition is TerminalGuardDisposition.DROP
    assert resolution.reason == QUALITY_FLAG_INSUFFICIENT_WINDOW
    assert QUALITY_FLAG_INSUFFICIENT_WINDOW in metadata.gap_reasons


def test_label_available_ts_derivation_matches_reference_availability_policy() -> None:
    source_ts = _dt("2024-01-02T14:30:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=30)
    availability_floor = "2024-01-02T16:00:00+00:00"
    ohlcv_rows = (
        _ohlcv_mapping(source_ts, close=Decimal("100"), contract_id="ESH4"),
        _ohlcv_mapping(terminal_ts, close=Decimal("101"), contract_id="ESH4"),
    )
    definition = build_fixed_horizon_label_definition(
        FixedHorizonLabelName.FWD_RET_30M,
        fixed_horizon_label_spec(availability_time=availability_floor),
        dataset_version_ids=(DATASET_ID,),
    )
    reference_records = compute_fixed_horizon_label(definition, _ohlcv_input_view(ohlcv_rows))
    panel = build_shared_label_panel(symbol="ES", year=2024, ohlcv_rows=ohlcv_rows)
    resolution = resolve_terminal_indices(
        panel,
        TerminalRequest(kind=TerminalKind.FIXED_HORIZON, horizon_minutes=30),
    ).resolutions[0]
    terminal = panel.row_at(resolution.terminal_index)

    derived = derive_label_available_ts(
        LabelAvailabilityFamily.FIXED_HORIZON,
        definition.contract.availability_policy,
        horizon_end_ts=terminal.event_ts,
        terminal_available_ts=terminal.available_ts,
    )

    assert len(reference_records) == 1
    assert derived == reference_records[0].label_available_ts
    assert derived == _dt(availability_floor)


def _ohlcv_mapping(
    event_ts: datetime,
    *,
    close: Decimal,
    contract_id: str = "ESH4",
    session_label: str = "RTH",
) -> dict[str, object]:
    return {
        "instrument_id": "ES",
        "contract_id": contract_id,
        "series_id": "ES_CONTINUOUS",
        "bar_start_ts": (event_ts - timedelta(minutes=1)).isoformat(),
        "bar_end_ts": event_ts.isoformat(),
        "event_ts": event_ts.isoformat(),
        "available_ts": (event_ts + timedelta(seconds=1)).isoformat(),
        "ingested_at": (event_ts + timedelta(seconds=2)).isoformat(),
        "open": close,
        "high": close + Decimal("0.25"),
        "low": close - Decimal("0.25"),
        "close": close,
        "volume": Decimal("10"),
        "data_version": DATASET_ID,
        "quality_flags": (),
        "session_label": session_label,
    }


def _ohlcv_input_view(rows: tuple[dict[str, object], ...]) -> OHLCVInputView:
    return OHLCVInputView(
        tuple(
            OHLCVInputRow(
                instrument_id=str(row["instrument_id"]),
                contract_id=str(row["contract_id"]),
                series_id=str(row["series_id"]),
                bar_start_ts=_dt(str(row["bar_start_ts"])),
                bar_end_ts=_dt(str(row["bar_end_ts"])),
                event_ts=_dt(str(row["event_ts"])),
                available_ts=_dt(str(row["available_ts"])),
                ingested_at=_dt(str(row["ingested_at"])),
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row["volume"])),
                data_version=DATASET_ID,
                quality_flags=tuple(row["quality_flags"]),
                session_label=str(row["session_label"]),
            )
            for row in rows
        )
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
