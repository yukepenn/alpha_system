# RISK_REGISTER — ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1

Severity/likelihood scale: Low / Med / High. Each risk lists detection,
mitigation, owner role, related phases, and the blocking condition that, if
triggered, halts merge/escalates per `campaign.yaml > stop_conditions`. The risk
emphasis is **substrate pollution**, not alpha ideation: wrong DatasetVersion,
wrong timestamp semantics, roll-splice contamination, BBO overclaim, cross-market
forward-fill, extended-horizon N_eff inflation, unsafe parallel registry writes,
committed Parquet/SQLite, and scope creep.

| ID | Risk | Sev | Likelihood | Owner | Related phases |
| --- | --- | --- | --- | --- | --- |
| R-001 | DatasetVersion acceptance not persisted | High | Med | Data Contract Auditor | P02 |
| R-002 | Existing data re-pulled unnecessarily | Med | Low | Data Contract Auditor | P02 |
| R-003 | Feature values materialized against wrong DatasetVersion | High | Med | Data Contract Auditor | P02,P06-P13,P14 |
| R-004 | Label values materialized against wrong DatasetVersion | High | Med | Data Contract Auditor | P02,P16-P20,P22 |
| R-005 | Registry identity not keystone-stable | High | Med | Feature/Label Engineer | P04,P14,P22 |
| R-006 | Hand-patched locks bypass official resolver | High | Low | No-Lookahead Auditor | P14,P22,P27 |
| R-007 | JSONL used as research-scale value store | Med | Med | Feature/Label Engineer | P05,P06-P20 |
| R-008 | Parquet / local SQLite accidentally committed | High | Med | Librarian | all materialization,P30 |
| R-009 | Roll-splice windows silently contaminate labels | High | High | No-Lookahead Auditor | P03,P16,P17,P21 |
| R-010 | Maintenance-crossing windows silently contaminate labels | High | Med | No-Lookahead Auditor | P03,P17,P18,P21 |
| R-011 | Approximate roll calendar overclaimed as provider-exact | Med | Med | Data Contract Auditor | P03,P21 |
| R-012 | Full roll execution engine scope creep | High | Low | Research Director | P03,P21 |
| R-013 | BBO top-book proxy overclaimed as execution truth | High | Med | Statistical Reviewer | P12,P19,P26 |
| R-014 | BBO FeaturePack timestamp semantics wrong | High | Med | No-Lookahead Auditor | P12,P14 |
| R-015 | Cross-market features forward-fill across instruments | High | Med | No-Lookahead Auditor | P13,P26 |
| R-016 | Cross-market available_ts discipline broken | High | Med | No-Lookahead Auditor | P13,P26 |
| R-017 | 240m / extended labels overstate N_eff | High | High | Statistical Reviewer | P17,P23,P25 |
| R-018 | Purge/embargo not wired into runtime | Med | Med | Diagnostics Runner | P24 |
| R-019 | N_eff missing or misleading | High | Med | Statistical Reviewer | P25,P28 |
| R-020 | Feature materialization becomes an unbounded feature zoo | Med | Med | Research Director | P05,P06-P13 |
| R-021 | Path labels too expensive or unstable | Med | Med | Label Engineer | P20 |
| R-022 | Materialization run not resumable / restart-safe | Med | Med | Feature/Label Engineer | P05,P06-P20 |
| R-023 | Coverage matrices omitted | Med | Low | Diagnostics Runner | P15,P23,P26 |
| R-024 | Core Pilot rerun becomes new alpha mining | High | Med | Research Director | P27,P28,P29 |
| R-025 | New alpha / profitability / tradability claims appear | High | Low | Statistical Reviewer | P28,P29 |
| R-026 | Multiple-testing engine attempted prematurely and incorrectly | Med | Med | Research Director | P24,P25,P31 |
| R-027 | FactorLibrary / AlphaBook scope creep | Med | Low | Research Director | P29,P32 |
| R-028 | Paper/live/broker scope creep | High | Low | Research Director | all |
| R-029 | Parallel materialization corrupts registry writes | High | Med | Diagnostics Runner | P02,P06-P14,P16-P22 |
| R-030 | Heavy local reports committed | Med | Low | Librarian | P15,P23,P26,P30 |
| R-031 | DatasetVersion accepted despite missing schema/symbol/year coverage | High | Med | Data Contract Auditor | P02 |
| R-032 | BBO missingness ignored in downstream diagnostics | Med | Med | Statistical Reviewer | P12,P26,P28 |
| R-033 | Cost-adjusted labels use stale fee/slippage assumptions | Med | Med | Label Engineer | P19 |
| R-034 | Validator accepts incomplete substrate because some families resolve | High | Med | Statistical Reviewer | P14,P22,P27 |
| R-035 | No clear handoff to Validation Governance / FactorLibrary | Med | Low | Research Director | P31,P32 |

## Detail

### R-001 — DatasetVersion acceptance not persisted
- **Sev/Likelihood**: High / Med · **Owner**: Data Contract Auditor · **Phases**: P02
- **Detection**: registry audit; Claude review
- **Mitigation**: P02 persists `ACCEPTED | ACCEPTED_WITH_WARNINGS | BLOCKED` + a coverage report per version; registered ≠ accepted.
- **Blocking**: materialization against a version without a persisted verdict → block merge / repair.

### R-002 — Existing data re-pulled unnecessarily
- **Sev/Likelihood**: Med / Low · **Owner**: Data Contract Auditor · **Phases**: P02
- **Detection**: import/network audit; Claude review
- **Mitigation**: `no_repull_unless_corrupt`; data is on disk; no external provider calls.
- **Blocking**: any external Databento/IBKR API call → stop and escalate.

### R-003 — Feature values materialized against wrong DatasetVersion
- **Sev/Likelihood**: High / Med · **Owner**: Data Contract Auditor · **Phases**: P02,P06-P13,P14
- **Detection**: `dataset_version_id` in registry record; resolver smoke; Claude review
- **Mitigation**: materialize only against accepted versions; record `dataset_version_id`; resolver-smoke ties locks to real Parquet.
- **Blocking**: feature lock resolves to the wrong/absent version → block merge / repair.

### R-004 — Label values materialized against wrong DatasetVersion
- **Sev/Likelihood**: High / Med · **Owner**: Data Contract Auditor · **Phases**: P02,P16-P20,P22
- **Detection**: registry `dataset_version_id`; label resolver smoke; Claude review
- **Mitigation**: as R-003 for labels.
- **Blocking**: label lock resolves to the wrong/absent version → block merge / repair.

### R-005 — Registry identity not keystone-stable
- **Sev/Likelihood**: High / Med · **Owner**: Feature/Label Engineer · **Phases**: P04,P14,P22
- **Detection**: P04 keystone preflight; content-hash check; Claude review
- **Mitigation**: enforce `dry-run preview == execute == registry record == lock == resolver`; content hash required.
- **Blocking**: identity mismatch across the chain → block merge / repair.

### R-006 — Hand-patched locks bypass official resolver
- **Sev/Likelihood**: High / Low · **Owner**: No-Lookahead Auditor · **Phases**: P14,P22,P27
- **Detection**: lock provenance audit; Claude review
- **Mitigation**: locks only via sanctioned tooling; resolver fails closed; no fuzzy-name fallback.
- **Blocking**: hand-patched lock or fuzzy resolver fallback → block merge / repair.

### R-007 — JSONL used as research-scale value store
- **Sev/Likelihood**: Med / Med · **Owner**: Feature/Label Engineer · **Phases**: P05,P06-P20
- **Detection**: value-store format audit; Claude review
- **Mitigation**: Parquet required at research scale; JSONL audit-tier only; SQLite metadata only.
- **Blocking**: research-scale store on JSONL → block merge / repair.

### R-008 — Parquet / local SQLite accidentally committed
- **Sev/Likelihood**: High / Med · **Owner**: Librarian · **Phases**: all materialization, P30
- **Detection**: `git ls-files` heavy globs; artifact audit; pre-merge gate
- **Mitigation**: explicit staging only; never-commit globs; P30 artifact audit.
- **Blocking**: any value/SQLite/heavy artifact staged or tracked → block merge / repair.

### R-009 — Roll-splice windows silently contaminate labels
- **Sev/Likelihood**: High / High · **Owner**: No-Lookahead Auditor · **Phases**: P03,P16,P17,P21
- **Detection**: P21 roll-window audit; roll guard tests; Claude review
- **Mitigation**: roll-splice guard applied at materialization (drop/truncate/flag/invalid); `roll_window` split; demonstrated on a known roll week (~100 splice points per series over 2018-2026).
- **Blocking**: a forward label books a contract-to-contract jump without the guard → block merge / rework.

### R-010 — Maintenance-crossing windows silently contaminate labels
- **Sev/Likelihood**: High / Med · **Owner**: No-Lookahead Auditor · **Phases**: P03,P17,P18,P21
- **Detection**: P21 maintenance-crossing invalidation matrix; tests; Claude review
- **Mitigation**: maintenance-crossing guard as a label materialization invariant; no position crosses the daily maintenance/trade-date break.
- **Blocking**: a forward/extended label silently crosses the maintenance break → block merge / rework.

### R-011 — Approximate roll calendar overclaimed as provider-exact
- **Sev/Likelihood**: Med / Med · **Owner**: Data Contract Auditor · **Phases**: P03,P21
- **Detection**: docs/claims scan; Claude review
- **Mitigation**: document the calendar as analytic/approximate; provider-internal splice not recoverable from the continuous series.
- **Blocking**: calendar presented as provider-exact splice truth → block merge / rework.

### R-012 — Full roll execution engine scope creep
- **Sev/Likelihood**: High / Low · **Owner**: Research Director · **Phases**: P03,P21
- **Detection**: scope/import audit; Claude review
- **Mitigation**: roll work is a leakage guard only; no live roll engine, IBKR mapping, or back-adjusted construction.
- **Blocking**: a roll execution engine / IBKR resolver appears → block merge / escalate.

### R-013 — BBO top-book proxy overclaimed as execution truth
- **Sev/Likelihood**: High / Med · **Owner**: Statistical Reviewer · **Phases**: P12,P19,P26
- **Detection**: claims scan; P26 BBO matrix; Claude review
- **Mitigation**: BBO-1m is a time-sampled + forward-filled tradability proxy; no passive-fill/queue/impact/execution claim.
- **Blocking**: BBO presented as execution truth → block merge / rework.

### R-014 — BBO FeaturePack timestamp semantics wrong
- **Sev/Likelihood**: High / Med · **Owner**: No-Lookahead Auditor · **Phases**: P12,P14
- **Detection**: `available_ts` audit; resolver smoke; Claude review
- **Mitigation**: enforce `available_ts` on every BBO feature; forward-fill semantics documented.
- **Blocking**: wrong/absent `available_ts` on BBO features → block merge / rework.

### R-015 — Cross-market features forward-fill across instruments
- **Sev/Likelihood**: High / Med · **Owner**: No-Lookahead Auditor · **Phases**: P13,P26
- **Detection**: cross-instrument availability audit; Claude review
- **Mitigation**: no cross-instrument forward-fill; per-instrument `available_ts` preserved.
- **Blocking**: forward-fill across instruments → block merge / rework.

### R-016 — Cross-market available_ts discipline broken
- **Sev/Likelihood**: High / Med · **Owner**: No-Lookahead Auditor · **Phases**: P13,P26
- **Detection**: no-lookahead audit on materialized cross-market values; Claude review
- **Mitigation**: re-verify the per-instrument availability assertion against real materialized values (the pilot's cross-market rejections depended on it).
- **Blocking**: broken per-instrument `available_ts` → block merge / rework.

### R-017 — 240m / extended labels overstate N_eff
- **Sev/Likelihood**: High / High · **Owner**: Statistical Reviewer · **Phases**: P17,P23,P25
- **Detection**: P25 N_eff report; overlap metadata; Claude review
- **Mitigation**: overlap-aware N_eff; rows ≠ independent samples; extended-horizon overlap surfaced.
- **Blocking**: extended labels reported without overlap-aware N_eff → block merge / rework.

### R-018 — Purge/embargo not wired into runtime
- **Sev/Likelihood**: Med / Med · **Owner**: Diagnostics Runner · **Phases**: P24
- **Detection**: P24 wiring smoke; import audit; Claude review
- **Mitigation**: wire `walk_forward_splits` + `apply_purge_embargo` into the diagnostics path, or ship a minimal callable path + precise handoff.
- **Blocking**: walk-forward neither wired nor handed off → block merge / repair.

### R-019 — N_eff missing or misleading
- **Sev/Likelihood**: High / Med · **Owner**: Statistical Reviewer · **Phases**: P25,P28
- **Detection**: P25 report; reviewer check; Claude review
- **Mitigation**: required N_eff reporting with rows-vs-effective distinction; available to Validation Governance.
- **Blocking**: overlapping labels reported without N_eff → block merge / rework.

### R-020 — Feature materialization becomes an unbounded feature zoo
- **Sev/Likelihood**: Med / Med · **Owner**: Research Director · **Phases**: P05,P06-P13
- **Detection**: scope/budget audit; Claude review
- **Mitigation**: reuse existing governed families only; no new feature zoo; batch plan bounds scope.
- **Blocking**: new features beyond existing governed families → block merge / rework.

### R-021 — Path labels too expensive or unstable
- **Sev/Likelihood**: Med / Med · **Owner**: Label Engineer · **Phases**: P20
- **Detection**: P20 compute/coverage report; Claude review
- **Mitigation**: materialize where feasible; flag expensive/unstable cases and record the bound (triple-barrier where feasible).
- **Blocking**: silent omission instead of a recorded bound → block merge / rework.

### R-022 — Materialization run not resumable / restart-safe
- **Sev/Likelihood**: Med / Med · **Owner**: Feature/Label Engineer · **Phases**: P05,P06-P20
- **Detection**: P05 batch plan; checkpoint audit; Claude review
- **Mitigation**: chunked, budgeted, checkpointed, restart-safe materialization.
- **Blocking**: unbounded/non-restart-safe materialization → block merge / repair.

### R-023 — Coverage matrices omitted
- **Sev/Likelihood**: Med / Low · **Owner**: Diagnostics Runner · **Phases**: P15,P23,P26
- **Detection**: file-existence checks; Claude review
- **Mitigation**: all six+ matrices required as gating inputs.
- **Blocking**: a required matrix omitted → block merge / repair.

### R-024 — Core Pilot rerun becomes new alpha mining
- **Sev/Likelihood**: High / Med · **Owner**: Research Director · **Phases**: P27,P28,P29
- **Detection**: scope audit; spec-diff vs Core Pilot; Claude review
- **Mitigation**: re-lock/re-run existing specs only; no new AlphaSpec batch; no tuning beyond original bounds.
- **Blocking**: a new AlphaSpec batch / broad search / tuning appears → block merge / escalate.

### R-025 — New alpha / profitability / tradability claims appear
- **Sev/Likelihood**: High / Low · **Owner**: Statistical Reviewer · **Phases**: P28,P29
- **Detection**: claims scan; Claude review
- **Mitigation**: allowed verdict states only; promotion evidence/cost-gated; no profitability/tradability language.
- **Blocking**: an unqualified alpha/profitability/tradability claim or forbidden state → block merge / escalate.

### R-026 — Multiple-testing engine attempted prematurely and incorrectly
- **Sev/Likelihood**: Med / Med · **Owner**: Research Director · **Phases**: P24,P25,P31
- **Detection**: scope audit; Claude review
- **Mitigation**: ship N_eff inputs only; full correction engine handed off to Validation Governance.
- **Blocking**: a full multiple-testing/DSR/PBO/PSR engine implemented here → block merge / escalate.

### R-027 — FactorLibrary / AlphaBook scope creep
- **Sev/Likelihood**: Med / Low · **Owner**: Research Director · **Phases**: P29,P32
- **Detection**: scope audit; Claude review
- **Mitigation**: handoff metadata only; no ingestion pipeline / AlphaBook here.
- **Blocking**: FactorLibrary ingestion / AlphaBook / Strategy Reference scope appears → block merge / escalate.

### R-028 — Paper/live/broker scope creep
- **Sev/Likelihood**: High / Low · **Owner**: Research Director · **Phases**: all
- **Detection**: scope/import audit; Claude review
- **Mitigation**: forbidden module list; no execution/broker/live/order code.
- **Blocking**: paper/live/broker/order code or a capital/live decision → stop and escalate.

### R-029 — Parallel materialization corrupts registry writes
- **Sev/Likelihood**: High / Med · **Owner**: Diagnostics Runner · **Phases**: P02,P06-P14,P16-P22
- **Detection**: `frontier-plan`; resource_class audit; dag_scheduler
- **Mitigation**: materialization phases share `resource_class: materialization_registry` and are not `parallel_safe`; the scheduler serializes them.
- **Blocking**: two registry-writing phases co-scheduled → stop phase selection.

### R-030 — Heavy local reports committed
- **Sev/Likelihood**: Med / Low · **Owner**: Librarian · **Phases**: P15,P23,P26,P30
- **Detection**: artifact audit; size/glob check; Claude review
- **Mitigation**: only value-free summaries committed; per-row values local-only.
- **Blocking**: heavy/value report staged → block merge / repair.

### R-031 — DatasetVersion accepted despite missing schema/symbol/year coverage
- **Sev/Likelihood**: High / Med · **Owner**: Data Contract Auditor · **Phases**: P02
- **Detection**: coverage verdict audit; Claude review
- **Mitigation**: coverage report required per version; missing schema/symbol/year → `BLOCKED` or `ACCEPTED_WITH_WARNINGS`, never silent `ACCEPTED`.
- **Blocking**: acceptance without coverage evidence → block merge / repair.

### R-032 — BBO missingness ignored in downstream diagnostics
- **Sev/Likelihood**: Med / Med · **Owner**: Statistical Reviewer · **Phases**: P12,P26,P28
- **Detection**: P26 BBO quality matrix; Claude review
- **Mitigation**: surface missingness / bad-quote / wide-spread regimes; treat as gating context.
- **Blocking**: BBO missingness omitted from diagnostics inputs → block merge / rework.

### R-033 — Cost-adjusted labels use stale fee/slippage assumptions
- **Sev/Likelihood**: Med / Med · **Owner**: Label Engineer · **Phases**: P19
- **Detection**: cost/fee/slippage version audit; Claude review
- **Mitigation**: document cost/fee/slippage assumptions + versions; BBO as proxy.
- **Blocking**: undocumented/stale cost assumptions → block merge / rework.

### R-034 — Validator accepts incomplete substrate because some families resolve
- **Sev/Likelihood**: High / Med · **Owner**: Statistical Reviewer · **Phases**: P14,P22,P27
- **Detection**: full coverage-matrix review; resolver-smoke over all families; Claude review
- **Mitigation**: require all eight feature families + full label horizon set + StudySpec resolver-smoke; explicit gap recording, not partial pass.
- **Blocking**: acceptance with unresolved required families/horizons → block merge / rework.

### R-035 — No clear handoff to Validation Governance / FactorLibrary
- **Sev/Likelihood**: Med / Low · **Owner**: Research Director · **Phases**: P31,P32
- **Detection**: handoff completeness review; Claude review
- **Mitigation**: P31/P32 produce concrete, evidence-driven requirement handoffs incl. N_eff/fold metadata + matrices.
- **Blocking**: missing/empty downstream handoff → block merge / repair.
