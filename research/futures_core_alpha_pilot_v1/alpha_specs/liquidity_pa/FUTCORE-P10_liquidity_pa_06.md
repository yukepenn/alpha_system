# FUTCORE-P10 Liquidity PA AlphaSpec 06

Status: draft evidence only. This file contains exactly one canonical governance `AlphaSpec` payload for the liquidity sweep / failed-breakout / objective PA family.

```json
{
  "alpha_spec_id": "aspec_39ffc190cfbfa6ba0b1a2a25",
  "hypothesis_id": "hyp_1978a01ab95fd2c53d564929",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "campaign_scope_ref": "Campaign scope is ALPHA_FUTURES_CORE_ALPHA_PILOT_V1; target universe is restricted to ES, NQ, and RTY.",
    "draft_protocol_ref": "AlphaSpec drafting follows research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md from FUTCORE-P05.",
    "queue_task_ref": "rq.p10.liquidity_pa_drafting owned by Hypothesis Scout; this draft is not approved, implemented, diagnosed, or promoted in FUTCORE-P10.",
    "family_budget": "Liquidity sweep / failed breakout / objective PA uses the 0.15 family-budget slice with minimum 4, target 6, maximum 6 drafts; this file is one of six target drafts.",
    "input_pack_binding": {
      "dataset_version": "Accepted DatasetVersion dsv_databento_ohlcv_05404069799decb0 for ES/NQ/RTY OHLCV one-minute bars, referenced by id only.",
      "feature_versions": [
        "Locked FeatureVersion fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f supplies base_ohlcv_rth_flag by reference only.",
        "Locked FeatureVersion fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978 supplies base_ohlcv_session_minute by reference only."
      ],
      "label_reference": "Locked LabelSpec lspec_cd6523694c850c9943b2067e and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395; longer primary horizons require later binding review.",
      "value_boundary": "No raw provider files, feature values, label values, Parquet, SQLite, diagnostics, costs, returns, or market rows are read or recorded by this draft."
    },
    "focus": "Failed-breakout reversal with explicit inside-close and reversal-magnitude thresholds.",
    "objective_rule_catalog": {
      "reference_levels": "prior_range_high_N20 and prior_range_low_N20 are the max high and min low over the 20 completed one-minute bars ending before the candidate trigger bar; compression_range_high_N8 and compression_range_low_N8 are fixed after an 8-bar completed compression window; every level available_ts is the maximum available_ts of its contributing completed bars and must be earlier than the trigger decision timestamp.",
      "liquidity_sweep": "A high-side sweep occurs when completed_bar_high >= prior_range_high_N20 + one instrument minimum tick; a low-side sweep occurs when completed_bar_low <= prior_range_low_N20 - one instrument minimum tick; the swept level must be available before the sweep bar is evaluated.",
      "close_back_inside": "After a high-side sweep, close-back-inside requires completed_bar_close <= prior_range_high_N20 and >= prior_range_low_N20 by the sweep bar close or the next completed bar; after a low-side sweep, close-back-inside requires completed_bar_close >= prior_range_low_N20 and <= prior_range_high_N20 by the same deadline.",
      "wick_rejection": "For a high-side rejection, upper_wick = high - max(open, close) must be at least 0.60 of completed_bar_range and body_abs = abs(close - open) must be at most 0.35 of completed_bar_range; low-side rejection mirrors this with lower_wick = min(open, close) - low. completed_bar_range must be greater than zero.",
      "displacement": "Directional displacement requires abs(close_t - close_t_minus_1) >= 1.50 times median_true_range over the previous 20 completed bars and close_t directionally beyond the selected trigger reference; the median window excludes the displacement bar.",
      "compression": "Compression requires an 8-completed-bar range width no greater than 0.65 times the median of prior non-overlapping 8-bar range widths from the previous 60 completed bars, with no missing OHLCV bars in either window.",
      "breakout": "A compression breakout requires completed_bar_close >= compression_range_high_N8 + one tick for an upside breakout or completed_bar_close <= compression_range_low_N8 - one tick for a downside breakout after the compression boundary is fixed and available.",
      "failed_breakout": "A failed breakout requires the breakout condition followed within two completed bars by a close back inside the fixed compression range and an opposite-direction close-to-close move of at least 1.00 times the previous-20-bar median_true_range.",
      "missing_ambiguous_level_exclusion": "Exclude rows with fewer than the required completed bars, high <= low boundaries, missing/late available_ts, crossed session boundaries inside the reference window unless explicitly allowed by the session view, or two simultaneously eligible reference windows with different fixed boundaries for the same decision timestamp."
    },
    "draft_trigger_logic": "Upside failed breakout requires an eligible breakout close above the fixed boundary, then within two completed bars close <= boundary_high and close >= boundary_low plus close_t_minus_1 - close_t >= 1.00 * prior20_median_true_range; downside failed breakout mirrors the rule with close back above boundary_low and opposite upward movement.",
    "horizon_policy": {
      "primary_horizons": "Primary review horizons are 5m, 10m, 15m, and 30m; the locked 5m LabelSpec is present and longer primary horizons require later audited label binding before diagnostics.",
      "fragile_horizons": "1m and 3m are execution-fragile diagnostics only, require stricter spread/liquidity/cost checks, and cannot be a favorable continuation basis.",
      "extended_intraday": "60m, 120m, 240m, and session_close are extended diagnostics only with overlap, sample-size, stability, and no-cross-maintenance-break caveats.",
      "maintenance_break": "No modeled holding period may cross the exchange daily maintenance or trade-date break."
    },
    "session_scope": {
      "in_scope": [
        "RTH and RTH_only are primary decision views for completed-bar liquidity/PA triggers.",
        "RTH_with_ETH_context is in scope only when ETH context is completed or explicitly running and has available_ts before the RTH decision."
      ],
      "diagnostic_only": [
        "full_session is a matrix coverage view only and cannot hide active segment boundaries.",
        "ETH_only, ETH_evening, and ETH_overnight are diagnostic-only thin-session views with stricter spread, slippage, capacity, and missingness caveats.",
        "pre_RTH and post_RTH are diagnostic-only transition views with thin-session overlays and stricter missingness treatment."
      ],
      "excluded": [
        "Any view with missing exchange_trade_date, missing session_segment, ambiguous segment boundary, or a modeled holding interval that crosses the exchange maintenance or trade-date break is excluded.",
        "Any trigger requiring final current-session high, low, range, VWAP, or volume before the session is complete is excluded."
      ]
    },
    "diagnostic_declarations": {
      "objective_trigger_counts": "Later diagnostics must count eligible triggers, missing-level exclusions, ambiguous-level exclusions, side, instrument, session view, and horizon without committing per-row values.",
      "level_availability": "Later StudySpec binding must emit each reference level id, level type, contributing window, and level available_ts so the no-lookahead auditor can check timing.",
      "family_rule_coverage": "The later P19 liquidity/PA diagnostics must preserve sweep, close-back-inside, wick rejection, displacement, compression, breakout, and failed-breakout flags even when a flag is diagnostic rather than the primary trigger.",
      "volume_overlay_boundary": "Volume_zscore may be used only as an overlay/split on the objective PA primitive and must not become a standalone activity family."
    },
    "duplicate_rejected_idea_awareness": "P12 must compare this draft against other P10 drafts, P08 VWAP/session range-context drafts, P09 compression/regime drafts, P07 cross-market confirmation drafts, P11 BBO confirmation overlays, and any later RejectedIdeaLedger entry before any StudySpec binding.",
    "critique_independence": "Draft is authored only by Hypothesis Scout; AlphaSpec Critic, reviewer, diagnostics runner, Statistical Reviewer, Librarian, promoter roles, and human capital judgment are not drafter roles."
  },
  "factor_inputs": [
    "dataset_version:dsv_databento_ohlcv_05404069799decb0:ohlcv_1m_bars_ES_NQ_RTY with open/high/low/close/volume and bar available_ts consumed by reference only.",
    "locked_feature_pack:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag available before each decision timestamp.",
    "locked_feature_pack:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute available before each decision timestamp.",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ROLLING_RANGE for causal completed-window range context.",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.ATR for completed-bar true-range context where later StudySpec binding supports it.",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.RETURNS for completed close-to-close movement only.",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.RANGE_POSITION for completed-bar position within a causal range.",
    "src.alpha_system.features.families.ohlcv.OHLCVFeatureName.VOLUME_ZSCORE as optional overlay only; it is not a standalone trigger or quota family."
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any decision where required OHLCV, session metadata, reference level, rolling metric, or label reference lacks valid available_ts or label_available_ts ordering.",
    "Exclude any construction that uses final-session high, low, range, VWAP, volume, or other final aggregate before the relevant session is complete.",
    "Exclude same-bar outcome use, future labels as features, centered windows, forward-filled missing bars, backfilled levels, or arbitrary wall-clock joins that ignore availability metadata.",
    "Exclude any modeled holding interval that crosses the exchange daily maintenance or trade-date break.",
    "Exclude thin-session variants with missing or unusable BBO/cost proxy metadata unless the later StudySpec marks the view diagnostic-only.",
    "Exclude duplicate variants that only rename another liquidity/PA, VWAP/session, regime, cross-market, or BBO confirmation exposure without a distinct objective trigger.",
    "Exclude failures whose inside-close uses an updated boundary after the breakout; the failure must use the same fixed boundary that defined the breakout."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "Decision is after a breakout beyond a fixed prior or compression boundary fails within two completed bars by closing back inside and producing an opposite-direction move of at least 1.00 times prior20 median true range.",
    "available_ts_usage": {
      "ohlcv_1m_bars": "Each open, high, low, close, and volume value is eligible only after its completed bar available_ts; no during-bar or same-bar outcome input is allowed.",
      "prior_range_levels": "prior_range_high_N20 and prior_range_low_N20 inherit the latest available_ts across their 20 completed contributing bars and must be fixed before the trigger bar is evaluated.",
      "compression_levels": "compression_range_high_N8 and compression_range_low_N8 inherit the latest available_ts across the 8 completed compression bars and must be fixed before a breakout or failure trigger is evaluated.",
      "rolling_metrics": "rolling range, ATR, returns, range position, and optional volume_zscore use only completed bars with available_ts not later than the decision timestamp.",
      "session_context": "RTH flag and session minute references are point-in-time metadata with available_ts at or before the decision timestamp."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395 are forward-label references only; label_available_ts is after the outcome window and the label cannot be used as a feature.",
    "bar_semantics": "Signals are formed after completed one-minute bars unless a later StudySpec records a stricter open-bar convention that still excludes same-bar outcomes.",
    "exchange_trade_date": "exchange_trade_date and session_segment define ETH, pre_RTH, RTH, post_RTH, and the maintenance-break boundary.",
    "final_aggregate_rejection": "Final current-session high, low, range, VWAP, volume, or close is unavailable intraday before that session is complete.",
    "missing_or_ambiguous_levels": "Rows are excluded when reference levels are missing, stale, late, degenerate, or ambiguous under the deterministic window rules."
  },
  "cost_assumptions": {
    "cost_model_version": "cmv_futcore_pilot_three_layer_session_stress_v1",
    "required_profile_name_set": "The exact profile set is zero_cost, base, stress_1, stress_2, and double_cost; no other profile name is in scope for this draft.",
    "profiles": {
      "zero_cost": "Diagnostic contrast only with promotion_basis_allowed=false; it cannot support retaining or advancing a draft that fails required non-zero profiles.",
      "base": "Central non-zero hard-cost, spread-crossing, slippage-proxy, and capacity-proxy sensitivity.",
      "stress_1": "Required non-zero stress profile not less conservative than base for every cost layer and capacity proxy.",
      "stress_2": "Required non-zero stress profile not less conservative than stress_1 for the same inputs and session view.",
      "double_cost": "Required upper non-zero cost sensitivity relative to base before applicable thin-session overlays."
    },
    "layers": {
      "layer_1_hard_transaction_cost": "Bound later from reviewed offline descriptors under the P04 contract.",
      "layer_2_spread_crossing": "Uses valid point-in-time BBO where later bound; missing, stale, crossed, or invalid BBO is flagged and never fabricated.",
      "layer_3_slippage_capacity_proxy": "Proxy sensitivity only; not realized slippage, fill-capacity proof, or execution-readiness evidence."
    },
    "thin_session_overlays": {
      "ETH_only": "Apply ETH thin-session overlay after each non-zero profile and do not relax spread, slippage, or capacity conservatism.",
      "ETH_evening": "Apply evening ETH overlay at least as conservative as ETH_only.",
      "ETH_overnight": "Apply overnight ETH overlay at least as conservative as ETH_only.",
      "pre_RTH": "Apply pre-RTH transition overlay with stricter spread, slippage, and capacity proxy than comparable RTH buckets.",
      "post_RTH": "Apply post-RTH transition overlay with stricter spread, slippage, and capacity proxy than comparable RTH buckets."
    },
    "maintenance_break": "No costed holding interval may cross the exchange daily maintenance or trade-date break."
  },
  "expected_failure_modes": [
    "No-lookahead audit may find a reference level, compression boundary, rolling metric, or session context was not available at the declared decision timestamp.",
    "Level missingness, degenerate high-low ranges, duplicate timestamps, stale bars, or ambiguous overlapping windows may remove many candidate rows under the exclusion rules.",
    "The locked label pack currently binds the 5m LabelSpec only; 10m, 15m, and 30m diagnostics require later audited label binding before use.",
    "1m and 3m diagnostic views may be too sensitive to spread, liquidity, timestamp alignment, and thin-session treatment for later review continuation.",
    "ETH, pre_RTH, and post_RTH views may be cost-fragile under required non-zero profiles and thin-session overlays.",
    "Session, volatility, and regime splits may show instability around RTH open, RTH close, ETH transition, or compressed-range release periods.",
    "Window length, tick-buffer, ratio, and failure-deadline choices may overfit unless P14 and P24 enforce finite variant budgets.",
    "The draft may duplicate exposure, label, session, horizon, or trigger logic from another P10 draft, the VWAP/session family, the regime compression draft, or a later known rejected idea.",
    "Failed breakout reversal may duplicate close-back-inside sweep or wick rejection drafts if the fixed-boundary breakout event is not separated in later diagnostics."
  ],
  "promotion_criteria": [
    "Independent P12 critique can verify exact top-level AlphaSpec fields, Hypothesis Scout drafter role, objective rule thresholds, duplicate-exposure notes, and no-lookahead declarations.",
    "Later StudySpec binding preserves decision timestamp, reference-level available_ts, feature available_ts, label_available_ts, session boundaries, and maintenance-break flatness.",
    "Later diagnostics report 5m, 10m, 15m, and 30m horizon coverage or document unavailable label bindings through P13/P15 instead of assuming them.",
    "Required non-zero cost profiles base, stress_1, stress_2, and double_cost are reported with thin-session overlays visible before any later continuation decision.",
    "Later diagnostics expose trigger counts, missing-level exclusions, session splits, horizon splits, and duplicate-exposure groups without committing value rows.",
    "No criterion here grants approval, implementation permission, paper/live readiness, broker use, deployment, production readiness, or capital allocation.",
    "Later diagnostics must report breakout side, failure deadline, reversal magnitude, fixed-boundary reuse, and cases that return inside without the reversal-magnitude threshold."
  ],
  "created_by": "Hypothesis Scout:rq.p10.liquidity_pa_drafting:failed_breakout_reversal",
  "created_at": "2026-06-07T06:38:10Z"
}
```
