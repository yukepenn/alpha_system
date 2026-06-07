# CLOSEOUT - ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P30`  
Closeout date: 2026-06-07  
Autonomous closeout verdict: `BLOCKED` (local-only `verify.py --all` failure)  
**Final verdict (coordinator resolution): `COMPLETE_WITH_WARNINGS`** — the four
failing tests are CI-green, pre-existing on `main`, and environmental; accepted
as documented out-of-scope exceptions. See
`CLOSEOUT_COORDINATOR_RESOLUTION.md`.

This closeout audits already-merged campaign evidence. It does not run new
research, alter prior evidence, assign a phase review verdict, create a PR,
merge, stage, commit, call a reviewer, or make any paper/live/broker,
production, capital-allocation, profitability, or tradability claim.

## Verdict Basis

The campaign evidence chain is audited, but the terminal closeout is blocked
because the required broad verifier failed:

- `python tools/verify.py --all` exited `1` with 4 failed tests and 2840 passed;
- the failing tests are outside the P30 markdown closeout scope, and this phase
  authorizes no source or test repairs;
- all 31 phase handoffs through `FUTCORE-P30` exist or are produced by this
  phase, but the campaign cannot be declared complete while this required check
  is failing;
- all 23 campaign-level acceptance criteria have cited evidence or a documented
  non-blocking warning;
- 6 of 7 gate-level requirements have cited evidence or a documented
  non-blocking warning; `handoff_and_closeout` is blocked on the verifier
  failure;
- P28 promotion states are limited to `REJECT` and `INCONCLUSIVE`;
- P28 records `0` `WATCH` and `0` `CANDIDATE_RESEARCH`, within the cap of `2`;
- P25 records independent statistical reviewer verdicts for the six
  evidence-stage survivors, all `INCONCLUSIVE`;
- P29 records concrete downstream failure-mode handoffs;
- artifact-policy checks recorded by this executor found no tracked `runs/**`
  paths and no tracked heavy data globs;
- `python tools/hooks/canary_runner.py` passed; exact validation results are
  recorded below.

The warnings are not favorable-evidence findings. They preserve the limits and
gaps surfaced by the pilot. The blocker is the failed broad verifier.

## Blocking Finding

| Finding | Scope | Citation | Disposition |
| --- | --- | --- | --- |
| `CB-P30-01` | Required terminal validation | `python tools/verify.py --all`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md` | Blocked. The command failed with 4 tests failing: `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`, `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`, `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`, and `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`. |

## Warnings

| Warning | Scope | Citation | Disposition |
| --- | --- | --- | --- |
| `CW-P30-01` | Cost and thin-session diagnostics | `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md` | Cost profile names exist, but cross-market cost reports are zero-fill after missingness rejection, several reports use BBO fallback/proxy language, and thin-session/RTH comparator gaps remain limitations. |
| `CW-P30-02` | Timing, label, and cross-instrument audit | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md` | P23 carries `LOOKAHEAD`, `LABEL_LEAKAGE`, and `CROSS_INSTRUMENT_AVAILABILITY` flags where locked evidence is unresolved. P25/P28 preserve those ideas as `INCONCLUSIVE` or `REJECT`, not as watch/candidate outcomes. |
| `CW-P30-03` | Variant-budget evidence format | `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md` | No over-budget execution, locked-test tuning, or repeated OOS selection was detected, but several pre-grid blocked reports lack explicit observed-variant-count fields. |
| `CW-P30-04` | Executor-side git/review limits | `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md` | The executor prompt forbids `git status`, `git diff`, staging, commit, push, Claude, reviewer execution, PR, merge, and phase PASS marking. Ralph owns the authoritative staged-set audit, review, verdict parsing, PR/CI, merge, and final done-check. |

## Campaign-Level Acceptance Audit

| # | Criterion | Result | Satisfying artifact citations |
| ---: | --- | --- | --- |
| 1 | Campaign contract completeness | `SATISFIED` | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/PHASE_PLAN.md`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACCEPTANCE.md`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RUNBOOK.md`; `ACTIVE_CAMPAIGN.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P00.md`. No campaign-local `ACTIVE_CAMPAIGN.md` exists. |
| 2 | Preflight readiness | `SATISFIED` | `docs/futures_core_alpha_pilot/PREFLIGHT.md`; `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P01.md`. Final broad verification is recorded below. |
| 3 | DatasetVersion / FeaturePack / LabelPack lock | `SATISFIED` | `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`; `docs/futures_core_alpha_pilot/INPUT_PACK.md`; `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P03.md`. |
| 4 | Parquet value access | `SATISFIED` | `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`; `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`; `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md`. These artifacts record registry-resolved Parquet references by id/hash only. |
| 5 | `session_label` guard | `SATISFIED` | `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`; `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`; `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; final canary result below. |
| 6 | Runtime smoke | `SATISFIED` | `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/INDEX.md`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/README.md`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/INDEX.md`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/INDEX.md`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/INDEX.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20.md`. |
| 7 | Agent Factory preflight | `SATISFIED` | `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`; `research/futures_core_alpha_pilot_v1/queue/research_queue.md`; `research/futures_core_alpha_pilot_v1/queue/role_assignment_map.md`; `research/futures_core_alpha_pilot_v1/queue/separation_of_duties.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P06.md`. |
| 8 | AlphaSpec batch quality | `SATISFIED` | `research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md`; `research/futures_core_alpha_pilot_v1/alpha_specs/BUDGET_AUDIT.md`; `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/`; `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/`; `research/futures_core_alpha_pilot_v1/alpha_specs/regime/`; `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/`; `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P07.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P11.md`. |
| 9 | StudySpec quality | `SATISFIED` | `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`; `research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`; `research/futures_core_alpha_pilot_v1/study_specs/sspec_*.json`; `docs/futures_core_alpha_pilot/STUDY_SPECS.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14.md`. |
| 10 | Family budget adherence | `SATISFIED` | `research/futures_core_alpha_pilot_v1/alpha_specs/BUDGET_AUDIT.md`; `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`; `docs/futures_core_alpha_pilot/CRITIQUE_AND_BUDGET.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P12.md`. The 15 percent families carry the recorded integer-rounding note. |
| 11 | Diagnostics outputs | `SATISFIED_WITH_WARNINGS` | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/**`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/**`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/**`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/**`; `docs/futures_core_alpha_pilot/diagnostics/*.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20.md`. Warnings are recorded in `CW-P30-01` and `CW-P30-02`. |
| 12 | Cost stress | `SATISFIED_WITH_WARNINGS` | `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`; `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `docs/futures_core_alpha_pilot/COST_MODEL.md`; `docs/futures_core_alpha_pilot/COST_SENSITIVITY.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P04.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P21.md`. `zero_cost` is recorded as diagnostic-only and no promotion basis. |
| 13 | Thin-session stress | `SATISFIED_WITH_WARNINGS` | `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`; `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P21.md`. Thin-session evidence remains research-only and limitation-bearing. |
| 14 | Session / horizon / regime matrix | `SATISFIED_WITH_WARNINGS` | `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `docs/futures_core_alpha_pilot/MATRIX.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P22.md`. No stable favorable narrow-cell-only survivor is recorded. |
| 15 | No-lookahead / leakage audit | `SATISFIED_WITH_WARNINGS` | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `docs/futures_core_alpha_pilot/NO_LOOKAHEAD_AUDIT.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; final canary result below. Same-bar optimism is not detected; unresolved timing, label, and cross-instrument dependencies are carried as flags. |
| 16 | TrialLedger completeness | `SATISFIED` | `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json`; `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/*.json`; `docs/futures_core_alpha_pilot/LEDGERS.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P26.md`. |
| 17 | RejectedIdeaLedger completeness | `SATISFIED` | `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/*.json`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P26.md`. Duplicate-exposure hints are recorded. |
| 18 | EvidenceDraft quality | `SATISFIED_WITH_WARNINGS` | `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`; `research/futures_core_alpha_pilot_v1/evidence/survivors.json`; `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/*.json`; `research/futures_core_alpha_pilot_v1/evidence/factor_cards/*.json`; `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/*.json`; `docs/futures_core_alpha_pilot/EVIDENCE.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P27.md`. P27 packages six `INCONCLUSIVE` evidence-stage survivors as not validated and not tradable. |
| 19 | Reviewer verdict independence | `SATISFIED` | `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/reviewer_verdict_*.json`; `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; `research/futures_core_alpha_pilot_v1/queue/separation_of_duties.md`; `research/futures_core_alpha_pilot_v1/queue/role_assignment_map.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P25.md`. |
| 20 | Promotion boundary | `SATISFIED` | `research/futures_core_alpha_pilot_v1/promotion/INDEX.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`; `research/futures_core_alpha_pilot_v1/promotion/decisions.json`; `research/futures_core_alpha_pilot_v1/promotion/decisions/*.json`; `docs/futures_core_alpha_pilot/PROMOTION_DECISIONS.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28.md`. States are 4 `REJECT`, 6 `INCONCLUSIVE`, 0 `WATCH`, and 0 `CANDIDATE_RESEARCH`. |
| 21 | DAG scheduler consistency | `SATISFIED` | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/PHASE_PLAN.md`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml`; `ACTIVE_CAMPAIGN.md`; phase handoffs under `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`. `ACTIVE_CAMPAIGN.md` is updated here only because P30 is `must_run_alone` closeout. |
| 22 | Artifact policy | `SATISFIED_WITH_WARNINGS` | `research/futures_core_alpha_pilot_v1/**` value-free evidence paths above; final `git ls-files runs` and heavy-glob checks below; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md`. The executor did not run forbidden staging/status/diff commands; Ralph owns staged-set confirmation. |
| 23 | Closeout handoff quality | `SATISFIED` | `research/futures_core_alpha_pilot_v1/downstream_handoffs/README.md`; `research/futures_core_alpha_pilot_v1/downstream_handoffs/validation_governance_v1.md`; `research/futures_core_alpha_pilot_v1/downstream_handoffs/factor_library_v1.md`; `research/futures_core_alpha_pilot_v1/downstream_handoffs/strategy_reference_validation_v1.md`; `docs/futures_core_alpha_pilot/DOWNSTREAM_HANDOFFS.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P29.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md`. |

## Gate-Level Acceptance Audit

| Gate | Result | Satisfying artifact citations |
| --- | --- | --- |
| `bootstrap_and_inputs` | `SATISFIED` | `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P00.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P06.md`; `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`; `research/futures_core_alpha_pilot_v1/scope/scope_contract.md`; `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`; `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`; `research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md`; `research/futures_core_alpha_pilot_v1/queue/research_queue.md`. |
| `alpha_spec_batches` | `SATISFIED` | `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P07.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P11.md`; `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/`; `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/`; `research/futures_core_alpha_pilot_v1/alpha_specs/regime/`; `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/`; `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/`. |
| `spec_audit_and_packs` | `SATISFIED` | `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P12.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15.md`; `research/futures_core_alpha_pilot_v1/alpha_specs/BUDGET_AUDIT.md`; `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`; `research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`; `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`; `research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md`; `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json`. |
| `family_diagnostics` | `SATISFIED_WITH_WARNINGS` | `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20.md`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/**`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/**`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/**`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/**`. Diagnostics are value-free and no promotion occurs in this gate. |
| `consolidation_and_audits` | `SATISFIED_WITH_WARNINGS` | `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P21.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24.md`; `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`. |
| `evidence_ledger_promotion` | `SATISFIED_WITH_WARNINGS` | `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P25.md` through `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28.md`; `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`. The warnings are inherited evidence limitations; promotion states remain bounded. |
| `handoff_and_closeout` | `BLOCKED` | `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P29.md`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md`; `research/futures_core_alpha_pilot_v1/downstream_handoffs/README.md`; `docs/futures_core_alpha_pilot/DOWNSTREAM_HANDOFFS.md`; this `CLOSEOUT.md`; `research/futures_core_alpha_pilot_v1/closeout/README.md`; `docs/futures_core_alpha_pilot/CLOSEOUT.md`; validation results below. The closeout audit artifacts exist, but the required `python tools/verify.py --all` command failed. Ralph-owned review and merge steps remain pending outside this executor. |

## Prohibited Shortcut Audit

| Shortcut family | Result | Evidence |
| --- | --- | --- |
| Raw provider reads or external provider API calls | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`; `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`; `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`; phase handoffs under `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`. |
| Arbitrary Parquet path reading or JSONL research-scale scans | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`; `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`; diagnostics reports under `research/futures_core_alpha_pilot_v1/diagnostics_reports/**`. |
| Diagnostics without StudySpecs or implementation without AlphaSpecs | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/alpha_specs/BUDGET_AUDIT.md`; `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`; `research/futures_core_alpha_pilot_v1/diagnostics_reports/**`. |
| Ungoverned new feature or label | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md`; `research/futures_core_alpha_pilot_v1/feature_requests/*.json`; `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json`; `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15.md`. |
| Missing cost stress or zero-cost promotion basis | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`; `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`. |
| Missing session split, RTH/ETH split, or session x horizon matrix | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`. |
| Missing VariantBudget, locked-test tuning, or repeated OOS selection | `NOT_DETECTED_WITH_WARNINGS` | `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`. Evidence-format warnings are recorded but no over-budget or locked-test tuning finding exists. |
| Rejected ideas omitted or duplicate exposure hidden | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`. |
| Self-review, self-promotion, or watch/candidate without reviewer verdict | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/queue/separation_of_duties.md`; `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; `research/futures_core_alpha_pilot_v1/promotion/INDEX.md`. |
| Strategy Reference, FactorLibrary V1, AlphaBook, paper/live/broker, production, capital, profitability, or tradability scope creep | `NOT_DETECTED` | `research/futures_core_alpha_pilot_v1/downstream_handoffs/README.md`; `docs/futures_core_alpha_pilot/DOWNSTREAM_HANDOFFS.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`; `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`. |
| Heavy/raw/value/DB data committed or `runs/**` tracked | `NOT_DETECTED` | Final `git ls-files runs` and heavy-glob results below; artifact-policy boundary statements across research reports and handoffs. |
| Parallel path collision or unauthorized `ACTIVE_CAMPAIGN.md` writes | `NOT_DETECTED` | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/PHASE_PLAN.md`; `ACTIVE_CAMPAIGN.md`; P30 is the must-run-alone coordinator-owned closeout exception. |

## Semantic Done-Check

Executor-local semantic done-check outcome: `BLOCKED`.

The check reconciled the campaign goal, the 23 campaign-level acceptance
criteria, the 7 gate-level criteria, the prohibited-shortcut list, the P25
independent statistical review record, the P28 promotion boundary, P29
downstream handoffs, artifact-policy checks, README/coordinator snapshots, and
the requested local validation commands. It found one blocker: the required
`python tools/verify.py --all` command failed. It retains the warnings listed
above and does not substitute for the fresh Yellow-lane review that Ralph must
route before merge.

## Validation Results

Validation was run from the repository root. The exact command outcomes are also
recorded in `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md`.

| Command | Outcome |
| --- | --- |
| `python tools/verify.py --all` | Failed; exit code `1`; summary: `4 failed, 2840 passed in 48.74s`. Failures: `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture` expected a list and received a tuple; `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture` expected a list and received a tuple; `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline` found `ohlcv_rows` empty; `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only` expected `RuntimeCacheStorageKind.RUN_ARTIFACTS` and received `RuntimeCacheStorageKind.ALPHA_DATA_ROOT`. |
| `python tools/hooks/canary_runner.py` | Passed; exit code `0`; output ended with `All Frontier canaries passed.` |
| `test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md` | Passed; exit code `0`; no output. |
| `grep -q "ALPHA_FUTURES_CORE_ALPHA_PILOT_V1" ACTIVE_CAMPAIGN.md` | Passed; exit code `0`; no output. |
| `git ls-files runs` | Passed; exit code `0`; output empty. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed; exit code `0`; output empty. |
| `git status --short` | Not run by Codex: explicitly forbidden by the executor prompt. |
| `git diff --cached --name-only` | Not run by Codex: explicitly forbidden by the executor prompt; no files were staged by Codex. |

## Closeout Boundary

This closeout preserves the campaign boundary: research evidence only, no
strategy readiness, no paper/live readiness, no broker or order workflow, no
production deployment, no capital allocation, no profitability claim, no
tradability claim, no FactorLibrary V1 promotion, and no Strategy Reference
validation.
