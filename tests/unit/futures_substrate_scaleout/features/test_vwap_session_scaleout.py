from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from alpha_system.features.families.ohlcv import (
    OHLCVFeatureName,
    build_ohlcv_feature_definition,
    compute_ohlcv_feature,
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
CONFIG_PATH = "configs/features/scaleout/vwap_session_auction.json"
DATASET_VERSION_ID = "dsv_databento_ohlcv_05404069799decb0"


class EmptyRegistryReader:
    def read_factor_versions(self) -> list[dict[str, object]]:
        return []


def test_vwap_session_scaleout_preview_is_symbol_scoped() -> None:
    config = load_scaleout_config(CONFIG_PATH)

    summary = run_scaleout(config, rollout="bounded-real")

    assert config.family == "vwap_session_auction"
    assert config.feature_names == (
        "running_vwap",
        "anchored_eth_vwap",
        "distance_to_vwap",
        "opening_range",
        "overnight_range",
        "rth_open_context",
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


def test_running_vwap_uses_current_available_ts_not_final_session_vwap() -> None:
    rows = _rows(("RTH", "RTH", "RTH"), prices=(100, 200, 500))
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.VWAP,
        _approved_request("running_vwap"),
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
        input_scope={"symbol": "ES", "partition_id": "ES.2024.full_year"},
    )

    records = compute_ohlcv_feature(definition, OHLCVInputView(rows))

    final_session_vwap = (100 + 200 + 500) / 3
    assert [record.available_ts for record in records] == [row.available_ts for row in rows]
    assert [record.value for record in records] == [100.0, 150.0, final_session_vwap]
    assert records[0].value != final_session_vwap
    assert records[1].value != final_session_vwap


def test_anchored_eth_vwap_carries_only_available_anchor_rows() -> None:
    rows = _rows(("ETH", "RTH", "RTH"), prices=(90, 120, 600))
    definition = build_ohlcv_feature_definition(
        OHLCVFeatureName.ANCHORED_VWAP,
        _approved_request("anchored_eth_vwap"),
        EmptyRegistryReader(),
        dataset_version_ids=(DATASET_VERSION_ID,),
        anchor_session_label="ETH",
        input_scope={"symbol": "ES", "partition_id": "ES.2024.full_year"},
    )

    records = compute_ohlcv_feature(definition, OHLCVInputView(rows))

    final_anchored_vwap = (90 + 120 + 600) / 3
    assert [record.available_ts for record in records] == [row.available_ts for row in rows]
    assert [record.value for record in records] == [90.0, 105.0, final_anchored_vwap]
    assert records[0].value != final_anchored_vwap
    assert records[1].value != final_anchored_vwap


def _rows(
    session_labels: tuple[str, ...],
    *,
    prices: tuple[int, ...],
) -> tuple[OHLCVInputRow, ...]:
    assert len(session_labels) == len(prices)
    start = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    return tuple(
        _row(
            start + timedelta(minutes=index),
            session_label=session,
            price=Decimal(str(price)),
        )
        for index, (session, price) in enumerate(zip(session_labels, prices, strict=True))
    )


def _row(bar_start_ts: datetime, *, session_label: str, price: Decimal) -> OHLCVInputRow:
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
        high=price,
        low=price,
        close=price,
        volume=Decimal("1"),
        data_version=DATASET_VERSION_ID,
        quality_flags=(),
        session_label=session_label,
    )


def _approved_request(feature_name: str) -> FeatureRequest:
    notes = ExposureCheckResult((), ExposureRegistryStatus.EMPTY, 0).to_notes()
    return create_feature_request(
        alpha_spec_id=ALPHA_SPEC_ID,
        requested_inputs=[f"vwap_session_auction_{feature_name}"],
        formula_sketch={
            "exposure_family": f"vwap_session_auction_{feature_name}",
            "inputs": ["ohlcv_1m"],
            "operation": feature_name,
            "window": "running_point_in_time",
        },
        availability_assumptions={
            "timing": "running VWAP state uses only rows with available_ts <= output available_ts",
            "forbidden": "no final-session aggregate is used intraday",
        },
        duplicate_or_equivalent_exposure_notes=notes,
        data_requirements={
            "fields": ["high", "low", "close", "volume", "session_label", "available_ts"],
            "source": "tiny synthetic OHLCV fixture",
        },
        approval_status=FeatureRequestApprovalStatus.APPROVED,
    )
