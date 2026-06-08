"""Vectorized feature producer core for the fast-path campaign."""

from alpha_system.features.fast.base_ohlcv import (
    BASE_OHLCV_DDOF,
    BASE_OHLCV_FEATURE_IDS,
    BASE_OHLCV_HORIZON,
    BASE_OHLCV_RESET_ON_SESSION,
    BASE_OHLCV_WINDOW_LENGTH,
    build_base_ohlcv_pack,
    supports_base_ohlcv_pack,
)
from alpha_system.features.fast.materializer import (
    FAST_PRODUCER_ENGINE_ID,
    FAST_VALUE_SCHEMA_VERSION,
    FastFeatureDeclaration,
    FastFeaturePack,
    PackMaterializer,
    PackMaterializerError,
    SymbolYearFrameRequest,
)
from alpha_system.features.fast.packs import build_fast_feature_pack
from alpha_system.features.fast.session_calendar_roll import (
    SESSION_CALENDAR_ROLL_FEATURE_IDS,
    build_session_calendar_roll_pack,
    supports_session_calendar_roll_pack,
)
from alpha_system.features.fast.vwap_session_auction import (
    VWAP_SESSION_AUCTION_FEATURE_IDS,
    VWAP_SESSION_AUCTION_FEATURE_NAMES,
    build_vwap_session_auction_pack,
    supports_vwap_session_auction_pack,
)

__all__ = [
    "BASE_OHLCV_DDOF",
    "BASE_OHLCV_FEATURE_IDS",
    "BASE_OHLCV_HORIZON",
    "BASE_OHLCV_RESET_ON_SESSION",
    "BASE_OHLCV_WINDOW_LENGTH",
    "FAST_PRODUCER_ENGINE_ID",
    "FAST_VALUE_SCHEMA_VERSION",
    "FastFeatureDeclaration",
    "FastFeaturePack",
    "PackMaterializer",
    "PackMaterializerError",
    "SESSION_CALENDAR_ROLL_FEATURE_IDS",
    "SymbolYearFrameRequest",
    "VWAP_SESSION_AUCTION_FEATURE_IDS",
    "VWAP_SESSION_AUCTION_FEATURE_NAMES",
    "build_base_ohlcv_pack",
    "build_fast_feature_pack",
    "build_session_calendar_roll_pack",
    "build_vwap_session_auction_pack",
    "supports_base_ohlcv_pack",
    "supports_session_calendar_roll_pack",
    "supports_vwap_session_auction_pack",
]
