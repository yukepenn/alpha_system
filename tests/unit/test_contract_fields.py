from __future__ import annotations

from alpha_system.backtest.contracts import BacktestSpec
from alpha_system.core.schema import missing_contract_fields
from alpha_system.data.contracts import (
    InstrumentMaster,
    OneMinuteBar,
    QuoteTradeReadiness,
    TradingSession,
)
from alpha_system.experiments.contracts import ExperimentSpec
from alpha_system.factors.contracts import FactorSpec, FactorValue
from alpha_system.labels.contracts import LabelSchema


def assert_contract_fields(
    contract_type: type[object],
    required_fields: tuple[str, ...],
) -> None:
    assert missing_contract_fields(contract_type, required_fields) == ()


def test_instrument_master_required_fields_present() -> None:
    assert_contract_fields(
        InstrumentMaster,
        (
            "instrument_id",
            "symbol",
            "asset_class",
            "exchange",
            "currency",
            "timezone",
            "tick_size",
            "lot_size",
            "multiplier",
            "start_date",
            "end_date",
            "corporate_action_policy",
            "metadata",
        ),
    )


def test_trading_session_required_fields_present() -> None:
    assert_contract_fields(
        TradingSession,
        (
            "calendar_id",
            "trading_date",
            "session_id",
            "open_ts",
            "close_ts",
            "is_holiday",
            "is_half_day",
            "session_type",
            "timezone",
            "quality_flags",
        ),
    )


def test_one_minute_bar_required_fields_present() -> None:
    assert_contract_fields(
        OneMinuteBar,
        (
            "instrument_id",
            "session_id",
            "bar_index",
            "bar_start_ts",
            "bar_end_ts",
            "event_ts",
            "available_ts",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "vwap",
            "trade_count",
            "bid",
            "ask",
            "spread",
            "source_version",
            "data_version",
            "quality_flags",
        ),
    )


def test_quote_trade_readiness_fields_present() -> None:
    assert_contract_fields(
        QuoteTradeReadiness,
        (
            "readiness_id",
            "instrument_id",
            "quote_data",
            "trade_prints",
            "bid_ask_spread",
            "executable_labels",
            "cost_modeling",
            "event_ts",
            "available_ts",
            "data_version",
            "quality_flags",
        ),
    )


def test_factor_spec_required_fields_present() -> None:
    assert_contract_fields(
        FactorSpec,
        (
            "factor_id",
            "name",
            "version",
            "owner",
            "description",
            "input_fields",
            "parameters",
            "frequency",
            "warmup_bars",
            "session_reset",
            "availability_lag",
            "factor_type",
            "evaluation_type",
            "code_hash",
            "config_hash",
            "status",
            "created_at",
            "validation_artifact_path",
        ),
    )


def test_factor_value_required_fields_present() -> None:
    assert_contract_fields(
        FactorValue,
        (
            "factor_id",
            "factor_version",
            "instrument_id",
            "event_ts",
            "available_ts",
            "session_id",
            "bar_index",
            "value",
            "normalized_value",
            "quality_flags",
            "data_version",
            "compute_version",
        ),
    )


def test_label_schema_required_fields_present() -> None:
    assert_contract_fields(
        LabelSchema,
        (
            "label_id",
            "instrument_id",
            "event_ts",
            "horizon",
            "label_type",
            "value",
            "path_metadata",
            "data_version",
            "label_available_ts",
        ),
    )


def test_backtest_experiment_reproducibility_fields_present() -> None:
    required = (
        "run_id",
        "code_hash",
        "config_hash",
        "data_version",
        "factor_versions",
        "label_versions",
        "engine_version",
        "parameters",
        "artifact_paths",
        "decision_status",
    )

    assert_contract_fields(BacktestSpec, required)
    assert_contract_fields(ExperimentSpec, required)
