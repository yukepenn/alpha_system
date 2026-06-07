# FUTCORE-P09 Regime AlphaSpec 04

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the regime-gated momentum/reversion family.

```json
{
  "alpha_spec_id": "aspec_d26b7959b12be5b53f969067",
  "hypothesis_id": "hyp_69d273adbd7a6145f5d78b6b",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "input_pack_binding": "Bind by reference to DatasetVersion dsv_databento_ohlcv_05404069799decb0, locked session FeatureVersions, and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395; this draft records no feature or label values.",
    "regime_activation_logic": {
      "regime_inputs": "Use point-in-time range_contraction, rolling_range, close_location_value, trendiness, and completed-bar return direction from existing OHLCV and liquidity-structure primitive families.",
      "momentum_gate": "Momentum is active when range compression releases beyond a causal rolling range boundary and the completed-bar trendiness regime is high.",
      "reversion_gate": "Reversion is active when range compression is followed by a close back inside the causal range or low-trendiness rejection of the attempted release.",
      "transition_state": "Compression release bars that cannot be classified from completed data are inactive until the momentum or reversion gate is unambiguous."
    },
    "horizon_policy": {
      "primary_horizons": "Use the locked 5m label reference for initial binding; 10m, 15m, and 30m are primary-policy candidates requiring later audited label availability.",
      "fragile_horizons": "1m and 3m can only be diagnostic views with explicit execution-fragility caveats.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded from this draft unless later StudySpec work records stronger overlap and stability caveats.",
      "maintenance_boundary": "All modeled windows remain flat before the daily maintenance or trade-date break."
    },
    "session_policy": {
      "primary_sessions": "RTH and RTH_with_ETH_context are primary views because range compression and release can be calculated from completed intraday bars.",
      "diagnostic_sessions": "full_session, ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH are diagnostic views with thin-session caveats.",
      "excluded_sessions": "Any session lacking causal rolling range availability, session metadata, or unambiguous range-boundary provenance is excluded."
    },
    "family_quota": "This draft stays inside the maximum six FUTCORE-P09 regime drafts and does not allocate volume or liquidity-family budget.",
    "declared_diagnostics": "Later diagnostics must report compression momentum releases, compression reversion failures, inactive transition states, and duplicate overlap with liquidity/PA drafts.",
    "duplicate_exposure": "This draft intentionally overlaps liquidity/PA compression and failed-breakout primitives; the distinguishing feature is the regime gate that chooses momentum or reversion."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.structure.StructureFeatureName.RANGE_CONTRACTION",
    "src.alpha_system.features.families.structure.StructureFeatureName.CLOSE_LOCATION_VALUE",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_RANGE",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.TRENDINESS",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.RETURNS",
    "src.alpha_system.features.families.session.SessionFeatureName.RTH_SEGMENT_FLAG",
    "locked_feature_pack:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "locked_feature_pack:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any compression, range boundary, or close-location input that is not available from completed bars at decision_ts.",
    "Exclude visual-only pattern labels or subjective breakout annotations; only computable primitive conditions are eligible.",
    "Exclude bars where momentum release and reversion failure conditions both appear active or neither can be assigned reliably.",
    "Exclude variants that duplicate liquidity/PA failed-breakout drafts without recording this regime-gated activation logic.",
    "Exclude any decision with missing label_available_ts, unresolved symbol coverage, or absent non-zero cost profile binding."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "The decision timestamp follows a completed bar and is no earlier than all range, close-location, trendiness, and session available_ts inputs.",
    "available_ts_usage": {
      "range_inputs": "Rolling range, range contraction, and close-location values are computed from causal windows and completed bars only.",
      "trend_inputs": "Trendiness and completed-bar return direction inherit the latest component available_ts.",
      "session_inputs": "Session flags and session minute are point-in-time metadata with availability not later than decision_ts."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e is a future target reference with label_available_ts after the outcome window and is never an input.",
    "session_boundaries": "No final session range, final session high, final session low, or final session VWAP can be used before session completion.",
    "same_bar_policy": "Same-bar outcomes, centered windows, and future windows are forbidden for both compression and release classification.",
    "cross_instrument_alignment": "All activation rules are per-instrument; no cross-instrument synchronization is part of this draft."
  },
  "cost_assumptions": {
    "cost_model_version": "cmv_futcore_pilot_three_layer_session_stress_v1",
    "profile_names": "Exactly zero_cost, base, stress_1, stress_2, and double_cost are in scope for later cost sensitivity.",
    "profiles": {
      "zero_cost": "Diagnostic contrast only with promotion_basis_allowed=false and no use as a favorable continuation condition.",
      "base": "Central non-zero hard cost, spread crossing, slippage proxy, and capacity proxy sensitivity.",
      "stress_1": "Non-zero stress profile not less conservative than base for hard cost, spread crossing, slippage proxy, and capacity proxy.",
      "stress_2": "Non-zero stress profile not less conservative than stress_1 for the same inputs and session view.",
      "double_cost": "Upper non-zero cost sensitivity relative to base before applicable thin-session overlays."
    },
    "layers": "Later StudySpec binding must include hard transaction cost, valid point-in-time spread crossing where available, and slippage plus capacity proxy.",
    "thin_session_overlay": "Thin-session views require stricter non-zero spread, slippage, and capacity proxy treatment.",
    "promotion_profile_boundary": "Later review criteria may reference base, stress_1, stress_2, and double_cost only; BBO and capacity outputs remain proxy sensitivities."
  },
  "expected_failure_modes": [
    "Range compression releases may be sparse and can concentrate in specific session or instrument cells.",
    "Compression-to-release transition bars can be unstable and sensitive to threshold definitions.",
    "The draft may duplicate liquidity/PA failed-breakout exposure if the critic cannot separate the regime gate from objective pattern primitives.",
    "Incomplete available_ts ordering or final range aggregation would create lookahead leakage.",
    "Non-5m primary horizons require later audited LabelSpec references before use.",
    "Non-zero cost and thin-session overlays may reveal cost fragility in later diagnostics."
  ],
  "promotion_criteria": [
    "The critic can trace each active decision to either a compression-release momentum gate or a compression-failure reversion gate.",
    "Later diagnostics record per-regime sample counts, transition inactive counts, session splits, and duplicate overlap with liquidity/PA drafts.",
    "Non-zero cost sensitivities for base, stress_1, stress_2, and double_cost are bound before evidence review.",
    "All range, close-location, and trend inputs are available at decision_ts with no final-session aggregate dependency.",
    "Any missing structure primitive FeatureVersion or non-5m LabelSpec is recorded as a FUTCORE-P13 or FUTCORE-P15 gap."
  ],
  "created_by": "Hypothesis Scout:rq.p09.regime_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
