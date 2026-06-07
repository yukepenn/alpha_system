# AlphaSpec Critique

```yaml
draft_id: "aspec_89fa98eb6439f131de4151cb"
family: "bbo_tradability"
title: "Missing-BBO, bad-quote, wide-spread, and low-depth quarantine overlay"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_04.md"
drafter_role: "Hypothesis Scout:rq.p11.bbo_tradability_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The quarantine overlay is valuable as a guard declaration, but it intentionally overlaps every other BBO draft."
  - "Revise into a required BBO quality precondition for later StudySpecs rather than spending the one BBO family slot on a standalone quarantine candidate."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: valid BBO requirements and bad quote exclusions"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: BBO as confirmation/risk-control evidence only"
duplicate_exposure_hint: "bbo-quote-quality-quarantine; merge with any accepted BBO StudySpec rather than standalone."
flags:
  - "no_lookahead_route: quote-quality flags and host-family signals both need available_ts audit."
  - "p13_p15_gap_route: BBO-capable feature binding must be confirmed before use."
```
