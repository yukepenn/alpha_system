# FUTCORE-P09 Regime AlphaSpec 05

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the regime-gated momentum/reversion family.

```json
{
  "alpha_spec_id": "aspec_f2de85c342e1bc2018297ff7",
  "hypothesis_id": "hyp_b546ba17d1763c2c3cfff616",
  "target_instruments": [
    "RTY",
    "ES"
  ],
  "data_assumptions": {
    "input_pack_binding": "Bind by reference to DatasetVersion dsv_databento_ohlcv_05404069799decb0, locked session FeatureVersions, and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395; no market values are recorded.",
    "regime_activation_logic": {
      "regime_inputs": "Use point-in-time session segment, minutes_from_RTH_open, minutes_to_RTH_close, trendiness, rolling_volatility, rolling_range, and completed-bar return direction.",
      "momentum_gate": "Momentum is active near an allowed session transition only when completed bars show high trendiness and volatility expansion after the transition boundary.",
      "reversion_gate": "Reversion is active after an allowed session transition when trendiness is low, volatility contracts, or rolling range compresses after an initial transition move.",
      "transition_state": "The exact boundary bars around pre_RTH, RTH open, RTH close, and post_RTH are inactive unless all session and regime inputs are available and unambiguous."
    },
    "horizon_policy": {
      "primary_horizons": "The locked 5m LabelSpec is the only current label reference; 10m, 15m, and 30m are primary-policy candidates deferred to later audited LabelSpec work.",
      "fragile_horizons": "1m and 3m are fragile diagnostics only and require stricter transition-session spread and cost caveats.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded because transition regimes need tighter same-session boundaries in this draft.",
      "maintenance_boundary": "No modeled position crosses the exchange maintenance or trade-date break."
    },
    "session_policy": {
      "primary_sessions": "RTH, pre_RTH, post_RTH, and RTH_with_ETH_context are the main transition views for this draft.",
      "diagnostic_sessions": "full_session, ETH_only, ETH_evening, and ETH_overnight are diagnostic views requiring thin-session stress and coverage caveats.",
      "excluded_sessions": "Any segment without point-in-time session boundary metadata, exchange_trade_date, or transition-minute availability is excluded."
    },
    "family_quota": "This is a regime-family draft inside the fixed P09 maximum of six and does not create a separate session-auction draft.",
    "declared_diagnostics": "Later diagnostics must report transition momentum cells, transition reversion cells, inactive boundary cells, thin-session overlays, and instrument-specific coverage.",
    "duplicate_exposure": "This draft overlaps session and volatility filters; the critic must check that the session transition only gates the momentum-versus-reversion regime."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.session.SessionFeatureName.MINUTES_FROM_RTH_OPEN",
    "src.alpha_system.features.families.session.SessionFeatureName.MINUTES_TO_RTH_CLOSE",
    "src.alpha_system.features.families.session.SessionFeatureName.RTH_SEGMENT_FLAG",
    "src.alpha_system.features.families.session.SessionFeatureName.ETH_SEGMENT_FLAG",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.TRENDINESS",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_VOLATILITY",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_RANGE",
    "locked_feature_pack:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "locked_feature_pack:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude session transition bars without point-in-time session boundary metadata and exchange_trade_date mapping.",
    "Exclude bars where transition momentum and transition reversion gates conflict or where the transition window cannot be assigned from completed data.",
    "Exclude ETH, pre_RTH, and post_RTH diagnostics unless thin-session non-zero cost overlays are bound.",
    "Exclude any final-session aggregate usage before the relevant session is complete.",
    "Exclude variants that reduce to a session-time filter without explicit trendiness, volatility, or range-compression gates."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "Decision_ts occurs after a completed bar and after session-boundary and regime inputs have available_ts not later than the decision timestamp.",
    "available_ts_usage": {
      "session_inputs": "Session segment, minutes_from_RTH_open, and minutes_to_RTH_close are point-in-time metadata, not labels.",
      "regime_inputs": "Trendiness, rolling volatility, rolling range, and completed return direction are causal completed-bar inputs anchored on available_ts.",
      "transition_inputs": "Pre_RTH, RTH open, RTH close, and post_RTH transition windows must be computed from timestamped session metadata only."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e is used only as a 5m target reference after label_available_ts.",
    "session_boundaries": "RTH_with_ETH_context may use completed ETH context only after completion, and no outcome may cross the maintenance or trade-date break.",
    "same_bar_policy": "Same-bar outcomes, future labels, centered windows, and arbitrary clock joins are forbidden.",
    "cross_instrument_alignment": "RTY and ES decisions are independent instrument cells; no lead-lag relation is defined."
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
    "layers": "Later StudySpec binding must include hard transaction cost, point-in-time spread crossing where available, and slippage plus capacity proxy.",
    "thin_session_overlay": "pre_RTH, post_RTH, ETH_only, ETH_evening, and ETH_overnight require stricter non-zero spread, slippage, and capacity proxy settings.",
    "promotion_profile_boundary": "Later review criteria may reference base, stress_1, stress_2, and double_cost only; cost outputs remain proxy sensitivities."
  },
  "expected_failure_modes": [
    "Session transition regimes may be under-covered or dominated by a narrow time-of-day cell.",
    "Boundary bars can be unstable because session metadata and completed-bar regime metrics update at different timestamps.",
    "The draft may duplicate session-auction or broad volatility filters if the transition gate is not treated as a regime selector.",
    "Thin-session and transition-session cost treatment may be especially fragile in later diagnostics.",
    "Only the 5m label is locked, so non-5m primary horizons require later LabelSpec references.",
    "Any session aggregate used before completion or same-bar outcome join would invalidate the draft."
  ],
  "promotion_criteria": [
    "The critic can verify that transition timing only gates momentum versus reversion and does not act as a standalone session filter.",
    "Later diagnostics record transition-cell sample counts, inactive boundary counts, session splits, and thin-session limitations.",
    "Non-zero cost sensitivities for base, stress_1, stress_2, and double_cost are bound before evidence review.",
    "Every transition input and regime metric is available at decision_ts and no final-session aggregate is consumed intraday.",
    "Any missing transition primitive or non-5m label is routed to FUTCORE-P13 or FUTCORE-P15 before downstream use."
  ],
  "created_by": "Hypothesis Scout:rq.p09.regime_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
