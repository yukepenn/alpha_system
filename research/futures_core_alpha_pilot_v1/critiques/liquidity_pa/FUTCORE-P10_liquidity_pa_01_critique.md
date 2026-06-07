# AlphaSpec Critique

```yaml
draft_id: "aspec_1c1cfee8bedf55ced10a391e"
family: "liquidity_pa"
title: "Prior high/low liquidity sweep against causal 20-bar range"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_01.md"
drafter_role: "Hypothesis Scout:rq.p10.liquidity_pa_drafting:prior_high_low_sweep"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft provides objective computable sweep rules and explicit reference-level available_ts handling."
  - "It is broader than accepted close-back-inside and failed-breakout candidates; revise or merge as a parent trigger definition rather than a standalone StudySpec."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: objective PA rules and timestamped level availability"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-012 variant explosion"
duplicate_exposure_hint: "pa-prior-range-sweep-parent; compare against accepted drafts 02 and 06."
flags:
  - "no_lookahead_route: prior range level available_ts audit required."
  - "p13_p15_gap_route: non-5m labels need audited binding."
```
