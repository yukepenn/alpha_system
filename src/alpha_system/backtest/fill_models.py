"""Conservative fill-model support used by local research simulations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from alpha_system.backtest.conservative_semantics import (
    MISSING_BID_ASK_FALLBACK_TO_OHLC,
    conservative_price,
)
from alpha_system.backtest.costs import CostBreakdown, CostInput, SupportsCost
from alpha_system.backtest.liquidity import LiquidityDecision, LiquidityInput, LiquidityPolicy
from alpha_system.backtest.slippage import SlippageInput, SlippageResult, SupportsSlippage


class FillModelError(ValueError):
    """Raised when a conservative fill cannot be resolved."""


@dataclass(frozen=True, slots=True)
class FillRequest:
    """One deterministic fill request over a normalized 1-minute bar."""

    direction: str
    intent: str
    quantity: Decimal
    bar: Mapping[str, Any]
    fallback_field: str = "open"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "direction", _enum_text(self.direction, "direction"))
        object.__setattr__(self, "intent", _enum_text(self.intent, "intent"))
        object.__setattr__(self, "quantity", _positive_decimal(self.quantity, "quantity"))
        object.__setattr__(self, "bar", dict(self.bar))
        object.__setattr__(self, "fallback_field", _text(self.fallback_field, "fallback_field"))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True, slots=True)
class ModeledFill:
    """Result of a conservative fill-model calculation."""

    base_price: Decimal
    fill_price: Decimal
    quantity: Decimal
    side: str
    price_source: str
    used_bid_ask: bool
    missing_bid_ask_fallback: bool
    slippage: SlippageResult
    costs: CostBreakdown
    liquidity: LiquidityDecision
    warnings: tuple[str, ...] = ()

    @property
    def total_cost(self) -> Decimal:
        return self.costs.total + self.liquidity.penalty_cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_price": _decimal_text(self.base_price),
            "fill_price": _decimal_text(self.fill_price),
            "quantity": _decimal_text(self.quantity),
            "side": self.side,
            "price_source": self.price_source,
            "used_bid_ask": self.used_bid_ask,
            "missing_bid_ask_fallback": self.missing_bid_ask_fallback,
            "slippage": self.slippage.to_dict(),
            "costs": self.costs.to_dict(),
            "liquidity": self.liquidity.to_dict(),
            "total_cost": _decimal_text(self.total_cost),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class ConservativeFillModel:
    """Resolve spread-aware, slippage-aware, liquidity-aware research fills."""

    cost_model: SupportsCost
    slippage_model: SupportsSlippage
    liquidity_policy: LiquidityPolicy = field(default_factory=LiquidityPolicy)
    missing_bid_ask_policy: str = MISSING_BID_ASK_FALLBACK_TO_OHLC

    def resolve(self, request: FillRequest) -> ModeledFill:
        price = conservative_price(
            direction=request.direction,
            intent=request.intent,
            bar=request.bar,
            fallback_field=request.fallback_field,
            missing_bid_ask_policy=self.missing_bid_ask_policy,
        )
        liquidity = self.liquidity_policy.evaluate(
            LiquidityInput(
                requested_quantity=request.quantity,
                bar_volume=_optional_decimal(request.bar.get("volume"), "volume"),
                price=price.price,
                metadata=request.metadata,
            )
        )
        slippage = self.slippage_model.apply(
            SlippageInput(
                price=price.price,
                quantity=liquidity.fill_quantity,
                side=price.side,
                bid=_optional_decimal(request.bar.get("bid"), "bid"),
                ask=_optional_decimal(request.bar.get("ask"), "ask"),
                spread=_optional_decimal(request.bar.get("spread"), "spread"),
                metadata=request.metadata,
            )
        )
        costs = self.cost_model.cost_for_fill(
            CostInput(
                price=slippage.adjusted_price,
                quantity=liquidity.fill_quantity,
                side=price.side,
                bid=_optional_decimal(request.bar.get("bid"), "bid"),
                ask=_optional_decimal(request.bar.get("ask"), "ask"),
                spread=_optional_decimal(request.bar.get("spread"), "spread"),
                metadata=request.metadata,
            )
        )
        warnings = (price.warning,) if price.warning else ()
        return ModeledFill(
            base_price=price.price,
            fill_price=slippage.adjusted_price,
            quantity=liquidity.fill_quantity,
            side=price.side,
            price_source=price.source,
            used_bid_ask=price.used_bid_ask,
            missing_bid_ask_fallback=price.missing_bid_ask_fallback,
            slippage=slippage,
            costs=costs,
            liquidity=liquidity,
            warnings=warnings,
        )


def _enum_text(value: Any, field_name: str) -> str:
    if hasattr(value, "value"):
        value = value.value
    return _text(value, field_name)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise FillModelError(msg)
    return value.strip()


def _decimal(value: Any, field_name: str) -> Decimal:
    if isinstance(value, bool):
        msg = f"{field_name} must be numeric"
        raise FillModelError(msg)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        msg = f"{field_name} must be numeric"
        raise FillModelError(msg) from exc


def _optional_decimal(value: Any, field_name: str) -> Decimal | None:
    if value is None:
        return None
    return _decimal(value, field_name)


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    active = _decimal(value, field_name)
    if active <= Decimal("0"):
        msg = f"{field_name} must be positive"
        raise FillModelError(msg)
    return active


def _decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")
