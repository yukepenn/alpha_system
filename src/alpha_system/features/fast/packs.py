"""Fast-pack resolver for governed V1 feature families."""

from __future__ import annotations

from alpha_system.features.contracts import FeatureSetSpec
from alpha_system.features.fast.base_ohlcv import (
    build_base_ohlcv_pack,
    supports_base_ohlcv_pack,
)
from alpha_system.features.fast.materializer import FastFeaturePack, PackMaterializerError
from alpha_system.features.fast.regime_vol_compression import (
    build_regime_vol_compression_pack,
    supports_regime_vol_compression_pack,
)
from alpha_system.features.fast.session_calendar_roll import (
    build_session_calendar_roll_pack,
    supports_session_calendar_roll_pack,
)
from alpha_system.features.fast.vwap_session_auction import (
    build_vwap_session_auction_pack,
    supports_vwap_session_auction_pack,
)


def build_fast_feature_pack(feature_set: FeatureSetSpec) -> FastFeaturePack:
    """Resolve a governed feature set to its V1 fast pack."""

    if supports_base_ohlcv_pack(feature_set):
        return build_base_ohlcv_pack(feature_set)
    if supports_session_calendar_roll_pack(feature_set):
        return build_session_calendar_roll_pack(feature_set)
    if supports_vwap_session_auction_pack(feature_set):
        return build_vwap_session_auction_pack(feature_set)
    if supports_regime_vol_compression_pack(feature_set):
        return build_regime_vol_compression_pack(feature_set)
    raise PackMaterializerError("no V1 fast pack registered for this FeatureSetSpec")


__all__ = ["build_fast_feature_pack"]
