from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.features.scaleout import load_scaleout_config, run_scaleout
from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.families.fixed_horizon import (
    FixedHorizonLabelName,
    build_fixed_horizon_label_definition,
    compute_fixed_horizon_label,
)


DATASET_ID = "dsv_futsub_p18_synthetic"
CONFIG_PATH = "configs/labels/scaleout/session_close_maintenance_flat.json"


def test_session_close_label_resolves_same_session_terminal_available_ts() -> None:
    definition = _definition(FixedHorizonLabelName.SESSION_CLOSE)
    source_ts = _dt("2024-01-02T20:58:00+00:00")
    terminal_ts = _dt("2024-01-02T21:00:00+00:00")
    terminal_available_ts = terminal_ts + timedelta(seconds=3)

    records = compute_fixed_horizon_label(
        definition,
        OHLCVInputView(
            (
                _row(source_ts, close=Decimal("100"), session_label="RTH"),
                _row(
                    source_ts + timedelta(minutes=1),
                    close=Decimal("101"),
                    session_label="RTH",
                ),
                _row(
                    terminal_ts,
                    close=Decimal("102"),
                    session_label="RTH",
                    available_ts=terminal_available_ts,
                ),
            )
        ),
    )

    assert len(records) == 2
    first = records[0]
    assert first.event_ts == source_ts
    assert first.horizon_end_ts == terminal_ts
    assert first.label_available_ts == terminal_available_ts
    assert first.value == pytest.approx(0.02)


def test_close_out_windows_do_not_cross_maintenance_or_roll() -> None:
    maintenance_definition = _definition(FixedHorizonLabelName.MAINTENANCE_FLAT)
    source_before_break = _dt("2024-01-02T21:45:00+00:00")

    maintenance_records = compute_fixed_horizon_label(
        maintenance_definition,
        OHLCVInputView(
            (
                _row(source_before_break, close=Decimal("100"), session_label="RTH"),
                _row(
                    _dt("2024-01-02T23:00:00+00:00"),
                    close=Decimal("101"),
                    session_label="ETH",
                ),
            )
        ),
    )

    assert maintenance_records == ()

    session_definition = _definition(FixedHorizonLabelName.SESSION_CLOSE)
    roll_source = _dt("2024-03-07T23:45:00+00:00")
    roll_terminal = _dt("2024-03-08T21:00:00+00:00")

    roll_records = compute_fixed_horizon_label(
        session_definition,
        OHLCVInputView(
            (
                _row(
                    roll_source,
                    contract_id="ESM4",
                    close=Decimal("100"),
                    session_label="ETH",
                ),
                _row(
                    roll_terminal,
                    contract_id="ESM4",
                    close=Decimal("101"),
                    session_label="RTH",
                ),
            )
        ),
    )

    assert roll_records == ()


def test_session_close_maintenance_flat_scaleout_plans_reference_label_units() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="full-window", workers=4)

    assert config.label_names == ("session_close", "maintenance_flat")
    assert summary.engine == "reference"
    assert summary.accepted_unit_count == 48
    assert summary.planned_count == 48
    assert summary.failed_count == 0
    assert summary.worker_plan.effective_workers == 1
    assert {record.unit.year for record in summary.records} == set(range(2019, 2027))
    assert all(record.status == "planned" for record in summary.records)
    assert all(record.label_version_ids for record in summary.records)
    assert all(not record.feature_version_ids for record in summary.records)


def _definition(name: FixedHorizonLabelName):
    return build_fixed_horizon_label_definition(
        name,
        create_label_spec(
            horizon=name.value,
            path_rules={
                "path": "trade_price_close_out_return",
                "close_out_terminal": name.value,
                "terminal_rule": "synthetic close-out terminal test",
                "terminal_key": "series_id+contract_id+event_ts",
            },
            cost_model={
                "model": "gross_unadjusted_close_out_return",
                "adjustment_scope": "not_applied_in_guard_test",
            },
            target_stop_rules={
                "target_rule": "not_used_for_close_out_guard_test",
                "stop_rule": "not_used_for_close_out_guard_test",
            },
            availability_time="2024-01-01T00:00:00+00:00",
            forbidden_feature_overlap={
                "label_ids": [name.value],
                "aliases": [f"synthetic_{name.value}"],
                "transforms": [f"label({name.value})"],
            },
            leakage_checks=["label_as_feature", "availability_time"],
        ),
        dataset_version_ids=(DATASET_ID,),
    )


def _row(
    event_ts: datetime,
    *,
    close: Decimal,
    contract_id: str = "ESH4",
    session_label: str,
    available_ts: datetime | None = None,
) -> OHLCVInputRow:
    available = available_ts or event_ts + timedelta(seconds=1)
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id=contract_id,
        series_id="ES_CONTINUOUS",
        bar_start_ts=event_ts - timedelta(minutes=1),
        bar_end_ts=event_ts,
        event_ts=event_ts,
        available_ts=available,
        ingested_at=available + timedelta(seconds=1),
        open=close,
        high=close + Decimal("0.25"),
        low=close - Decimal("0.25"),
        close=close,
        volume=Decimal("10"),
        data_version=DATASET_ID,
        quality_flags=(),
        session_label=session_label,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
