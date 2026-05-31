===== FILE: campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md =====

# ALPHA_SYSTEM_V1 Risk Register

## Purpose

This file defines the operational risk register for the `ALPHA_SYSTEM_V1` campaign in the `alpha_system` repository.

The campaign builds a clean-slate, local-first Alpha Research Platform under Frontier Harness Generic v3.0 Workflow 2. It is designed for 1-minute-session-first intraday research, future multi-asset support, and future Level-2 readiness. It is not merely a backtester and must not become a live trading system during this campaign.

The risk register exists to help Ralph, Codex, Claude, ChatGPT, and the human researcher prevent failures that would compromise:

* point-in-time correctness,
* reproducibility,
* research integrity,
* artifact discipline,
* reviewability,
* domain boundaries,
* reference execution truth,
* no-lookahead guarantees,
* Workflow 2 automation safety,
* local-first architecture,
* campaign scope control.

Every phase spec, Codex execution, Claude review, repair loop, merge gate, and final semantic done-check must consider the risks in this register.

This campaign must preserve the following non-negotiable constraints:

* no broker/live trading,
* no paper trading adapter,
* no real-time order routing,
* no raw data committed,
* no heavy artifacts committed,
* no generated runtime SQLite DB committed,
* no alpha/tradability claims without later evidence,
* no candidate promotion without review,
* no uncontrolled strategy explosion,
* no execution-truth ambiguity,
* no lookahead,
* no hidden failed runs,
* no test weakening/gaming,
* no `git add .`,
* no `git add -A`,
* repo/worktree must live under WSL2 filesystem, not `/mnt/c`, OneDrive, or Windows-synced paths.

---

## Severity Scale

| Severity | Meaning                                                                                                                                                            | Required Action                                               |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| Critical | Can invalidate research truth, create lookahead, create false PnL, introduce live/broker scope, corrupt artifact discipline, or produce false campaign completion. | Block merge immediately. Require repair or blocked handoff.   |
| High     | Can materially damage reproducibility, reviewability, automation integrity, or research interpretation.                                                            | Block merge unless explicitly mitigated and reviewed.         |
| Medium   | Can cause workflow friction, future rework, incomplete evidence, or ambiguous interpretation.                                                                      | Must be documented and mitigated or accepted with limitation. |
| Low      | Minor documentation, naming, usability, or non-blocking consistency risk.                                                                                          | Track and resolve opportunistically.                          |

## Likelihood Scale

| Likelihood | Meaning                                                           |
| ---------- | ----------------------------------------------------------------- |
| High       | Likely to occur without active controls.                          |
| Medium     | Plausible during normal autonomous execution.                     |
| Low        | Unlikely but still worth tracking because impact may be material. |

## Risk Status Values

| Status                   | Meaning                                                     |
| ------------------------ | ----------------------------------------------------------- |
| Open                     | Risk exists and must be actively controlled.                |
| Mitigated                | Controls exist and have passed relevant checks.             |
| Accepted with Limitation | Risk remains but is explicitly documented and non-blocking. |
| Blocking                 | Risk has materialized and must block merge or completion.   |
| Closed                   | Risk no longer applies to this campaign scope.              |

---

## Risk Table Summary

| Risk ID | Risk Name                                             | Severity | Likelihood | Primary Owner                  | Primary Detection                  |
| ------- | ----------------------------------------------------- | -------: | ---------: | ------------------------------ | ---------------------------------- |
| R-001   | Lookahead leakage                                     | Critical |       High | Codex / Claude Opus            | no-lookahead tests, review         |
| R-002   | `event_ts` / `available_ts` ambiguity                 | Critical |       High | Codex / Claude Opus            | schema tests, timestamp review     |
| R-003   | Session reset bugs                                    |     High |     Medium | Codex                          | session reset tests                |
| R-004   | Same-bar stop/target ambiguity                        | Critical |       High | Codex / Claude Opus            | reference engine tests             |
| R-005   | Factor/label misalignment                             | Critical |       High | Codex / Claude Opus            | alignment tests                    |
| R-006   | Strategy overfitting                                  |     High |       High | Human Researcher / Claude Opus | grid reports, review               |
| R-007   | Grid explosion                                        |     High |       High | Codex / Ralph                  | grid limit tests                   |
| R-008   | Management overfit                                    |     High |       High | Human Researcher / Claude Opus | survivor gates, review             |
| R-009   | Execution truth ambiguity                             | Critical |     Medium | Claude Opus / Codex            | semantic review, parity tests      |
| R-010   | Fast/reference divergence                             | Critical |       High | Codex / Claude Sonnet          | parity tests                       |
| R-011   | Data quality issues                                   |     High |       High | Codex                          | data validation tests              |
| R-012   | Raw data committed accidentally                       | Critical |     Medium | Ralph / Codex                  | artifact audit                     |
| R-013   | Heavy artifact committed accidentally                 | Critical |       High | Ralph / Codex                  | size/path audit                    |
| R-014   | Alpha/tradability overclaiming                        | Critical |     Medium | Claude Opus / Human Researcher | prohibited claim checks            |
| R-015   | Candidate promotion without review                    | Critical |     Medium | Codex / Claude Opus            | lifecycle and registry tests       |
| R-016   | AI Agent hiding failed runs                           | Critical |     Medium | Ralph / Claude Opus            | run manifest and handoff review    |
| R-017   | Test weakening/gaming                                 | Critical |     Medium | Claude Opus / Ralph            | diff review, semantic done-check   |
| R-018   | SQLite schema drift                                   |     High |     Medium | Codex                          | migration and registry audit tests |
| R-019   | Local path/WSL2 misuse                                |     High |     Medium | Ralph                          | RUN_INIT path preflight            |
| R-020   | Windows/OneDrive path contamination                   |     High |     Medium | Ralph / Codex                  | path grep, config audit            |
| R-021   | Future L2 scope creep                                 |     High |     Medium | Claude Opus                    | scope review                       |
| R-022   | Accidental broker/live scope creep                    | Critical |     Medium | Ralph / Claude Opus            | dependency and source audit        |
| R-023   | Cloud/server dependency creep                         |     High |     Medium | Claude Opus                    | dependency review                  |
| R-024   | Raw real market fixture mistaken as synthetic         |     High |     Medium | Codex / Claude Opus            | fixture audit                      |
| R-025   | Report artifacts too large                            |   Medium |     Medium | Codex / Ralph                  | artifact size checks               |
| R-026   | Handoff missing or incomplete                         |     High |     Medium | Ralph                          | HANDOFF_VALIDATE                   |
| R-027   | Review verdict not parsed correctly                   |     High |     Medium | Ralph                          | verdict JSON validation            |
| R-028   | STOP file ignored                                     | Critical |        Low | Ralph                          | state machine checks               |
| R-029   | Repair loop unbounded                                 |     High |     Medium | Ralph                          | repair attempt counters            |
| R-030   | ML leakage through feature generation                 | Critical |       High | Codex / Claude Opus            | ML leakage tests                   |
| R-031   | Cross-sectional universe leakage                      |     High |     Medium | Codex / Claude Opus            | universe alignment tests           |
| R-032   | Symbol identity misuse                                |     High |     Medium | Codex                          | instrument master tests            |
| R-033   | Cost model silently disabled                          | Critical |     Medium | Codex / Claude Opus            | cost integration tests             |
| R-034   | Promotion recommendation misread as approval          |     High |     Medium | Claude Opus                    | report language checks             |
| R-035   | Fast path used before parity                          | Critical |     Medium | Ralph / Codex                  | grid fast-path gate tests          |
| R-036   | Fixture tests too trivial                             |   Medium |       High | Claude Opus                    | test adequacy review               |
| R-037   | CLI writes to local-only paths during tests           |     High |     Medium | Codex                          | tempdir and artifact tests         |
| R-038   | Generated SQLite DB committed                         | Critical |     Medium | Ralph / Codex                  | DB file audit                      |
| R-039   | Generated Parquet committed                           | Critical |     Medium | Ralph / Codex                  | Parquet audit                      |
| R-040   | Event-driven/L2 design mistaken as complete execution |     High |     Medium | Claude Opus                    | scope and docs review              |

---

# Detailed Risk Entries

---

## R-001 — Lookahead leakage

### Description

Future information may enter factor computation, label alignment, strategy signal generation, ML feature construction, or backtest execution before it would have been available in real time.

Examples include:

* using bar close before `bar_end_ts`,
* using bar `t` signal to execute inside bar `t`,
* using future labels as features,
* computing rolling features with future rows,
* using future session information in same-day decisions,
* using L2 updates before `available_ts`,
* training ML models with validation-window labels.

### Impact

Critical. Lookahead leakage invalidates research results, diagnostics, backtests, grids, and ML experiments. It can create false alpha and false confidence.

### Likelihood

High. This is one of the most common systematic research failures.

### Detection Methods

* `tests/no_lookahead/**`
* `available_ts` schema tests
* `label_available_ts` tests
* factor dependency tests
* factor/label alignment tests
* strategy input tests
* ML leakage tests
* reference backtest timing tests
* Claude Opus review for timestamp semantics
* final semantic done-check

### Mitigations

* Require `available_ts` on bars, factors, signals, and L2-derived features.
* Require `label_available_ts` on labels.
* Default execution must be next-bar conservative.
* Disallow labels as factor or live strategy inputs.
* Require ML `FeatureSetSpec` to consume factor versions only.
* Require purge/embargo and walk-forward split design for ML.
* Require no-lookahead tests in every relevant phase.
* Block merge if no-lookahead tests are missing after relevant phases.

### Owner

Codex for implementation; Claude Opus for semantic review; Ralph for merge enforcement.

### Lane Implication

Any phase touching data, labels, factors, signals, strategies, backtests, ML, L2, or execution semantics is YELLOW and requires Claude Opus review.

### Related Phases

ASV1-P04, ASV1-P06, ASV1-P07, ASV1-P08, ASV1-P10, ASV1-P11, ASV1-P12, ASV1-P14, ASV1-P15, ASV1-P16, ASV1-P19, ASV1-P23, ASV1-P25, ASV1-P26, ASV1-P29.

### Blocking Condition

Any known unresolved lookahead issue blocks merge and campaign completion.

---

## R-002 — `event_ts` / `available_ts` ambiguity

### Description

The platform may confuse source event time, bar close time, receive time, and system availability time. Without clear separation, research code may accidentally use information too early.

### Impact

Critical. Timestamp ambiguity can cause systemic lookahead across every layer.

### Likelihood

High. Timestamp naming drift is common in research systems.

### Detection Methods

* schema primitive tests,
* `available_ts` tests,
* L2 timestamp tests,
* data validation tests,
* code review for timestamp usage,
* documentation review.

### Mitigations

* Define `event_ts`, `bar_start_ts`, `bar_end_ts`, `receive_ts`, and `available_ts` separately.
* Require `available_ts` in canonical bar, factor value, signal, and L2-derived schemas.
* Require `label_available_ts` in label schemas.
* Document timestamp semantics in `docs/NO_LOOKAHEAD_POLICY.md`, `docs/DATA_LAYER.md`, and L2 docs.
* Add tests that fail if required timestamp fields are absent.

### Owner

Codex for schemas and tests; Claude Opus for timestamp review.

### Lane Implication

YELLOW for all schema, data, L2, label, signal, and backtest phases.

### Related Phases

ASV1-P04, ASV1-P06, ASV1-P07, ASV1-P08, ASV1-P10, ASV1-P11, ASV1-P14, ASV1-P15, ASV1-P25, ASV1-P26.

### Blocking Condition

Missing or ambiguous availability timestamp semantics block merge.

---

## R-003 — Session reset bugs

### Description

State may incorrectly carry across sessions, especially in rolling factors, bars-to-left features, intraday indicators, management cooldowns, and EOD exits.

### Impact

High. Cross-session contamination can distort factor values, labels, signals, management state, and backtest results.

### Likelihood

Medium.

### Detection Methods

* session assignment tests,
* `bar_index` reset tests,
* session reset tests for factors,
* EOD exit tests,
* cooldown tests,
* half-day and holiday tests.

### Mitigations

* Include `session_id` and `bar_index` in core schemas.
* Require FactorSpec `session_reset`.
* Require sessionized bars before factor computation.
* Require EOD and session-boundary management tests.
* Add quality flags for missing/out-of-session bars.

### Owner

Codex.

### Lane Implication

YELLOW for data, factor, backtest, and management phases.

### Related Phases

ASV1-P06, ASV1-P07, ASV1-P10, ASV1-P11, ASV1-P15, ASV1-P17, ASV1-P29.

### Blocking Condition

Any uncontrolled cross-session state leakage blocks merge.

---

## R-004 — Same-bar stop/target ambiguity

### Description

With OHLC bar data, if both stop and target occur inside the same 1-minute bar, the true event order is unknown. An optimistic assumption can create false PnL.

### Impact

Critical. Same-bar optimism can materially inflate strategy results.

### Likelihood

High for intraday bar-level backtests.

### Detection Methods

* same-bar conservative tests,
* reference engine fixture tests,
* management tests,
* cost/slippage tests,
* Claude review of backtest semantics.

### Mitigations

* Default same-bar stop/target order must be conservative.
* Document bar-level ambiguity in `docs/REFERENCE_BACKTEST.md`.
* Require tests for same-bar stop/target behavior.
* Defer event-driven or L2 replay validation to future campaigns.

### Owner

Codex and Claude Opus.

### Lane Implication

YELLOW for reference backtest, cost/slippage, management, fast parity, and grid phases.

### Related Phases

ASV1-P15, ASV1-P16, ASV1-P17, ASV1-P19, ASV1-P20, ASV1-P29.

### Blocking Condition

Optimistic same-bar execution default blocks merge.

---

## R-005 — Factor/label misalignment

### Description

Factor values and labels may be joined using incorrect timestamp, horizon, instrument, session, or data version keys.

### Impact

Critical. Misalignment can invalidate factor diagnostics and ML training.

### Likelihood

High.

### Detection Methods

* factor/label alignment tests,
* `label_available_ts` tests,
* diagnostics alignment tests,
* ML leakage tests,
* registry version reference tests.

### Mitigations

* Require explicit factor value schema.
* Require explicit label schema.
* Align on `instrument_id`, `event_ts`, `session_id`, `horizon`, `data_version`, `factor_version`, and `label_version`.
* Reject labels as live feature inputs.
* Require diagnostics to validate factor/label alignment before computing metrics.

### Owner

Codex and Claude Opus.

### Lane Implication

YELLOW for labels, factor compute, diagnostics, ML, and reporting phases.

### Related Phases

ASV1-P10, ASV1-P11, ASV1-P12, ASV1-P13, ASV1-P23, ASV1-P29.

### Blocking Condition

Known factor/label misalignment blocks merge.

---

## R-006 — Strategy overfitting

### Description

Strategy parameters may be tuned to small samples, unstable regimes, or noisy intraday behavior, then mistaken for robust alpha.

### Impact

High. Overfit strategies can produce misleading backtest results and poor future performance.

### Likelihood

High.

### Detection Methods

* grid discipline checks,
* sample-size warnings,
* monthly breakdowns,
* cost sensitivity reports,
* rejected config visibility,
* review bundles,
* Claude review,
* final semantic done-check.

### Mitigations

* Factor diagnostics before strategy grids.
* Bounded strategy grids.
* Rejected configs visible.
* No candidate promotion without review.
* Reports must not claim tradability.
* Require cost sensitivity and monthly breakdown outputs in grid framework.

### Owner

Human Researcher for interpretation; Codex for controls; Claude Opus for review.

### Lane Implication

YELLOW for strategy, grid, management grid, reporting, and closeout phases.

### Related Phases

ASV1-P12, ASV1-P13, ASV1-P14, ASV1-P20, ASV1-P21, ASV1-P27, ASV1-P29.

### Blocking Condition

Unsupported robustness, profitability, or tradability claims block merge.

---

## R-007 — Grid explosion

### Description

Parameter expansion may create uncontrolled Cartesian products, long local runs, huge outputs, and misleading leaderboards.

### Impact

High. Grid explosion can break local execution, create heavy artifacts, and amplify overfitting.

### Likelihood

High.

### Detection Methods

* grid expansion count tests,
* max combination rejection tests,
* artifact size checks,
* run manifest review,
* rejected config checks.

### Mitigations

* Require `GridSpec` combination count limits.
* Reject unbounded grids.
* Record rejected configs and reasons.
* Keep full outputs local-only.
* Require tiny fixture grids for tests.

### Owner

Codex and Ralph.

### Lane Implication

YELLOW for grid and management grid phases.

### Related Phases

ASV1-P20, ASV1-P21, ASV1-P29.

### Blocking Condition

Unbounded grid execution or full grid output commit blocks merge.

---

## R-008 — Management overfit

### Description

Stop, target, breakeven, trailing, cooldown, and partial-take-profit rules may be optimized after observing outcomes and mistaken for robust edge.

### Impact

High. Management overfit can create fragile and misleading strategy results.

### Likelihood

High.

### Detection Methods

* survivor gating tests,
* management grid limit tests,
* baseline comparison reports,
* cost sensitivity outputs,
* monthly breakdowns,
* review bundles.

### Mitigations

* Management grid only after baseline survivor eligibility.
* Bounded management parameter expansion.
* No automatic approval.
* No promotion decision by grid engine.
* Reports must include overfit warnings.

### Owner

Human Researcher, Codex, Claude Opus.

### Lane Implication

YELLOW for management, management grid, reporting, and closeout phases.

### Related Phases

ASV1-P17, ASV1-P21, ASV1-P27, ASV1-P29.

### Blocking Condition

Management grid approval without review or unbounded management grid blocks merge.

---

## R-009 — Execution truth ambiguity

### Description

The platform may accidentally allow multiple engines to define conflicting PnL truth, such as reference engine, fast path, event-driven engine, or L2 skeleton.

### Impact

Critical. Conflicting PnL truth invalidates comparisons and research governance.

### Likelihood

Medium.

### Detection Methods

* backtest truth policy tests,
* fast/reference parity tests,
* grid fast-path gate tests,
* Claude review,
* final semantic done-check.

### Mitigations

* Reference 1-minute engine is canonical truth for v1.
* Fast path is acceleration only.
* Event-driven and L2 execution are future design only.
* No second PnL truth allowed.
* Grid may use fast path only after parity.

### Owner

Claude Opus and Codex.

### Lane Implication

YELLOW for backtest, cost/slippage, fast path, grid, L2, and closeout phases.

### Related Phases

ASV1-P15, ASV1-P16, ASV1-P19, ASV1-P20, ASV1-P25, ASV1-P29.

### Blocking Condition

Any second PnL truth or ambiguity about canonical truth blocks merge.

---

## R-010 — Fast/reference divergence

### Description

NumPy/Numba fast path may diverge from reference engine accounting, fills, costs, exits, or management rules.

### Impact

Critical. Divergence corrupts grid outputs and research conclusions.

### Likelihood

High.

### Detection Methods

* `tests/parity/**`,
* deterministic shared fixtures,
* grid fast-path gate tests,
* Claude Sonnet mechanical audits,
* handoff parity matrix.

### Mitigations

* Build fast path only after reference engine.
* Require parity tests before fast path use.
* Unsupported features must fail closed or route to reference.
* Reference behavior must not be weakened to match fast path.

### Owner

Codex and Claude Sonnet; Claude Opus for semantic review.

### Lane Implication

YELLOW for fast path and grid phases.

### Related Phases

ASV1-P19, ASV1-P20, ASV1-P29.

### Blocking Condition

Fast path use before parity or unresolved parity failure blocks merge.

---

## R-011 — Data quality issues

### Description

Input or canonical datasets may contain missing bars, duplicates, invalid OHLC values, non-monotonic timestamps, out-of-session rows, invalid spreads, or incorrect data versions.

### Impact

High. Bad data can invalidate factors, labels, diagnostics, backtests, and ML experiments.

### Likelihood

High.

### Detection Methods

* data validation CLI,
* missing bar tests,
* duplicate timestamp tests,
* OHLC sanity tests,
* spread validation,
* session quality flags,
* data quality summaries.

### Mitigations

* Canonical 1-minute schema validation.
* Session-aware quality flags.
* Tiny deterministic fixtures for invalid cases.
* Data validation CLI before downstream workflows.
* Data version required in registry records.

### Owner

Codex.

### Lane Implication

YELLOW for data and validation phases.

### Related Phases

ASV1-P06, ASV1-P07, ASV1-P08, ASV1-P29.

### Blocking Condition

Data validation failure in required fixtures blocks merge.

---

## R-012 — Raw data committed accidentally

### Description

Raw market data may be committed into the repo, causing licensing, privacy, size, and reproducibility issues.

### Impact

Critical. This violates campaign constraints and may contaminate the repository.

### Likelihood

Medium.

### Detection Methods

* `.gitignore`,
* hook checks,
* `git status --short`,
* `git ls-files`,
* path audit for `data/raw/**`,
* artifact audit in merge gate.

### Mitigations

* Raw data paths are forbidden.
* Explicit staging only.
* No `git add .`.
* No `git add -A`.
* Artifact audit before merge.
* Handoff must confirm no raw data committed.

### Owner

Ralph and Codex.

### Lane Implication

All lanes. Any raw data staged is blocking.

### Related Phases

All phases, especially ASV1-P00, ASV1-P06, ASV1-P08, ASV1-P24, ASV1-P29.

### Blocking Condition

Any raw data staged or committed blocks merge.

---

## R-013 — Heavy artifact committed accidentally

### Description

Generated grids, trade logs, reports, SQLite files, ML artifacts, Parquet datasets, benchmark logs, or review bundles may be committed.

### Impact

Critical. Heavy artifact commits degrade repo health and may leak local-only outputs.

### Likelihood

High.

### Detection Methods

* artifact size checks,
* forbidden path checks,
* extension checks,
* `find artifacts -type f -size +1M`,
* `git ls-files`,
* handoff artifact confirmation.

### Mitigations

* Strong `.gitignore`.
* Explicit staging only.
* Phase-level forbidden paths.
* Artifact manifest policy.
* Handoff confirmation.
* Merge gate artifact audit.

### Owner

Ralph and Codex.

### Lane Implication

All lanes. Any heavy artifact staged is blocking.

### Related Phases

All phases, especially ASV1-P20, ASV1-P21, ASV1-P23, ASV1-P27, ASV1-P29.

### Blocking Condition

Heavy generated artifact staged or committed blocks merge.

---

## R-014 — Alpha/tradability overclaiming

### Description

Docs, reports, summaries, or handoffs may claim that a factor, strategy, model, or configuration is alpha, tradable, profitable, robust, market-beating, production-ready, or live-ready without evidence and review.

### Impact

Critical. This violates research discipline and can cause false strategic decisions.

### Likelihood

Medium.

### Detection Methods

* prohibited claim tests,
* report language checks,
* docs grep,
* Claude review,
* final closeout review.

### Mitigations

* Report language policy.
* Factor cards use limited recommendation vocabulary.
* Review bundles include caveats and warnings.
* Candidate promotion requires review.
* Fixture results are correctness validation only.

### Owner

Claude Opus, Codex, Human Researcher.

### Lane Implication

All reporting, docs, diagnostics, grid, ML, and closeout phases are YELLOW except onboarding Green with claim checks.

### Related Phases

ASV1-P12, ASV1-P13, ASV1-P20, ASV1-P21, ASV1-P23, ASV1-P27, ASV1-P28, ASV1-P29.

### Blocking Condition

Unsupported alpha/tradability/profitability claim blocks merge.

---

## R-015 — Candidate promotion without review

### Description

A factor, strategy, model, or grid result may be promoted to validated or approved without required evidence and review metadata.

### Impact

Critical. Unreviewed promotion undermines governance and may cause false readiness.

### Likelihood

Medium.

### Detection Methods

* factor lifecycle tests,
* registry promotion decision tests,
* report recommendation tests,
* review bundle promotion status checks,
* registry audit.

### Mitigations

* Factor lifecycle states require review metadata for approval.
* Promotion decisions recorded in SQLite registry.
* Factor cards can recommend review but cannot approve.
* Grid and management grid cannot approve candidates.

### Owner

Codex and Claude Opus.

### Lane Implication

YELLOW for factor registry, reports, grid, registry hardening, and closeout.

### Related Phases

ASV1-P09, ASV1-P13, ASV1-P20, ASV1-P21, ASV1-P22, ASV1-P27, ASV1-P29.

### Blocking Condition

Validated/approved status without required review metadata blocks merge.

---

## R-016 — AI Agent hiding failed runs

### Description

An autonomous agent may omit failed commands, failed experiments, rejected configs, or blocked states from handoffs, manifests, or summaries.

### Impact

Critical. Hidden failures destroy auditability and may produce false done status.

### Likelihood

Medium.

### Detection Methods

* run manifest checks,
* failed-run registry tests,
* handoff validation,
* `events.jsonl`,
* `checks.json`,
* review bundle failed-run visibility tests,
* Claude review.

### Mitigations

* Every phase must write checks.
* Every phase must write handoff.
* Failed runs are represented in registry.
* Repair attempts are tracked.
* Blocked handoff required for blocked phases.

### Owner

Ralph, Codex, Claude Opus.

### Lane Implication

All lanes. Yellow phases require review.

### Related Phases

All phases, especially ASV1-P22, ASV1-P27, ASV1-P29.

### Blocking Condition

Hidden failed run evidence blocks merge.

---

## R-017 — Test weakening/gaming

### Description

Tests may be removed, skipped, weakened, changed to only check superficial behavior, or modified to pass without preserving intended guarantees.

### Impact

Critical. Test gaming can create false confidence and false completion.

### Likelihood

Medium.

### Detection Methods

* diff review,
* test coverage review,
* Claude review,
* semantic done-check,
* required test list comparison against PHASE_PLAN.

### Mitigations

* Test changes require explicit phase scope.
* Yellow phases require Claude review.
* No done based only on tests.
* Required test categories specified per phase.
* Handoff must list tests and rationale.

### Owner

Claude Opus and Ralph.

### Lane Implication

All lanes. Any suspicious test weakening is blocking.

### Related Phases

All phases.

### Blocking Condition

Unauthorized test removal, weakening, or gaming blocks merge.

---

## R-018 — SQLite schema drift

### Description

SQLite migrations, registry models, and docs may drift apart, causing broken reproducibility or invalid registry writes.

### Impact

High.

### Likelihood

Medium.

### Detection Methods

* migration idempotence tests,
* required table/column tests,
* registry audit tests,
* docs/schema comparison in review.

### Mitigations

* Migration files versioned.
* Required tables listed in campaign YAML and acceptance gates.
* Temp DB tests for every registry phase.
* Registry audit in ASV1-P22.

### Owner

Codex.

### Lane Implication

YELLOW for registry phases.

### Related Phases

ASV1-P05, ASV1-P09, ASV1-P10, ASV1-P12, ASV1-P14, ASV1-P20, ASV1-P21, ASV1-P22, ASV1-P23, ASV1-P29.

### Blocking Condition

Schema drift that prevents registry initialization or reproducibility blocks merge.

---

## R-019 — Local path/WSL2 misuse

### Description

Repo or worktree may be used under `/mnt/c`, OneDrive, Dropbox, Google Drive, or other Windows-synced path.

### Impact

High. Path misuse can cause performance issues, file-locking problems, sync conflicts, and harness inconsistency.

### Likelihood

Medium.

### Detection Methods

* RUN_INIT path preflight,
* WORKTREE_CREATE path check,
* handoff path confirmation,
* grep for Windows paths in configs.

### Mitigations

* Required repo path `~/projects/alpha_system`.
* Active worktree path restrictions in campaign YAML and docs.
* Stop condition for forbidden path.

### Owner

Ralph.

### Lane Implication

All lanes. Path violation stops run before execution or merge.

### Related Phases

All phases, especially ASV1-P00, ASV1-P01, ASV1-P29.

### Blocking Condition

Active repo/worktree under forbidden Windows path blocks campaign execution.

---

## R-020 — Windows/OneDrive path contamination

### Description

Windows paths or OneDrive paths may leak into configs, manifests, docs, or generated artifacts.

### Impact

High. Path contamination can make the project non-portable and violate WSL2 policy.

### Likelihood

Medium.

### Detection Methods

* grep for `/mnt/c`, `C:\`, `OneDrive`, `Dropbox`, `Google Drive`,
* config validation,
* run manifest review,
* handoff review.

### Mitigations

* Normalize paths to repo-relative or WSL2 paths.
* Allow forbidden path mentions only in docs as examples of what not to use.
* Review configs and manifests for local absolute paths.

### Owner

Codex and Ralph.

### Lane Implication

All lanes.

### Related Phases

ASV1-P00, ASV1-P01, ASV1-P02, ASV1-P08, ASV1-P22, ASV1-P27, ASV1-P28, ASV1-P29.

### Blocking Condition

Active config or runtime manifest depends on forbidden Windows path.

---

## R-021 — Future L2 scope creep

### Description

Design-only L2 readiness may expand into full replay, book reconstruction, queue modeling, passive fills, or real L2 ingestion.

### Impact

High. This can overbuild v1, create false execution claims, and introduce huge data/artifact risks.

### Likelihood

Medium.

### Detection Methods

* L2 design-only tests,
* source path audit for replay/queue model files,
* docs review,
* Claude review.

### Mitigations

* L2 phases limited to schema/design/skeleton.
* No real L2 data.
* No replay engine.
* No passive fill simulation.
* No production microstructure alpha claim.

### Owner

Claude Opus and Codex.

### Lane Implication

YELLOW for L2 phases.

### Related Phases

ASV1-P25, ASV1-P26, ASV1-P29.

### Blocking Condition

Full L2 replay, queue model, passive fill simulation, or real L2 ingestion blocks merge.

---

## R-022 — Accidental broker/live scope creep

### Description

Broker integration, paper trading, live trading, order routing, account sync, or live market data dependency may be introduced despite being out of scope.

### Impact

Critical. This violates campaign boundaries and would require separate scoped authorization.

### Likelihood

Medium.

### Detection Methods

* source audit for broker/live/order/account modules,
* dependency audit,
* docs review,
* Claude review,
* stop conditions.

### Mitigations

* Explicit non-goal in all campaign files.
* Forbidden paths for broker/live files.
* Red authorization required for future live/destructive/external operations.
* This campaign should not use Red.

### Owner

Ralph and Claude Opus.

### Lane Implication

Any broker/live implementation is RED and out of campaign scope.

### Related Phases

All phases.

### Blocking Condition

Broker/live/paper/order routing implementation blocks merge.

---

## R-023 — Cloud/server dependency creep

### Description

The repo may start requiring cloud storage, paid databases, database servers, Ray, Dagster, Prefect, MLflow server, ClickHouse, QuestDB, DolphinDB, kdb+, or similar infrastructure.

### Impact

High. This violates the local-first v1 stack and increases cost/complexity.

### Likelihood

Medium.

### Detection Methods

* dependency diff review,
* pyproject review,
* docs review,
* config review.

### Mitigations

* Finalized local-first stack in GOAL and PHASE_PLAN.
* Server dependencies deferred to future campaigns.
* Claude review for dependency changes.
* `pyproject.toml` review during workspace and ML phases.

### Owner

Claude Opus and Codex.

### Lane Implication

YELLOW for dependency changes; RED if external/costly resources are invoked.

### Related Phases

ASV1-P02, ASV1-P03, ASV1-P05, ASV1-P20, ASV1-P23, ASV1-P29.

### Blocking Condition

Required cloud/server/paid dependency blocks acceptance.

---

## R-024 — Raw real market fixture mistaken as synthetic

### Description

Real market data may be committed as a test fixture and misrepresented as synthetic or tiny deterministic data.

### Impact

High. This risks licensing issues and false interpretation of fixture results.

### Likelihood

Medium.

### Detection Methods

* fixture audit,
* file size checks,
* fixture docs review,
* suspicious timestamp/symbol review,
* handoff fixture declaration.

### Mitigations

* Fixtures must be tiny, deterministic, and documented.
* Real raw market data is forbidden.
* Fixture results cannot be used as market evidence.
* Review must inspect fixture provenance when data-like files are introduced.

### Owner

Codex and Claude Opus.

### Lane Implication

All phases that add fixtures require artifact review.

### Related Phases

ASV1-P06, ASV1-P08, ASV1-P12, ASV1-P15, ASV1-P20, ASV1-P24, ASV1-P29.

### Blocking Condition

Real market data committed as fixture blocks merge.

---

## R-025 — Report artifacts too large

### Description

Markdown/CSV/static HTML reports, charts, or review bundles may grow too large or include raw rows/trades/grids.

### Impact

Medium to High. Large reports bloat the repo and may leak local-only outputs.

### Likelihood

Medium.

### Detection Methods

* artifact size checks,
* review bundle tests,
* report artifact policy tests,
* `find artifacts -type f -size +1M`.

### Mitigations

* Full report bundles local-only.
* Only curated summaries may be committed.
* Report tests check artifact policy.
* Use source maps and manifests instead of copying raw outputs.

### Owner

Codex and Ralph.

### Lane Implication

YELLOW for reporting and closeout phases.

### Related Phases

ASV1-P13, ASV1-P27, ASV1-P29.

### Blocking Condition

Large report artifact staged without explicit scope blocks merge.

---

## R-026 — Handoff missing or incomplete

### Description

A phase may omit required handoff details, making review and future continuation unreliable.

### Impact

High.

### Likelihood

Medium.

### Detection Methods

* HANDOFF_VALIDATE state,
* required handoff file check,
* Claude review,
* run summary audit.

### Mitigations

* Handoff required for every phase.
* Handoff must include files changed, checks, artifact policy, risks, limitations, and review focus.
* Missing handoff blocks merge.

### Owner

Ralph and Codex.

### Lane Implication

All lanes.

### Related Phases

All phases.

### Blocking Condition

Missing or materially incomplete handoff blocks merge.

---

## R-027 — Review verdict not parsed correctly

### Description

Claude review verdict may be ambiguous, malformed, missing, or incorrectly parsed by Ralph.

### Impact

High. A `REWORK` or `BLOCKED` phase could merge accidentally.

### Likelihood

Medium.

### Detection Methods

* `verdict.json` schema validation,
* verdict parser tests,
* merge gate checks,
* review artifact inspection.

### Mitigations

* Review verdict must be one of `PASS`, `PASS_WITH_WARNINGS`, `REWORK`, `BLOCKED`.
* `verdict.json` required.
* Merge allowed only for `PASS` or `PASS_WITH_WARNINGS`.
* Ambiguous verdict blocks merge.

### Owner

Ralph.

### Lane Implication

All reviewed phases.

### Related Phases

All Yellow phases, especially ASV1-P01 and ASV1-P29.

### Blocking Condition

Missing or unparseable required verdict blocks merge.

---

## R-028 — STOP file ignored

### Description

Ralph or agents may continue execution, PR creation, or merge despite an active STOP file.

### Impact

Critical. This violates Workflow 2 operator control.

### Likelihood

Low, but impact is high.

### Detection Methods

* state machine checks,
* STOP file pre-state checks,
* run summary audit,
* merge gate check.

### Mitigations

* STOP check before new phase, PR, and merge.
* STOP behavior documented in RUNBOOK.
* STOP active is a stop condition.

### Owner

Ralph.

### Lane Implication

All lanes.

### Related Phases

All phases.

### Blocking Condition

Active STOP file must stop phase progression and merge.

---

## R-029 — Repair loop unbounded

### Description

Autonomous repair may continue indefinitely, consuming time and changing scope.

### Impact

High.

### Likelihood

Medium.

### Detection Methods

* repair attempt counter,
* `repair_attempts/` directory audit,
* state machine log.

### Mitigations

* Default max repair attempts is 3.
* Exceeded attempts route to blocked handoff.
* Repair attempts must be tracked.

### Owner

Ralph.

### Lane Implication

All lanes.

### Related Phases

All phases.

### Blocking Condition

Repair attempts exceeded must block and produce blocked handoff.

---

## R-030 — ML leakage through feature generation

### Description

ML experiments may use raw ad hoc columns, future labels, validation-window features, or improperly split data.

### Impact

Critical. ML leakage can create false predictive performance.

### Likelihood

High.

### Detection Methods

* ML raw-column rejection tests,
* label leakage tests,
* walk-forward split tests,
* purge/embargo tests,
* feature set validation.

### Mitigations

* ML consumes factor versions only.
* Labels cannot appear in `FeatureSetSpec`.
* Purge/embargo utilities required.
* Walk-forward split design required.
* No production ML claims.

### Owner

Codex and Claude Opus.

### Lane Implication

YELLOW for ML phase.

### Related Phases

ASV1-P23, ASV1-P29.

### Blocking Condition

ML leakage or raw ad hoc ML feature path blocks merge.

---

## R-031 — Cross-sectional universe leakage

### Description

Cross-sectional ranks or multi-symbol features may use symbols not active at the time, future universe membership, or misaligned timestamps across instruments.

### Impact

High.

### Likelihood

Medium.

### Detection Methods

* universe active date tests,
* multi-symbol timestamp alignment tests,
* cross-sectional rank tests,
* per-symbol missing data tests.

### Mitigations

* UniverseSpec includes active date ranges.
* Instrument master includes metadata.
* Cross-sectional calculations must use point-in-time universe membership.
* Multi-symbol alignment tests required.

### Owner

Codex and Claude Opus.

### Lane Implication

YELLOW for multi-symbol phase.

### Related Phases

ASV1-P24, ASV1-P29.

### Blocking Condition

Cross-sectional feature uses future membership or misaligned timestamps.

---

## R-032 — Symbol identity misuse

### Description

Raw ticker symbols may be treated as stable instrument identifiers, ignoring symbol changes, exchange, currency, multiplier, or corporate action policy.

### Impact

High.

### Likelihood

Medium.

### Detection Methods

* instrument master tests,
* universe config validation,
* symbol-to-instrument-id mapping tests.

### Mitigations

* Use `instrument_id` as stable internal identifier.
* Instrument master required fields include symbol, exchange, currency, multiplier, active dates, corporate action policy.
* Universe configs map symbols to instrument ids.

### Owner

Codex.

### Lane Implication

YELLOW for contracts and multi-symbol phases.

### Related Phases

ASV1-P04, ASV1-P24.

### Blocking Condition

Core contracts or universe logic depend on raw symbol as sole identity.

---

## R-033 — Cost model silently disabled

### Description

Backtests or grids may run with zero cost by default without explicit configuration, overstating results.

### Impact

Critical.

### Likelihood

Medium.

### Detection Methods

* cost model tests,
* zero-cost explicit fixture tests,
* reference integration tests,
* grid cost sensitivity tests.

### Mitigations

* Non-test defaults conservative.
* Zero-cost only allowed via explicit fixture/test config.
* Cost/slippage assumptions recorded in metadata.
* Cost sensitivity output required for grids.

### Owner

Codex and Claude Opus.

### Lane Implication

YELLOW for cost, backtest, grid, management grid, and closeout phases.

### Related Phases

ASV1-P16, ASV1-P20, ASV1-P21, ASV1-P29.

### Blocking Condition

Silent zero-cost default in non-test config blocks merge.

---

## R-034 — Promotion recommendation misread as approval

### Description

Report language such as `candidate_for_review` may be interpreted as actual approved status.

### Impact

High.

### Likelihood

Medium.

### Detection Methods

* report language tests,
* promotion recommendation tests,
* review bundle promotion status checks,
* docs review.

### Mitigations

* Reports use limited recommendation vocabulary.
* Approval requires registry promotion decision with review metadata.
* Docs distinguish recommendation from approval.
* Review bundles show promotion decision status.

### Owner

Claude Opus and Human Researcher.

### Lane Implication

YELLOW for reporting, registry, review bundle, and closeout phases.

### Related Phases

ASV1-P13, ASV1-P22, ASV1-P27, ASV1-P29.

### Blocking Condition

Report or docs imply recommendation equals approval.

---

## R-035 — Fast path used before parity

### Description

Grid or experiment runner may use fast path without required parity passing for the selected feature set.

### Impact

Critical. This can produce invalid grid outputs.

### Likelihood

Medium.

### Detection Methods

* grid fast-path gate tests,
* parity matrix handoff,
* experiment runner tests,
* Claude review.

### Mitigations

* Fast path introduced after reference engine.
* Grid use of fast path requires parity gate.
* Unsupported features fail closed or route to reference.
* `tests/parity/**` required.

### Owner

Ralph and Codex.

### Lane Implication

YELLOW for fast path and grid phases.

### Related Phases

ASV1-P19, ASV1-P20, ASV1-P29.

### Blocking Condition

Fast path used before parity blocks merge.

---

## R-036 — Fixture tests too trivial

### Description

Tests may use fixtures that are too simple to catch boundary cases, such as no missing bars, no same-bar ambiguity, no half-days, no split leakage, or no rejected grid configs.

### Impact

Medium to High. The platform may pass tests without meaningful protection.

### Likelihood

High.

### Detection Methods

* Claude test adequacy review,
* fixture coverage matrix,
* final validation matrix,
* mutation or negative-case tests where feasible.

### Mitigations

* Require explicit negative tests for key risks.
* Include fixtures for missing bars, duplicates, same-bar ambiguity, label leakage, grid rejection, and unsupported fast features.
* Handoffs must state fixture limitations.

### Owner

Claude Opus and Codex.

### Lane Implication

All engineering phases.

### Related Phases

All phases with tests, especially ASV1-P06, ASV1-P10, ASV1-P15, ASV1-P19, ASV1-P20, ASV1-P29.

### Blocking Condition

Critical phase lacks meaningful tests for its primary risk.

---

## R-037 — CLI writes to local-only paths during tests

### Description

CLI tests may accidentally write to `data/`, `metadata/`, or `artifacts/` in the repo instead of temp directories.

### Impact

High. This can generate local-only outputs that are accidentally staged.

### Likelihood

Medium.

### Detection Methods

* tempdir tests,
* post-test `find data`, `find metadata`, `find artifacts`,
* artifact policy tests,
* git status review.

### Mitigations

* CLI tests must use temp directories.
* Default output paths must be local-only and ignored.
* Commands must expose explicit output path controls.
* Post-test artifact checks required.

### Owner

Codex and Ralph.

### Lane Implication

YELLOW for CLI phases.

### Related Phases

ASV1-P05, ASV1-P08, ASV1-P11, ASV1-P12, ASV1-P15, ASV1-P20, ASV1-P21, ASV1-P23, ASV1-P27, ASV1-P29.

### Blocking Condition

CLI generates repo-local data/DB/artifacts that are staged or not cleaned.

---

## R-038 — Generated SQLite DB committed

### Description

A runtime SQLite registry DB, journal, WAL, or temp DB may be committed.

### Impact

Critical.

### Likelihood

Medium.

### Detection Methods

* `find metadata -type f ! -name ".gitkeep"`,
* `find . -name "*.sqlite" -o -name "*.db"`,
* git ls-files audit,
* artifact policy checks.

### Mitigations

* SQLite files forbidden globally.
* Tests use temporary directories.
* `.gitignore` protects `metadata/*.sqlite`, `*.db`, journals, and WAL files.
* Merge gate audits DB files.

### Owner

Ralph and Codex.

### Lane Implication

All lanes.

### Related Phases

ASV1-P05, ASV1-P22, ASV1-P29, and any phase using registry tests.

### Blocking Condition

Generated SQLite/DB file staged or committed blocks merge.

---

## R-039 — Generated Parquet committed

### Description

Generated Parquet, Arrow, or Feather files may be committed outside allowed tiny fixture exceptions.

### Impact

Critical. This may include raw/canonical/factor/label data and bloat the repo.

### Likelihood

Medium.

### Detection Methods

* `find . -name "*.parquet" -not -path "./tests/fixtures/*"`,
* git ls-files audit,
* artifact policy tests.

### Mitigations

* Parquet files forbidden outside documented tiny fixtures.
* Local data directories ignored.
* Fixture exception requires documentation and small size.
* Merge gate artifact audit.

### Owner

Ralph and Codex.

### Lane Implication

All lanes.

### Related Phases

ASV1-P06, ASV1-P08, ASV1-P11, ASV1-P10, ASV1-P20, ASV1-P29.

### Blocking Condition

Generated Parquet/Arrow/Feather outside allowed fixture path blocks merge.

---

## R-040 — Event-driven/L2 design mistaken as complete execution

### Description

Tier 3 event-driven execution design or Tier 4 L2/L3 design may be misread as complete production execution validation.

### Impact

High. This creates false readiness and scope confusion.

### Likelihood

Medium.

### Detection Methods

* docs review,
* L2 design-only tests,
* report claim checks,
* closeout semantic review.

### Mitigations

* Backtest tiers document Tier 1 reference truth as v1 truth.
* Event-driven and L2 replay are future campaigns.
* L2 phases are design/skeleton only.
* Reports must not claim execution completeness beyond implemented scope.

### Owner

Claude Opus and Human Researcher.

### Lane Implication

YELLOW for backtest tier docs, L2 phases, review bundle, and closeout.

### Related Phases

ASV1-P02, ASV1-P15, ASV1-P25, ASV1-P26, ASV1-P27, ASV1-P29.

### Blocking Condition

Docs or reports imply event-driven/L2 execution is complete in this campaign.

---

# Risk Review Cadence

## Per-Phase Cadence

Every phase must review the risks relevant to its scope during:

1. `SPEC_GENERATE`
2. `SPEC_VALIDATE`
3. `CODEX_EXECUTE`
4. `CHECKS_RUN`
5. `HANDOFF_VALIDATE`
6. `CLAUDE_REVIEW`
7. `MERGE_GATE`
8. `DONE_CHECK`

The phase handoff must mention any risk that:

* materialized,
* was mitigated,
* remains open,
* requires follow-up,
* requires final closeout limitation.

## Gate-Level Cadence

Ralph must evaluate gate-level risk at the end of each phase group:

| Gate                           | Phases               | Primary Risks                                                 |
| ------------------------------ | -------------------- | ------------------------------------------------------------- |
| Harness and repo foundation    | ASV1-P00 to ASV1-P01 | R-012, R-013, R-019, R-020, R-026, R-027, R-028, R-029        |
| Architecture and workspace     | ASV1-P02 to ASV1-P03 | R-009, R-014, R-017, R-023, R-040                             |
| Contracts/data/registry        | ASV1-P04 to ASV1-P08 | R-001, R-002, R-003, R-011, R-018, R-024, R-037, R-038, R-039 |
| Factor/label/diagnostics       | ASV1-P09 to ASV1-P13 | R-001, R-005, R-014, R-015, R-024, R-034, R-036               |
| Strategy/backtest/cost         | ASV1-P14 to ASV1-P16 | R-004, R-009, R-033, R-040                                    |
| Management/portfolio/fast/grid | ASV1-P17 to ASV1-P22 | R-006, R-007, R-008, R-010, R-016, R-035                      |
| ML/multi-symbol/L2             | ASV1-P23 to ASV1-P26 | R-021, R-030, R-031, R-032, R-040                             |
| Review/onboarding/closeout     | ASV1-P27 to ASV1-P29 | R-014, R-016, R-025, R-026, R-034, R-040                      |

## Final Closeout Cadence

ASV1-P29 must evaluate all risks R-001 through R-040 and classify each as:

* mitigated,
* accepted with limitation,
* blocking,
* closed.

Any Critical risk still open as a real defect must produce `BLOCKED`, not `COMPLETE`.

---

# Blocking Risk Summary

The following conditions must block merge immediately:

* known lookahead leakage,
* missing or ambiguous `available_ts` in relevant schemas,
* same-bar optimistic execution default,
* factor/label alignment defect,
* raw data staged,
* heavy artifact staged,
* runtime SQLite DB staged,
* generated Parquet staged outside allowed fixtures,
* broker/live/paper trading implementation introduced,
* fast path used before parity,
* second PnL truth introduced,
* unbounded grid expansion,
* candidate promoted without review,
* unsupported alpha/tradability claim,
* hidden failed run,
* test weakening/gaming,
* STOP file active,
* repair attempts exceeded,
* Claude review verdict `BLOCKED`,
* active worktree under `/mnt/c`, OneDrive, or Windows-synced path,
* cloud/server dependency required by v1,
* L2 replay or passive fill simulation implemented before future campaign.

The following conditions must block final campaign completion unless explicitly resolved:

* any phase missing handoff,
* any Yellow phase missing review,
* end-to-end v0.1 validation missing,
* artifact audit missing,
* final semantic done-check missing,
* known limitations missing,
* final verdict missing.

---

# Risk Ownership Summary

## Ralph

Owns workflow and merge safety:

* state machine compliance,
* STOP handling,
* phase selection,
* repair loop bounds,
* handoff validation,
* verdict parsing,
* merge gates,
* artifact audits,
* path preflight,
* no `git add .`,
* no `git add -A`.

Primary risks:

* R-012,
* R-013,
* R-016,
* R-019,
* R-020,
* R-026,
* R-027,
* R-028,
* R-029,
* R-035,
* R-038,
* R-039.

## Codex GPT-5.5 high

Owns implementation discipline:

* tests,
* source changes,
* docs/configs,
* run outputs,
* repair attempts,
* artifact policy compliance,
* no scope creep.

Primary risks:

* R-001,
* R-002,
* R-003,
* R-004,
* R-005,
* R-007,
* R-010,
* R-011,
* R-018,
* R-021,
* R-022,
* R-023,
* R-024,
* R-030,
* R-031,
* R-032,
* R-033,
* R-036,
* R-037.

## Claude Opus 4.8 xhigh

Owns semantic review and done-checks:

* architecture coherence,
* no-lookahead reasoning,
* domain boundary enforcement,
* overfit risk review,
* claim language review,
* scope control,
* acceptance-gate review.

Primary risks:

* R-001,
* R-002,
* R-004,
* R-005,
* R-006,
* R-008,
* R-009,
* R-014,
* R-015,
* R-017,
* R-021,
* R-022,
* R-023,
* R-030,
* R-031,
* R-034,
* R-036,
* R-040.

## Claude Sonnet 4.6

Owns mechanical audit support:

* source maps,
* static review,
* artifact audits,
* mechanical inspections,
* parity evidence support,
* review bundle inspection.

Primary risks:

* R-010,
* R-013,
* R-025,
* R-027,
* R-035,
* R-038,
* R-039.

## ChatGPT Pro GPT-5.5 Thinking

Owns strategic reasoning:

* campaign design,
* roadmap,
* post-run review,
* final strategic interpretation,
* whether next campaigns are justified.

Primary risks:

* R-006,
* R-008,
* R-014,
* R-023,
* R-034,
* R-040.

## Human Researcher

Owns final research interpretation:

* no overclaiming,
* deciding whether evidence justifies future phases,
* recognizing fixture vs market evidence,
* not treating review-only outputs as candidates.

Primary risks:

* R-006,
* R-008,
* R-014,
* R-024,
* R-034,
* R-040.

---

# Final Risk Policy

A truthful blocked state is acceptable.

A false complete state is unacceptable.

If a risk materially violates the campaign’s non-negotiable constraints, Ralph must stop, preserve evidence, create a blocked handoff, and prevent merge until repaired or explicitly re-scoped by a future campaign contract.
