# AlphaSpec Critique

```yaml
draft_id: "aspec_4fee1276b9f37cb75bd7be48"
family: "cross_market"
title: "RTY beta residual versus ES/NQ basket"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_07_rty_beta_residual_vs_es_nq_basket.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm07"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The payload is value-free and declares cross-market missingness, stale-input exclusion, and residual timing controls."
  - "It overlaps both the accepted residual representative and accepted RTY rotation representative; revise to prove the residual question is not another small-cap catch-up variant."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: family-specific diagnostics and duplicate-exposure exclusions"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: bounded cross-market family scope"
duplicate_exposure_hint: "cm-rty-residual-catchup; compare against drafts 03, 05, and 10."
flags:
  - "no_lookahead_route: point-in-time basket/residual audit required."
  - "p13_p15_gap_route: primary 10m horizon needs audited label binding."
```
