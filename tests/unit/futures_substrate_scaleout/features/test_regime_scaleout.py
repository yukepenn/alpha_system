from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
)
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
CONFIG_PATH = "configs/features/scaleout/regime_volatility_compression.json"
DATASET_VERSION_ID = "dsv_databento_ohlcv_05404069799decb0"


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_regime_scaleout_preview_is_symbol_scoped() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="bounded-real")

    assert config.family == "regime_volatility_compression"
    assert config.feature_names == (
        "trendiness",
        "atr_volatility_regime",
        "range_compression",
        "range_expansion",
        "momentum_reversion_state",
    )
    assert summary.accepted_unit_count == 24
    assert summary.bounded_unit_count == 3
    assert summary.failed_count == 0
    assert {record.unit.symbol for record in summary.records} == {"ES", "NQ", "RTY"}
    version_sets = [set(record.feature_version_ids) for record in summary.records]
    assert len(set.union(*version_sets)) == len(config.feature_names) * len(summary.records)
    for record in summary.records:
        assert len(record.feature_version_ids) == len(config.feature_names)
        assert all(version_id.startswith("fver_") for version_id in record.feature_version_ids)


def test_regime_primitives_preserve_current_available_ts() -> None:
    rows = _rows((100, 102, 101, 106, 105))
    view = OHLCVInputView(rows)
    ohlcv_definitions = (
        build_ohlcv_feature_definition(
            OHLCVFeatureName.TRENDINESS,
            _approved_request("trendiness"),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_VERSION_ID,),
            window_length=3,
            input_scope={"symbol": "ES", "partition_id": "ES.2024.synthetic"},
        ),
        build_ohlcv_feature_definition(
            OHLCVFeatureName.ATR,
            _approved_request("atr_volatility_regime"),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_VERSION_ID,),
            window_length=3,
            input_scope={"symbol": "ES", "partition_id": "ES.2024.synthetic"},
        ),
        build_ohlcv_feature_definition(
            OHLCVFeatureName.RETURNS,
            _approved_request("momentum_reversion_state"),
            EmptyRegistryReader(),
            dataset_version_ids=(DATASET_VERSION_ID,),
            horizon=1,
            input_scope={"symbol": "ES", "partition_id": "ES.2024.synthetic"},
        ),
    )
    structure_definition = build_structure_feature_definition(
        StructureFeatureName.RANGE_CONTRACTION,
        _approved_request("range_compression"),
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
        window_length=3,
        input_scope={"symbol": "ES", "partition_id": "ES.2024.synthetic"},
    )

    records_by_feature = [
        compute_ohlcv_feature(definition, view) for definition in ohlcv_definitions
    ]
    records_by_feature.append(compute_structure_feature(structure_definition, view))

    expected_available_ts = [row.available_ts for row in rows]
    for records in records_by_feature:
        assert [record.available_ts for record in records] == expected_available_ts
        assert all(record.available_ts >= record.event_ts for record in records)
        assert all(record.feature_version_id.startswith("fver_") for record in records)


def _rows(prices: tuple[int, ...]) -> tuple[OHLCVInputRow, ...]:
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    return tuple(
        _row(
            start + timedelta(minutes=index),
            price=Decimal(str(price)),
            high=Decimal(str(price + 1)),
            low=Decimal(str(price - 1)),
        )
        for index, price in enumerate(prices)
    )


def _row(
    bar_start_ts: datetime,
    *,
    price: Decimal,
    high: Decimal,
    low: Decimal,
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
        open=price,
        high=high,
        low=low,
        close=price,
        volume=Decimal("1"),
        data_version=DATASET_VERSION_ID,
        quality_flags=(),
        session_label="RTH",
    )


def _approved_request(feature_name: str) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"regime_volatility_compression_{feature_name}"],
        formula_sketch={
            "exposure_family": f"regime_volatility_compression_{feature_name}",
            "inputs": ["ohlcv_1m"],
            "operation": feature_name,
            "window": "causal_point_in_time_or_rolling",
        },
        availability_assumptions={
            "timing": "feature value is emitted at the current row available_ts",
            "forbidden": "no future label or final-session aggregate is used",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["high", "low", "close", "volume", "session_label", "available_ts"],
            "source": "tiny synthetic OHLCV fixture",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )
