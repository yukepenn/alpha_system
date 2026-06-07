# AlphaSpec Critique

```yaml
draft_id: "aspec_a41dcccac5552de945aba825"
family: "cross_market"
title: "RTY catch-up rotation context"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_10_rty_catchup_rotation_context.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm10"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "accept-for-StudySpec"
reasons:
  - "The draft is schema-complete and declares aligned ES/NQ context, RTY target exposure, missingness handling, and duplicate-exposure awareness."
  - "Selected as the cross-market rotation representative because it is narrower than the broad defensive and rank-turnover rotation drafts."
  - "Acceptance is for StudySpec consideration only and is conditioned on later label and no-lookahead audits."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: rotation diagnostics, available_ts alignment, horizon rules"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: cross-market rotation family focus"
duplicate_exposure_hint: "cm-rty-rotation; compare against drafts 02, 03, 07, 11, 12, and 15."
flags:
  - "no_lookahead_route: completed-bar agreement and RTY decision timestamp must be audited."
  - "p13_p15_gap_route: primary 15m horizon needs audited label binding."
```
