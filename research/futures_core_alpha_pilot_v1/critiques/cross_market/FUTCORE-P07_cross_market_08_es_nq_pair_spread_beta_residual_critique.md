# AlphaSpec Critique

```yaml
draft_id: "aspec_0cc1c674fbe038809819be79"
family: "cross_market"
title: "ES/NQ pair-spread beta residual"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_08_es_nq_pair_spread_beta_residual.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm08"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft declares the required point-in-time hedge relationship, label availability, and cost-profile boundaries."
  - "Pair-only residual exposure overlaps accepted draft 05 and accepted divergence draft 14; revise to define whether pair spread adds a materially separate diagnostic."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: beta/residual construction assumptions"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-012 and R-014"
duplicate_exposure_hint: "cm-pair-residual-divergence; compare against drafts 05, 06, and 14."
flags:
  - "no_lookahead_route: hedge estimation and spread construction require prior-window audit."
  - "p13_p15_gap_route: primary 10m horizon needs audited label binding."
```
