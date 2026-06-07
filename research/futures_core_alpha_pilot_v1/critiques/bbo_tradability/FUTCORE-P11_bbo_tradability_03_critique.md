# AlphaSpec Critique

```yaml
draft_id: "aspec_857ea832d75aa4fc23b376d6"
family: "bbo_tradability"
title: "Top-book depth and imbalance risk-control filter"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_03.md"
drafter_role: "Hypothesis Scout:rq.p11.bbo_tradability_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft declares top-book depth, imbalance, quote-quality exclusions, and confirmation/risk-control framing."
  - "It overlaps accepted spread/depth overlay and liquidity/PA liquidity proxies; revise to make depth a shared overlay or distinct BBO diagnostic state."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: BBO confirmation overlay and duplicate-exposure review"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-014 duplicate exposure"
duplicate_exposure_hint: "bbo-depth-imbalance; compare against accepted draft 01 and liquidity/PA overlays."
flags:
  - "no_lookahead_route: top-book depth and imbalance available_ts audit required."
  - "p13_p15_gap_route: BBO-capable feature binding and non-5m labels need audit."
```
