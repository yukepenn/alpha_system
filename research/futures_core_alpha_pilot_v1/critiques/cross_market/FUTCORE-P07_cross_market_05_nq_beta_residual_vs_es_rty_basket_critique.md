# AlphaSpec Critique

```yaml
draft_id: "aspec_8d9e272e4b78eedcd27f0bec"
family: "cross_market"
title: "NQ beta residual versus ES/RTY basket"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket.json"
drafter_role: "Hypothesis Scout:rq.p07.cross_market_drafting:cm05"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "accept-for-StudySpec"
reasons:
  - "P05 schema, cost, timestamp, missingness, and duplicate-exposure declarations are present."
  - "The residual construction has a distinct family role if beta estimation is kept point-in-time and audited before diagnostics."
  - "Selected as the cross-market residual representative; sibling residual drafts should not be accepted without narrowing."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: beta/residual assumptions, no-lookahead rules, cost profiles"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml: family budget and approved AlphaSpec cap"
duplicate_exposure_hint: "cm-beta-residual; compare against drafts 06, 07, 08, and NQ leadership draft 09."
flags:
  - "no_lookahead_route: beta or hedge ratio estimation must use prior available data only."
  - "p13_p15_gap_route: primary 10m horizon needs audited label binding before diagnostics."
```
