# FUTCORE-P25 Reviewer Verdicts

`FUTCORE-P25` records independent statistical reviewer verdicts for the six
P22-P24 non-rejected consolidation survivors. All six verdicts are
`INCONCLUSIVE` and cite upstream evidence by path. They do not promote any idea,
assign a PromotionDecision, or make paper/live/broker/deployment/capital claims.

## Verdict Summary

| StudySpec | Family | Judgement | Evidence refs |
| --- | --- | --- | --- |
| `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | `INCONCLUSIVE` | diagnostics, P21 cost/thin-session report, P22 matrix, P23 audit, P24 audit |
| `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | `INCONCLUSIVE` | diagnostics, P21 cost/thin-session report, P22 matrix, P23 audit, P24 audit |
| `sspec_267cc052e37668339c38d179` | `regime` | `INCONCLUSIVE` | diagnostics, P21 cost/thin-session report, P22 matrix, P23 audit, P24 audit |
| `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | `INCONCLUSIVE` | diagnostics, P21 cost/thin-session report, P22 matrix, P23 audit, P24 audit |
| `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | `INCONCLUSIVE` | diagnostics, P21 cost/thin-session report, P22 matrix, P23 audit, P24 audit |
| `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | `INCONCLUSIVE` | diagnostics, P21 cost/thin-session report, P22 matrix, P23 audit, P24 audit |

Verdict artifacts live under
`research/futures_core_alpha_pilot_v1/reviewer_verdicts/`. The P25
watch/candidate budget impact is `0`; P28 remains responsible for downstream
allowed research-state recording and cap enforcement.

## Shared Basis

- P21 records required nonzero cost profile coverage for `base`, `stress_1`,
  `stress_2`, and `double_cost`, while preserving cost-gradient,
  thin-session, and BBO proxy limitations.
- P22 carries fragile `1m` and `3m` horizon status, ETH/pre_RTH/post_RTH
  research-only status, unresolved `15m` coverage, and no robust narrow-cell
  survivor support.
- P23 flags every reviewed survivor for unresolved timing and label-pack
  dependencies; same-bar optimism is not flagged in the committed audit.
- P24 records no over-budget execution, locked-test tuning, or repeated OOS
  selection, while preserving evidence-format warnings where source diagnostics
  did not expose explicit observed counts.
- P06 separation-of-duties records the statistical reviewer as independent of
  the drafter, critic, feature/label implementers, diagnostics runner,
  no-lookahead auditor, budget auditor, and downstream librarian.

## Boundaries

The verdicts are evidence-quality judgements only. They are value-free and cite
paths, ids, roles, statuses, flags, and limitations. They do not contain raw
provider payloads, row-level market values, feature values, label values,
runtime values, Parquet/Arrow/Feather payloads, local databases, logs, caches,
secrets, model binaries, or run-local artifacts.
