"""Enumerations shared by contract/schema primitives."""

from __future__ import annotations

from enum import Enum


class TextEnum(str, Enum):
    """String-valued enum base for stable serialized contract values."""


class AssetClass(TextEnum):
    EQUITY = "equity"
    ETF = "etf"
    FUTURE = "future"
    OPTION = "option"
    FX = "fx"
    CRYPTO = "crypto"


class CorporateActionPolicy(TextEnum):
    RAW = "raw"
    ADJUSTED = "adjusted"
    POINT_IN_TIME = "point_in_time"


class SessionType(TextEnum):
    REGULAR = "regular"
    PRE_MARKET = "pre_market"
    POST_MARKET = "post_market"
    OVERNIGHT = "overnight"


class ReadinessState(TextEnum):
    NOT_READY = "not_ready"
    DESIGN_ONLY = "design_only"
    READY = "ready"


class FactorStatus(TextEnum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class FactorInputDomain(TextEnum):
    BAR = "bar"
    QUOTE = "quote"
    TRADE = "trade"
    L2 = "l2"
    FACTOR = "factor"


class FactorFrequency(TextEnum):
    ONE_MINUTE = "1m"
    SESSION = "session"
    DAILY = "daily"


class FactorType(TextEnum):
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    EVENT = "event"
    REGIME = "regime"


class FactorEvaluationType(TextEnum):
    POINT_IN_TIME = "point_in_time"
    SESSION_RESET = "session_reset"
    CROSS_SECTIONAL = "cross_sectional"


class LabelType(TextEnum):
    FORWARD_RETURN_1M = "forward_return_1m"
    FORWARD_RETURN_3M = "forward_return_3m"
    FORWARD_RETURN_5M = "forward_return_5m"
    FORWARD_RETURN_10M = "forward_return_10m"
    FORWARD_RETURN_30M = "forward_return_30m"
    MFE_BY_HORIZON = "mfe_by_horizon"
    MAE_BY_HORIZON = "mae_by_horizon"
    TARGET_BEFORE_STOP = "target_before_stop"
    STOP_BEFORE_TARGET = "stop_before_target"
    FUTURE_REALIZED_VOLATILITY = "future_realized_volatility"
    FUTURE_SPREAD_LIQUIDITY = "future_spread_liquidity"


class Direction(TextEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"
    LONG_SHORT = "long_short"


class ExecutionTiming(TextEnum):
    NEXT_BAR_CONSERVATIVE = "next_bar_conservative"


class BookSide(TextEnum):
    BID = "bid"
    ASK = "ask"


class L2EventType(TextEnum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    CLEAR = "clear"


class DecisionStatus(TextEnum):
    DRAFT = "draft"
    REVIEW_REQUIRED = "review_required"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
