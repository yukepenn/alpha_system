# FUTCORE-P09 Regime AlphaSpec 01

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the regime-gated momentum/reversion family.

```json
{
  "alpha_spec_id": "aspec_eb962fc197eaf3955c5e4711",
  "hypothesis_id": "hyp_2ec78fe9f0947242f88c0413",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "input_pack_binding": "Bind by reference to DatasetVersion dsv_databento_ohlcv_05404069799decb0, FeatureVersions fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f and fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978, and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395; no value files are read by this draft.",
    "regime_activation_logic": {
      "regime_inputs": "Use point-in-time base_ohlcv trendiness, rolling_volatility, rolling_range, and completed-bar return direction computed only from bars whose available_ts is not later than the decision timestamp.",
      "momentum_gate": "Momentum is active only when completed-bar trendiness is in a high-efficiency regime, realized volatility is not in the highest stress band, and rolling_range is not in a compression regime.",
      "reversion_gate": "Reversion is active when completed-bar trendiness is low or range compression is present after a failed directional extension; no global momentum-or-reversion choice is allowed outside those gates.",
      "gate_priority": "If both gates are ambiguous during a transition, the StudySpec must mark the decision cell as inactive rather than forcing a directional arm."
    },
    "horizon_policy": {
      "primary_horizons": "Primary review starts with the locked 5m label and may request 10m, 15m, and 30m labels only through later audited LabelSpec work.",
      "fragile_horizons": "1m and 3m are sampling or execution-fragile diagnostics only and cannot carry later review continuation by themselves.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded from the main pilot readout unless later StudySpec binding adds explicit overlap and regime-sample caveats.",
      "maintenance_boundary": "No modeled holding period may cross the exchange daily maintenance or trade-date break."
    },
    "session_policy": {
      "primary_sessions": "RTH and RTH_with_ETH_context are the primary decision views because they can use completed ETH context without intraday final-session leakage.",
      "diagnostic_sessions": "full_session, ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH are diagnostic views with thin-session cost and coverage caveats.",
      "excluded_sessions": "Any session segment lacking session metadata available_ts, exchange_trade_date, or unambiguous segment boundaries is excluded for this draft."
    },
    "family_quota": "Regime momentum/reversion uses the FUTCORE-P09 family quota of minimum 4, target 6, maximum 6 drafts from the 0.15 family-budget slice.",
    "declared_diagnostics": "Later diagnostics must report activation counts by momentum gate, reversion gate, inactive transition state, session view, instrument, and horizon without committing per-row values.",
    "duplicate_exposure": "This draft intentionally overlaps broad trend and volatility filters; the critic must compare it against other regime drafts and any cross-market trend exposure before any later StudySpec binding."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.TRENDINESS",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_VOLATILITY",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_RANGE",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.RETURNS",
    "src.alpha_system.features.families.session.SessionFeatureName.RTH_SEGMENT_FLAG",
    "locked_feature_pack:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "locked_feature_pack:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any decision where required OHLCV, session metadata, regime metric, or label reference lacks valid available_ts or label_available_ts ordering.",
    "Exclude any decision that depends on final-session high, low, range, volume, or VWAP before the relevant session is complete.",
    "Exclude transition bars where the momentum and reversion gates both trigger or where the prior regime cannot be assigned from completed bars.",
    "Exclude regime cells with inadequate per-regime coverage, instrument coverage unresolved by FUTCORE-P13, or missing non-zero cost profile binding.",
    "Exclude duplicate-exposure variants that reduce to a broad trend filter or broad volatility filter without the explicit regime gate recorded here."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "The decision timestamp is after a completed one-minute bar and is no earlier than the maximum available_ts across all regime inputs.",
    "available_ts_usage": {
      "ohlcv_inputs": "Open, high, low, close, volume, and VWAP inputs are consumed only after their bar-level available_ts.",
      "regime_metrics": "Trendiness, rolling volatility, rolling range, and return direction are recomputed from completed bars and inherit the latest component available_ts.",
      "session_context": "RTH flags and session minute references are point-in-time session metadata and must be available before the decision timestamp."
    },
    "label_available_ts_usage": "The LabelSpec lspec_cd6523694c850c9943b2067e is used only as a future target with label_available_ts after the 5m outcome window and is never used as a feature.",
    "session_boundaries": "exchange_trade_date and session segment boundaries must be joined by timestamped metadata; completed ETH context may inform RTH_with_ETH_context only after the ETH window is complete.",
    "same_bar_policy": "Same-bar outcome information, centered windows, future windows, and arbitrary wall-clock joins that ignore available_ts are forbidden.",
    "cross_instrument_alignment": "Each instrument is evaluated independently; no cross-instrument lead-lag join is part of this regime draft."
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
    "layers": "Layer 1 hard transaction cost, Layer 2 valid point-in-time BBO spread crossing where available, and Layer 3 slippage and capacity proxy must be bound by later StudySpec configuration.",
    "thin_session_overlay": "ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH require stricter spread, slippage, and capacity proxy treatment on every non-zero profile.",
    "promotion_profile_boundary": "Later review criteria may reference base, stress_1, stress_2, and double_cost only; BBO and capacity outputs remain proxy sensitivities."
  },
  "expected_failure_modes": [
    "The high-trendiness gate can collapse into a generic trend filter if the critic cannot distinguish the explicit volatility and range gates.",
    "Low-trendiness reversion cells may have sparse or uneven coverage by instrument, session view, or primary horizon.",
    "Regime transitions can oscillate near thresholds and create unstable inactive-versus-active classifications.",
    "The locked pack currently exposes only the 5m label, so 10m, 15m, and 30m claims require later audited LabelSpec work before use.",
    "Missing or stale available_ts, bad session metadata, final-session aggregate leakage, or same-bar optimism would invalidate the draft.",
    "Non-zero cost profiles or thin-session overlays may make the idea cost-fragile in later diagnostics."
  ],
  "promotion_criteria": [
    "Independent critique can verify that every momentum or reversion decision is produced by the declared point-in-time regime gate.",
    "Later StudySpec binding records per-regime sample counts, inactive transition counts, session splits, horizon splits, and duplicate-exposure notes.",
    "Non-zero cost sensitivities for base, stress_1, stress_2, and double_cost are available for review with thin-session overlays visible.",
    "No final-session aggregate, label value, same-bar outcome, centered window, or future window is used as an input.",
    "Any missing 10m, 15m, or 30m label requirement is routed to FUTCORE-P13 or FUTCORE-P15 instead of being assumed available."
  ],
  "created_by": "Hypothesis Scout:rq.p09.regime_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
