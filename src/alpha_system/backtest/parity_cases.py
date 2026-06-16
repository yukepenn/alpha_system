"""Enumerated fast/reference parity cases for ASV1-P19."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from alpha_system.backtest.execution_config import ExecutionConfig
from alpha_system.backtest.fast_path import (
    FAST_PATH_MODE_ACCELERATED,
    FAST_PATH_MODE_REFERENCE_FALLBACK,
)
from alpha_system.backtest.fixtures import (
    entry_exit_signals,
    falling_bars,
    fixture_cost_config,
    fixture_zero_cost_config,
    no_trade_signals,
    signal_record,
    synthetic_bar,
    synthetic_bars,
)
from alpha_system.backtest.slippage import BpsSlippageModel, CompositeSlippageModel
from alpha_system.management.spec import ManagementSpec


@dataclass(frozen=True, slots=True)
class ParityTolerance:
    """Deterministic comparison tolerances for parity domains."""

    summary_decimal: Decimal = Decimal("0")
    trade_decimal: Decimal = Decimal("0")
    equity_decimal: Decimal = Decimal("0")
    fill_decimal: Decimal = Decimal("0")

    def to_dict(self) -> dict[str, str]:
        return {
            "summary_decimal": str(self.summary_decimal),
            "trade_decimal": str(self.trade_decimal),
            "equity_decimal": str(self.equity_decimal),
            "fill_decimal": str(self.fill_decimal),
        }


@dataclass(frozen=True, slots=True)
class ParityCase:
    """One deterministic fixture case for reference/fast parity."""

    case_id: str
    description: str
    features: tuple[str, ...]
    expected_mode: str
    bars: tuple[Mapping[str, Any], ...]
    signals: tuple[Mapping[str, Any], ...]
    config: Any
    tolerance: ParityTolerance = ParityTolerance()
    management_spec: ManagementSpec | None = None
    initial_cash: Decimal = Decimal("100000")
    instrument_multipliers: Mapping[str, Decimal] | None = None

    @property
    def run_id(self) -> str:
        return f"parity-{self.case_id}"

    @property
    def resolved_instrument_multipliers(self) -> Mapping[str, Decimal]:
        """Per-instrument multipliers for the engine; defaults the synthetic ``SYNTH`` fixture to 1."""
        if self.instrument_multipliers is not None:
            return self.instrument_multipliers
        return {"SYNTH": Decimal("1")}


def parity_cases() -> tuple[ParityCase, ...]:
    """Return all ASV1-P19 parity cases in stable order."""

    return (
        _no_trade_case(),
        _simple_long_case(),
        _simple_short_case(),
        _costs_case(),
        _slippage_case(),
        _fixed_stop_case(),
        _target_case(),
        _same_bar_ambiguity_case(),
        _partial_exit_case(),
        _eod_exit_case(),
        _cooldown_case(),
        _max_holding_case(),
        _equity_curve_case(),
        _trade_summary_case(),
    )


def parity_case(case_id: str) -> ParityCase:
    """Return one parity case by id."""

    cases = {case.case_id: case for case in parity_cases()}
    try:
        return cases[case_id]
    except KeyError as exc:
        msg = f"unknown parity case: {case_id}"
        raise ValueError(msg) from exc


def parity_case_ids() -> tuple[str, ...]:
    return tuple(case.case_id for case in parity_cases())


def _no_trade_case() -> ParityCase:
    return ParityCase(
        case_id="no_trade",
        description="Hold-only signal produces no trades and deterministic equity.",
        features=("no_trade", "equity_curve"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=synthetic_bars(3),
        signals=no_trade_signals(),
        config=fixture_zero_cost_config(),
    )


def _simple_long_case() -> ParityCase:
    return ParityCase(
        case_id="simple_long",
        description="One long entry and one signal exit under next-bar semantics.",
        features=("simple_long", "trade_summary", "equity_curve"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=synthetic_bars(4),
        signals=entry_exit_signals(direction="long"),
        config=fixture_zero_cost_config(),
    )


def _simple_short_case() -> ParityCase:
    return ParityCase(
        case_id="simple_short",
        description="One short entry and one signal exit under next-bar semantics.",
        features=("simple_short", "trade_summary", "equity_curve"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=falling_bars(4),
        signals=entry_exit_signals(direction="short"),
        config=fixture_zero_cost_config(),
    )


def _costs_case() -> ParityCase:
    return ParityCase(
        case_id="costs",
        description="Fixed bps cost compatibility hook is reflected in PnL.",
        features=("costs", "simple_long", "trade_summary"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=synthetic_bars(4),
        signals=entry_exit_signals(direction="long"),
        config=fixture_cost_config(fixed_bps="100"),
    )


def _slippage_case() -> ParityCase:
    return ParityCase(
        case_id="slippage",
        description="ExecutionConfig slippage metadata routes to reference fallback.",
        features=("slippage", "simple_long", "trade_summary"),
        expected_mode=FAST_PATH_MODE_REFERENCE_FALLBACK,
        bars=synthetic_bars(4),
        signals=entry_exit_signals(direction="long"),
        config=ExecutionConfig(
            slippage_model=CompositeSlippageModel(models=(BpsSlippageModel(Decimal("25")),))
        ),
    )


def _fixed_stop_case() -> ParityCase:
    return ParityCase(
        case_id="fixed_stop",
        description="Fixed percent stop exits conservatively on the fill bar.",
        features=("fixed_stop", "simple_long", "trade_summary"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=(
            synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
            synthetic_bar(1, open_price="100", high="100.5", low="98.5", close="99"),
            synthetic_bar(2, open_price="99", high="100", low="98", close="99"),
        ),
        signals=(signal_record(0, "entry", signal_id="stop-entry", direction="long"),),
        config=fixture_zero_cost_config(stop_loss_pct=Decimal("0.01")),
    )


def _target_case() -> ParityCase:
    return ParityCase(
        case_id="target",
        description="Fixed percent target exits conservatively on the fill bar.",
        features=("target", "simple_long", "trade_summary"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=(
            synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
            synthetic_bar(1, open_price="100", high="102.5", low="99.5", close="101"),
            synthetic_bar(2, open_price="101", high="102", low="100", close="101"),
        ),
        signals=(signal_record(0, "entry", signal_id="target-entry", direction="long"),),
        config=fixture_zero_cost_config(target_profit_pct=Decimal("0.01")),
    )


def _same_bar_ambiguity_case() -> ParityCase:
    return ParityCase(
        case_id="same_bar_ambiguity",
        description="Same-bar stop and target touch resolves adverse-first.",
        features=("same_bar_ambiguity", "fixed_stop", "target", "trade_summary"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=(
            synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
            synthetic_bar(1, open_price="100", high="103", low="97", close="101"),
            synthetic_bar(2, open_price="101", high="102", low="100", close="101"),
        ),
        signals=(signal_record(0, "entry", signal_id="same-bar-entry", direction="long"),),
        config=fixture_zero_cost_config(
            stop_loss_pct=Decimal("0.01"),
            target_profit_pct=Decimal("0.01"),
        ),
    )


def _partial_exit_case() -> ParityCase:
    return ParityCase(
        case_id="partial_exit",
        description="Laddered partial management routes to reference fallback.",
        features=("partial_exit", "management_fixed_stop", "management_eod_exit", "trade_summary"),
        expected_mode=FAST_PATH_MODE_REFERENCE_FALLBACK,
        bars=(
            synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
            synthetic_bar(1, open_price="100", high="102.5", low="99", close="101"),
            synthetic_bar(2, open_price="102", high="103", low="101", close="102"),
        ),
        signals=(signal_record(0, "entry", signal_id="partial-entry", direction="long"),),
        config=fixture_zero_cost_config(default_quantity=Decimal("1")),
        management_spec=ManagementSpec.from_mapping(
            {
                "fixed_stop": {"enabled": True, "stop_pct": "0.02"},
                "laddered_partial_take_profit": {
                    "enabled": True,
                    "steps": [
                        {
                            "label": "half_at_1r",
                            "threshold_r": "1",
                            "exit_fraction": "0.5",
                        }
                    ],
                },
                "eod_exit": True,
            }
        ),
    )


def _eod_exit_case() -> ParityCase:
    return ParityCase(
        case_id="eod_exit",
        description="Reference eod_flat closes an open position on the last bar.",
        features=("eod_exit", "simple_long", "trade_summary", "equity_curve"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=synthetic_bars(3),
        signals=(signal_record(0, "entry", signal_id="eod-entry", direction="long"),),
        config=fixture_zero_cost_config(eod_flat=True),
    )


def _cooldown_case() -> ParityCase:
    return ParityCase(
        case_id="cooldown",
        description="Management cooldown routes to reference fallback.",
        features=("cooldown", "management_fixed_stop", "management_eod_exit", "trade_summary"),
        expected_mode=FAST_PATH_MODE_REFERENCE_FALLBACK,
        bars=(
            synthetic_bar(0, open_price="100", high="101", low="99", close="100"),
            synthetic_bar(1, open_price="100", high="101", low="98", close="99"),
            synthetic_bar(2, open_price="99", high="100", low="98", close="99"),
            synthetic_bar(3, open_price="99", high="100", low="98", close="99"),
            synthetic_bar(4, open_price="99", high="100", low="98", close="99"),
        ),
        signals=(
            signal_record(0, "entry", signal_id="cooldown-entry-1", direction="long"),
            signal_record(1, "entry", signal_id="cooldown-blocked", direction="long"),
            signal_record(2, "entry", signal_id="cooldown-entry-2", direction="long"),
        ),
        config=fixture_zero_cost_config(default_quantity=Decimal("1")),
        management_spec=ManagementSpec.from_mapping(
            {
                "fixed_stop": {"enabled": True, "stop_pct": "0.01"},
                "cooldown": {"enabled": True, "bars": 2},
                "eod_exit": True,
            }
        ),
    )


def _max_holding_case() -> ParityCase:
    return ParityCase(
        case_id="max_holding_bars",
        description="Management max holding bars routes to reference fallback.",
        features=("max_holding_bars", "trade_summary", "equity_curve"),
        expected_mode=FAST_PATH_MODE_REFERENCE_FALLBACK,
        bars=synthetic_bars(5),
        signals=(signal_record(0, "entry", signal_id="max-hold-entry", direction="long"),),
        config=fixture_zero_cost_config(default_quantity=Decimal("1")),
        management_spec=ManagementSpec.from_mapping(
            {"max_holding_bars": {"enabled": True, "max_bars": 2}}
        ),
    )


def _equity_curve_case() -> ParityCase:
    return ParityCase(
        case_id="equity_curve",
        description="Equity curve serialization is deterministic and equal.",
        features=("simple_long", "equity_curve"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=synthetic_bars(4),
        signals=entry_exit_signals(direction="long"),
        config=fixture_zero_cost_config(),
    )


def _trade_summary_case() -> ParityCase:
    return ParityCase(
        case_id="trade_summary",
        description="Trade journal and summary serialization are deterministic and equal.",
        features=("simple_long", "trade_summary"),
        expected_mode=FAST_PATH_MODE_ACCELERATED,
        bars=synthetic_bars(4),
        signals=entry_exit_signals(direction="long"),
        config=fixture_zero_cost_config(),
    )
