# AlphaSpec Critique

```yaml
draft_id: "aspec_4d5ebc78dc8269d8b8d2ca20"
family: "cross_market"
title: "Defensive rotation among ES/NQ/RTY"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_11_defensive_rotation_between_es_nq_rty.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm11"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "reject"
reasons:
  - "Although the P05 fields are populated, the defensive rotation state is a broad umbrella over drafts 09, 10, and 12."
  - "Rejecting the standalone draft avoids budget drift and variant inflation; narrower components can be reconsidered through revised records."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: duplicate-exposure and variant-budget discipline"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-012 and R-025"
duplicate_exposure_hint: "cm-broad-rotation; duplicates accepted RTY rotation unless narrowed."
flags:
  - "no_lookahead_route: no immediate breach recorded, but any replacement needs explicit rank/state timestamps."
  - "budget_route: reject as broad duplicate under finite cross-market seats."
```
