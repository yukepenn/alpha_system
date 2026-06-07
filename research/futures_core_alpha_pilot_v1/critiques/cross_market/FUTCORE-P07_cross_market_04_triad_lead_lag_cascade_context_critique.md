# AlphaSpec Critique

```yaml
draft_id: "aspec_c6a0645fbad79e0a263737a6"
family: "cross_market"
title: "Three-instrument lead/lag cascade context"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_04_triad_lead_lag_cascade_context.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm04"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "reject"
reasons:
  - "The record is schema-complete, but its triad cascade is a broad superset of pairwise lead/lag drafts 01-03."
  - "Forwarding this as a standalone StudySpec would inflate variants without a distinct, predeclared exposure boundary."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: duplicate exposure and variant containment"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-012 variant explosion and R-014 duplicate exposure"
duplicate_exposure_hint: "cm-lead-lag-triad; duplicates pairwise lead/lag group unless narrowed."
flags:
  - "no_lookahead_route: no immediate breach recorded, but any future triad version needs strict max-available_ts alignment."
  - "budget_route: reject as over-broad duplicate, not as an edge or profitability judgment."
```
