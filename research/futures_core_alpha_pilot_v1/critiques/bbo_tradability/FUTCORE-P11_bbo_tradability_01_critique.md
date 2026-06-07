# AlphaSpec Critique

```yaml
draft_id: "aspec_1284e49b083df11eeb0481ea"
family: "bbo_tradability"
title: "Spread-zscore plus top-book depth confirmation overlay"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_01.md"
drafter_role: "Hypothesis Scout:rq.p11.bbo_tradability_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "accept-for-StudySpec"
reasons:
  - "The draft frames BBO spread and depth as confirmation or risk-control only, not as standalone edge evidence."
  - "Valid BBO requirements, stale/crossed/missing quote exclusions, available_ts ordering, cost profiles, and BBO binding gaps are declared."
  - "Selected as the one BBO representative under the 10% accepted budget."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: BBO tradability/confirmation framing and valid BBO requirements"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: BBO family priority and no tradability claim boundary"
duplicate_exposure_hint: "bbo-spread-depth-confirmation; compare against BBO drafts 02, 03, 04 and cost-stress overlays."
flags:
  - "no_lookahead_route: BBO available_ts, stale quote, and spread zscore causal-window audit required."
  - "p13_p15_gap_route: BBO-capable feature binding and non-5m labels need audited binding before diagnostics."
```
