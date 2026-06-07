# Variant Budget Audit

This page mirrors the value-free FUTCORE-P24 bounded-grid audit at
`research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`.
It records ids, counts, paths, statuses, and dispositions only. It does not
rerun diagnostics, read raw or row-level data, select ideas, promote ideas,
create a reviewer verdict, or make any paper/live, broker, deployment,
production, capital-allocation, profitability, or tradability claim.

## Summary

Every approved `FUTCORE-P14` StudySpec declares `variant_budget: 4`. The P14
count rule states that the two predeclared axes create at most four parameter
combinations, while sessions, horizons, instruments, and cost profiles are fixed
reporting slices and do not multiply the variant grid.

No StudySpec exceeded its declared VariantBudget in the committed P16-P22
diagnostic and consolidation evidence. No locked-test tuning was detected. No
repeated selection on the same OOS partition was detected.

The audit records WARN findings for families whose diagnostics were rejected or
blocked before variant-grid execution and therefore did not expose an explicit
`observed_variant_count` field. Those WARNs are evidence-format gaps only; they
are not favorable-evidence claims.

## Per-Study Reconciliation

| StudySpec | Family | Declared budget | Actual count | Within budget | Delta | Disposition |
| --- | --- | ---: | ---: | --- | ---: | --- |
| `sspec_dde3e64667fe158f9bad527d` | `cross_market` | 4 | 0 | true | -4 | `WARN` |
| `sspec_c671fbeeb143512cbc03bc5b` | `cross_market` | 4 | 0 | true | -4 | `WARN` |
| `sspec_90b28233d828128664588a9a` | `cross_market` | 4 | 0 | true | -4 | `WARN` |
| `sspec_7c8fb13628843890c171b122` | `cross_market` | 4 | 0 | true | -4 | `WARN` |
| `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | 4 | 0 | true | -4 | `WARN` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | 4 | 0 | true | -4 | `WARN` |
| `sspec_267cc052e37668339c38d179` | `regime` | 4 | 4 | true | 0 | `PASS` |
| `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | 4 | 0 | true | -4 | `WARN` |
| `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | 4 | 0 | true | -4 | `WARN` |
| `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | 4 | 4 | true | 0 | `PASS` |

`actual_count` is the explicit variant-grid cell count recorded or reached in
committed diagnostics. Fixed reporting slices are excluded under the P14 count
rule. Cross-market, VWAP/session, and liquidity/PA reports are within budget
because they were rejected or blocked before variant-grid execution and record no
post-diagnostic expansion.

## Rollup

| Family | StudySpecs | Declared variant cap | Explicit actual variant cells | Rollup |
| --- | ---: | ---: | ---: | --- |
| `cross_market` | 4 | 16 | 0 | P14 family seat budget aligned; P16 rejected before variant-grid execution. |
| `vwap_session` | 2 | 8 | 0 | P14 family seat budget aligned; P17 signal probes blocked before variant-grid execution. |
| `regime` | 1 | 4 | 4 | P18 observed count equals declared cap. |
| `liquidity_pa` | 2 | 8 | 0 | P19 trigger grid not executed; no pilot-side recomputation. |
| `bbo_tradability` | 1 | 4 | 4 | P20 observed count equals declared cap. |
| **Total** | 10 | 40 | 8 | Approved cap `<=10` and declared variant total cap both held. |

## Anti-Overfit Checks

All ten StudySpecs bind to `development_partition` and carry the P14 freeze
policy forbidding locked-test tuning, repeated OOS selection, and
post-diagnostic variant expansion. P17 explicitly records
`development_partition_no_oos_selection`; the other family reports record
diagnostic rejection or inconclusive status without promotion, watch, candidate,
ranking, or selection decisions.

No locked-test tuning or repeated OOS selection was detected.

## Findings

| Finding id | Severity | Detail |
| --- | --- | --- |
| `VB-P24-W1` | WARN | P16 cross-market reports lack explicit `observed_variant_count` fields after pre-grid rejection. |
| `VB-P24-W2` | WARN | P17 VWAP reports lack explicit `observed_variant_count` fields after signal-probe blocking. |
| `VB-P24-W3` | WARN | P19 liquidity/PA reports lack explicit `observed_variant_count` fields after trigger-grid blocking. |

No `FAIL` finding was detected for over-budget execution, locked-test tuning, or
repeated OOS selection.
