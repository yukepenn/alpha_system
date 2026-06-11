from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

import alpha_system.features.scaleout.driver as scaleout_driver
import alpha_system.labels.registry as label_registry_module
from alpha_system.core.value_store import ValueStoreFormat
from alpha_system.features.input_views import BBOInputRow, BBOInputView
from alpha_system.features.scaleout import (
    MaterializedUnitEvidence,
    ScaleoutTarget,
    load_scaleout_config,
    run_scaleout,
)
from alpha_system.governance.label_spec import create_label_spec
from alpha_system.labels.families.cost_adjusted import (
    CostAdjustedLabelError,
    CostAdjustedLabelName,
    build_cost_adjusted_label_definition,
    compute_cost_adjusted_labels,
)


CONFIG_PATH = "configs/labels/scaleout/cost_adjusted.json"
DATASET_ID = "dsv_futsub_p19_bbo_synthetic"


def test_cost_adjusted_variants_emit_label_available_ts_and_cost_delta() -> None:
    source_ts = _dt("2024-01-02T14:30:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=5)
    definitions = (
        _definition(CostAdjustedLabelName.COST_ADJUSTED_FWD_RET),
        _definition(CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET),
    )

    records = compute_cost_adjusted_labels(
        definitions,
        BBOInputView(
            (
                _bbo_row(source_ts, mid=Decimal("100.00")),
                _bbo_row(
                    terminal_ts,
                    mid=Decimal("101.00"),
                    available_ts=terminal_ts + timedelta(seconds=7),
                ),
            )
        ),
    )

    cost_record = records[CostAdjustedLabelName.COST_ADJUSTED_FWD_RET][0]
    spread_record = records[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET][0]
    assert cost_record.label_available_ts == terminal_ts + timedelta(seconds=7)
    assert spread_record.label_available_ts == terminal_ts + timedelta(seconds=7)
    assert cost_record.value < spread_record.value
    assert cost_record.value == pytest.approx(spread_record.value - 0.000025)


def test_cost_adjusted_label_available_ts_includes_source_quote_availability() -> None:
    source_ts = _dt("2024-01-02T14:30:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=5)
    source_available_ts = terminal_ts + timedelta(seconds=11)
    definition = _definition(CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET)

    records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(
            (
                _bbo_row(
                    source_ts,
                    mid=Decimal("100.00"),
                    available_ts=source_available_ts,
                ),
                _bbo_row(
                    terminal_ts,
                    mid=Decimal("101.00"),
                    available_ts=terminal_ts + timedelta(seconds=7),
                ),
            )
        ),
    )[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET]

    source_records = tuple(record for record in records if record.event_ts == source_ts)
    assert len(source_records) == 1
    assert source_records[0].label_available_ts == source_available_ts


def test_cost_adjusted_resolves_intra_bar_bbo_events_by_bar_end_proxy() -> None:
    source_bar_start = _dt("2024-01-02T14:30:00+00:00")
    source_bar_end = source_bar_start + timedelta(minutes=1)
    terminal_bar_end = source_bar_end + timedelta(minutes=5)
    definition = _definition(CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET)

    records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(
            (
                _bbo_row(
                    source_bar_start + timedelta(seconds=37),
                    bar_start_ts=source_bar_start,
                    bar_end_ts=source_bar_end,
                    mid=Decimal("100.00"),
                ),
                _bbo_row(
                    terminal_bar_end - timedelta(seconds=41),
                    bar_start_ts=terminal_bar_end - timedelta(minutes=1),
                    bar_end_ts=terminal_bar_end,
                    mid=Decimal("101.00"),
                ),
            )
        ),
    )[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET]

    source_records = tuple(record for record in records if record.event_ts == source_bar_end)
    assert len(source_records) == 1
    assert source_records[0].horizon_end_ts == terminal_bar_end
    assert source_records[0].label_available_ts == terminal_bar_end + timedelta(seconds=1)
    assert source_records[0].value is not None
    assert "missing_terminal_bbo" not in source_records[0].quality_flags


def test_cost_adjusted_rejects_bbo_events_after_bar_end() -> None:
    bar_start = _dt("2024-01-02T14:30:00+00:00")
    bar_end = bar_start + timedelta(minutes=1)
    definition = _definition(CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET)

    with pytest.raises(CostAdjustedLabelError, match="event_ts must be at or before"):
        compute_cost_adjusted_labels(
            (definition,),
            BBOInputView(
                (
                    _bbo_row(
                        bar_end + timedelta(seconds=1),
                        bar_start_ts=bar_start,
                        bar_end_ts=bar_end,
                    ),
                )
            ),
        )


def test_cost_adjusted_guard_drops_roll_and_maintenance_crossings() -> None:
    definition = _definition(CostAdjustedLabelName.COST_ADJUSTED_FWD_RET, horizon="30m")

    roll_source_ts = _dt("2024-03-07T23:45:00+00:00")
    roll_records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(
            (
                _bbo_row(roll_source_ts, contract_id="ESM4"),
                _bbo_row(roll_source_ts + timedelta(minutes=30), contract_id="ESM4"),
            )
        ),
    )
    assert all(
        record.event_ts != roll_source_ts
        for record in roll_records[CostAdjustedLabelName.COST_ADJUSTED_FWD_RET]
    )

    maintenance_source_ts = _dt("2024-01-02T21:45:00+00:00")
    maintenance_records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(
            (
                _bbo_row(maintenance_source_ts, contract_id="ESH4"),
                _bbo_row(
                    maintenance_source_ts + timedelta(minutes=30),
                    contract_id="ESH4",
                ),
            )
        ),
    )
    assert all(
        record.event_ts != maintenance_source_ts
        for record in maintenance_records[CostAdjustedLabelName.COST_ADJUSTED_FWD_RET]
    )


def test_cost_adjusted_terminal_key_is_contract_scoped() -> None:
    definition = _definition(CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET, horizon="30m")
    source_ts = _dt("2024-01-02T14:30:00+00:00")

    records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(
            (
                _bbo_row(source_ts, contract_id="ESH4"),
                _bbo_row(source_ts + timedelta(minutes=30), contract_id="ESM4"),
            )
        ),
    )[CostAdjustedLabelName.SPREAD_ADJUSTED_FWD_RET]

    source_records = tuple(record for record in records if record.event_ts == source_ts)
    assert len(source_records) == 1
    assert source_records[0].value is None
    assert "missing_terminal_bbo" in source_records[0].quality_flags


def test_cost_adjusted_duplicate_bbo_key_is_gap_not_silent_quote_choice() -> None:
    definition = _definition(CostAdjustedLabelName.COST_ADJUSTED_FWD_RET)
    source_ts = _dt("2024-01-02T14:30:00+00:00")
    terminal_ts = source_ts + timedelta(minutes=5)

    source_duplicate_records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(
            (
                _bbo_row(source_ts, mid=Decimal("100.00")),
                _bbo_row(source_ts, mid=Decimal("100.25")),
                _bbo_row(terminal_ts, mid=Decimal("101.00")),
            )
        ),
    )[CostAdjustedLabelName.COST_ADJUSTED_FWD_RET]

    source_records = tuple(
        record for record in source_duplicate_records if record.event_ts == source_ts
    )
    assert len(source_records) == 1
    assert source_records[0].value is None
    assert "label_gap" in source_records[0].quality_flags
    assert "duplicate_bbo_key" in source_records[0].quality_flags

    terminal_duplicate_records = compute_cost_adjusted_labels(
        (definition,),
        BBOInputView(
            (
                _bbo_row(source_ts, mid=Decimal("100.00")),
                _bbo_row(terminal_ts, mid=Decimal("101.00")),
                _bbo_row(terminal_ts, mid=Decimal("101.25")),
            )
        ),
    )[CostAdjustedLabelName.COST_ADJUSTED_FWD_RET]

    terminal_source_records = tuple(
        record for record in terminal_duplicate_records if record.event_ts == source_ts
    )
    assert len(terminal_source_records) == 1
    assert terminal_source_records[0].value is None
    assert "label_gap" in terminal_source_records[0].quality_flags
    assert "terminal_duplicate_bbo_key" in terminal_source_records[0].quality_flags


def test_cost_adjusted_contract_metadata_documents_assumptions_and_guards() -> None:
    definition = _definition(CostAdjustedLabelName.COST_ADJUSTED_FWD_RET)

    metadata = definition.spec.label_contract.contract_metadata.to_dict()

    assert metadata["scaleout_phase"] == "FUTSUB-P19"
    assert metadata["label_anchor"] == "source_bar_end_ts"
    assert metadata["terminal_key"] == "series_id+contract_id+bar_end_ts"
    assert metadata["terminal_resolution"] == "bar_end_aligned_bbo_proxy"
    assert metadata["roll_guard_version"] == "roll_guard_v1"
    assert metadata["maintenance_guard_version"] == "maintenance_crossing_guard_v1"
    assert metadata["bbo_proxy_semantics"] == "time_sampled_forward_filled_tradability_proxy"


def test_cost_adjusted_contract_identity_can_be_materialization_scoped() -> None:
    es_definition = build_cost_adjusted_label_definition(
        CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
        _label_spec(CostAdjustedLabelName.COST_ADJUSTED_FWD_RET),
        dataset_version_ids=(DATASET_ID,),
        materialization_scope={
            "dataset_version_id": DATASET_ID,
            "partition_id": "ES.2024.1m",
            "partition_schema": "ohlcv_1m",
            "symbol": "ES",
            "window_start_ts": "2024-01-01T00:00:00+00:00",
            "window_end_ts": "2025-01-01T00:00:00+00:00",
            "horizon": "1m",
        },
    )
    nq_definition = build_cost_adjusted_label_definition(
        CostAdjustedLabelName.COST_ADJUSTED_FWD_RET,
        _label_spec(CostAdjustedLabelName.COST_ADJUSTED_FWD_RET),
        dataset_version_ids=(DATASET_ID,),
        materialization_scope={
            "dataset_version_id": DATASET_ID,
            "partition_id": "NQ.2024.1m",
            "partition_schema": "ohlcv_1m",
            "symbol": "NQ",
            "window_start_ts": "2024-01-01T00:00:00+00:00",
            "window_end_ts": "2025-01-01T00:00:00+00:00",
            "horizon": "1m",
        },
    )

    assert es_definition.label_version_id != nq_definition.label_version_id


def test_cost_adjusted_scaleout_registry_metadata_uses_bar_end_terminal_contract() -> None:
    config = load_scaleout_config(CONFIG_PATH)
    summary = run_scaleout(
        config,
        rollout="full-window",
        execute=False,
        engine="reference",
        target=ScaleoutTarget(symbols=("ES",), years=(2024,)),
    )
    metadata = scaleout_driver._label_scaleout_metadata(config, summary.records[0].unit)

    assert metadata["terminal_key"] == "series_id+contract_id+bar_end_ts"
    assert metadata["terminal_resolution"] == "bar_end_aligned_bbo_proxy"


def test_cost_adjusted_scaleout_uses_reference_engine_and_checkpoint_skip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_scaleout_config(CONFIG_PATH)
    calls: list[str] = []
    registry_records: dict[str, _FakeLabelRecord] = {}

    class _FakeLabelRegistry:
        def resolve_label(self, label_version_id: str) -> _FakeLabelRecord | None:
            return registry_records.get(label_version_id)

    monkeypatch.setattr(
        scaleout_driver,
        "_require_persisted_acceptance_lock",
        lambda _unit, _dataset_registry_path: None,
    )
    monkeypatch.setattr(
        label_registry_module.LabelRegistry,
        "from_alpha_data_root",
        staticmethod(lambda _root=None, **_kwargs: _FakeLabelRegistry()),
    )

    def fake_executor(
        _config,
        unit,
        alpha_root: Path,
        _registry: Path,
        _canonical: Path,
    ) -> MaterializedUnitEvidence:
        calls.append(unit.unit_id)
        parquet_path = alpha_root / "fake_cost_adjusted" / f"{unit.unit_id}.parquet"
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        parquet_path.write_text("synthetic cost-adjusted placeholder\n", encoding="utf-8")
        label_version_ids = scaleout_driver._preview_label_version_ids(_config, unit)
        content_hash = "sha256:" + "9" * 64
        for label_version_id in label_version_ids:
            registry_records[label_version_id] = _FakeLabelRecord(
                dataset_version_id=unit.dataset_version_id,
                partition_id=unit.partition_id,
                parquet_path=parquet_path.as_posix(),
                content_hash=content_hash,
                row_count=11,
            )
        return MaterializedUnitEvidence(
            parquet_path=parquet_path.as_posix(),
            content_hash=content_hash,
            row_count=22,
            label_version_ids=label_version_ids,
        )

    kwargs = {
        "alpha_data_root": tmp_path / "alpha_data",
        "dataset_registry_path": tmp_path / "registry.sqlite",
        "canonical_root": tmp_path / "canonical",
        "rollout": "full-window",
        "execute": True,
        "engine": "reference",
        "unit_executor": fake_executor,
        "target": ScaleoutTarget(symbols=("ES",), years=(2024,)),
    }
    first = run_scaleout(config, **kwargs)
    second = run_scaleout(config, **kwargs)

    assert first.engine == "reference"
    assert first.completed_count == 9
    assert second.skipped_count == 9
    assert second.completed_count == 0
    assert calls == [record.unit.unit_id for record in first.records]
    assert all(
        record.message == "completed unit skipped from checkpoint + registry truth"
        for record in second.records
    )


def test_cost_adjusted_scaleout_label_versions_are_partition_scoped(
    tmp_path: Path,
) -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(
        config,
        alpha_data_root=tmp_path / "alpha_data",
        dataset_registry_path=tmp_path / "registry.sqlite",
        canonical_root=tmp_path / "canonical",
        rollout="full-window",
        execute=False,
        engine="reference",
        target=ScaleoutTarget(symbols=("ES", "NQ"), years=(2024,)),
    )

    one_minute_records = {
        record.unit.symbol: record.label_version_ids
        for record in summary.records
        if record.unit.horizon == "1m"
    }

    assert set(one_minute_records) == {"ES", "NQ"}
    assert one_minute_records["ES"] != one_minute_records["NQ"]


class _FakeLabelRecord:
    def __init__(
        self,
        *,
        dataset_version_id: str,
        partition_id: str,
        parquet_path: str,
        content_hash: str,
        row_count: int,
    ) -> None:
        self.dataset_version_id = dataset_version_id
        self.partition_id = partition_id
        self.value_store_format = ValueStoreFormat.PARQUET.value
        self.parquet_path = parquet_path
        self.value_content_hash = content_hash
        self.value_record_count = row_count
        self.producer_engine_id = "alpha_system.labels.reference_engine.v1"


def _definition(
    name: CostAdjustedLabelName,
    *,
    horizon: str = "5m",
):
    return build_cost_adjusted_label_definition(
        name,
        _label_spec(name, horizon=horizon),
        dataset_version_ids=(DATASET_ID,),
    )


def _label_spec(
    name: CostAdjustedLabelName,
    *,
    horizon: str = "5m",
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


def _bbo_row(
    event_ts: datetime,
    *,
    contract_id: str = "ESH4",
    mid: Decimal = Decimal("100.00"),
    bar_start_ts: datetime | None = None,
    bar_end_ts: datetime | None = None,
    available_ts: datetime | None = None,
) -> BBOInputRow:
    bar_end = bar_end_ts or event_ts
    bar_start = bar_start_ts or bar_end - timedelta(minutes=1)
    available = available_ts or bar_end + timedelta(seconds=1)
    spread = Decimal("0.25")
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
