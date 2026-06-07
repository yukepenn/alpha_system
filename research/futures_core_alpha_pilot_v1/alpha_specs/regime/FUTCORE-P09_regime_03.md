# FUTCORE-P09 Regime AlphaSpec 03

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the regime-gated momentum/reversion family.

```json
{
  "alpha_spec_id": "aspec_edc47c5593bcaaf6d2d8c42b",
  "hypothesis_id": "hyp_071664b41c10dccc28fbd65d",
  "target_instruments": [
    "ES",
    "NQ"
  ],
  "data_assumptions": {
    "input_pack_binding": "Bind by reference to DatasetVersion dsv_databento_ohlcv_05404069799decb0, locked session FeatureVersions, and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395; no data values are read by this draft.",
    "regime_activation_logic": {
      "regime_inputs": "Use completed ETH session context, RTH_with_ETH_context session metadata, early RTH trendiness, rolling volatility, rolling range, and completed-bar return direction.",
      "momentum_gate": "Momentum is active only during RTH_with_ETH_context when completed ETH direction and early RTH high-trendiness regime agree and volatility is not in a high-stress band.",
      "reversion_gate": "Reversion is active when early RTH trendiness is low, rolling range is compressed, and the current bar rejects a completed ETH extreme or completed ETH directional context.",
      "lookahead_boundary": "Completed ETH context may be used only after the ETH window is complete; final RTH high, low, range, volume, or VWAP cannot be used intraday."
    },
    "horizon_policy": {
      "primary_horizons": "The locked 5m label is referenced now; 10m, 15m, and 30m remain primary-policy candidates requiring later LabelSpec coverage.",
      "fragile_horizons": "1m and 3m are diagnostics-only fragile views and must carry stricter spread, liquidity, and thin-session caveats.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded unless later review requires extended diagnostics with regime-overlap caveats.",
      "maintenance_boundary": "The modeled outcome window must close before the exchange daily maintenance or trade-date break."
    },
    "session_policy": {
      "primary_sessions": "RTH_with_ETH_context is the primary decision view because the regime uses completed ETH context and current RTH point-in-time inputs.",
      "diagnostic_sessions": "RTH, RTH_only, full_session, pre_RTH, and post_RTH are diagnostic comparisons; ETH_only, ETH_evening, and ETH_overnight are context windows rather than direct decision sessions for the main draft.",
      "excluded_sessions": "Any RTH decision lacking completed ETH context availability or unambiguous exchange_trade_date mapping is excluded."
    },
    "family_quota": "This draft consumes one of the maximum six regime-family slots and does not expand the P09 quota.",
    "declared_diagnostics": "Later diagnostics must split completed-ETH-aligned momentum, completed-ETH-rejection reversion, inactive transition states, and RTH_with_ETH_context coverage.",
    "duplicate_exposure": "The draft overlaps VWAP/session and broad trend context, so the critic must verify that completed ETH context is only a regime gate and not a separate session-auction family draft."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.OVERNIGHT_RANGE",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.TRENDINESS",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_VOLATILITY",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_RANGE",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.RETURNS",
    "src.alpha_system.features.families.session.SessionFeatureName.RTH_SEGMENT_FLAG",
    "src.alpha_system.features.families.session.SessionFeatureName.ETH_SEGMENT_FLAG",
    "locked_feature_pack:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "locked_feature_pack:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any RTH_with_ETH_context decision before the ETH context window is complete and timestamped as available.",
    "Exclude any use of final RTH aggregates before RTH close, including final RTH high, low, range, volume, or VWAP.",
    "Exclude bars where completed ETH direction, early RTH trendiness, rolling volatility, or rolling range cannot be computed from completed available_ts-aligned inputs.",
    "Exclude transition bars where ETH-aligned momentum and ETH-rejection reversion both appear active.",
    "Exclude any variant that duplicates a VWAP/session-auction draft without preserving the explicit regime activation gates."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "Decision_ts is inside RTH after the current completed bar and after all ETH context fields used by the gate have available_ts not later than decision_ts.",
    "available_ts_usage": {
      "completed_eth_context": "Completed ETH high, low, direction, and range context are eligible only after the ETH window is complete and available.",
      "rth_inputs": "Early RTH trendiness, volatility, range, and return direction use completed bars only and inherit the latest component available_ts.",
      "session_metadata": "RTH and ETH segment flags, session minute, and exchange_trade_date are point-in-time session metadata."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e is a downstream target reference and cannot influence any RTH decision input.",
    "session_boundaries": "RTH_with_ETH_context must join completed ETH context to the same exchange_trade_date convention without crossing the daily maintenance break.",
    "same_bar_policy": "Same-bar outcome, future label, centered window, and final-session aggregate joins are forbidden.",
    "cross_instrument_alignment": "ES and NQ cells are evaluated independently; this draft does not consume one instrument as a signal for another."
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
    "layers": "Layer 1 hard costs, Layer 2 valid point-in-time BBO spread crossing where available, and Layer 3 slippage plus capacity proxy are required in later StudySpec binding.",
    "thin_session_overlay": "ETH context is not a direct execution-session claim; any ETH_only or transition diagnostic still requires the P04 thin-session overlay on non-zero profiles.",
    "promotion_profile_boundary": "Later review criteria may reference base, stress_1, stress_2, and double_cost only; cost and capacity outputs remain proxy sensitivities."
  },
  "expected_failure_modes": [
    "Completed ETH context may have sparse or uneven coverage by instrument and exchange_trade_date convention.",
    "Early RTH regime transitions can be unstable around the open and can flip momentum and reversion gates too frequently.",
    "The idea can duplicate VWAP/session or overnight-context exposure unless the regime gate remains explicit.",
    "Using final RTH or incomplete ETH aggregates would create lookahead leakage and invalidate the draft.",
    "Only the 5m label is currently locked; other primary horizons require later audited LabelSpec references.",
    "Thin-session and RTH transition cost treatment may reveal cost fragility in later diagnostics."
  ],
  "promotion_criteria": [
    "Independent critique can verify completed ETH context availability and early RTH point-in-time regime gates without final-session leakage.",
    "Later diagnostics record coverage separately for ETH-aligned momentum, ETH-rejection reversion, and inactive transition states.",
    "Non-zero cost sensitivities for base, stress_1, stress_2, and double_cost are bound with visible thin-session context caveats.",
    "The draft remains a regime-family idea and does not become a duplicate VWAP/session-auction draft without separate critique.",
    "Any missing ETH context or non-5m label coverage is routed to FUTCORE-P13 or FUTCORE-P15 before downstream use."
  ],
  "created_by": "Hypothesis Scout:rq.p09.regime_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
