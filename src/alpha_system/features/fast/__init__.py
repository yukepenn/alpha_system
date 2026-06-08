"""Vectorized feature producer core for the fast-path campaign."""

from alpha_system.features.fast.bbo_tradability import (
    BBO_TRADABILITY_DDOF,
    BBO_TRADABILITY_FEATURE_IDS,
    BBO_TRADABILITY_LOW_DEPTH_THRESHOLD,
    BBO_TRADABILITY_RESET_ON_SESSION,
    BBO_TRADABILITY_WIDE_SPREAD_BPS_THRESHOLD,
    BBO_TRADABILITY_WINDOW_LENGTH,
    build_bbo_tradability_pack,
    supports_bbo_tradability_pack,
)
from alpha_system.features.fast.base_ohlcv import (
    BASE_OHLCV_DDOF,
    BASE_OHLCV_FEATURE_IDS,
    BASE_OHLCV_HORIZON,
    BASE_OHLCV_RESET_ON_SESSION,
    BASE_OHLCV_WINDOW_LENGTH,
    build_base_ohlcv_pack,
    supports_base_ohlcv_pack,
)
from alpha_system.features.fast.cross_market_panel import (
    CROSS_MARKET_FEATURE_IDS,
    build_cross_market_pack,
    supports_cross_market_pack,
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
from alpha_system.features.fast.liquidity_pa_structure import (
    LIQUIDITY_PA_STRUCTURE_FEATURE_IDS,
    build_liquidity_pa_structure_pack,
    supports_liquidity_pa_structure_pack,
)
from alpha_system.features.fast.packs import build_fast_feature_pack
from alpha_system.features.fast.regime_vol_compression import (
    REGIME_VOL_COMPRESSION_FEATURE_IDS,
    build_regime_vol_compression_pack,
    supports_regime_vol_compression_pack,
)
from alpha_system.features.fast.session_calendar_roll import (
    SESSION_CALENDAR_ROLL_FEATURE_IDS,
    build_session_calendar_roll_pack,
    supports_session_calendar_roll_pack,
)
from alpha_system.features.fast.volume_activity import (
    VOLUME_ACTIVITY_DDOF,
    VOLUME_ACTIVITY_FEATURE_IDS,
    VOLUME_ACTIVITY_HORIZON,
    VOLUME_ACTIVITY_RESET_ON_SESSION,
    VOLUME_ACTIVITY_WINDOW_LENGTH,
    build_volume_activity_pack,
    supports_volume_activity_pack,
)
from alpha_system.features.fast.vwap_session_auction import (
    VWAP_SESSION_AUCTION_FEATURE_IDS,
    VWAP_SESSION_AUCTION_FEATURE_NAMES,
    build_vwap_session_auction_pack,
    supports_vwap_session_auction_pack,
)

__all__ = [
    "BBO_TRADABILITY_DDOF",
    "BBO_TRADABILITY_FEATURE_IDS",
    "BBO_TRADABILITY_LOW_DEPTH_THRESHOLD",
    "BBO_TRADABILITY_RESET_ON_SESSION",
    "BBO_TRADABILITY_WIDE_SPREAD_BPS_THRESHOLD",
    "BBO_TRADABILITY_WINDOW_LENGTH",
    "BASE_OHLCV_DDOF",
    "BASE_OHLCV_FEATURE_IDS",
    "BASE_OHLCV_HORIZON",
    "BASE_OHLCV_RESET_ON_SESSION",
    "BASE_OHLCV_WINDOW_LENGTH",
    "CROSS_MARKET_FEATURE_IDS",
    "FAST_PRODUCER_ENGINE_ID",
    "FAST_VALUE_SCHEMA_VERSION",
    "FastFeatureDeclaration",
    "FastFeaturePack",
    "LIQUIDITY_PA_STRUCTURE_FEATURE_IDS",
    "PackMaterializer",
    "PackMaterializerError",
    "REGIME_VOL_COMPRESSION_FEATURE_IDS",
    "SESSION_CALENDAR_ROLL_FEATURE_IDS",
    "SymbolYearFrameRequest",
    "VOLUME_ACTIVITY_DDOF",
    "VOLUME_ACTIVITY_FEATURE_IDS",
    "VOLUME_ACTIVITY_HORIZON",
    "VOLUME_ACTIVITY_RESET_ON_SESSION",
    "VOLUME_ACTIVITY_WINDOW_LENGTH",
    "VWAP_SESSION_AUCTION_FEATURE_IDS",
    "VWAP_SESSION_AUCTION_FEATURE_NAMES",
    "build_bbo_tradability_pack",
    "build_base_ohlcv_pack",
    "build_cross_market_pack",
    "build_fast_feature_pack",
    "build_liquidity_pa_structure_pack",
    "build_regime_vol_compression_pack",
    "build_session_calendar_roll_pack",
    "build_volume_activity_pack",
    "build_vwap_session_auction_pack",
    "supports_bbo_tradability_pack",
    "supports_base_ohlcv_pack",
    "supports_cross_market_pack",
    "supports_liquidity_pa_structure_pack",
    "supports_regime_vol_compression_pack",
    "supports_session_calendar_roll_pack",
    "supports_volume_activity_pack",
    "supports_vwap_session_auction_pack",
]
