# AlphaSpec Critique

```yaml
draft_id: "aspec_cfb2aad22b43bc23391a7806"
family: "bbo_tradability"
title: "Microprice-minus-mid and top-book imbalance overlay"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_02.md"
drafter_role: "Hypothesis Scout:rq.p11.bbo_tradability_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft correctly frames microprice and imbalance as confirmation overlays with point-in-time BBO requirements."
  - "It is not selected because the BBO family has one accepted slot; revise or merge with the accepted spread/depth overlay after P13 confirms BBO feature bindings."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: BBO confirmation role and stale/missing quote exclusions"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml: BBO 10% budget"
duplicate_exposure_hint: "bbo-microprice-imbalance; compare against accepted draft 01 and depth draft 03."
flags:
  - "no_lookahead_route: microprice and imbalance inputs need same-quote-state available_ts audit."
  - "p13_p15_gap_route: BBO-capable feature binding and non-5m labels need audit."
```
