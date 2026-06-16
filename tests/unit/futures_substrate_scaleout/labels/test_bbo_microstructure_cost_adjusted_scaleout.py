"""Canaries for the BBO-resident microstructure cost-adjusted label config.

These guards lock the load-bearing properties of
``configs/labels/scaleout/bbo_microstructure_cost_adjusted.json``:

1. Planned units REGISTER on the BBO DatasetVersion (``dsv_databento_bbo_*`` /
   ``schema_id == "bbo_1m"``) rather than the deprecated OHLCV-primary
   DatasetVersion. This is the core flip versus ``cost_adjusted.json`` and the
   reason the microstructure lane is unblocked with zero new materialization.
2. The single-dsv wall is respected: each unit wires exactly one input
   DatasetVersion, and it is the BBO one.
3. The config writes to a value namespace distinct from the deprecated
   OHLCV-primary cost_adjusted namespace (no value-truth collision).
4. The reference cost_adjusted engine math is unchanged: no look-ahead
   (``label_available_ts >= horizon_end_ts > event_ts``) and a hand-checked
   value on a tiny BBO fixture (entry mid 100.00 -> terminal mid 101.00 at +5m).

The value math itself lives ONLY in the sanctioned reference engine
(``alpha_system.labels.families.cost_adjusted``); this config selects parameters
and an input schema and adds no second value truth.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from alpha_system.features.input_views import BBOInputRow, BBOInputView
from alpha_system.features.scaleout import (
    ScaleoutTarget,
    load_scaleout_config,
    run_scaleout,
)
from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelName,
    build_cost_adjusted_label_definition,
    compute_cost_adjusted_labels,
)

CONFIG_PATH = "configs/labels/scaleout/bbo_microstructure_cost_adjusted.json"
OHLCV_PRIMARY_CONFIG_PATH = "configs/labels/scaleout/cost_adjusted.json"
DATASET_ID = "dsv_futsub_bbo_microstructure_synthetic"


def _summary_for(config_path: str):
    config = load_scaleout_config(config_path)
    return config, run_scaleout(
        config,
        rollout="full-window",
        execute=False,
        engine="reference",
        target=ScaleoutTarget(symbols=("ES",), years=(2024,)),
    )


def test_bbo_microstructure_units_register_on_bbo_dataset_version() -> None:
    """Core flip: planned units bind to the BBO dsv + bbo_1m schema."""

    _config, summary = _summary_for(CONFIG_PATH)

    assert summary.records, "expected planned label units"
    for record in summary.records:
        unit = record.unit
        assert unit.schema_id == "bbo_1m", (
            f"unit {unit.unit_id} primary schema is {unit.schema_id}, expected bbo_1m"
        )
        assert unit.dataset_version_id.startswith("dsv_databento_bbo_"), (
            f"unit {unit.unit_id} binds {unit.dataset_version_id}, expected a BBO dsv"
        )


def test_bbo_microstructure_flips_primary_versus_ohlcv_primary_config() -> None:
    """The microstructure config registers on BBO where cost_adjusted.json uses OHLCV."""

    _bbo_config, bbo_summary = _summary_for(CONFIG_PATH)
    _ohlcv_config, ohlcv_summary = _summary_for(OHLCV_PRIMARY_CONFIG_PATH)

    bbo_schemas = {record.unit.schema_id for record in bbo_summary.records}
    ohlcv_schemas = {record.unit.schema_id for record in ohlcv_summary.records}

    assert bbo_schemas == {"bbo_1m"}
    assert "ohlcv_1m" in ohlcv_schemas
    # The deprecated config registers on OHLCV; the new config flips to BBO.
    assert bbo_schemas != ohlcv_schemas


def test_bbo_microstructure_respects_single_dsv_wall() -> None:
    """Each unit wires exactly one input DatasetVersion, and it is the BBO one."""

    _config, summary = _summary_for(CONFIG_PATH)

    for record in summary.records:
        unit = record.unit
        assert len(unit.input_datasets) == 1, (
            f"unit {unit.unit_id} wires {len(unit.input_datasets)} input datasets; "
            "the single-dsv wall must not be relaxed"
        )
        only = unit.input_datasets[0]
        assert only.schema_id == "bbo_1m"
        assert only.dataset_version_id == unit.dataset_version_id


def test_bbo_microstructure_uses_distinct_value_namespace() -> None:
    """The microstructure namespace must not collide with deprecated OHLCV-primary lvers."""

    bbo_config = load_scaleout_config(CONFIG_PATH)
    ohlcv_config = load_scaleout_config(OHLCV_PRIMARY_CONFIG_PATH)

    assert bbo_config.value_namespace != ohlcv_config.value_namespace
    assert "bbo_microstructure" in bbo_config.value_namespace


def test_bbo_microstructure_governed_scope_is_cost_aware_gate_plus_diagnostic() -> None:
    """Pre-registered GATE = spread_adjusted_fwd_ret; gross/cost variant is diagnostic."""

    config = load_scaleout_config(CONFIG_PATH)
    assert config.family == "cost_adjusted"
    assert set(config.label_names) == {
        "spread_adjusted_fwd_ret",
        "cost_adjusted_fwd_ret",
    }
    assert set(config.horizons) == {"5m", "15m", "30m"}


@pytest.mark.parametrize("horizon", ["5m", "15m", "30m"])
def test_bbo_microstructure_no_look_ahead(horizon: str) -> None:
    """label_available_ts >= horizon_end_ts > event_ts on a BBO fixture."""

    source_ts = _dt("2024-01-02T14:30:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=int(horizon.removesuffix("m")))
    definition = _definition(CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET, horizon=horizon)

    records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(
            (
                _bbo_row(source_ts, mid=Decimal("100.00")),
                _bbo_row(terminal_ts, mid=Decimal("101.00")),
            )
        ),
    )[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET]

    source_records = tuple(r for r in records if r.event_ts == source_ts)
    assert len(source_records) == 1
    record = source_records[0]
    assert record.event_ts < record.horizon_end_ts
    assert record.horizon_end_ts <= record.label_available_ts


def test_bbo_microstructure_hand_computed_value_matches_reference_engine() -> None:
    """Entry mid 100.00 -> terminal mid 101.00 at +5m, spread 0.25 both legs.

    gross  = 101/100 - 1 = 0.01
    half-spread round trip adjustment
           = 0.5*(0.25/100) + 0.5*(0.25/101)
    spread_adjusted_fwd_ret = gross - adjustment
    cost_adjusted_fwd_ret   = spread_adjusted_fwd_ret - 0.25 bps (0.000025)
    """

    source_ts = _dt("2024-01-02T14:30:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=5)
    entry_mid = Decimal("100.00")
    terminal_mid = Decimal("101.00")
    spread = Decimal("0.25")

    gross = terminal_mid / entry_mid - Decimal("1")
    adjustment = Decimal("0.5") * (spread / entry_mid) + Decimal("0.5") * (spread / terminal_mid)
    expected_spread_adjusted = gross - adjustment
    expected_cost_adjusted = expected_spread_adjusted - Decimal("0.25") / Decimal("10000")

    definitions = (
        _definition(CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET),
        _definition(CostAdjustedLabelName.COST_ADJUSTED_FWD_RET),
    )
    records = compute_cost_adjusted_labels(
        definitions,
        BBOInputView(
            (
                _bbo_row(source_ts, mid=entry_mid, spread=spread),
                _bbo_row(terminal_ts, mid=terminal_mid, spread=spread),
            )
        ),
    )

    spread_record = records[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET][0]
    cost_record = records[CostAdjustedLabelName.COST_ADJUSTED_FWD_RET][0]

    # gross sanity: the cost-aware GATE sits below the gross internal terminal.
    assert float(gross) == pytest.approx(0.01)
    assert spread_record.value == pytest.approx(float(expected_spread_adjusted))
    assert cost_record.value == pytest.approx(float(expected_cost_adjusted))
    # Cost overlay is strictly more conservative than the spread-only gate.
    assert cost_record.value < spread_record.value


def _definition(name: CostAdjustedLabelName, *, horizon: str = "5m"):
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
    spec = create_label_spec(
        horizon=horizon,
        path_rules={
            "path": "bbo_mid_forward_return",
            "terminal_rule": "synthetic exact BBO horizon",
            "horizon_steps": int(horizon.removesuffix("m")),
        },
        cost_model=cost_model,
        target_stop_rules={
            "target_rule": "not_used_for_cost_adjusted_test",
            "stop_rule": "not_used_for_cost_adjusted_test",
        },
        availability_time="2024-01-01T00:00:00+00:00",
        forbidden_feature_overlap={
            "label_ids": [name.value],
            "aliases": [f"synthetic_{name.value}"],
            "transforms": [f"label({name.value})"],
        },
        leakage_checks=["label_as_feature", "availability_time"],
    )
    return build_cost_adjusted_label_definition(
        name,
        spec,
        dataset_version_ids=(DATASET_ID,),
    )


def _bbo_row(
    event_ts: datetime,
    *,
    contract_id: str = "ESH4",
    mid: Decimal = Decimal("100.00"),
    spread: Decimal = Decimal("0.25"),
    bar_start_ts: datetime | None = None,
    bar_end_ts: datetime | None = None,
    available_ts: datetime | None = None,
) -> BBOInputRow:
    bar_end = bar_end_ts or event_ts
    bar_start = bar_start_ts or bar_end - timedelta(minutes=1)
    available = available_ts or bar_end + timedelta(seconds=1)
    return BBOInputRow(
        instrument_id="ES",
        contract_id=contract_id,
        series_id="ES_CONTINUOUS",
        bar_start_ts=bar_start,
        bar_end_ts=bar_end,
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
