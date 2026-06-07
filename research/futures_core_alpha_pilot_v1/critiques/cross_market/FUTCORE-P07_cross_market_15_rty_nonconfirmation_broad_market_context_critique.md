# AlphaSpec Critique

```yaml
draft_id: "aspec_6fa402d0ecaaa3491c6a52cd"
family: "cross_market"
title: "RTY non-confirmation against ES/NQ broad market"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_15_rty_nonconfirmation_broad_market_context.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm15"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "P05 fields and cross-market timing controls are present."
  - "The RTY non-confirmation exposure overlaps accepted RTY rotation and triad confirmation candidates; revise to define one non-duplicative confirmation rule before any StudySpec slot."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: duplicate exposure, confirmation diagnostics, and missingness checks"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACCEPTANCE.md: duplicate-exposure hints"
duplicate_exposure_hint: "cm-rty-nonconfirmation; compare against drafts 02, 07, 10, and 13."
flags:
  - "no_lookahead_route: broad-market movement and RTY state alignment must be audited."
  - "p13_p15_gap_route: primary 30m horizon needs audited label binding."
```
