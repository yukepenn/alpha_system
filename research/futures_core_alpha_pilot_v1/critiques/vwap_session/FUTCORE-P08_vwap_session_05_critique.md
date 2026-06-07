# AlphaSpec Critique

```yaml
draft_id: "aspec_ee701ec09d58e30b746c8e06"
family: "vwap_session"
title: "Completed overnight high/low with running RTH VWAP"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_05.md"
drafter_role: "Hypothesis Scout:rq.p08.vwap_session_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft declares completed ETH context and running RTH VWAP timing, satisfying the core no-lookahead requirement."
  - "It overlaps liquidity sweep and overnight level hypotheses; revise to make the VWAP/session context dominant and objective before a StudySpec slot."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: overnight high/low availability and final aggregate rejection"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-014 duplicate exposure"
duplicate_exposure_hint: "vwap-overnight-level; compare against liquidity sweep and failed-breakout level drafts."
flags:
  - "no_lookahead_route: completed ETH context must be available before RTH decision."
  - "budget_route: revise due accepted budget and level-overlap."
```
