# AlphaSpec Critique

```yaml
draft_id: "aspec_a3a0979f1cb8d95982605a5c"
family: "cross_market"
title: "Triad dispersion and confirmation/divergence context"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_16_triad_dispersion_confirmation_context.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm16"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "reject"
reasons:
  - "The draft is value-free and declares required controls, but it is the broadest confirmation/divergence variant in the batch."
  - "Reject as a standalone StudySpec candidate to prevent the accepted confirmation seat from expanding into multiple overlapping triad variants."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: duplicate-exposure review and finite variant discipline"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-012, R-014, R-025"
duplicate_exposure_hint: "cm-broad-confirmation; duplicates drafts 13, 14, and 15 unless narrowed."
flags:
  - "no_lookahead_route: no immediate breach recorded, but any future rewrite needs precise aligned dispersion timestamps."
  - "budget_route: reject as over-broad duplicate under cross-market budget."
```
