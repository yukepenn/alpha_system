# FUTCORE-P24 Variant Budget Audit

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P24`  
Audit type: value-free bounded-grid / VariantBudget reconciliation  
Generated from committed `FUTCORE-P14` through `FUTCORE-P23` evidence only.

This audit reconciles declared StudySpec `VariantBudget` limits against the
variant-grid evidence recorded by family diagnostics and consolidation reports.
It does not rerun diagnostics, read raw or row-level data, edit StudySpecs,
select ideas, promote ideas, create a reviewer verdict, or make any paper/live,
broker, deployment, production, capital-allocation, profitability, or
tradability claim.

`zero_cost` remains diagnostic-only policy context and is never a selection,
survival, promotion, watch, candidate, or favorable-evidence basis.

## Sources Consulted

| Source | Role |
| --- | --- |
| `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md` and `study_specs/sspec_*.json` | Declared StudySpec ids, AlphaSpec ids, family seats, variant axes, variant budgets, split policy, and stopping rules. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**` | P16 cross-market diagnostic status and absence of variant-cell execution after alignment rejection. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/**` | P17 VWAP/session diagnostic status, signal-probe blocking, and no-OOS contamination policy. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/**` | P18 explicit `observed_variant_count`, variant cells, and no post-diagnostic expansion. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/**` | P19 liquidity/PA diagnostic status and unresolved objective-trigger cells without pilot-side recomputation. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/**` | P20 explicit `observed_variant_count`, variant cells, and respected budget status. |
| `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md` | P21 cost-profile consolidation and zero-cost boundary. |
| `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md` | P22 survivor/rejected-source set and fixed reporting-slice consolidation. |
| `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md` | P23 temporal audit set and no-promotion boundary. |
| `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml` | Research-budget and anti-overfit policies. |

Run-local `runs/**` files were not consulted or copied.

## Count Method

The P14 StudySpec pack states that every StudySpec declares `variant_budget: 4`.
Each StudySpec has two predeclared axes with two values each, yielding at most
four parameter combinations. P14 also states that sessions, horizons,
instruments, and cost profiles are fixed reporting slices and must not multiply
the variant grid.

`actual_count` below means explicit variant-grid cells exercised or recorded in
the committed diagnostics evidence:

- If a report records `observed_variant_count` or `variant_cells`, that field is
  used directly.
- If a report records the StudySpec as rejected or blocked before signal, gate,
  or trigger variant execution, and records no `variant_cells` or
  `observed_variant_count`, `actual_count` is `0` explicit variant-grid cells.
- Fixed session x horizon x cost-profile x regime slices are excluded from
  `actual_count` under the P14 count rule.

The absence of an explicit observed-count field in a pre-grid blocked report is
recorded as a `WARN`, not as an over-budget finding, because the committed
evidence records no post-diagnostic expansion and no selection action.

## Per-Study Reconciliation

| StudySpec | Family | Declared budget | Actual count | Within budget | Delta | Disposition | Note |
| --- | --- | ---: | ---: | --- | ---: | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `cross_market` | 4 | 0 | true | -4 | `WARN` | P16 rejected before variant-grid execution because aligned ES/NQ/RTY snapshots were unavailable; report records `study_spec.variant_budget=4` but no explicit observed-count field. |
| `sspec_c671fbeeb143512cbc03bc5b` | `cross_market` | 4 | 0 | true | -4 | `WARN` | P16 rejected before variant-grid execution because aligned ES/NQ/RTY snapshots were unavailable; no post-diagnostic variant expansion is recorded. |
| `sspec_90b28233d828128664588a9a` | `cross_market` | 4 | 0 | true | -4 | `WARN` | P16 rejected before variant-grid execution with unresolved `15m` label binding also recorded; no explicit observed-count field or expansion is recorded. |
| `sspec_7c8fb13628843890c171b122` | `cross_market` | 4 | 0 | true | -4 | `WARN` | P16 rejected before variant-grid execution because aligned ES/NQ/RTY snapshots were unavailable; no explicit observed-count field or expansion is recorded. |
| `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | 4 | 0 | true | -4 | `WARN` | P17 records no locked running VWAP/reclaim FeaturePack and no signal-probe execution; no explicit observed-count field is present. |
| `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | 4 | 0 | true | -4 | `WARN` | P17 records no locked completed ETH VWAP / first-RTH running VWAP FeaturePack and no signal-probe execution; no explicit observed-count field is present. |
| `sspec_267cc052e37668339c38d179` | `regime` | 4 | 4 | true | 0 | `PASS` | P18 records `declared_variant_budget=4`, `observed_variant_count=4`, four variant cells, `variant_budget_exceeded=false`, and `post_diagnostic_variant_expansion=false`. |
| `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | 4 | 0 | true | -4 | `WARN` | P19 records unresolved objective-rule trigger cells and `pilot_side_recomputation_performed=false`; no explicit observed-count field or variant expansion is recorded. |
| `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | 4 | 0 | true | -4 | `WARN` | P19 records unresolved objective-rule trigger cells and `pilot_side_recomputation_performed=false`; no explicit observed-count field or variant expansion is recorded. |
| `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | 4 | 4 | true | 0 | `PASS` | P20 records `observed_variant_count=4`, `variant_budget=4`, `variant_budget_status=RESPECTED`, and four BBO variant cells blocked by missing locked BBO FeaturePack. |

No StudySpec exceeded its declared VariantBudget in the committed evidence.

## Locked-Test Tuning Check

All ten StudySpecs bind to `development_partition` in the P03/P14 input pack and
carry the P14 freeze policy: StudySpec ids, session-horizon matrix, cost
profiles, no-lookahead targets, and variant budget were frozen before
diagnostics. The P14 policy forbids locked-test tuning, repeated OOS selection,
and post-diagnostic variant expansion.

| StudySpec | Selection basis found | Locked-test touch | Evidence note |
| --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | none; P16 diagnostic rejection | false | No promotion or selection decision made; no locked-test partition reference found. |
| `sspec_c671fbeeb143512cbc03bc5b` | none; P16 diagnostic rejection | false | No promotion or selection decision made; no locked-test partition reference found. |
| `sspec_90b28233d828128664588a9a` | none; P16 diagnostic rejection | false | No promotion or selection decision made; no locked-test partition reference found. |
| `sspec_7c8fb13628843890c171b122` | none; P16 diagnostic rejection | false | No promotion or selection decision made; no locked-test partition reference found. |
| `sspec_69c22ec5847395ac8e81b5b6` | none; P17 diagnostic `INCONCLUSIVE` | false | Signal probe not executed; runtime contamination policy records development partition with no OOS selection. |
| `sspec_aff70fcbc4b7ff226fcc8149` | none; P17 diagnostic `INCONCLUSIVE` | false | Signal probe not executed; runtime contamination policy records development partition with no OOS selection. |
| `sspec_267cc052e37668339c38d179` | fixed P14 axes; P18 diagnostic `INCONCLUSIVE` | false | P18 records four predeclared cells, no post-diagnostic expansion, and no return-magnitude grid search. |
| `sspec_27bf1262b0bd23d27191cc86` | none; P19 diagnostic `INCONCLUSIVE` | false | Objective triggers unresolved; pilot-side recomputation and selection were not performed. |
| `sspec_02c400a561891171a33c0c66` | none; P19 diagnostic `INCONCLUSIVE` | false | Objective triggers unresolved; pilot-side recomputation and selection were not performed. |
| `sspec_9f6f741192a4b534f06e51c0` | fixed P14 axes; P20 diagnostic `INCONCLUSIVE` | false | P20 records four predeclared blocked BBO variant cells and no promotion basis. |

No locked-test tuning was detected.

## Repeated-OOS Selection Check

No committed report records a locked-test, held-out, or OOS selection event.
P17 explicitly records `development_partition_no_oos_selection` for its runtime
contamination policy, and the other family reports record diagnostic rejection
or inconclusive status without promotion, watch, candidate, ranking, or
selection decisions.

| StudySpec | OOS selection lineage | Repeated same-OOS selection detected |
| --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | none; rejected diagnostic source retained by P22/P23 | false |
| `sspec_c671fbeeb143512cbc03bc5b` | none; rejected diagnostic source retained by P22/P23 | false |
| `sspec_90b28233d828128664588a9a` | none; rejected diagnostic source retained by P22/P23 | false |
| `sspec_7c8fb13628843890c171b122` | none; rejected diagnostic source retained by P22/P23 | false |
| `sspec_69c22ec5847395ac8e81b5b6` | none; P17 diagnostic only, no OOS selection | false |
| `sspec_aff70fcbc4b7ff226fcc8149` | none; P17 diagnostic only, no OOS selection | false |
| `sspec_267cc052e37668339c38d179` | none; P18 diagnostic only, fixed predeclared cells | false |
| `sspec_27bf1262b0bd23d27191cc86` | none; P19 diagnostic only, no trigger recomputation | false |
| `sspec_02c400a561891171a33c0c66` | none; P19 diagnostic only, no trigger recomputation | false |
| `sspec_9f6f741192a4b534f06e51c0` | none; P20 diagnostic only, fixed predeclared blocked cells | false |

No repeated selection on an identical OOS partition was detected.

## Family And Campaign Rollup

| Family | Campaign family budget | StudySpecs | Seat share | Declared variant cap | Explicit actual variant cells | Rollup |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `cross_market` | 0.40 | 4 | 0.40 | 16 | 0 | Seat budget aligned; diagnostics rejected before variant-grid execution. |
| `vwap_session` | 0.20 | 2 | 0.20 | 8 | 0 | Seat budget aligned; signal probes blocked before variant-grid execution. |
| `regime` | 0.15 | 1 | 0.10 | 4 | 4 | Integer seat share matches P14 rounding note; observed count equals cap. |
| `liquidity_pa` | 0.15 | 2 | 0.20 | 8 | 0 | Integer seat share matches P14 rounding note; trigger grid not executed. |
| `bbo_tradability` | 0.10 | 1 | 0.10 | 4 | 4 | Seat budget aligned; observed count equals cap. |
| **Total** | 1.00 | 10 | 1.00 | 40 | 8 | Approved StudySpec cap `<=10` held; explicit variant cells stay within declared total cap. |

Campaign policy reconciliation:

- `max_approved_alpha_specs: 10`: held with exactly 10 approved StudySpecs.
- `variant_budget_required: true`: held; every StudySpec declares
  `variant_budget: 4`.
- `family_budget_required: true`: held by the P14 family seat allocation and
  integer-rounding notes.
- `locked_test_tuning_forbidden: true`: no locked-test tuning detected.
- `no_repeated_selection_on_same_oos: true`: no OOS selection event detected.

## Findings

| Finding id | Severity | Scope | Disposition | Detail |
| --- | --- | --- | --- | --- |
| `VB-P24-W1` | WARN | P16 cross-market reports | noted | Four cross-market reports expose declared `variant_budget` but no explicit `observed_variant_count`; they are still within budget because diagnostics rejected before variant-grid execution and no expansion is recorded. |
| `VB-P24-W2` | WARN | P17 VWAP reports | noted | Two VWAP reports expose declared `variant_budget` but no explicit `observed_variant_count`; signal-probe execution was blocked by missing locked VWAP FeaturePacks. |
| `VB-P24-W3` | WARN | P19 liquidity/PA reports | noted | Two liquidity/PA reports expose unresolved trigger cells and no pilot-side recomputation, but no explicit `observed_variant_count`; no expansion is recorded. |

No `FAIL` finding was detected for over-budget execution, locked-test tuning, or
repeated OOS selection. The WARN findings are evidence-format gaps for future
diagnostics hardening and are not favorable-evidence claims.

## Boundary Confirmations

- No diagnostics were rerun for this audit.
- No StudySpec, AlphaSpec, diagnostics report, runtime primitive, feature,
  label, data, broker, CLI, or consumed `src/alpha_system/**` primitive was
  edited by this audit.
- No raw/canonical market data, provider response, feature value, label value,
  Parquet, SQLite, DB, cache, log, model binary, or run-local artifact is
  included.
- No `runs/**` path is a commit-eligible artifact.
- No Claude call, reviewer run, `review.md`, `verdict.json`, PR, merge,
  staging, commit, push, or phase PASS marking is created by this audit.
