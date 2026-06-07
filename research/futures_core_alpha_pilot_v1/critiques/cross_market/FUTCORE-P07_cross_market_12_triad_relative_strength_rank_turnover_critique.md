# AlphaSpec Critique

```yaml
draft_id: "aspec_b2243f2aa448902d9d99d386"
family: "cross_market"
title: "Triad relative-strength rank turnover"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_12_triad_relative_strength_rank_turnover.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm12"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft names rank turnover, timestamp alignment, missingness, and cost-profile requirements in a value-free way."
  - "It overlaps NQ leadership and broad rotation drafts; revise to bind one predeclared turnover definition or merge into the accepted rotation StudySpec candidate."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: rank/rotation construction and duplicate-exposure hints"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACCEPTANCE.md: rejected ideas and duplicate-exposure visibility"
duplicate_exposure_hint: "cm-rank-turnover; compare against drafts 09, 10, and 11."
flags:
  - "no_lookahead_route: rank turnover must use completed bars only."
  - "p13_p15_gap_route: primary 15m horizon needs audited label binding."
```
