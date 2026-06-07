# FUTCORE-P09 Regime AlphaSpec 06

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the regime-gated momentum/reversion family.

```json
{
  "alpha_spec_id": "aspec_ad998ced05be1a90c92bee1e",
  "hypothesis_id": "hyp_e3f92fc321263008ab748040",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "input_pack_binding": "Bind by reference to DatasetVersion dsv_databento_ohlcv_05404069799decb0, locked session FeatureVersions, and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395; no value rows are recorded.",
    "regime_activation_logic": {
      "regime_inputs": "Use point-in-time distance_to_vwap, anchored_vwap or running VWAP context, rolling_volatility, rolling_range, trendiness, and completed-bar return direction.",
      "momentum_gate": "Momentum is active when distance_to_vwap expands with high trendiness and non-stressed volatility, using only running or anchored VWAP values available at decision_ts.",
      "reversion_gate": "Reversion is active when distance_to_vwap is extended while trendiness is low or rolling range is compressed, again using only point-in-time VWAP context.",
      "lookahead_boundary": "Final-session VWAP, final-session range, and final-session volume are forbidden intraday; only running or completed context with available_ts may define the gate."
    },
    "horizon_policy": {
      "primary_horizons": "The locked 5m LabelSpec is referenced now; 10m, 15m, and 30m require later audited LabelSpec availability before use.",
      "fragile_horizons": "1m and 3m are execution-fragile diagnostics only with stricter spread, liquidity, and cost caveats.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded unless later StudySpec work adds explicit extended-horizon stability caveats.",
      "maintenance_boundary": "No modeled holding period may cross the exchange maintenance or trade-date break."
    },
    "session_policy": {
      "primary_sessions": "RTH and RTH_with_ETH_context are primary because running VWAP and completed ETH context can be made point-in-time.",
      "diagnostic_sessions": "full_session, ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH are diagnostic views with thin-session and VWAP-availability caveats.",
      "excluded_sessions": "Any session without running VWAP available_ts, session metadata, or clear completed-context provenance is excluded."
    },
    "family_quota": "This draft is the sixth and final target regime-family draft under the hard maximum of six.",
    "declared_diagnostics": "Later diagnostics must report VWAP-distance momentum gates, VWAP-distance reversion gates, inactive transition states, running-versus-final VWAP checks, and duplicate VWAP/session exposure.",
    "duplicate_exposure": "This draft overlaps VWAP/session and broad trend filters; it remains in the regime family only because VWAP distance is a gate for momentum versus reversion."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.DISTANCE_TO_VWAP",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ANCHORED_VWAP",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.VWAP",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_VOLATILITY",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_RANGE",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.TRENDINESS",
    "src.alpha_system.features.families.session.SessionFeatureName.RTH_SEGMENT_FLAG",
    "locked_feature_pack:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "locked_feature_pack:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any use of final-session VWAP, final-session range, final-session volume, or other final aggregate before session completion.",
    "Exclude decisions where running VWAP, anchored VWAP, distance_to_vwap, trendiness, volatility, range, or session metadata lacks valid available_ts.",
    "Exclude transition bars where VWAP-distance momentum and VWAP-distance reversion gates conflict.",
    "Exclude variants that are only VWAP/session-auction drafts without the explicit trendiness, volatility, or range-compression gate.",
    "Exclude any downstream binding without non-zero cost profiles and thin-session overlays for affected session views."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "The decision timestamp follows a completed bar and is no earlier than the latest available_ts for running VWAP context, volatility, range, trendiness, and session metadata.",
    "available_ts_usage": {
      "vwap_inputs": "VWAP context must be running, anchored, or completed-context data with explicit available_ts; final-session VWAP is unavailable intraday.",
      "regime_inputs": "Trendiness, rolling volatility, rolling range, and distance_to_vwap use causal completed-bar windows.",
      "session_inputs": "RTH flags and session minute are point-in-time session metadata and are not future labels."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e remains a 5m target reference with label_available_ts after the target window.",
    "session_boundaries": "RTH_with_ETH_context may use completed ETH context only after ETH completion, and all outcomes must finish before the maintenance break.",
    "same_bar_policy": "Same-bar outcome information, final-session aggregates, centered windows, and future windows are forbidden.",
    "cross_instrument_alignment": "ES, NQ, and RTY are evaluated independently with no cross-instrument join in this draft."
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
    "layers": "Later StudySpec binding must include hard transaction cost, valid point-in-time BBO spread crossing where available, and slippage plus capacity proxy.",
    "thin_session_overlay": "ETH, pre_RTH, and post_RTH diagnostics require stricter non-zero spread, slippage, and capacity proxy treatment.",
    "promotion_profile_boundary": "Later review criteria may reference base, stress_1, stress_2, and double_cost only; cost and capacity outputs remain proxy sensitivities."
  },
  "expected_failure_modes": [
    "VWAP-distance activation can duplicate VWAP/session drafts unless the trendiness and volatility regime gates remain explicit.",
    "Running VWAP availability may differ by session view and can create sparse or uneven per-regime coverage.",
    "Regime transition states near VWAP can oscillate between momentum and reversion gates.",
    "Final-session VWAP or final-session volume usage would create intraday lookahead leakage and invalidate the draft.",
    "Only the 5m LabelSpec is currently locked, so other primary horizons require later audited label coverage.",
    "Non-zero cost profiles and thin-session overlays may expose cost fragility in later diagnostics."
  ],
  "promotion_criteria": [
    "The critic can verify that VWAP distance only gates momentum versus reversion and does not become a standalone VWAP/session draft.",
    "Later diagnostics record running-versus-final VWAP checks, per-regime sample counts, transition inactive counts, and duplicate exposure notes.",
    "Non-zero cost sensitivities for base, stress_1, stress_2, and double_cost are bound before evidence review.",
    "Every VWAP and regime input has available_ts not later than decision_ts and no final-session aggregate is consumed intraday.",
    "Any missing VWAP FeatureVersion or non-5m label reference is routed to FUTCORE-P13 or FUTCORE-P15 before downstream use."
  ],
  "created_by": "Hypothesis Scout:rq.p09.regime_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
