# AlphaSpec Critique

```yaml
draft_id: "aspec_532c35c3e7571acf8c8f40d1"
family: "cross_market"
title: "RTY completed-bar risk context for later NQ decision"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_03_rty_leads_nq_risk_context.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm03"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "P05 timestamp and missingness rules are declared, including completed-bar use and exclusion of stale cross-market inputs."
  - "The exposure overlaps small-cap relative context already represented by accepted draft 10 and residual draft 05; a later version needs a clearer non-duplicative risk-context role."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: cross-market family requirements and duplicate-exposure review"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-014 duplicate exposure"
duplicate_exposure_hint: "cm-small-cap-risk; compare against drafts 05, 07, and 10."
flags:
  - "no_lookahead_route: standard RTY/NQ alignment audit."
  - "budget_route: revise for duplicate exposure before any StudySpec slot."
```
