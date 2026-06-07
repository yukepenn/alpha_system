# FUTCORE-P25 Statistical Reviewer Verdict Index

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P25`  
Artifact type: value-free statistical reviewer verdict index

This directory records exactly one statistical reviewer verdict artifact for
each P22-P24 non-rejected consolidation survivor. The artifacts cite upstream
evidence paths only. They do not run diagnostics, recompute statistics, read raw
or row-level values, assign a PromotionDecision, instantiate an autonomous
agent, or make paper/live/broker/deployment/capital claims.

## Verdict Set

| StudySpec | Family | Verdict artifact | Judgement | Watch/candidate budget impact | Primary blocker summary |
| --- | --- | --- | --- | ---: | --- |
| `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | `reviewer_verdict_sspec_69c22ec5847395ac8e81b5b6.json` | `INCONCLUSIVE` | 0 | Unlocked VWAP/session FeaturePack, unresolved `15m` label pack, P23 timing and label flags. |
| `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | `reviewer_verdict_sspec_aff70fcbc4b7ff226fcc8149.json` | `INCONCLUSIVE` | 0 | Unlocked VWAP/session FeaturePack, active-session final aggregate boundary unresolved, P23 timing and label flags. |
| `sspec_267cc052e37668339c38d179` | `regime` | `reviewer_verdict_sspec_267cc052e37668339c38d179.json` | `INCONCLUSIVE` | 0 | Missing locked trendiness and activation binding, source probe arms rejected in P22 context, P23 timing and label flags. |
| `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | `reviewer_verdict_sspec_27bf1262b0bd23d27191cc86.json` | `INCONCLUSIVE` | 0 | Objective trigger binding unresolved, thin subsegments unresolved, P23 timing and label flags. |
| `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | `reviewer_verdict_sspec_02c400a561891171a33c0c66.json` | `INCONCLUSIVE` | 0 | Objective trigger binding unresolved, thin subsegments unresolved, P23 timing and label flags. |
| `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | `reviewer_verdict_sspec_9f6f741192a4b534f06e51c0.json` | `INCONCLUSIVE` | 0 | Missing locked BBO FeaturePack, RTH comparator gap, P23 timing and label flags. |

Survivor count for P25 review: `6`. Watch/candidate count from P25 verdicts:
`0`, within the downstream informational cap of `<=2`. P28 owns any allowed
research-state decision and cap enforcement.

## Shared Evidence References

- Diagnostics: `research/futures_core_alpha_pilot_v1/diagnostics_reports/**`
- Cost and thin-session stress:
  `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`
- Session/horizon/regime matrix:
  `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`
- No-lookahead/leakage/same-bar audit:
  `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`
- Variant-budget audit:
  `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`
- Independence basis:
  `research/futures_core_alpha_pilot_v1/queue/separation_of_duties.md` and
  `research/futures_core_alpha_pilot_v1/queue/role_assignment_map.md`

## Boundary Notes

- `zero_cost` remains diagnostic-only policy context and is not a favorable
  evidence basis.
- Fragile `1m` and `3m` horizon evidence, ETH/pre_RTH/post_RTH thin-session
  evidence, narrow-cell gaps, and proxy-only cost/capacity support are carried
  as limitations.
- No verdict in this directory is a promotion, FactorLibrary entry, Reference
  validation, trading approval, broker action, deployment action, or phase
  review verdict.
