# FUTCORE-P09 Regime AlphaSpec 02

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the regime-gated momentum/reversion family.

```json
{
  "alpha_spec_id": "aspec_7db3a23e98ca7ff99b1805c6",
  "hypothesis_id": "hyp_393c3bb221369b0358821e11",
  "target_instruments": [
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "input_pack_binding": "Bind by reference to DatasetVersion dsv_databento_ohlcv_05404069799decb0, the locked session FeatureVersions, and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395; no value files are read by this draft.",
    "regime_activation_logic": {
      "regime_inputs": "Use point-in-time rolling_volatility, ATR, rolling_range, trendiness, and completed-bar return direction from causal base_ohlcv primitives.",
      "momentum_gate": "Momentum is active when rolling volatility and ATR are expanding from completed bars, trendiness is rising, and the completed return direction agrees with the expansion regime.",
      "reversion_gate": "Reversion is active when rolling volatility is contracting, rolling range is compressed, and trendiness is low; this is a volatility-compression reversion gate rather than a global fade rule.",
      "transition_state": "During volatility expansion-to-contraction or contraction-to-expansion flips, the StudySpec must record an inactive transition state until the point-in-time gate is stable."
    },
    "horizon_policy": {
      "primary_horizons": "The locked 5m label is the only currently referenced label; 10m, 15m, and 30m are primary-policy candidates that require later audited labels.",
      "fragile_horizons": "1m and 3m may be sampled only for execution-fragile diagnostics and cannot drive later review continuation alone.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded from this draft unless a later StudySpec adds explicit extended-horizon caveats.",
      "maintenance_boundary": "All modeled windows must close before the exchange maintenance and trade-date break."
    },
    "session_policy": {
      "primary_sessions": "RTH and RTH_with_ETH_context are primary because volatility expansion and compression can be checked after completed bars.",
      "diagnostic_sessions": "ETH_only, ETH_evening, ETH_overnight, pre_RTH, post_RTH, and full_session are diagnostic views requiring thin-session coverage and cost caveats.",
      "excluded_sessions": "Any segment with missing session minute, unknown exchange_trade_date, or unresolved symbol coverage is excluded."
    },
    "family_quota": "This is one of six target regime drafts under the fixed FUTCORE-P09 quota and does not reallocate unused budget from any other family.",
    "declared_diagnostics": "Later diagnostics must split activation counts by volatility-expansion momentum, volatility-compression reversion, inactive transition state, session view, horizon, and instrument.",
    "duplicate_exposure": "The draft has deliberate exposure to broad realized-volatility filters; the critic must check that the separate trendiness and compression gates add a distinct regime condition."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_VOLATILITY",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ATR",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_RANGE",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.TRENDINESS",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.RETURNS",
    "src.alpha_system.features.families.session.SessionFeatureName.MINUTES_FROM_RTH_OPEN",
    "locked_feature_pack:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "locked_feature_pack:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any volatility gate computed from incomplete bars, centered windows, future bars, or same-bar outcome information.",
    "Exclude any decision where ATR, rolling volatility, rolling range, trendiness, session metadata, or the 5m label reference lacks valid availability metadata.",
    "Exclude inactive transition bars and near-threshold gate flips from both momentum and reversion arms.",
    "Exclude thin-session diagnostics unless non-zero cost profiles and thin-session overlays are explicitly bound by the later StudySpec.",
    "Exclude variants that are indistinguishable from a generic volatility filter without the declared trendiness and compression conditions."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "Signals form after a completed bar, with decision_ts equal to or later than the latest available_ts of the volatility, range, trendiness, and session inputs.",
    "available_ts_usage": {
      "ohlcv_inputs": "High, low, close, and volume inputs are consumed only after the completed bar available_ts.",
      "volatility_inputs": "Rolling volatility and ATR use causal rolling windows anchored on available_ts and must never include the decision bar outcome.",
      "session_inputs": "Session minute and RTH flag inputs are point-in-time metadata that must precede the decision timestamp."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e is used only after its label_available_ts and remains a downstream target reference.",
    "session_boundaries": "RTH_with_ETH_context may use completed ETH context only when the ETH window is finished; final RTH aggregates are unavailable before RTH close.",
    "same_bar_policy": "Same-bar outcome joins, future label leakage, and arbitrary wall-clock joins are forbidden.",
    "cross_instrument_alignment": "NQ and RTY are evaluated as independent instrument cells; this draft does not define cross-market lead-lag alignment."
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
    "layers": "Layer 1 hard transaction cost, Layer 2 point-in-time spread crossing, and Layer 3 slippage plus capacity proxy must be configured later by StudySpec.",
    "thin_session_overlay": "ETH, pre_RTH, and post_RTH views require stricter non-zero cost and capacity proxy treatment than comparable RTH cells.",
    "promotion_profile_boundary": "Later review criteria may reference base, stress_1, stress_2, and double_cost only; cost outputs remain proxy sensitivities."
  },
  "expected_failure_modes": [
    "Volatility expansion can become a broad volatility filter if the trendiness and completed-direction gates are not enforced.",
    "Volatility compression cells may have limited coverage and unstable boundaries near session transitions.",
    "NQ and RTY may show different missingness or symbol-level pack coverage that FUTCORE-P13 must audit before any StudySpec binding.",
    "The locked label pack covers only 5m, so non-5m primary horizons are deferred until audited label references exist.",
    "Bad available_ts ordering, final-session aggregate usage, or same-bar joins would invalidate the draft.",
    "Non-zero cost and thin-session overlays may expose cost fragility in later diagnostics."
  ],
  "promotion_criteria": [
    "The critic can identify a separate volatility-expansion momentum gate and volatility-compression reversion gate in every active decision cell.",
    "Later diagnostics record per-regime sample and coverage caveats by instrument, session, and primary horizon.",
    "Non-zero cost sensitivities for base, stress_1, stress_2, and double_cost are bound before any evidence review uses the draft.",
    "StudySpec binding either proves the needed feature and label references exist or records a gap for FUTCORE-P13 or FUTCORE-P15.",
    "Duplicate exposure to generic volatility filters is explicitly assessed before this draft can continue to the StudySpec pack."
  ],
  "created_by": "Hypothesis Scout:rq.p09.regime_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
