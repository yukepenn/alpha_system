# AlphaSpec Critique

```yaml
draft_id: "aspec_8c9bc3ea6722e507f02b94de"
family: "vwap_session"
title: "RTH running-VWAP reject and close-back-side event"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_02.md"
drafter_role: "Hypothesis Scout:rq.p08.vwap_session_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft satisfies the family requirement to use running VWAP and reject final-session aggregates."
  - "It is paired tightly with accepted reclaim draft 01 and with liquidity failed-breakout ideas; revise to avoid duplicating the same VWAP transition exposure."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: VWAP/session diagnostic declarations and duplicate-exposure exclusions"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-014 duplicate exposure"
duplicate_exposure_hint: "vwap-reclaim-reject; compare against accepted draft 01 and liquidity/PA close-back-inside drafts."
flags:
  - "no_lookahead_route: running VWAP and close-back-side timestamp audit required."
  - "budget_route: revise due two-seat VWAP/session accepted cap."
```
