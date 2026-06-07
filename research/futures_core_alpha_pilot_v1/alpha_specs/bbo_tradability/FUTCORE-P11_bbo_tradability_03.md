# FUTCORE-P11 BBO Tradability AlphaSpec 03

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the BBO tradability / top-book confirmation
family.

```json
{
  "alpha_spec_id": "aspec_857ea832d75aa4fc23b376d6",
  "hypothesis_id": "hyp_70727d83baa99c852e1d552b",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "family_budget": "FUTCORE-P11 owns the 0.10 BBO family budget with minimum 3, target 4, maximum 4 drafts; this file is one of four target drafts.",
    "overlay_role": "This draft treats top-book depth and imbalance as a risk-control or confirmation filter for later StudySpecs; it is not a standalone executable edge and contains no trade-readiness conclusion.",
    "input_pack_refs": {
      "dataset_version": "Accepted DatasetVersion dsv_databento_ohlcv_05404069799decb0 anchors the ES/NQ/RTY universe without reading or copying values.",
      "session_features": "Locked session FeatureVersions fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f and fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978 are referenced for RTH and session-minute context.",
      "label_reference": "LabelSpec lspec_cd6523694c850c9943b2067e is the locked 5m label; 10m, 15m, and 30m labels remain later audited bindings.",
      "bbo_binding_gap": "Top-book depth, bid_size, ask_size, and imbalance require a valid BBO-capable pack or a later approved FeatureRequest before diagnostics can consume them."
    },
    "bbo_requirements": {
      "valid_bbo": "Bid and ask sides must both be present, ordered, non-stale, same-instrument, and available before the decision timestamp.",
      "depth": "Top-book depth is bid_size plus ask_size from the same BBO row and is used only as a filter or risk-control diagnostic.",
      "imbalance": "Top-book imbalance must be computed from same-row bid_size and ask_size and must expose low-depth or missing-side limitations.",
      "quote_quality": "Missing BBO, bad quote, wide spread, low depth, stale quote, crossed quote, and quarantined quote states are exclusions or diagnostic cells."
    },
    "horizon_policy": {
      "primary_horizons": "5m, 10m, 15m, and 30m are the primary pilot horizons, with only the 5m LabelSpec locked at this stage.",
      "fragile_horizons": "1m and 3m diagnostics are fragile because displayed depth can change rapidly and cannot support continuation by themselves.",
      "extended_horizons": "60m, 120m, 240m, and session_close are outside the primary readout and require later extended diagnostic caveats.",
      "maintenance_break": "No modeled holding period can cross the maintenance or trade-date break."
    },
    "session_scope": {
      "primary_sessions": "RTH and RTH_with_ETH_context are primary only when top-book depth coverage is adequate and point-in-time.",
      "diagnostic_sessions": "full_session, ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH are diagnostic-only with stricter low-depth, spread, and cost treatment.",
      "excluded_sessions": "Any session cell with missing BBO side, stale quote carry, ambiguous exchange_trade_date, or insufficient top-book depth metadata is excluded."
    },
    "duplicate_rejected_idea_awareness": "This draft overlaps liquidity/PA and volume/activity overlays because depth is a liquidity proxy; P12 must ensure it does not duplicate spread-zscore, microprice, or broad liquidity filters, and later Librarian work must compare rejected low-liquidity ideas.",
    "value_free_boundary": "No BBO values, depth values, imbalance values, labels, diagnostics, cost estimates, or conclusions are stored in this draft."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.bbo.BBOFeatureName.BID_SIZE",
    "src.alpha_system.features.families.bbo.BBOFeatureName.ASK_SIZE",
    "src.alpha_system.features.families.bbo.BBOFeatureName.TOP_BOOK_DEPTH",
    "src.alpha_system.features.families.bbo.BBOFeatureName.TOP_BOOK_IMBALANCE",
    "src.alpha_system.features.families.bbo.BBOFeatureName.LOW_DEPTH_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.WIDE_SPREAD_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.MISSING_BBO_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.BAD_QUOTE_FLAG",
    "feature_version:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "feature_version:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude BBO rows with missing bid side, missing ask side, non-positive displayed size where size is required, stale quotes, crossed quotes, quarantined quotes, or unavailable available_ts.",
    "Exclude any top-book depth or imbalance value derived by forward-filling missing sides, mixing quote timestamps, or using a later quote than the decision timestamp.",
    "Exclude low-depth cells from any later favorable review unless the later StudySpec explicitly marks them as risk-control exclusions rather than signal evidence.",
    "Exclude thin-session cells that do not expose separate spread, depth, missingness, and non-zero cost overlays.",
    "Exclude 1m and 3m diagnostics from any continuation criterion because top-book depth can be execution-fragile at those horizons.",
    "Exclude variants that collapse into a generic volume/activity or liquidity filter without the explicit BBO top-book depth and imbalance contract."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "Decision timestamp is after a completed signal bar and after available_ts for same-row bid_size, ask_size, top_book_depth, top_book_imbalance, quality flags, and session context.",
    "available_ts_usage": {
      "depth_inputs": "Bid_size, ask_size, and top_book_depth inherit the BBO row available_ts and cannot be forward-filled from stale rows.",
      "imbalance_inputs": "Top_book_imbalance must be computed from same-row displayed sizes whose available_ts is not later than the decision timestamp.",
      "quality_inputs": "Low-depth, missing-BBO, bad-quote, and wide-spread flags must be available before a row is admitted or excluded."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e is available only after its forward window and cannot influence any top-book filter.",
    "bar_and_quote_semantics": "The overlay may be applied only to a completed-bar decision using point-in-time BBO state; same-bar outcome and future quote information are forbidden.",
    "session_boundaries": "exchange_trade_date, session segments, and maintenance-break boundaries must be preserved in every later session x horizon diagnostic split.",
    "cross_instrument_alignment": "No cross-instrument depth aggregation is part of this draft; instrument-level depth and imbalance are evaluated independently."
  },
  "cost_assumptions": {
    "cost_model_version": "CostModelVersion cmv_futcore_pilot_three_layer_session_stress_v1 is required for all later diagnostics.",
    "profiles": {
      "zero_cost": "Diagnostic-only contrast with promotion_basis_allowed=false and no use as a continuation criterion.",
      "base": "Central non-zero profile required for later cost sensitivity.",
      "stress_1": "Non-zero stress profile not less conservative than base.",
      "stress_2": "Non-zero stress profile not less conservative than stress_1.",
      "double_cost": "Upper non-zero stress profile relative to base before session overlays."
    },
    "layers": {
      "hard_transaction_cost": "Layer 1 hard costs use reviewed offline descriptors only.",
      "spread_crossing": "Layer 2 spread crossing uses valid BBO and separately reports missing or invalid quotes.",
      "slippage_capacity_proxy": "Layer 3 slippage and capacity proxy may use depth buckets only as conservative sensitivities, not capacity proof."
    },
    "thin_session_overlays": "ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH require stricter spread, slippage, low-depth, and capacity proxy treatment on non-zero profiles.",
    "depth_proxy_boundary": "Displayed top-book depth is a fragile proxy for risk control and must not be described as available fill capacity."
  },
  "expected_failure_modes": [
    "Displayed top-book depth may be sparse, unstable, or regime-dependent across instruments and session views.",
    "Top-book imbalance may duplicate microprice pressure or generic liquidity filters unless its role is limited to risk control.",
    "Missing or stale BBO rows may create sample-selection artifacts if exclusions are not reported by instrument and session.",
    "Thin-session observations may be dominated by low-depth flags and stricter non-zero cost overlays.",
    "Current locked labels cover only the 5m horizon, so longer primary horizons require later audited LabelSpec work.",
    "Any implementation using future quotes, forward-filled depth, final-session aggregates, or same-bar label information would fail no-lookahead review."
  ],
  "promotion_criteria": [
    "FUTCORE-P12 can verify that top-book depth and imbalance are risk-control or confirmation overlays rather than standalone alpha evidence.",
    "Later StudySpec binding must preserve same-row BBO size semantics, missing-side exclusions, and low-depth diagnostic cells.",
    "Later diagnostics must report admitted and excluded counts by instrument, session view, horizon, and depth or quote-quality state.",
    "Non-zero profiles base, stress_1, stress_2, and double_cost are present with thin-session overlays and BBO limitations visible.",
    "Missing BBO feature bindings or non-5m labels are treated as audit gaps for FUTCORE-P13 or FUTCORE-P15.",
    "Duplicate-exposure review distinguishes this draft from volume/activity, liquidity/PA, spread-zscore, and microprice pressure variants."
  ],
  "created_by": "Hypothesis Scout:rq.p11.bbo_tradability_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
