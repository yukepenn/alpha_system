# AlphaSpec Critique

```yaml
draft_id: "aspec_55c1351d04054c943c2c3721"
family: "liquidity_pa"
title: "Compression breakout from fixed range boundary"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_05.md"
drafter_role: "Hypothesis Scout:rq.p10.liquidity_pa_drafting:compression_breakout"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The compression and breakout windows are objective and include missing/ambiguous level exclusions."
  - "It overlaps accepted failed-breakout reversal and regime compression-release drafts; revise to clarify whether plain breakout survives duplicate-exposure review."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: compression, breakout, and failed-breakout computability"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-014 duplicate exposure"
duplicate_exposure_hint: "pa-compression-breakout; compare against accepted draft 06 and regime draft 04."
flags:
  - "no_lookahead_route: compression boundary available_ts audit required."
  - "budget_route: revise due overlap with accepted failed-breakout candidate."
```
