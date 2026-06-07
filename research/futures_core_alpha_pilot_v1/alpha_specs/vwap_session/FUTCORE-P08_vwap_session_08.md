{
  "alpha_spec_id": "aspec_5abca2fa010fc9e7174e0d7d",
  "hypothesis_id": "hyp_86b4431a474dc10e489d6d03",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "family_budget": "VWAP and session-auction family budget is twenty percent with exactly eight target drafts and no reallocation to other families.",
    "formulation": "Evaluate diagnostic-only pre-RTH and post-RTH session-transition events where price is extended from running_vwap_so_far, with RTH decisions evaluated separately.",
    "input_pack_refs": {
      "dataset_version": "Accepted ES/NQ/RTY OHLCV one-minute DatasetVersion dsv_databento_ohlcv_05404069799decb0 from FUTCORE-P03 input pack lock.",
      "feature_rth_flag": "Locked session-context FeatureVersion fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f for base_ohlcv_rth_flag, consumed by reference only.",
      "feature_session_minute": "Locked session-context FeatureVersion fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978 for base_ohlcv_session_minute, consumed by reference only.",
      "label_reference": "Locked forward-return LabelSpec lspec_cd6523694c850c9943b2067e and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395; longer horizons require later binding review.",
      "value_boundary": "Draft records ids, assumptions, and diagnostic declarations only; no market rows, feature values, label values, or diagnostics are recorded."
    },
    "horizon_policy": {
      "primary_5m_10m_15m_30m": "Primary review band is five, ten, fifteen, and thirty minutes; the locked five-minute label is present and other horizons need later label binding before use.",
      "fragile_1m_3m": "One-minute and three-minute views are diagnostic-only, require stricter spread, liquidity, and cost review, and cannot satisfy continuation criteria.",
      "extended_intraday": "Sixty, one-hundred-twenty, two-hundred-forty minute and session-close views are extended diagnostics only with overlap, sample, and stability caveats.",
      "maintenance_break": "No modeled holding interval may cross the exchange daily maintenance or trade-date break; flat-before-break is a hard downstream requirement."
    },
    "session_scope": {
      "full_session": "Context view only for session-matrix diagnostics; decisions must still obey the active segment and maintenance-break boundary.",
      "RTH_only": "Primary decision view when the trigger is evaluated during regular trading hours after a completed bar.",
      "ETH_only": "Diagnostic-only comparator for transition behavior under stricter ETH overlays.",
      "ETH_evening": "Diagnostic-only thin-session subview for later matrix coverage; no decision can cross the maintenance boundary.",
      "ETH_overnight": "Diagnostic-only or completed-context view depending on the draft; completed overnight context is allowed only after the ETH window ends.",
      "pre_RTH": "Primary diagnostic transition view with thin-session overlays and no claim beyond later research review.",
      "RTH": "Primary segment for regular-hours triggers and labels where the decision is made after a completed bar.",
      "post_RTH": "Primary diagnostic transition view with thin-session overlays and no carry across the trade-date break.",
      "RTH_with_ETH_context": "In-scope when only completed ETH context or point-in-time running ETH context is used under available_ts.",
      "excluded_views": "No additional session views are introduced; any trigger requiring final current-session aggregates before close is excluded."
    },
    "diagnostic_declarations": {
      "running_vs_final_vwap": "Use running_vwap_so_far under available_ts for intraday decisions; final-session VWAP is diagnostic only after completion.",
      "opening_range_availability": "Opening-range high and low are available only after the configured opening window has completed.",
      "overnight_high_low_availability": "Overnight high and low are completed ETH context only after the overnight window ends, otherwise running context must be named as such.",
      "gap_construction_timing": "Gap references use prior completed session close and current session open reference known by the declared post-bar decision timestamp.",
      "session_transition_handling": "RTH, ETH, pre-RTH, and post-RTH transitions must be split in the later session x horizon matrix.",
      "final_aggregate_lookahead_rejection": "Final-session VWAP, high, low, range, and volume are forbidden as intraday inputs before session completion."
    },
    "duplicate_rejected_idea_awareness": "This draft intentionally overlaps with distance-to-VWAP buckets but isolates pre-RTH and post-RTH transition windows for later session-matrix audit.",
    "critique_independence": "Draft is authored only by Hypothesis Scout; AlphaSpec Critic, reviewer, diagnostics runner, and promoter roles are not named as drafters."
  },
  "factor_inputs": [
    "Locked FeatureVersion fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f base_ohlcv_rth_flag for separating RTH from transition windows by available_ts.",
    "Locked FeatureVersion fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978 base_ohlcv_session_minute for transition-window timing controls by available_ts.",
    "Existing SessionFeatureName.ETH_SEGMENT_FLAG or accepted session_segment metadata as point-in-time transition context if later binding permits.",
    "Existing OHLCVFeatureName.VWAP configured as running_vwap_so_far within each active session segment.",
    "Existing OHLCVFeatureName.DISTANCE_TO_VWAP for diagnostic transition distance buckets under available_ts."
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any row where required OHLCV or session-context inputs are missing, duplicated, non-monotonic, or not available by the decision timestamp.",
    "Exclude any trigger that uses final_session_vwap, final_session_high, final_session_low, final_session_range, or final_session_volume before that session is complete.",
    "Exclude any same-bar construction where the feature, decision, or label outcome would share unavailable future information.",
    "Exclude any modeled holding interval that crosses the exchange daily maintenance or trade-date break.",
    "Exclude thin-session variants with missing BBO or unusable cost proxy metadata unless the later StudySpec marks them diagnostic-only.",
    "Exclude duplicate variants that merely relabel another FUTCORE-P08 draft without a distinct trigger, session, horizon, or diagnostic purpose.",
    "Exclude transition signals that carry across the exchange daily maintenance or trade-date break.",
    "Exclude any pre-RTH or post-RTH continuation criterion based on zero_cost or without thin-session non-zero overlays."
  ],
  "timestamp_assumptions": {
    "decision_timing": "Decision is after a completed pre-RTH or post-RTH bar for diagnostic transition views, and after a completed RTH bar for any RTH comparator.",
    "available_ts_features": "Every factor input, including running_vwap_so_far, opening range, overnight context, gap reference, and session metadata, must be available before the decision timestamp.",
    "label_available_ts": "Label reference lspec_cd6523694c850c9943b2067e is a forward five-minute label and may be consumed only as a label with label_available_ts, never as a feature input.",
    "bar_semantics": "Signals are formed after completed bars unless the later StudySpec explicitly records a stricter open-bar convention without same-bar outcome use.",
    "exchange_trade_date": "exchange_trade_date and session_segment boundaries define RTH, ETH, pre_RTH, post_RTH, and the maintenance-break flatness constraint.",
    "running_vs_final_vwap": "running_vwap_so_far is point-in-time under available_ts; final-session VWAP is available only after the relevant session closes.",
    "final_aggregate_rejection": "final_session_high, final_session_low, final_session_vwap, final_session_range, and final_session_volume are rejected before session completion.",
    "session_transition_handling": "pre_RTH, post_RTH, ETH_only, and RTH comparators must be reported separately in the later session x horizon matrix.",
    "running_vwap_context": "Transition VWAP inputs are running_vwap_so_far within the active segment; final ETH or final RTH aggregates are unavailable until completion."
  },
  "cost_assumptions": {
    "cost_model_version": "CostModelVersion cmv_futcore_pilot_three_layer_session_stress_v1 is the only cost contract referenced by this draft.",
    "layers": {
      "hard_transaction_cost": "Layer one hard transaction cost must be applied by later diagnostics under the selected profile.",
      "spread_crossing": "Layer two spread crossing uses valid point-in-time BBO where available and flags missing or unusable BBO explicitly.",
      "slippage_capacity_proxy": "Layer three slippage and capacity proxy is diagnostic sensitivity only and does not prove fill capacity."
    },
    "profiles": {
      "zero_cost": "Diagnostic contrast only; promotion_basis_allowed is false and this profile cannot satisfy any continuation criterion.",
      "base": "Central non-zero profile required for later cost sensitivity reporting under the P04 cost contract.",
      "stress_1": "First stress profile required and not less conservative than the central non-zero profile.",
      "stress_2": "Second stress profile required and not less conservative than the first stress profile.",
      "double_cost": "Upper non-zero cost bound required for later sensitivity reporting before any review continuation."
    },
    "thin_session_overlays": {
      "ETH_only": "Apply ETH thin-session overlay after every non-zero profile, never reducing spread, slippage, or capacity conservatism.",
      "ETH_evening": "Apply evening ETH overlay at least as conservative as the ETH-only overlay for non-zero profiles.",
      "ETH_overnight": "Apply overnight ETH overlay at least as conservative as the ETH-only overlay for non-zero profiles.",
      "pre_RTH": "Apply pre-RTH transition overlay with stricter spread, slippage, and capacity proxy than comparable RTH buckets.",
      "post_RTH": "Apply post-RTH transition overlay with stricter spread, slippage, and capacity proxy than comparable RTH buckets."
    },
    "zero_cost_boundary": "Any later result that is only interesting under zero_cost must be marked cost-fragile or rejected by later review policy."
  },
  "expected_failure_modes": [
    "No-lookahead audit may find that an opening range, overnight range, gap, or VWAP input was not available at the declared decision timestamp.",
    "The locked label pack currently binds only the five-minute LabelSpec, so longer primary horizons may require later LabelSpec work before diagnostics.",
    "One-minute or three-minute diagnostic variants may be too sensitive to spread, liquidity, and timestamp alignment for review continuation.",
    "Thin-session overlays may dominate ETH, pre-RTH, or post-RTH variants under non-zero cost profiles.",
    "Session transition effects may be unstable across RTH, ETH overnight, pre-RTH, and post-RTH matrix splits.",
    "Variant selection may overfit opening-window, threshold, or horizon choices unless P14 and P24 enforce a finite VariantBudget.",
    "Thin-session spread and slippage overlays may make pre-RTH or post-RTH transition diagnostics insufficient for any later continuation.",
    "Transition distance buckets may duplicate generic distance-to-VWAP exposure unless session segmentation is the main reviewed dimension."
  ],
  "promotion_criteria": [
    "FUTCORE-P12 may pass the draft to later binding only if all required fields, role separation, duplicate-exposure notes, and no-lookahead declarations are complete.",
    "Later diagnostics must report the primary five, ten, fifteen, and thirty minute horizon matrix or document why a locked label binding is unavailable.",
    "Continuation cannot be based on zero_cost; base, stress_1, stress_2, and double_cost must be reported and reviewed as non-zero sensitivity conditions.",
    "Later StudySpec binding must preserve the declared decision timestamp, available_ts inputs, label_available_ts labels, and maintenance-break flatness.",
    "Any continuation decision must remain value-free research review only and cannot imply paper, live, broker, deployment, production, or capital-allocation readiness.",
    "Later diagnostics must treat pre-RTH and post-RTH as diagnostic-only transition views unless an independent review explicitly binds them with thin-session caveats."
  ],
  "created_by": "Hypothesis Scout:rq.p08.vwap_session_drafting",
  "created_at": "2026-06-07T04:30:00Z"
}
