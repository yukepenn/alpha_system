from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest

from alpha_system.data.foundation.rolls import (
    build_analytic_cme_equity_index_quarterly_roll_calendar,
)
from alpha_system.features.input_views import BBOInputRow, BBOInputView
from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelName,
    build_cost_adjusted_label_definition,
    compute_cost_adjusted_labels,
)
from alpha_system.labels.families.cost_adjusted.family import (
    _bbo_rows_by_key,
    _validated_rows,
)
from alpha_system.labels.roll_guard import RollCrossPolicy, RollGuardAction, evaluate_roll_guard
from tools.futures_substrate_scaleout.guard_drop_enumerator import (
    classify_guard_window,
    enumerate_counts_for_rows,
)

DATASET_ID = "dsv_futsub_p121500_synthetic"


def test_cost_adjusted_guard_drop_counts_match_reference_family() -> None:
    definition = _definition(CostAdjustedLabelName.COST_ADJUSTED_FWD_RET, horizon="30m")
    normal_source = _dt("2024-01-02T14:30:00+00:00")
    roll_source = _dt("2024-03-07T23:45:00+00:00")
    maintenance_source = _dt("2024-01-02T21:45:00+00:00")
    rows = (
        _bbo_row(normal_source, contract_id="ESH4"),
        _bbo_row(normal_source + timedelta(minutes=30), contract_id="ESH4"),
        _bbo_row(roll_source, contract_id="ESM4"),
        _bbo_row(roll_source + timedelta(minutes=30), contract_id="ESM4"),
        _bbo_row(maintenance_source, contract_id="ESH4"),
        _bbo_row(maintenance_source + timedelta(minutes=30), contract_id="ESH4"),
    )

    reference_records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(rows),
    )[CostAdjustedLabelName.COST_ADJUSTED_FWD_RET]
    source_events = {record.event_ts for record in reference_records}
    assert normal_source in source_events
    assert roll_source not in source_events
    assert maintenance_source not in source_events

    (counts,) = enumerate_counts_for_rows(
        rows,
        symbol="ES",
        year=2024,
        horizons=("30m",),
        ohlcv_dataset_version_id=DATASET_ID,
        bbo_dataset_version_id=DATASET_ID,
        acceptance_state="ACCEPTED",
    )

    assert counts.source_row_count == 6
    assert counts.terminal_present_count == 3
    assert counts.kept_count == 1
    assert counts.roll_drop_count == 1
    assert counts.maintenance_drop_count == 1
    assert counts.guard_drop_count == 2
    assert counts.truncated_count == 0
    assert counts.flagged_count == 0


@pytest.mark.parametrize("policy", tuple(RollCrossPolicy))
def test_roll_policy_classification_matches_roll_guard_primitive(
    policy: RollCrossPolicy,
) -> None:
    calendar = build_analytic_cme_equity_index_quarterly_roll_calendar(
        root_symbols=("ES",),
        start_year=2024,
        end_year=2024,
    )
    roll_record = next(record for record in calendar if record.root_symbol == "ES")
    source_ts = datetime.combine(
        roll_record.roll_date - timedelta(days=1),
        time(23, 45),
        tzinfo=UTC,
    )
    boundary_ts = datetime.combine(roll_record.roll_date, time.min, tzinfo=UTC)
    terminal_ts = source_ts + timedelta(minutes=240)
    rows = _validated_rows(
        (
            _bbo_row(source_ts, contract_id="ESH4"),
            _bbo_row(boundary_ts, contract_id="ESH4"),
            _bbo_row(terminal_ts, contract_id="ESH4"),
        )
    )
    row_index = _bbo_rows_by_key(rows)
    source = row_index[("ES_CONTINUOUS", "ESH4", source_ts)]
    terminal = row_index[("ES_CONTINUOUS", "ESH4", terminal_ts)]

    decision = classify_guard_window(
        source,
        terminal,
        terminal_by_key=row_index,
        roll_calendar_cache={},
        policy=policy,
    )
    verdict = evaluate_roll_guard(
        entry_ts=source_ts,
        label_horizon_ts=terminal_ts,
        calendar=calendar,
        policy=policy,
        root_symbol="ES",
    )

    assert decision.reason == verdict.reason
    assert decision.roll_calendar_id == verdict.matched_roll_calendar_id
    if verdict.action is RollGuardAction.DROP:
        assert decision.disposition == "roll_drop"
    elif verdict.action is RollGuardAction.TRUNCATE:
        assert decision.disposition == "truncated"
    elif verdict.action is RollGuardAction.FLAG:
        assert decision.disposition == "flagged"
    elif verdict.action is RollGuardAction.INVALID:
        assert decision.disposition == "roll_drop"
    else:  # pragma: no cover - RollGuardAction currently has no other crossing action.
        raise AssertionError(f"unexpected action: {verdict.action}")


def _definition(
    name: CostAdjustedLabelName,
    *,
    horizon: str = "30m",
):
    return build_cost_adjusted_label_definition(
        name,
        _label_spec(name, horizon=horizon),
        dataset_version_ids=(DATASET_ID,),
    )


def _label_spec(
    name: CostAdjustedLabelName,
    *,
    horizon: str,
):
    model = (
        "spread_plus_bps"
        if name is CostAdjustedLabelName.COST_ADJUSTED_FWD_RET
        else "spread_adjusted"
    )
    cost_model: dict[str, object] = {
        "model": model,
        "spread_adjustment": "half_spread_round_trip",
    }
    if model == "spread_plus_bps":
        cost_model["fixed_cost_bps"] = 0.25
    return create_label_spec(
        horizon=horizon,
        path_rules={
            "path": "bbo_mid_forward_return",
            "terminal_rule": "synthetic exact BBO horizon",
            "horizon_steps": int(horizon.removesuffix("m")),
        },
        cost_model=cost_model,
        target_stop_rules={
            "target_rule": "not_used_for_guard_drop_count_test",
            "stop_rule": "not_used_for_guard_drop_count_test",
        },
        availability_time="2024-01-01T00:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [name.value],
            "aliases": [f"synthetic_{name.value}"],
            "transforms": [f"label({name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )


def _bbo_row(
    event_ts: datetime,
    *,
    contract_id: str,
    mid: Decimal = Decimal("100.00"),
) -> BBOInputRow:
    bar_start = event_ts - timedelta(minutes=1)
    available = event_ts + timedelta(seconds=1)
    spread = Decimal("0.25")
    return BBOInputRow(
        instrument_id="ES",
        contract_id=contract_id,
        series_id="ES_CONTINUOUS",
        bar_start_ts=bar_start,
        bar_end_ts=event_ts,
        event_ts=event_ts,
        available_ts=available,
        ingested_at=available + timedelta(seconds=1),
        bid=mid - spread / Decimal("2"),
        ask=mid + spread / Decimal("2"),
        bid_size=Decimal("10"),
        ask_size=Decimal("10"),
        mid=mid,
        spread=spread,
        data_version=DATASET_ID,
        quality_flags=(),
        session_label="ETH",
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)
