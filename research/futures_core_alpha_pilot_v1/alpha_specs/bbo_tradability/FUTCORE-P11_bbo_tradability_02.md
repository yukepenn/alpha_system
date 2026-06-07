# FUTCORE-P11 BBO Tradability AlphaSpec 02

Status: draft evidence only. This file contains exactly one canonical
governance `AlphaSpec` payload for the BBO tradability / top-book confirmation
family.

```json
{
  "alpha_spec_id": "aspec_cfb2aad22b43bc23391a7806",
  "hypothesis_id": "hyp_38f323cff1a4daea065cffed",
  "target_instruments": [
    "ES",
    "NQ",
    "RTY"
  ],
  "data_assumptions": {
    "family_budget": "BBO tradability / top-book confirmation uses the FUTCORE-P11 target of 4 drafts and does not reallocate budget to any other family.",
    "overlay_role": "This draft records microprice-minus-mid and top-book imbalance as a confirmation overlay for later diagnostics; it is not a standalone edge hypothesis and records no tradability or profitability result.",
    "input_pack_refs": {
      "dataset_version": "DatasetVersion dsv_databento_ohlcv_05404069799decb0 anchors the ES/NQ/RTY universe by reference.",
      "session_features": "FeatureVersions fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f and fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978 supply locked session context by reference.",
      "label_reference": "LabelSpec lspec_cd6523694c850c9943b2067e is the locked 5m forward label reference; other primary horizons need later audited LabelSpec binding.",
      "bbo_binding_gap": "Canonical BBO rows and BBO feature versions must be audited in FUTCORE-P13 and routed through FUTCORE-P15 if approved bindings are missing."
    },
    "bbo_requirements": {
      "valid_bbo": "Microprice requires valid bid, ask, bid_size, ask_size, mid, and microprice fields from the same top-book state with available_ts at or before the decision timestamp.",
      "microprice_minus_mid": "The signed difference between microprice and mid is a top-book pressure confirmation input only and must be computed from valid quote sizes.",
      "imbalance": "Top-book imbalance must use bid_size and ask_size from the same BBO row and must flag zero-size or missing-side conditions.",
      "quote_quality": "Missing BBO, quarantined BBO, crossed quotes, stale quotes, and invalid sizes are exclusions or diagnostic flags, not evidence in favor of the draft."
    },
    "horizon_policy": {
      "primary_horizons": "5m, 10m, 15m, and 30m are the primary pilot horizons; only the locked 5m label is currently referenced.",
      "fragile_horizons": "1m and 3m are diagnostic-only and require stricter BBO validity, spread, depth, and non-zero cost review.",
      "extended_horizons": "60m, 120m, 240m, and session_close are excluded from primary interpretation and may be requested only as extended diagnostics.",
      "maintenance_break": "No modeled interval may cross the exchange daily maintenance or trade-date break."
    },
    "session_scope": {
      "primary_sessions": "RTH and RTH_with_ETH_context are primary if microprice, imbalance, and session context are point-in-time.",
      "diagnostic_sessions": "full_session, ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH are diagnostic-only with thin-session BBO and cost caveats.",
      "excluded_sessions": "Segments with ambiguous exchange_trade_date, missing BBO, stale quote carry, or unavailable session metadata are excluded."
    },
    "duplicate_rejected_idea_awareness": "This draft overlaps imbalance and order-book pressure ideas but differs from spread-zscore gating because it focuses on signed microprice displacement; P12 must compare it to cross-market confirmation, regime pressure, and any rejected imbalance-style ideas.",
    "value_free_boundary": "The draft records only references and assumptions. It does not contain quote values, feature values, label values, diagnostics, capacity estimates, or research outcomes."
  },
  "factor_inputs": [
    "src.alpha_system.features.families.bbo.BBOFeatureName.MID",
    "src.alpha_system.features.families.bbo.BBOFeatureName.MICROPRICE",
    "src.alpha_system.features.families.bbo.BBOFeatureName.MICROPRICE_MINUS_MID",
    "src.alpha_system.features.families.bbo.BBOFeatureName.TOP_BOOK_IMBALANCE",
    "src.alpha_system.features.families.bbo.BBOFeatureName.SPREAD",
    "src.alpha_system.features.families.bbo.BBOFeatureName.MISSING_BBO_FLAG",
    "src.alpha_system.features.families.bbo.BBOFeatureName.BAD_QUOTE_FLAG",
    "feature_version:fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f:base_ohlcv_rth_flag",
    "feature_version:fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978:base_ohlcv_session_minute"
  ],
  "label_references": [
    "lspec_cd6523694c850c9943b2067e"
  ],
  "exclusion_rules": [
    "Exclude rows where bid, ask, mid, microprice, bid_size, ask_size, or top-book imbalance is missing, stale, crossed, quarantined, zero-size invalid, or unavailable by the decision timestamp.",
    "Exclude rows where microprice_minus_mid is derived from different quote timestamps, different instruments, or any future or same-bar outcome information.",
    "Exclude all 1m and 3m diagnostic views from favorable review criteria because microprice signals are especially sensitive to quote timing and spread crossing.",
    "Exclude thin-session observations unless later diagnostics mark their BBO coverage, spread, depth, and non-zero cost overlays explicitly.",
    "Exclude any modeled holding period crossing the maintenance or trade-date break.",
    "Exclude variants that duplicate generic imbalance, direction, or regime-pressure drafts without the explicit microprice-minus-mid confirmation contract."
  ],
  "timestamp_assumptions": {
    "decision_timestamp": "The decision timestamp is after a completed signal bar and is no earlier than the latest available_ts among microprice, mid, imbalance, spread, quote-quality, OHLCV, and session inputs.",
    "available_ts_usage": {
      "microprice_inputs": "Bid, ask, bid_size, ask_size, mid, microprice, and microprice_minus_mid are consumed only when their BBO row available_ts is not later than the decision timestamp.",
      "imbalance_inputs": "Top-book imbalance uses same-row bid_size and ask_size and inherits the BBO row available_ts.",
      "quality_inputs": "Missing, bad quote, crossed, stale, and invalid-size flags must be available before they can permit or exclude a row."
    },
    "label_available_ts_usage": "Label reference lspec_cd6523694c850c9943b2067e is evaluated only as a future label after label_available_ts and is never available to the signal.",
    "bar_and_quote_semantics": "The overlay is formed after the completed bar using the latest valid quote state available as of the decision timestamp; arbitrary wall-clock joins are forbidden.",
    "session_boundaries": "exchange_trade_date, session_segment, RTH, ETH, pre_RTH, post_RTH, and maintenance-break boundaries must remain explicit in later diagnostics.",
    "cross_instrument_alignment": "No cross-instrument timestamp join is in scope; ES, NQ, and RTY are evaluated separately under their own BBO availability."
  },
  "cost_assumptions": {
    "cost_model_version": "CostModelVersion cmv_futcore_pilot_three_layer_session_stress_v1 is mandatory for any later diagnostics.",
    "profiles": {
      "zero_cost": "Diagnostic contrast only with promotion_basis_allowed=false and no use as continuation support.",
      "base": "Central non-zero profile required for hard cost, spread crossing, slippage proxy, and capacity proxy review.",
      "stress_1": "Required non-zero stress profile not less conservative than base.",
      "stress_2": "Required non-zero stress profile not less conservative than stress_1.",
      "double_cost": "Required upper non-zero stress profile relative to base before thin-session overlays."
    },
    "layers": {
      "hard_transaction_cost": "Layer 1 hard cost is applied from reviewed offline descriptors only.",
      "spread_crossing": "Layer 2 uses valid BBO spread crossing; bad or missing BBO cannot be fabricated.",
      "slippage_capacity_proxy": "Layer 3 slippage and capacity remain proxy sensitivities and cannot be interpreted as execution quality."
    },
    "thin_session_overlays": "ETH_only, ETH_evening, ETH_overnight, pre_RTH, and post_RTH require stricter non-zero spread, slippage, and capacity proxy overlays.",
    "microprice_boundary": "Microprice and imbalance are confirmation inputs only; favorable-looking quote pressure cannot override non-zero cost or missing BBO limitations."
  },
  "expected_failure_modes": [
    "Microprice-minus-mid can overfit transient quote pressure or queue imbalance that is not stable across sessions or instruments.",
    "Invalid quote sizes, crossed quotes, stale quotes, or missing BBO can remove a large fraction of the potential sample.",
    "The overlay can duplicate generic top-book imbalance or regime-pressure filters unless P12 confirms the signed microprice displacement is distinct.",
    "Thin-session BBO observations may be too sparse or too costly under non-zero cost profiles.",
    "Longer primary horizons require later audited LabelSpec binding and cannot be assumed available.",
    "No-lookahead audit may reject any implementation that joins quote rows after the decision timestamp or uses same-bar label outcomes."
  ],
  "promotion_criteria": [
    "FUTCORE-P12 can verify the draft is a confirmation overlay and not a standalone directional alpha claim.",
    "Later StudySpec binding preserves same-row microprice, mid, size, imbalance, quality flag, and available_ts semantics.",
    "Later diagnostics report exclusion counts for missing, stale, crossed, quarantined, invalid-size, and thin-session BBO states.",
    "Non-zero profiles base, stress_1, stress_2, and double_cost are reviewed with spread-crossing and thin-session overlays visible.",
    "Any missing BBO feature binding or non-5m label requirement is escalated to FUTCORE-P13 or FUTCORE-P15.",
    "Duplicate-exposure review distinguishes this draft from generic imbalance, spread, regime, and cross-market confirmation ideas."
  ],
  "created_by": "Hypothesis Scout:rq.p11.bbo_tradability_drafting",
  "created_at": "2026-06-07T04:13:43Z"
}
```
