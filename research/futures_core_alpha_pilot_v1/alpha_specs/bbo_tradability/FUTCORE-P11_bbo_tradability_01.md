# FUTCORE-P11 BBO Tradability AlphaSpec 01

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the BBO tradability / top-book confirmation
family.

```json
{
  "alpha_spec_id": "aspec_1284e49b083df11eeb0481ea",
  "hypothesis_id": "hyp_f598b58b133d59a56d557a08",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "family_budget": "BBO tradability / top-book confirmation uses the FUTCORE-P11 quota: minimum 3, target 4, maximum 4 drafts from the 0.10 family budget.",
    "overlay_role": "This draft is a spread-zscore and depth confirmation overlay for later StudySpec gating; it is not a standalone edge hypothesis and cannot be interpreted as a tradability, profitability, fill-capacity, or readiness result.",
    "input_pack_refs": {
      "dataset_version": "Accepted ES/NQ/RTY DatasetVersion dsv_databento_ohlcv_05404069799decb0 is the campaign input-pack anchor; this draft records references only and reads no data.",
      "feature_pack_refs": "Locked session FeatureVersions fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f and fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978 provide session context by reference.",
      "label_reference": "Locked forward-return LabelSpec lspec_cd6523694c850c9943b2067e and LabelVersion lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395 are the only locked label references.",
      "bbo_binding_gap": "BBO quote, spread, and depth inputs require later P13 data-contract audit and P15 FeatureRequest routing if the locked pack lacks a valid BBO-capable feature binding."
    },
    "bbo_requirements": {
      "valid_bbo": "Bid, ask, bid_size, ask_size, mid, spread, spread_ticks, quality_flags, and available_ts must be present, ordered, same-instrument, and point-in-time before the decision timestamp.",
      "spread_zscore": "Spread zscore must be causal, reset on the declared session where applicable, and computed only from valid prior or current available BBO rows.",
      "depth_filter": "Top-book depth and low-depth flags are confirmation or risk-control overlays; they must not create a standalone directional rule.",
      "quote_quality": "missing_bbo_flag, bad_quote_flag, wide_spread_flag, and low_depth_flag are diagnostic inputs and exclusion gates rather than favorable evidence."
    },
    "horizon_policy": {
      "primary_horizons": "Primary review horizons are 5m, 10m, 15m, and 30m; the locked 5m label is available by reference and longer horizons require later audited LabelSpec binding.",
      "fragile_horizons": "1m and 3m views are execution-fragile diagnostics only and cannot be a continuation basis.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded from this draft except as later extended diagnostics with overlap and stability caveats.",
      "maintenance_break": "No modeled holding interval may cross the exchange daily maintenance or trade-date break."
    },
    "session_scope": {
      "primary_sessions": "RTH and RTH_with_ETH_context are primary review views when BBO availability and session metadata are point-in-time.",
      "diagnostic_sessions": "full_session, ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH are diagnostic views with explicit thin-session cost, spread, depth, and missingness caveats.",
      "excluded_sessions": "Any session segment without exchange_trade_date, session boundary, BBO availability, or session metadata available_ts is excluded."
    },
    "duplicate_rejected_idea_awareness": "This draft overlaps cost-stress, VWAP/session, and liquidity/PA filters because spread and depth can become broad market-quality gates; P12 must check that it does not duplicate another spread or risk-control variant or a known RejectedIdeaLedger entry.",
    "value_free_boundary": "The draft contains assumptions, ids, and diagnostic declarations only; no market values, feature values, label values, cost outputs, diagnostics, or research result is recorded."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.bbo.BBOFeatureName.SPREAD",
    "src.alpha_system.features.families.bbo.BBOFeatureName.SPREAD_TICKS",
    "src.alpha_system.features.families.bbo.BBOFeatureName.SPREAD_ZSCORE",
    "src.alpha_system.features.families.bbo.BBOFeatureName.TOP_BOOK_DEPTH",
    "src.alpha_system.features.families.bbo.BBOFeatureName.WIDE_SPREAD_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.LOW_DEPTH_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.MISSING_BBO_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.BAD_QUOTE_FLAG",
    "feature_version:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "feature_version:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any observation where required BBO fields are missing, stale, crossed, locked without an approved policy, quarantined, non-positive where sizes must be positive, or not available by the decision timestamp.",
    "Exclude any row whose spread zscore, spread ticks, top-book depth, quote-quality flag, or session context lacks valid available_ts ordering.",
    "Exclude all 1m and 3m diagnostic views from favorable review criteria because they are execution-fragile and sensitive to spread and depth.",
    "Exclude any modeled holding period that crosses the exchange daily maintenance or trade-date break.",
    "Exclude variants that reduce to a generic cost filter, broad spread filter, or duplicate BBO quality gate without the explicit spread-zscore plus depth overlay described here.",
    "Exclude any downstream interpretation that treats the overlay as a standalone edge, fill-capacity result, paper/live readiness result, or capital-allocation input."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "The decision timestamp is after the completed signal bar and no earlier than the maximum available_ts across BBO, OHLCV, and session-context inputs.",
    "available_ts_usage": {
      "bbo_inputs": "Bid, ask, sizes, mid, spread, spread_ticks, quote-quality flags, spread_zscore, and top-book depth are consumed only at or after their own available_ts.",
      "session_context": "RTH flag and session minute references are point-in-time session metadata and must be available before the decision timestamp.",
      "causal_window": "Spread zscore uses a trailing causal window only; centered, future, or final-session windows are forbidden."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e is a future target consumed only through label_available_ts and never as a feature input.",
    "bar_and_quote_semantics": "BBO state used for a decision must be the latest valid point-in-time quote state available for the same instrument and session context; same-bar outcome values are not eligible inputs.",
    "session_boundaries": "exchange_trade_date and session_segment define RTH, ETH, pre_RTH, post_RTH, and maintenance-break boundaries; RTH_with_ETH_context may use only completed or point-in-time ETH context.",
    "cross_instrument_alignment": "Each instrument is evaluated independently in this BBO overlay; no cross-instrument BBO join or lead-lag timestamp computation is part of the draft."
  },
  "cost_assumptions": {
    "cost_model_version": "CostModelVersion cmv_futcore_pilot_three_layer_session_stress_v1 is the only cost contract referenced by this draft.",
    "profiles": {
      "zero_cost": "Diagnostic contrast only with promotion_basis_allowed=false; it cannot satisfy any later continuation criterion.",
      "base": "Central non-zero profile required for later review of hard cost, spread crossing, slippage proxy, and capacity proxy.",
      "stress_1": "First non-zero stress profile not less conservative than base.",
      "stress_2": "Second non-zero stress profile not less conservative than stress_1.",
      "double_cost": "Upper non-zero stress profile relative to base before required thin-session overlays."
    },
    "layers": {
      "hard_transaction_cost": "Layer 1 hard transaction costs must be bound by reviewed offline descriptors before diagnostics.",
      "spread_crossing": "Layer 2 spread crossing must use valid point-in-time BBO where available and flag bad or missing quotes explicitly.",
      "slippage_capacity_proxy": "Layer 3 slippage and capacity proxy remains a sensitivity proxy and not fill-capacity evidence."
    },
    "thin_session_overlays": "ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH require stricter spread, slippage, depth, and capacity proxy treatment on every non-zero profile.",
    "bbo_proxy_boundary": "BBO spread and depth diagnostics are risk-control inputs and proxy sensitivities only; they cannot prove tradability or execution capacity."
  },
  "expected_failure_modes": [
    "Spread zscore may become a generic cost or volatility filter rather than a distinct BBO confirmation overlay.",
    "BBO coverage may be incomplete for ES, NQ, RTY, thin sessions, or the development partition and must be audited before diagnostics.",
    "Stale, crossed, missing, or quarantined quotes can dominate the sample and leave too little usable coverage.",
    "Top-book depth thresholds may be unstable across instruments, sessions, and contract rolls if later grids are not bounded.",
    "Longer primary horizons currently lack locked LabelSpec references and require later audited binding before use.",
    "Thin-session overlays and non-zero cost profiles may make any downstream variant cost-fragile.",
    "No-lookahead audit may reject the draft if spread zscore uses centered windows, future quotes, final-session aggregates, or same-bar outcomes."
  ],
  "promotion_criteria": [
    "FUTCORE-P12 can verify that this is a BBO confirmation or risk-control overlay and not a standalone edge hypothesis.",
    "Later StudySpec binding must preserve valid BBO requirements, stale/crossed/missing quote exclusions, and point-in-time spread-zscore construction.",
    "Later diagnostics must report coverage, exclusions, and sample counts by instrument, session view, horizon, and BBO quality state.",
    "Non-zero cost profiles base, stress_1, stress_2, and double_cost must be available for review with thin-session overlays visible.",
    "Any missing BBO FeaturePack or non-5m LabelSpec binding is routed to FUTCORE-P13 or FUTCORE-P15 instead of being assumed available.",
    "Duplicate-exposure review can distinguish the spread-zscore plus depth overlay from generic cost, VWAP/session, liquidity/PA, and other BBO quality filters."
  ],
  "created_by": "Hypothesis Scout:rq.p11.bbo_tradability_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
