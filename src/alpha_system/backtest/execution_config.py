"""Execution cost/slippage configuration consumed by reference research runs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from alpha_system.backtest.conservative_semantics import (
    MISSING_BID_ASK_FALLBACK_TO_OHLC,
    NEXT_BAR_CONSERVATIVE,
    SAME_BAR_ADVERSE_FIRST,
    assert_conservative_execution_defaults,
)
from alpha_system.backtest.costs import (
    CompositeCostModel,
    conservative_default_cost_model,
    cost_model_from_mapping,
    explicit_fixture_zero_cost_model,
)
from alpha_system.backtest.fill_models import ConservativeFillModel
from alpha_system.backtest.liquidity import LiquidityPolicy, liquidity_policy_from_mapping
from alpha_system.backtest.slippage import (
    CompositeSlippageModel,
    conservative_default_slippage_model,
    explicit_fixture_no_slippage_model,
    slippage_model_from_mapping,
)
from alpha_system.core.hashing import hash_config


REFERENCE_ENGINE_VERSION = "reference_1min_v1"


class ExecutionConfigError(ValueError):
    """Raised when execution configuration would violate conservative defaults."""


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    """Conservative research execution config for the reference engine."""

    data_latency_seconds: int = 0
    execution_timing: str = NEXT_BAR_CONSERVATIVE
    same_bar_policy: str = SAME_BAR_ADVERSE_FIRST
    eod_flat: bool = False
    default_quantity: Decimal = Decimal("1")
    stop_loss_pct: Decimal | None = None
    target_profit_pct: Decimal | None = None
    cost_model: CompositeCostModel = field(default_factory=conservative_default_cost_model)
    slippage_model: CompositeSlippageModel = field(default_factory=conservative_default_slippage_model)
    liquidity_policy: LiquidityPolicy = field(default_factory=LiquidityPolicy)
    missing_bid_ask_policy: str = MISSING_BID_ASK_FALLBACK_TO_OHLC
    zero_cost_fixture: bool = False
    engine_version: str = REFERENCE_ENGINE_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "data_latency_seconds",
            _non_negative_int(self.data_latency_seconds, "data_latency_seconds"),
        )
        object.__setattr__(self, "execution_timing", _text(self.execution_timing, "execution_timing"))
        object.__setattr__(self, "same_bar_policy", _text(self.same_bar_policy, "same_bar_policy"))
        object.__setattr__(self, "eod_flat", _bool(self.eod_flat, "eod_flat"))
        object.__setattr__(self, "default_quantity", _positive_decimal(self.default_quantity, "default_quantity"))
        object.__setattr__(
            self,
            "stop_loss_pct",
            _optional_positive_decimal(self.stop_loss_pct, "stop_loss_pct"),
        )
        object.__setattr__(
            self,
            "target_profit_pct",
            _optional_positive_decimal(self.target_profit_pct, "target_profit_pct"),
        )
        object.__setattr__(self, "missing_bid_ask_policy", _text(self.missing_bid_ask_policy, "missing_bid_ask_policy"))
        object.__setattr__(self, "engine_version", _text(self.engine_version, "engine_version"))

        active_cost_model = self.cost_model.with_reference_quantity(self.default_quantity)
        object.__setattr__(self, "cost_model", active_cost_model)
        if self.zero_cost_fixture:
            if not active_cost_model.fixture_zero_cost:
                msg = "zero_cost_fixture requires an explicit fixture zero-cost cost model"
                raise ExecutionConfigError(msg)
            if not self.slippage_model.fixture_zero_slippage:
                msg = "zero_cost_fixture requires explicit fixture no-slippage"
                raise ExecutionConfigError(msg)
        else:
            assert_conservative_execution_defaults(
                execution_timing=self.execution_timing,
                same_bar_policy=self.same_bar_policy,
                zero_cost_fixture=False,
            )
            if active_cost_model.total_is_zero:
                msg = "non-test default execution config must not be zero-cost"
                raise ExecutionConfigError(msg)
            if self.slippage_model.total_is_zero:
                msg = "non-test default execution config must not have zero slippage"
                raise ExecutionConfigError(msg)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "ExecutionConfig":
        if payload is None:
            return cls()
        return cls(
            data_latency_seconds=payload.get("data_latency_seconds", 0),
            execution_timing=str(payload.get("execution_timing", NEXT_BAR_CONSERVATIVE)),
            same_bar_policy=str(payload.get("same_bar_policy", SAME_BAR_ADVERSE_FIRST)),
            eod_flat=payload.get("eod_flat", False),
            default_quantity=_decimal(payload.get("default_quantity", "1"), "default_quantity"),
            stop_loss_pct=_optional_decimal(payload.get("stop_loss_pct"), "stop_loss_pct"),
            target_profit_pct=_optional_decimal(payload.get("target_profit_pct"), "target_profit_pct"),
            cost_model=cost_model_from_mapping(payload.get("cost_model")),
            slippage_model=slippage_model_from_mapping(payload.get("slippage_model")),
            liquidity_policy=liquidity_policy_from_mapping(payload.get("liquidity_policy")),
            missing_bid_ask_policy=str(
                payload.get("missing_bid_ask_policy", MISSING_BID_ASK_FALLBACK_TO_OHLC)
            ),
            zero_cost_fixture=bool(payload.get("zero_cost_fixture", False)),
            engine_version=str(payload.get("engine_version", REFERENCE_ENGINE_VERSION)),
        )

    def to_fill_model(self) -> ConservativeFillModel:
        """Return a fill model with this config's cost/slippage/liquidity semantics."""

        return ConservativeFillModel(
            cost_model=self.cost_model,
            slippage_model=self.slippage_model,
            liquidity_policy=self.liquidity_policy,
            missing_bid_ask_policy=self.missing_bid_ask_policy,
        )

    def config_hash(self) -> str:
        """Return a deterministic hash for reproducibility metadata."""

        return hash_config(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "data_latency_seconds": self.data_latency_seconds,
            "execution_timing": self.execution_timing,
            "same_bar_policy": self.same_bar_policy,
            "eod_flat": self.eod_flat,
            "default_quantity": _decimal_text(self.default_quantity),
            "stop_loss_pct": _optional_decimal_text(self.stop_loss_pct),
            "target_profit_pct": _optional_decimal_text(self.target_profit_pct),
            "cost_model": self.cost_model.to_dict(),
            "slippage_model": self.slippage_model.to_dict(),
            "liquidity_policy": self.liquidity_policy.to_dict(),
            "missing_bid_ask_policy": self.missing_bid_ask_policy,
            "zero_cost_fixture": self.zero_cost_fixture,
            "research_only": True,
        }


def default_execution_config() -> ExecutionConfig:
    """Return the non-test conservative default execution config."""

    return ExecutionConfig()


def fixture_zero_cost_execution_config(**overrides: Any) -> ExecutionConfig:
    """Return explicit zero-cost/no-slippage config for tiny fixture tests only."""

    payload = {
        "cost_model": explicit_fixture_zero_cost_model(),
        "slippage_model": explicit_fixture_no_slippage_model(),
        "zero_cost_fixture": True,
    }
    payload.update(overrides)
    return ExecutionConfig(**payload)


def load_execution_config(path: str | Path) -> ExecutionConfig:
    """Load a JSON or small YAML execution config without adding a CLI command."""

    from alpha_system.backtest.engine_config import _parse_simple_yaml  # local compatibility parser

    config_path = Path(path).expanduser().resolve(strict=False)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        import json

        payload = json.loads(text)
    else:
        payload = _parse_simple_yaml(text)
    if not isinstance(payload, Mapping):
        msg = "execution config root must be a mapping"
        raise ExecutionConfigError(msg)
    return ExecutionConfig.from_mapping(payload)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise ExecutionConfigError(msg)
    return value.strip()


def _bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    msg = f"{field_name} must be boolean"
    raise ExecutionConfigError(msg)


def _non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        msg = f"{field_name} must be a non-negative integer"
        raise ExecutionConfigError(msg)
    try:
        active = int(value)
    except (TypeError, ValueError) as exc:
        msg = f"{field_name} must be a non-negative integer"
        raise ExecutionConfigError(msg) from exc
    if active < 0:
        msg = f"{field_name} must be non-negative"
        raise ExecutionConfigError(msg)
    return active


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise ExecutionConfigError(msg)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise ExecutionConfigError(msg) from exc


def _optional_decimal(value: Any, field_name: str) -> Decimal | None:
    if value in (None, ""):
        return None
    return _decimal(value, field_name)


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= Decimal("0"):
        msg = f"{field_name} must be positive"
        raise ExecutionConfigError(msg)
    return active


def _optional_positive_decimal(value: Any, field_name: str) -> Decimal | None:
    if value is None:
        return None
    return _positive_decimal(value, field_name)


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _optional_decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else _decimal_text(value)
