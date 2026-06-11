from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("polars")

from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.families.path import (
    PathLabelName,
    build_path_label_definition,
)
from alpha_system.labels.fast.panel import SharedLabelPanel, SharedLabelPanelRow
from alpha_system.labels.fast.path import compute_path_records_from_panel


def test_path_fast_labels_resolve_values_and_point_in_time_availability() -> None:
    source_ts = _dt("2024-01-02T14:30:00+00:00")
    panel = SharedLabelPanel(
        symbol="ES",
        year=2024,
        rows=(
            _row(0, source_ts, close=100.0, high=100.0, low=100.0),
            _row(1, source_ts + timedelta(minutes=1), close=100.5, high=101.0, low=99.0),
            _row(2, source_ts + timedelta(minutes=2), close=102.0, high=103.0, low=99.5),
            _row(3, source_ts + timedelta(minutes=3), close=101.0, high=102.0, low=97.0),
        ),
    )

    mfe = _records(panel, PathLabelName.MFE, horizon_steps=3)
    mae = _records(panel, PathLabelName.MAE, horizon_steps=3)
    target_before_stop = _records(
        panel,
        PathLabelName.TARGET_BEFORE_STOP,
        horizon_steps=3,
    )

    mfe_source = _single_record(mfe, source_ts)
    mae_source = _single_record(mae, source_ts)
    target_source = _single_record(target_before_stop, source_ts)

    assert mfe_source.value == pytest.approx(0.03)
    assert mae_source.value == pytest.approx(-0.03)
    assert mfe_source.horizon_end_ts == source_ts + timedelta(minutes=3)
    assert mae_source.horizon_end_ts == source_ts + timedelta(minutes=3)
    assert mfe_source.label_available_ts == source_ts + timedelta(minutes=3, seconds=1)
    assert mae_source.label_available_ts == source_ts + timedelta(minutes=3, seconds=1)

    assert target_source.value is True
    assert target_source.horizon_end_ts == source_ts + timedelta(minutes=2)
    assert target_source.label_available_ts == source_ts + timedelta(minutes=2, seconds=1)


def test_path_fast_labels_drop_roll_and_maintenance_crossing_windows() -> None:
    roll_source_ts = _dt("2024-03-07T23:45:00+00:00")
    roll_panel = SharedLabelPanel(
        symbol="ES",
        year=2024,
        rows=(
            _row(0, roll_source_ts, close=100.0, high=100.0, low=100.0, contract_id="ESH4"),
            _row(
                1,
                roll_source_ts + timedelta(minutes=15),
                close=100.5,
                high=101.0,
                low=99.5,
                contract_id="ESH4",
            ),
            _row(
                2,
                roll_source_ts + timedelta(minutes=30),
                close=101.0,
                high=101.5,
                low=100.0,
                contract_id="ESH4",
            ),
        ),
    )

    maintenance_source_ts = _dt("2024-01-02T21:45:00+00:00")
    maintenance_panel = SharedLabelPanel(
        symbol="ES",
        year=2024,
        rows=(
            _row(0, maintenance_source_ts, close=100.0, high=100.0, low=100.0),
            _row(
                1,
                maintenance_source_ts + timedelta(minutes=15),
                close=100.5,
                high=101.0,
                low=99.5,
            ),
            _row(
                2,
                maintenance_source_ts + timedelta(minutes=30),
                close=101.0,
                high=101.5,
                low=100.0,
            ),
        ),
    )

    roll_records = _records(roll_panel, PathLabelName.MFE, horizon_steps=2)
    maintenance_records = _records(
        maintenance_panel,
        PathLabelName.TARGET_BEFORE_STOP,
        horizon_steps=2,
    )

    assert all(record.event_ts != roll_source_ts for record in roll_records)
    assert all(
        record.event_ts != maintenance_source_ts for record in maintenance_records
    )


def test_path_label_identity_is_materialization_scoped() -> None:
    es_definition = _definition(
        PathLabelName.MFE,
        horizon_steps=5,
        materialization_scope={
            "symbol": "ES",
            "partition_id": "ES_2024_5m",
            "dataset_version_id": "dsv_synthetic",
            "window_start_ts": "2024-01-01T00:00:00+00:00",
            "window_end_ts": "2025-01-01T00:00:00+00:00",
            "horizon": "5m",
        },
    )
    nq_definition = _definition(
        PathLabelName.MFE,
        horizon_steps=5,
        materialization_scope={
            "symbol": "NQ",
            "partition_id": "NQ_2024_5m",
            "dataset_version_id": "dsv_synthetic",
            "window_start_ts": "2024-01-01T00:00:00+00:00",
            "window_end_ts": "2025-01-01T00:00:00+00:00",
            "horizon": "5m",
        },
    )

    assert es_definition.label_version_id != nq_definition.label_version_id


def _records(
    panel: SharedLabelPanel,
    name: PathLabelName,
    *,
    horizon_steps: int,
) -> tuple[object, ...]:
    return compute_path_records_from_panel(
        panel,
        _definition(name, horizon_steps=horizon_steps),
    )


def _definition(
    name: PathLabelName,
    *,
    horizon_steps: int,
    materialization_scope: dict[str, str] | None = None,
):
    return build_path_label_definition(
        name,
        create_label_spec(
            horizon=f"{horizon_steps}_trade_bars",
            path_rules={
                "path": "ohlcv_trade_truth_forward_path",
                "horizon_steps": horizon_steps,
                "price_field": "close",
                "direction": "long",
            },
            cost_model={"model": "gross_path_labels_unadjusted"},
            target_stop_rules={
                "target_return": 0.02,
                "stop_return": -0.02,
                "same_bar_policy": "ambiguous",
            },
            availability_time="2024-01-01T00:00:00+00:00",
            forbidden_feature_overlap={
                "label_ids": [f"path_{name.value}"],
                "aliases": [name.value],
                "transforms": [f"label(path_{name.value})"],
            },
            leakage_checks=["label_as_feature", "availability_time"],
        ),
        dataset_version_ids=("dsv_synthetic",),
        materialization_scope=materialization_scope,
    )


def _row(
    index: int,
    event_ts: datetime,
    *,
    close: float,
    high: float,
    low: float,
    contract_id: str = "ESH4",
) -> SharedLabelPanelRow:
    return SharedLabelPanelRow(
        row_index=index,
        instrument_id="ES",
        series_id="ES.c.0",
        contract_id=contract_id,
        event_ts=event_ts,
        bar_end_ts=event_ts,
        available_ts=event_ts + timedelta(seconds=1),
        open=close,
        trade_price=close,
        high=high,
        low=low,
        volume=1.0,
    )


def _single_record(records: tuple[object, ...], event_ts: datetime):
    matches = tuple(record for record in records if record.event_ts == event_ts)
    assert len(matches) == 1
    return matches[0]


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
