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
    "SymbolYearFrameRequest",
    "build_base_ohlcv_pack",
    "build_fast_feature_pack",
    "supports_base_ohlcv_pack",
]
