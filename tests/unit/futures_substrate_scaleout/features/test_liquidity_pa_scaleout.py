from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from alpha_system.features.families.structure import (
    StructureFeatureName,
    build_structure_feature_definition,
    compute_structure_feature,
)
from alpha_system.features.input_views import OHLCVInputRow, OHLCVInputView
from alpha_system.features.scaleout import load_scaleout_config, run_scaleout
from alpha_system.governance.duplicate_exposure import (
    ExposureCheckResult,
    ExposureRegistryStatus,
)
from alpha_system.governance.feature_request import (
    FeatureRequest,
    FeatureRequestApprovalStatus,
    create_feature_request,
)

ALPHA_SPEC_ID = "aspec_af848bc999a4c4b11a421bd0"
CONFIG_PATH = "configs/features/scaleout/liquidity_sweep_pa_structure.json"
DATASET_VERSION_ID = "dsv_databento_ohlcv_05404069799decb0"

P10_PRIMITIVES = (
    StructureFeatureName.PRIOR_HIGH_DISTANCE,
    StructureFeatureName.PRIOR_LOW_DISTANCE,
    StructureFeatureName.SWEEP_HIGH_FLAG,
    StructureFeatureName.SWEEP_LOW_FLAG,
    StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG,
    StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG,
    StructureFeatureName.CLOSE_LOCATION_VALUE,
    StructureFeatureName.WICK_REJECTION_SCORE,
    StructureFeatureName.RANGE_CONTRACTION,
)


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_liquidity_pa_scaleout_preview_maps_objective_structure_primitives() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="bounded-real")

    assert config.family == "liquidity_sweep_pa_structure"
    assert config.feature_names == (
        "prior_high_low_sweep",
        "close_back_inside",
        "wick_rejection",
        "displacement",
        "compression_breakout",
        "failed_breakout",
    )
    assert summary.accepted_unit_count == 24
    assert summary.bounded_unit_count == 3
    assert summary.failed_count == 0
    assert {record.unit.symbol for record in summary.records} == {"ES", "NQ", "RTY"}
    version_sets = [set(record.feature_version_ids) for record in summary.records]
    assert len(set.union(*version_sets)) == len(P10_PRIMITIVES) * len(summary.records)
    for record in summary.records:
        assert len(record.feature_version_ids) == len(P10_PRIMITIVES)
        assert all(version_id.startswith("fver_") for version_id in record.feature_version_ids)


def test_liquidity_pa_primitives_preserve_current_available_ts() -> None:
    rows = _rows()
    view = OHLCVInputView(rows)
    definitions = tuple(
        build_structure_feature_definition(
            name,
            _approved_request(name),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_VERSION_ID,),
            window_length=3,
            input_scope={"symbol": "ES", "partition_id": "ES.2024.synthetic"},
        )
        for name in P10_PRIMITIVES
    )

    records_by_name = {
        definition.name: compute_structure_feature(definition, view)
        for definition in definitions
    }

    expected_available_ts = [row.available_ts for row in rows]
    for definition in definitions:
        records = records_by_name[definition.name]
        assert [record.available_ts for record in records] == expected_available_ts
        assert all(record.available_ts >= record.event_ts for record in records)
        assert all(record.feature_version_id == definition.feature_version_id for record in records)

    assert records_by_name[StructureFeatureName.SWEEP_HIGH_FLAG][3].value == 1
    assert records_by_name[StructureFeatureName.FAILED_HIGH_BREAKOUT_FLAG][3].value == 1
    assert records_by_name[StructureFeatureName.SWEEP_LOW_FLAG][4].value == 1
    assert records_by_name[StructureFeatureName.FAILED_LOW_BREAKOUT_FLAG][4].value == 1


def _rows() -> tuple[OHLCVInputRow, ...]:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    bars = (
        (Decimal("100"), Decimal("101"), Decimal("99"), Decimal("100")),
        (Decimal("101"), Decimal("102"), Decimal("100"), Decimal("101")),
        (Decimal("102"), Decimal("103"), Decimal("101"), Decimal("102")),
        (Decimal("102"), Decimal("105"), Decimal("101"), Decimal("102.5")),
        (Decimal("102"), Decimal("103"), Decimal("98"), Decimal("101")),
    )
    return tuple(
        _row(
            start + timedelta(minutes=index),
            open_=open_,
            high=high,
            low=low,
            close=close,
        )
        for index, (open_, high, low, close) in enumerate(bars)
    )


def _row(
    bar_start_ts: datetime,
    *,
    open_: Decimal,
    high: Decimal,
    low: Decimal,
    close: Decimal,
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
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=Decimal("1"),
        data_version=DATASET_VERSION_ID,
        quality_flags=(),
        session_label="RTH",
    )


def _approved_request(feature_name: StructureFeatureName) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"liquidity_sweep_pa_structure_{feature_name.value}"],
        formula_sketch={
            "exposure_family": f"liquidity_sweep_pa_structure_{feature_name.value}",
            "inputs": ["ohlcv_1m"],
            "operation": feature_name.value,
            "window": "causal_point_in_time_or_rolling",
        },
        availability_assumptions={
            "timing": "feature value is emitted at the current row available_ts",
            "forbidden": "no future label, final-session aggregate, or subjective PA input is used",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["open", "high", "low", "close", "session_label", "available_ts"],
            "source": "tiny synthetic OHLCV fixture",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )
