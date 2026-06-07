# AlphaSpec Critique

```yaml
draft_id: "aspec_a98c25c5b437e0906320ac56"
family: "cross_market"
title: "ES completed-bar context for later RTY decision"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_02_es_leads_rty_completed_bar_context.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm02"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "Schema and point-in-time declarations are adequate under P05, but the accepted cross-market set already includes RTY rotation and pairwise lead/lag coverage."
  - "The draft should be narrowed or merged before StudySpec binding to avoid rediscovering the same ES/RTY broad-market exposure as drafts 10 and 15."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: duplicate-exposure exclusions and cross-market missingness diagnostics"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACCEPTANCE.md: AlphaSpec quality and family budget adherence"
duplicate_exposure_hint: "cm-lead-lag-rty; compare against RTY catch-up, RTY non-confirmation, and broad-market confirmation drafts."
flags:
  - "no_lookahead_route: standard cross-instrument available_ts audit."
  - "budget_route: revise due cross_market seat pressure, not due result evidence."
```
