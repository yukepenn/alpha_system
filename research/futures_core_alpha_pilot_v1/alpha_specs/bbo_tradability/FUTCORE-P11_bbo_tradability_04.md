# FUTCORE-P11 BBO Tradability AlphaSpec 04

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the BBO tradability / top-book confirmation
family.

```json
{
  "alpha_spec_id": "aspec_89fa98eb6439f131de4151cb",
  "hypothesis_id": "hyp_3d3e3f9ea18a6150b14ab5e3",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "family_budget": "This is the fourth FUTCORE-P11 BBO draft, reaching the target and hard maximum of 4 without reallocating unused slots.",
    "overlay_role": "This draft is a quote-quality quarantine and BBO availability overlay for later diagnostics; it is a risk-control screen only and not a standalone edge hypothesis.",
    "input_pack_refs": {
      "dataset_version": "DatasetVersion dsv_databento_ohlcv_05404069799decb0 anchors ES/NQ/RTY by reference only.",
      "session_features": "Locked session FeatureVersions fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f and fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978 supply session context where available.",
      "label_reference": "LabelSpec lspec_cd6523694c850c9943b2067e remains the locked 5m label reference for later review.",
      "bbo_binding_gap": "missing_bbo_flag, bad_quote_flag, wide_spread_flag, and low_depth_flag require audited BBO-capable feature bindings before any diagnostics can consume them."
    },
    "bbo_requirements": {
      "valid_bbo": "A valid BBO row has present bid and ask, ordered prices, non-stale timestamp, usable sizes where required, quality flags, and available_ts no later than the decision timestamp.",
      "missing_bbo": "Missing BBO is an explicit exclusion or diagnostic cell and must never be filled with OHLCV mid, prior quotes, or synthetic spread values.",
      "bad_quote": "Bad quote covers stale, crossed, quarantined, invalid-size, missing-side, or otherwise unusable top-book states.",
      "spread_depth_filter": "Wide-spread and low-depth flags are filter or quarantine overlays and cannot become favorable evidence."
    },
    "horizon_policy": {
      "primary_horizons": "Primary pilot horizons are 5m, 10m, 15m, and 30m, with only 5m locked by current LabelSpec reference.",
      "fragile_horizons": "1m and 3m are diagnostic-only because quote-quality filters are highly sensitive to BBO timestamping and spread crossing.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded from primary review except as later extended diagnostics.",
      "maintenance_break": "Modeled holding intervals must be flat before the exchange maintenance or trade-date break."
    },
    "session_scope": {
      "primary_sessions": "RTH and RTH_with_ETH_context are primary views only when quote-quality coverage is explicit and point-in-time.",
      "diagnostic_sessions": "full_session, ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH are diagnostic views with stricter missing-BBO, spread, depth, and cost caveats.",
      "excluded_sessions": "Sessions with ambiguous boundaries, missing exchange_trade_date, or unresolved BBO availability are excluded."
    },
    "duplicate_rejected_idea_awareness": "This draft intentionally overlaps all other BBO drafts as the quote-quality gate they depend on; P12 must verify it remains a quarantine overlay, not a duplicate spread, depth, or microprice hypothesis, and later ledger review must compare known rejected bad-data ideas.",
    "value_free_boundary": "The draft records only policy and references. It includes no quote rows, data values, feature values, label values, cost outputs, diagnostics, or acceptance result."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.bbo.BBOFeatureName.MISSING_BBO_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.BAD_QUOTE_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.WIDE_SPREAD_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.LOW_DEPTH_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.SPREAD",
    "src.alpha_system.features.families.bbo.BBOFeatureName.SPREAD_TICKS",
    "src.alpha_system.features.families.bbo.BBOFeatureName.TOP_BOOK_DEPTH",
    "feature_version:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "feature_version:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude any row with missing BBO unless the later diagnostic is explicitly counting missing-BBO coverage as a quarantine cell without using it as a signal input.",
    "Exclude stale, crossed, locked without approved policy, quarantined, invalid-size, missing-side, or otherwise bad quotes from any admitted decision sample.",
    "Exclude any spread or depth proxy fabricated from OHLCV bars, prior quotes, forward-filled quotes, or session averages.",
    "Exclude 1m and 3m views from continuation criteria because quote-quality behavior at those horizons is execution-fragile.",
    "Exclude any modeled holding period crossing the exchange maintenance or trade-date break.",
    "Exclude variants that treat the absence of bad quotes as favorable alpha evidence instead of a required data-quality precondition."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "The decision timestamp is after a completed signal bar and no earlier than available_ts for quote-quality flags, BBO fields, session context, and any host-family signal this overlay later gates.",
    "available_ts_usage": {
      "quality_flags": "missing_bbo_flag, bad_quote_flag, wide_spread_flag, and low_depth_flag must be produced from BBO state available at or before the decision timestamp.",
      "bbo_fields": "Bid, ask, spread, spread_ticks, and top_book_depth cannot be forward-filled or reconstructed after the fact.",
      "host_signal": "If this overlay gates another family signal later, the host signal and this BBO quality overlay must both satisfy available_ts ordering."
    },
    "label_available_ts_usage": "LabelSpec lspec_cd6523694c850c9943b2067e is used only as a future outcome after label_available_ts and cannot determine BBO quarantine state.",
    "bar_and_quote_semantics": "Quote-quality state is point-in-time and must be joined by instrument, exchange_trade_date, session segment, and decision timestamp rather than arbitrary wall-clock proximity.",
    "session_boundaries": "RTH, ETH, pre_RTH, post_RTH, and RTH_with_ETH_context splits must remain visible, with no modeled horizon crossing maintenance.",
    "cross_instrument_alignment": "The quality overlay is instrument-local; no cross-instrument quote-quality alignment is authorized in this draft."
  },
  "cost_assumptions": {
    "cost_model_version": "CostModelVersion cmv_futcore_pilot_three_layer_session_stress_v1 is mandatory for later diagnostics.",
    "profiles": {
      "zero_cost": "Diagnostic-only contrast with promotion_basis_allowed=false; missing or bad BBO cannot be excused by this profile.",
      "base": "Central non-zero profile required for later cost sensitivity review.",
      "stress_1": "Required non-zero profile not less conservative than base.",
      "stress_2": "Required non-zero profile not less conservative than stress_1.",
      "double_cost": "Required upper non-zero profile relative to base before thin-session overlays."
    },
    "layers": {
      "hard_transaction_cost": "Layer 1 hard costs are reviewed offline descriptors only.",
      "spread_crossing": "Layer 2 must use valid point-in-time BBO and visibly route missing or bad BBO to the approved fallback or exclusion policy.",
      "slippage_capacity_proxy": "Layer 3 slippage and capacity proxy must remain conservative and cannot turn quote availability into capacity evidence."
    },
    "thin_session_overlays": "ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH require stricter spread, missing-BBO, low-depth, slippage, and capacity proxy overlays on non-zero profiles.",
    "quality_boundary": "Quote-quality pass/fail is a prerequisite or exclusion diagnostic only; it is not favorable evidence and cannot prove execution readiness."
  },
  "expected_failure_modes": [
    "The draft may be too broad because every BBO-dependent idea requires quote-quality quarantine, so P12 must verify that it remains a bounded overlay.",
    "Missing BBO or bad quote rates may be high in ETH, pre_RTH, post_RTH, or instrument-specific cells.",
    "A downstream StudySpec may accidentally fabricate spread or depth from OHLCV or stale quotes unless the exclusion policy is enforced.",
    "The overlay can duplicate spread-zscore or depth filters if wide_spread_flag and low_depth_flag are not kept as quarantine diagnostics.",
    "Longer primary horizons beyond 5m require later LabelSpec binding and cannot be assumed.",
    "Non-zero cost and thin-session overlays may turn most admitted cells into cost-fragile or unusable diagnostics."
  ],
  "promotion_criteria": [
    "FUTCORE-P12 can verify that the draft is a quote-quality quarantine overlay and not a standalone alpha or favorable evidence claim.",
    "Later StudySpec binding explicitly preserves missing, stale, crossed, quarantined, wide-spread, and low-depth exclusion handling.",
    "Later diagnostics report BBO availability, bad-quote, wide-spread, and low-depth coverage by instrument, session view, and horizon.",
    "Non-zero profiles base, stress_1, stress_2, and double_cost are present and show how bad or missing BBO is handled under the P04 cost contract.",
    "No spread, depth, microprice, or quality flag is fabricated from OHLCV, prior quotes, future quotes, or label information.",
    "Duplicate-exposure review distinguishes this quarantine overlay from the spread-zscore, microprice, and depth drafts it may gate."
  ],
  "created_by": "Hypothesis Scout:rq.p11.bbo_tradability_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
