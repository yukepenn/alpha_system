# AlphaSpec Critique

```yaml
draft_id: "aspec_39ffc190cfbfa6ba0b1a2a25"
family: "liquidity_pa"
title: "Failed-breakout reversal with inside-close and reversal-magnitude thresholds"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_06.md"
drafter_role: "Hypothesis Scout:rq.p10.liquidity_pa_drafting:failed_breakout_reversal"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "accept-for-StudySpec"
reasons:
  - "The draft defines objective failed-breakout, inside-close, and reversal-magnitude rules with fixed boundaries."
  - "Accepted as the second rounded liquidity/PA representative because it is distinct from the sweep/close-back-inside candidate and keeps PA rules computable."
  - "The accepted status is only for StudySpec consideration and does not infer any outcome."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: failed-breakout reversal and objective PA requirements"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml: family budget and approved AlphaSpec cap"
duplicate_exposure_hint: "pa-failed-breakout; compare against compression breakout draft 05 and regime compression draft 04."
flags:
  - "no_lookahead_route: fixed boundary, breakout, and failure deadline available_ts audit required."
  - "p13_p15_gap_route: non-5m labels need audited binding."
```
