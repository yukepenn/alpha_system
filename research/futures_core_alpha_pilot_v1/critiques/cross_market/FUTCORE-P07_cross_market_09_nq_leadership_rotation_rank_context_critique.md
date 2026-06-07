# AlphaSpec Critique

```yaml
draft_id: "aspec_677bf829db3937be87e8fff4"
family: "cross_market"
title: "NQ leadership rotation rank context"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_09_nq_leadership_rotation_rank_context.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm09"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "Rank construction, availability, and missingness checks are declared, satisfying the P05 critique surface."
  - "The exposure is close to accepted NQ lead/lag and residual representatives; a revision should narrow rank turnover or defer it to a single rotation StudySpec."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: cross-market rank/rotation diagnostics"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml: finite approved AlphaSpec cap"
duplicate_exposure_hint: "cm-nq-rotation; compare against drafts 01, 05, and 12."
flags:
  - "no_lookahead_route: rank inputs must preserve completed-bar available_ts ordering."
  - "p13_p15_gap_route: primary 15m horizon needs audited label binding."
```
