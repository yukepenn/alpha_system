from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.governance.label_spec import LabelSpec, create_label_spec
from alpha_system.labels.families.path import (
    PathLabelError,
    PathLabelName,
    build_path_label_definition,
    build_path_label_definitions,
    compute_path_label,
    compute_path_labels,
    supported_path_labels,
)
from alpha_system.labels.version import LabelContractError, LabelFamily


def test_all_path_labels_are_governance_bound_versioned_and_available() -> None:
    view = _fixture_view()
    definitions = build_path_label_definitions(
        {name: _label_spec() for name in supported_path_labels()},
        dataset_version_ids=("dsv_synthetic_path",),
    )

    results = compute_path_labels(definitions, view)

    assert set(results) == set(PathLabelName)
    for definition in definitions:
        assert definition.contract.family is LabelFamily.PATH
        assert definition.contract.label_spec_id.startswith("lspec_")
        assert definition.version == definition.contract.derive_label_version()
        assert all(
            record.label_spec_id == definition.contract.label_spec_id
            and record.label_version_id == definition.label_version_id
            and record.label_available_ts >= record.horizon_end_ts
            and record.label_available_ts
            >= definition.contract.availability_policy.availability_time
            for record in results[definition.name]
        )

    mfe = results[PathLabelName.MFE][0]
    mae = results[PathLabelName.MAE][0]
    target_before_stop = results[PathLabelName.TARGET_BEFORE_STOP][0]
    triple_barrier = results[PathLabelName.TRIPLE_BARRIER][0]

    assert mfe.event_ts == _dt("2024-01-02T14:31:00+00:00")
    assert mfe.horizon_end_ts == _dt("2024-01-02T14:34:00+00:00")
    assert mfe.label_available_ts == _dt("2024-01-02T14:34:01+00:00")
    assert mfe.value == pytest.approx(0.03)
    assert mae.value == pytest.approx(-0.03)
    assert target_before_stop.value is True
    assert target_before_stop.horizon_end_ts == _dt("2024-01-02T14:33:00+00:00")
    assert target_before_stop.label_available_ts == _dt("2024-01-02T14:33:01+00:00")
    assert triple_barrier.value == 1


def test_target_stop_and_horizon_resolution_times_are_used() -> None:
    view = _fixture_view()
    target_before_stop = build_path_label_definition(
        PathLabelName.TARGET_BEFORE_STOP,
        _label_spec(target_return=0.02, stop_return=-0.02),
    )
    triple_barrier = build_path_label_definition(
        PathLabelName.TRIPLE_BARRIER,
        _label_spec(target_return=0.02, stop_return=-0.02),
    )

    target_records = compute_path_label(target_before_stop, view)
    triple_records = compute_path_label(triple_barrier, view)

    target_by_event = {record.event_ts: record for record in target_records}
    triple_by_event = {record.event_ts: record for record in triple_records}

    assert target_by_event[_dt("2024-01-02T14:31:00+00:00")].value is True
    assert target_by_event[_dt("2024-01-02T14:33:00+00:00")].value is False
    assert triple_by_event[_dt("2024-01-02T14:33:00+00:00")].value == -1
    assert triple_by_event[_dt("2024-01-02T14:33:00+00:00")].horizon_end_ts == _dt(
        "2024-01-02T14:34:00+00:00"
    )

    no_hit_definition = build_path_label_definition(
        PathLabelName.TRIPLE_BARRIER,
        _label_spec(target_return=0.10, stop_return=-0.10, horizon_steps=2),
    )
    no_hit_records = compute_path_label(no_hit_definition, view)
    assert no_hit_records[0].value == 0
    assert no_hit_records[0].quality_flags == ("horizon_no_barrier",)
    assert no_hit_records[0].horizon_end_ts == _dt("2024-01-02T14:33:00+00:00")


def test_label_available_ts_is_never_before_governed_availability_time() -> None:
    definition = build_path_label_definition(
        PathLabelName.TRIPLE_BARRIER,
        _label_spec(availability_time="2024-01-02T15:00:00+00:00"),
    )

    record = compute_path_label(definition, _fixture_view())[0]

    assert record.horizon_end_ts == _dt("2024-01-02T14:33:00+00:00")
    assert record.label_available_ts == _dt("2024-01-02T15:00:00+00:00")


def test_no_trade_rows_are_excluded_from_path_evaluation() -> None:
    view = _fixture_view()
    definition = build_path_label_definition(PathLabelName.MFE, _label_spec(horizon_steps=3))

    records = compute_path_label(definition, view)

    assert _dt("2024-01-02T14:35:00+00:00") not in {record.event_ts for record in records}
    assert records[1].horizon_end_ts == _dt("2024-01-02T14:36:00+00:00")
    expected_mfe = float((Decimal("104") - Decimal("100.5")) / Decimal("100.5"))
    assert records[1].value == pytest.approx(expected_mfe)


def test_missing_label_spec_and_missing_available_ts_fail_closed() -> None:
    with pytest.raises(PathLabelError, match="LabelSpec"):
        build_path_label_definition(PathLabelName.MFE, None)

    view = _fixture_view()
    corrupt_resolution_row = view.rows[2]
    object.__setattr__(corrupt_resolution_row, "available_ts", None)
    definition = build_path_label_definition(PathLabelName.TRIPLE_BARRIER, _label_spec())

    with pytest.raises(PathLabelError, match="available_ts"):
        compute_path_label(definition, view)


def test_label_as_feature_attempt_is_rejected() -> None:
    definition = build_path_label_definition(PathLabelName.MFE, _label_spec())

    with pytest.raises(LabelContractError, match="live feature"):
        definition.contract.validate_live_feature_references(
            [
                {
                    "feature_id": definition.label_id,
                    "available_at": "2024-01-02T14:31:00+00:00",
                }
            ]
        )


def _fixture_view() -> OHLCVInputView:
    rows = (
        _row("2024-01-02T14:30:00+00:00", open_="100", high="100", low="99", close="100"),
        _row("2024-01-02T14:31:00+00:00", open_="100", high="101", low="99", close="100.5"),
        _row("2024-01-02T14:32:00+00:00", open_="100.5", high="103", low="100", close="102"),
        _row("2024-01-02T14:33:00+00:00", open_="102", high="102", low="97", close="98"),
        _row(
            "2024-01-02T14:34:00+00:00",
            open_="98",
            high="98",
            low="98",
            close="98",
            volume="0",
            quality_flags=("no_trade",),
        ),
        _row("2024-01-02T14:35:00+00:00", open_="98", high="104", low="96", close="103"),
    )
    return OHLCVInputView(rows)


def _row(
    bar_start_ts: str,
    *,
    open_: str,
    high: str,
    low: str,
    close: str,
    volume: str = "10",
    quality_flags: tuple[str, ...] = (),
) -> OHLCVInputRow:
    start = _dt(bar_start_ts)
    return OHLCVInputRow(
        instrument_id="ES",
        contract_id="ESM4",
        series_id="ES.c.0",
        bar_start_ts=start,
        bar_end_ts=start + timedelta(minutes=1),
        event_ts=start + timedelta(minutes=1),
        available_ts=start + timedelta(minutes=1, seconds=1),
        ingested_at=start + timedelta(minutes=1, seconds=2),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        data_version="dsv_synthetic_path",
        quality_flags=quality_flags,
        session_label="RTH",
    )


def _label_spec(
    *,
    horizon_steps: int = 3,
    target_return: float = 0.02,
    stop_return: float = -0.02,
    availability_time: str = "2024-01-02T14:29:00+00:00",
) -> LabelSpec:
    path_ids = [
        "path_mfe",
        "path_mae",
        "path_target_before_stop",
        "path_triple_barrier",
    ]
    return create_label_spec(
        horizon=f"{horizon_steps}_trade_bars",
        path_rules={
            "path": "ohlcv_trade_truth_forward_path",
            "horizon_steps": horizon_steps,
            "price_field": "close",
            "direction": "long",
            "trade_truth_predicate": "alpha_system.features.semantics.is_real_trade_bar",
        },
        cost_model={"model": "gross_path_labels_unadjusted", "reason": "no cost adjustment"},
        target_stop_rules={
            "target_return": target_return,
            "stop_return": stop_return,
            "same_bar_policy": "ambiguous",
        },
        availability_time=availability_time,
        forbidden_feature_overlap={
            "label_ids": path_ids,
            "aliases": ["mfe", "mae", "target_before_stop", "triple_barrier"],
            "transforms": [f"label({label_id})" for label_id in path_ids],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
