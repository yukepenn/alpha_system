# AlphaSpec Critique

```yaml
draft_id: "aspec_d26b7959b12be5b53f969067"
family: "regime"
title: "Range-compression release gate"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_04.md"
drafter_role: "Hypothesis Scout:rq.p09.regime_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The activation logic is computable and names causal range boundaries, momentum/reversion gates, and inactive states."
  - "It overlaps liquidity/PA compression breakout and failed-breakout drafts; revise to bind this as a regime gate only or merge with accepted liquidity candidates."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: regime activation logic and price-action overlap handling"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-014 duplicate exposure"
duplicate_exposure_hint: "regime-compression-release; compare against liquidity drafts 05 and 06."
flags:
  - "no_lookahead_route: compression boundary available_ts audit required."
  - "p13_p15_gap_route: non-5m labels and primitive bindings need audit."
```
