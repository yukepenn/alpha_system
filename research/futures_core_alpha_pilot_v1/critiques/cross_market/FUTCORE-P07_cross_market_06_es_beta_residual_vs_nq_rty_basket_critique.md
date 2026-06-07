# AlphaSpec Critique

```yaml
draft_id: "aspec_bd439bada940f95f45288535"
family: "cross_market"
title: "ES beta residual versus NQ/RTY basket"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_06_es_beta_residual_vs_nq_rty_basket.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm06"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft satisfies P05 field and timestamp discipline, including point-in-time residual estimation requirements."
  - "It is not selected because the residual family seat is represented by draft 05; this version needs a clearer reason to carry separate ES-specific residual exposure."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: residual construction and duplicate-exposure review"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-014 duplicate exposure"
duplicate_exposure_hint: "cm-beta-residual; compare against accepted draft 05 and pair residual draft 08."
flags:
  - "no_lookahead_route: residual coefficients require point-in-time audit."
  - "p13_p15_gap_route: primary 10m horizon needs audited label binding."
```
