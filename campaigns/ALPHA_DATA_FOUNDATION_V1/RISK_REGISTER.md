# ALPHA_DATA_FOUNDATION_V1 Risk Register

## Purpose

This register records the campaign-specific risks for the read-only real-market-data
truth layer, with detection methods, mitigations, owners, related phases, and blocking
conditions. Because this campaign is the data foundation that future AI alpha research
will stand on, most risks here are about **data-foundation integrity, scope creep, and
artifact discipline** — the truth layer silently failing open, forbidden trading scope
slipping in, or real data leaking into git — rather than market risk. Ralph must treat
every "Blocking condition" as a hard STOP/merge-block.

## Severity Scale

* **S1 Critical** — corrupts the data-truth guarantee, exposes order/trading scope, or commits forbidden real-data artifacts; campaign cannot be accepted.
* **S2 High** — materially weakens a data-foundation guard, provenance trail, or quality/coverage gate.
* **S3 Medium** — local correctness or clarity issue with contained impact.
* **S4 Low** — cosmetic or documentation-only issue.

## Likelihood Scale

* **L1 Rare** — unlikely given current controls.
* **L2 Possible** — plausible without explicit attention.
* **L3 Likely** — expected if not actively prevented.

## Risk Status Values

* **Open** — active and monitored.
* **Mitigated** — controls in place; residual risk accepted.
* **Closed** — no longer applicable.

## Risk Table Summary

| ID | Risk | Severity | Likelihood | Related Phases | Status |
| -- | ---- | -------- | ---------- | -------------- | ------ |
| R-001 | IBKR connector accidentally exposes order placement | S1 | L2 | DATA-P04, DATA-P03 | Open |
| R-002 | clientId collision with paper account clients 101/102 | S1 | L2 | DATA-P03 | Open |
| R-003 | TWS/IB Gateway host/port assumptions wrong under WSL2 | S2 | L3 | DATA-P03, DATA-P22 | Open |
| R-004 | IBKR pacing violations / throttling | S2 | L3 | DATA-P08, DATA-P22 | Open |
| R-005 | Incomplete historical chunks silently accepted | S1 | L2 | DATA-P08, DATA-P16 | Open |
| R-006 | Continuous futures misused as dated-contract truth | S1 | L2 | DATA-P11 | Open |
| R-007 | Expired futures availability overpromised | S2 | L2 | DATA-P06, DATA-P11 | Open |
| R-008 | Contract economics wrong: multiplier/tick/tick value | S1 | L2 | DATA-P05 | Open |
| R-009 | Roll calendar wrong or undocumented | S2 | L2 | DATA-P13 | Open |
| R-010 | Session calendar / DST / early close errors | S2 | L2 | DATA-P12, DATA-P15 | Open |
| R-011 | available_ts / event_ts lookahead semantics wrong | S1 | L2 | DATA-P15 | Open |
| R-012 | Duplicate or non-monotonic bars | S2 | L2 | DATA-P14, DATA-P16 | Open |
| R-013 | Missing volume / zero-volume anomalies ignored | S2 | L2 | DATA-P16 | Open |
| R-014 | Provider errors not recorded | S2 | L2 | DATA-P08 | Open |
| R-015 | Raw real data committed | S1 | L2 | all, esp DATA-P09, DATA-P22, DATA-P23 | Open |
| R-016 | Heavy canonical artifacts committed | S1 | L2 | all, esp DATA-P15, DATA-P24 | Open |
| R-017 | Data quality reports contain too much raw data | S2 | L2 | DATA-P16 | Open |
| R-018 | Micro and mini batches mixed incorrectly | S2 | L2 | DATA-P10, DATA-P19 | Open |
| R-019 | Optional BID_ASK requests explode pacing/storage | S2 | L2 | DATA-P20 | Open |
| R-020 | DatasetVersion not reproducible | S1 | L2 | DATA-P17 | Open |
| R-021 | Governance bypass: data used for alpha search before quality accepted | S1 | L2 | DATA-P18, all | Open |
| R-022 | Locked-test contamination begins at data foundation stage | S2 | L2 | DATA-P18 | Open |
| R-023 | Real-time/live feed creep | S1 | L2 | DATA-P04, all | Open |
| R-024 | Paper/live/broker scope creep | S1 | L2 | DATA-P04, all | Open |
| R-025 | Human authorization bypassed for external data pulls | S1 | L2 | DATA-P22, DATA-P23 | Open |

---

# Detailed Risk Entries

## R-001 — IBKR connector accidentally exposes order placement

### Description
The IBKR connector or read-only boundary leaves an order/account/trading API surface
reachable through the data module (e.g. `placeOrder`, account or position queries),
turning a historical-data path into a potential execution path.

### Impact
Forbidden order/account scope becomes reachable from the data foundation, crossing the
read-only boundary the campaign is built to protect. S1.

### Likelihood
L2 — the TWS API exposes order and account surfaces alongside historical data, so the
order surface is reachable unless explicitly blocked.

### Detection
* Read-only boundary tests asserting order/account methods are absent or kill-switched.
* Order-method kill-switch tests that fail closed if any order method is callable.
* `git grep` for order/account API surface inside `src/alpha_system/data/**`.
* Claude Opus review of the boundary; merge global-blocker on order API reachable through the data module.

### Mitigation
Read-only boundary plus an order-method kill switch; the data connector exposes only the
historical/read-only surface; `ALPHA_IBKR_READ_ONLY_MODE` defaults on; order/account paths
are unreachable and tested as such.

### Owner
Codex (boundary + kill switch) / Claude Opus (boundary review).

### Related Phases
DATA-P04, DATA-P03.

### Blocking Condition
Any order, account, or position API is reachable through the data module.

---

## R-002 — clientId collision with paper account clients 101/102

### Description
The connector accepts clientId `101` or `102`, colliding with the reserved paper-account
clients, instead of failing closed and using the data namespace `201–209` (default `201`).

### Impact
A data pull collides with paper-account client sessions, risking interference with a
separate account context and violating the clientId safety policy. S1.

### Likelihood
L2 — the existing local pattern uses `clientId=101`, so the unsafe value is a likely
default unless hard-blocked.

### Detection
* clientId guard tests asserting `101`/`102` fail closed (not a warning).
* Tests asserting default `201` and that allowed IDs stay in range `201–209`.
* Merge global-blocker on clientId `101` or `102` accepted.
* Claude Opus review of `IBKRClientIdPolicy`.

### Mitigation
Fail-closed clientId validation: forbidden `{101, 102}`, allowed range `201–209`, default
`201`, worker IDs `ES=201/NQ=202/RTY=203`; `client_id_collision_policy: fail_closed`.

### Owner
Codex (clientId guard) / Claude Opus (policy review).

### Related Phases
DATA-P03.

### Blocking Condition
clientId `101` or `102` is accepted by the connector.

---

## R-003 — TWS/IB Gateway host/port assumptions wrong under WSL2

### Description
Host/port assumptions (default `127.0.0.1:4002`) are wrong because TWS/IB Gateway runs on
the Windows host while code runs in WSL2, so the connector silently retries into the wrong
host instead of reporting reachability failure.

### Impact
Silent connection failures, wrong-host retries, or wasted authorized pull windows; pulls
appear to fail mysteriously. S2.

### Likelihood
L3 — Windows-host / WSL2-runtime split makes loopback/host reachability a common,
expected failure mode.

### Detection
* Connection doctor required before any pull; reports host/port reachability rather than retrying.
* Doctor diagnostics in `IBKRConnectionProfile` (`doctor_status`, `validated_at`).
* Configurable `ALPHA_IBKR_HOST` / `ALPHA_IBKR_PORT`; smoke-pull doctor run in DATA-P22.
* Claude Opus review of connection-doctor coverage.

### Mitigation
Connection doctor detects and reports host/port reachability failures with clear
diagnostics; no silent wrong-host retry; host/port configurable via env, default
`127.0.0.1:4002`.

### Owner
Codex (connection doctor) / Claude Opus (diagnostics review).

### Related Phases
DATA-P03, DATA-P22.

### Blocking Condition
A pull can proceed or silently retry without a passing connection-doctor reachability check.

---

## R-004 — IBKR pacing violations / throttling

### Description
A naive request loop ignores IBKR pacing limits, triggering throttling, soft bans, or
incomplete responses, especially for heavier `BID_ASK` requests.

### Impact
Throttling, dropped requests, and incomplete data; the authorized pull window is wasted
and coverage is silently degraded. S2.

### Likelihood
L3 — naive loops are the default failure mode without explicit pacing controls.

### Detection
* Pacing-guard tests; naive-loop-forbidden assertion.
* Request manifest + request-id tracking + duplicate-request detection.
* Provider error ledger records pacing/throttle errors; resume ledger reconciles attempts.
* Claude Opus review against current pacing docs or a local smoke check.

### Mitigation
`RequestPacingPolicy` with conservative, configurable throttling, chunked requests,
retry-with-backoff, request-id tracking, duplicate-request detection, and `bid_ask`
counted heavier; verify against current docs or local smoke rather than hardcoded truth.

### Owner
Codex (pacing guard + ledgers) / Claude Opus (pacing-policy review).

### Related Phases
DATA-P08, DATA-P22.

### Blocking Condition
A provider pull path runs without a pacing guard, or a naive unthrottled loop is present.

---

## R-005 — Incomplete historical chunks silently accepted

### Description
Missing or partial chunks are treated as complete, so a dataset is versioned over silent
gaps without an explicit incomplete ledger.

### Impact
Canonical data and dataset versions are built over hidden gaps, corrupting the truth
guarantee for downstream research. S1.

### Likelihood
L2 — partial responses are common and easy to mistake for completeness without a
fail-closed coverage check.

### Detection
* No-silent-gaps coverage check; coverage report `missing_intervals` / `incomplete_chunks`.
* `HistoricalPullLedger` reconciles all expected chunks; `RAW_COMPLETE` requires all chunks accounted for or an explicit incomplete ledger.
* Quality/coverage report fails closed; merge global-blocker on data gaps silently ignored.
* Claude Opus review of coverage completeness.

### Mitigation
Fail-closed coverage: every expected chunk is accounted for or explicitly recorded as
incomplete; silent gaps block versioning; `no_silent_gaps` enforced in the pull ledger.

### Owner
Codex (coverage/quality fail-closed) / Claude Opus (coverage review).

### Related Phases
DATA-P08, DATA-P16.

### Blocking Condition
A dataset is versioned while expected chunks are missing without an explicit incomplete record.

---

## R-006 — Continuous futures misused as dated-contract truth

### Description
Provider-continuous (`CONTFUT`) history is treated as dated-contract truth or as
orderable, conflating a research-diagnostic continuous series with the dated-contract
ground truth.

### Impact
Continuous-series artifacts (roll-adjusted or stitched) masquerade as contract truth,
poisoning provenance for any downstream study. S1.

### Likelihood
L2 — continuous series are convenient and easy to misuse as truth without explicit
provenance separation.

### Detection
* Provenance-separation tests: continuous series labeled `provider_continuous`, `non_orderable`, `not_dated_contract_truth`, `research_diagnostics_only`.
* `ContinuousFuturesSeriesRecord` vs `DatedFuturesSeriesRecord` distinct provenance.
* Merge global-blocker on continuous futures treated as dated-contract truth.
* Claude Opus review of provenance labeling.

### Mitigation
Keep provider-continuous, dated-contract, canonical-stitched, roll-adjusted, and
non-adjusted series explicitly separate; continuous never claims dated truth or
orderability; provenance labels mandatory.

### Owner
Codex (provenance records) / Claude Opus (provenance/claims review).

### Related Phases
DATA-P11.

### Blocking Condition
A continuous series is used or labeled as dated-contract truth or as orderable.

---

## R-007 — Expired futures availability overpromised

### Description
The campaign or contract discovery promises full dated-contract history (e.g. back to
2015/2018) through IBKR, beyond what `include_expired` actually returns.

### Impact
Coverage and roll-validation work is planned against data that does not exist; downstream
assumptions about depth of dated history are wrong. S2.

### Likelihood
L2 — dated/expired availability is easy to assume rather than discover.

### Detection
* Availability discovery logged, not assumed; `include_expired_support_status` on `FuturesContractRecord`.
* No-full-history-promise assertion in dated-futures policy and docs.
* Coverage report distinguishes discovered vs expected availability.
* Claude Opus review of any history-depth claim.

### Mitigation
Dated-contract truth is strongest only for current contracts, recent expired contracts
available from IBKR, and roll-validation windows; availability is discovered and logged;
no full-history promise.

### Owner
Codex (availability discovery + logging) / Claude Opus (claims review).

### Related Phases
DATA-P06, DATA-P11.

### Blocking Condition
A claim or plan assumes dated-contract availability that has not been discovered and logged.

---

## R-008 — Contract economics wrong: multiplier/tick/tick value

### Description
Instrument-master economics (point value, tick size, tick value, multiplier) are wrong or
internally inconsistent for ES/NQ/RTY or MES/MNQ/M2K.

### Impact
Wrong contract economics propagate silently into every downstream sizing, cost, and
quality computation. S1.

### Likelihood
L2 — per-root economics are easy to transcribe incorrectly without a consistency check.

### Detection
* Instrument-master tests asserting `tick_value = tick_size × point_value` where applicable.
* Per-root fixtures for ES/NQ/RTY and MES/MNQ/M2K against the GOAL economics anchors.
* `python -m pytest tests/unit/data`.
* Claude Opus review of `InstrumentMasterRecord` economics.

### Mitigation
First-class `InstrumentMasterRecord` economics with a `tick_value = tick_size × point_value`
consistency test; per-root values verified against official sources and repo fixtures; not
production-certified until verified.

### Owner
Codex (instrument-master + economics tests) / Claude Opus (economics review).

### Related Phases
DATA-P05.

### Blocking Condition
Any root's `tick_value` is inconsistent with `tick_size × point_value`, or economics are unverified where required.

---

## R-009 — Roll calendar wrong or undocumented

### Description
The roll policy or roll calendar uses an incorrect or undocumented roll trigger,
adjustment method, or roll dates, with no recorded evidence or validation status.

### Impact
Stitched/adjusted series carry undocumented roll discontinuities, undermining provenance
and any roll-sensitive diagnostic. S2.

### Likelihood
L2 — roll logic is subtle and easy to leave undocumented.

### Detection
* Roll-policy/roll-calendar tests; `RollCalendarRecord` requires `method`, `evidence`, `validation_status`.
* Quality report `roll_discontinuities` summary.
* Claude Opus review of roll method and evidence.

### Mitigation
`RollPolicy` and `RollCalendarRecord` document method, trigger, adjustment, evidence, and
validation status; roll discontinuities surfaced in the quality report; no tradable/best-execution roll claim.

### Owner
Codex (roll policy/calendar + tests) / Claude Opus (roll-method review).

### Related Phases
DATA-P13.

### Blocking Condition
A roll calendar is used without a documented method, evidence, and validation status.

---

## R-010 — Session calendar / DST / early close errors

### Description
Session templates or the trading calendar mishandle RTH/ETH boundaries, maintenance
breaks, DST transitions, holidays, or early closes.

### Impact
Bars are mislabeled by session or shifted across DST, corrupting session-aware views and
timestamp alignment. S2.

### Likelihood
L2 — DST and early-close edge cases are classic, easily missed defects.

### Detection
* Session-template and calendar tests covering RTH/ETH, maintenance breaks, DST, holidays, early closes.
* Quality report `dst_anomalies` and `session_coverage` summaries.
* Claude Opus review of session/DST coverage.

### Mitigation
`SessionTemplate` and `TradingCalendarRecord` with explicit timezone, RTH/ETH, breaks,
holiday, and early-close fields; DST and early-close test cases; session coverage in the
quality report.

### Owner
Codex (session/calendar + DST tests) / Claude Opus (session review).

### Related Phases
DATA-P12, DATA-P15.

### Blocking Condition
Session/DST/early-close handling is untested or produces mislabeled or DST-shifted bars.

---

## R-011 — available_ts / event_ts lookahead semantics wrong

### Description
Canonical bars conflate `available_ts`, `event_ts`, `bar_start_ts`, and `bar_end_ts`, or
`available_ts` reflects when the historical API returned the bar rather than when the
completed bar would have been usable in research/backtest semantics.

### Impact
Lookahead leakage is baked into the canonical layer, invalidating any future
point-in-time study built on it. S1.

### Likelihood
L2 — timestamp conflation is a subtle, common source of lookahead leakage.

### Detection
* No-lookahead test suite plus `available_ts` semantics checks aligned with V1 no-lookahead semantics.
* Assertions that `event_ts` / `bar_end_ts` / `available_ts` / `ingested_at` are distinct fields.
* Merge global-blocker on canonical bars missing `available_ts`.
* Claude Opus review of `TimestampSemanticsPolicy` and the canonical bar contract.

### Mitigation
`TimestampSemanticsPolicy` defines each timestamp; `available_ts` represents research/backtest
usability of the completed bar, separate from `ingested_at`; missing `available_ts` blocks
canonicalization; no-lookahead tests fail closed.

### Owner
Codex (timestamp policy + no-lookahead tests) / Claude Opus (timestamp/leakage review).

### Related Phases
DATA-P15.

### Blocking Condition
Canonical timestamp fields are conflated, missing `available_ts`, or fail no-lookahead checks.

---

## R-012 — Duplicate or non-monotonic bars

### Description
Parsed or canonical bars contain duplicate or non-monotonic timestamps that pass through
to the canonical layer without detection.

### Impact
Duplicate/out-of-order bars corrupt downstream time-series integrity and quality
accounting. S2.

### Likelihood
L2 — chunk overlaps and retries make duplicates and ordering defects plausible.

### Detection
* Parser/canonical tests for duplicate and non-monotonic bars.
* Quality report `duplicate_summary` and `non_monotonic_summary`.
* `python -m pytest tests/unit/data`.
* Claude Opus review of dedupe/ordering coverage.

### Mitigation
Parser and canonical contract enforce deduplication and monotonic ordering; duplicate and
non-monotonic summaries are mandatory in the quality report and fail closed when material.

### Owner
Codex (parser/canonical dedupe + quality checks) / Claude Opus (integrity review).

### Related Phases
DATA-P14, DATA-P16.

### Blocking Condition
Duplicate or non-monotonic bars reach the canonical layer without being detected and recorded.

---

## R-013 — Missing volume / zero-volume anomalies ignored

### Description
Missing-volume or zero-volume bars are accepted without flagging, hiding data defects or
session-edge artifacts.

### Impact
Volume anomalies pass silently into canonical data and coverage, masking real gaps or
defects. S2.

### Likelihood
L2 — zero/missing volume at session edges is common and easy to ignore.

### Detection
* Quality report `zero_volume_anomalies` and `ohlc_errors` summaries.
* Tests asserting zero/missing-volume bars are flagged, not dropped silently.
* Claude Opus review of anomaly handling.

### Mitigation
`DataQualityReport` records zero-volume and OHLC anomalies; anomalies are flagged and
surfaced rather than silently accepted or discarded.

### Owner
Codex (quality anomaly checks) / Claude Opus (anomaly review).

### Related Phases
DATA-P16.

### Blocking Condition
Missing or zero-volume anomalies are dropped or ignored without a recorded quality flag.

---

## R-014 — Provider errors not recorded

### Description
IBKR errors, retries, and incomplete responses are not logged to a permanent provider
error ledger, hiding the true failure surface of a pull.

### Impact
The provenance and resume trail is incomplete; failures and retries cannot be audited. S2.

### Likelihood
L2 — error logging is easy to omit under a working happy path.

### Detection
* `ProviderErrorRecord` tests asserting errors, codes, retries, and resolution are recorded.
* Pull ledger `error_summary` reconciliation.
* Claude Opus review of error-ledger completeness.

### Mitigation
Permanent `ProviderErrorRecord` ledger with error code, message, retryable flag, attempt,
and resolution; `require_provider_error_ledger` enforced; errors reconciled into the pull ledger.

### Owner
Codex (provider error ledger) / Claude Opus (ledger review).

### Related Phases
DATA-P08.

### Blocking Condition
A pull path can encounter provider errors that are not recorded in the error ledger.

---

## R-015 — Raw real data committed

### Description
Raw provider responses, account info, IBKR logs, or other real-data artifacts are staged
or committed instead of remaining local-only.

### Impact
Real market data / provider responses enter git, violating the artifact policy and risking
data exposure; campaign cannot be accepted. S1.

### Likelihood
L2 — raw outputs land near the repo and are easy to stage accidentally without explicit
staging discipline.

### Detection
* `git ls-files runs` returns empty; `find data -type f` excluding README/.gitkeep.
* `git grep`/audit for provider responses, account info, and credential paths.
* Pre-merge artifact audit; merge global-blockers on raw/provider/account data staged.
* Claude Opus review of the staged set.

### Mitigation
Raw data local-only under `ALPHA_DATA_ROOT` (e.g. `~/alpha_data/alpha_system`); explicit
staging only; no `git add .`/`git add -A`; `never_commit` globs enforced; raw-data commit blocks merge.

### Owner
Ralph (artifact policy + merge gating) / Codex (local-only writes).

### Related Phases
All phases, especially DATA-P09, DATA-P22, DATA-P23.

### Blocking Condition
Any raw real data, provider response, account info, or credential path is staged.

---

## R-016 — Heavy canonical artifacts committed

### Description
Heavy canonical artifacts — parquet/arrow/feather, local SQLite/DB/WAL files, npy/npz, or
generated report bundles — are staged or committed.

### Impact
Repository pollution with heavy binaries and local DBs, violating the artifact policy. S1.

### Likelihood
L2 — canonical layer and quality reports naturally produce heavy files that are easy to stage.

### Detection
* `find data/canonical`, `find metadata`, `find artifacts`; parquet/arrow/feather and DB grep.
* `git ls-files runs` empty; pre-merge artifact audit.
* Merge global-blockers on heavy artifact or local DB staged.
* Claude Opus review of the staged set.

### Mitigation
Canonical data and heavy artifacts local-only; `**/*.parquet`, `**/*.arrow`, `**/*.feather`,
`metadata/*.sqlite|*.db|*.wal`, and report bundles in `never_commit`; explicit staging only;
tiny synthetic fixtures only under `tests/fixtures/**`.

### Owner
Ralph (artifact policy + merge gating) / Codex (local-only writes).

### Related Phases
All phases, especially DATA-P15, DATA-P24.

### Blocking Condition
Any heavy canonical artifact, parquet/arrow/feather file, or local DB is staged.

---

## R-017 — Data quality reports contain too much raw data

### Description
Committed data-quality or coverage summaries embed too much raw market data (e.g. full bar
dumps) rather than aggregate statistics.

### Impact
Real data leaks into git through report bodies, partially defeating the local-only policy. S2.

### Likelihood
L2 — reports tend to inline samples for convenience unless bounded.

### Detection
* Report-content tests asserting aggregate summaries, not raw bar dumps.
* Artifact audit / grep for raw-data-like payloads in committed reports.
* Claude Opus review of curated summary content.

### Mitigation
Quality and coverage reports commit only aggregate summaries (counts, intervals, statuses);
raw bars and full series stay local-only; curated-summary-only policy enforced.

### Owner
Codex (report content bounds) / Claude Opus (summary-content review).

### Related Phases
DATA-P16.

### Blocking Condition
A committed quality/coverage report embeds raw market data beyond aggregate summaries.

---

## R-018 — Micro and mini batches mixed incorrectly

### Description
MES/MNQ/M2K micro requests are mixed into the ES/NQ/RTY mini batch, violating the
separate-batch policy and the `max_concurrent_roots` limit.

### Impact
Mixed batches confuse provenance, concurrency limits, and parity checks between mini and
micro roots. S2.

### Likelihood
L2 — convenience makes mixing batches a plausible shortcut.

### Detection
* `SymbolBatchPlan` / `MicroBatchPolicy` tests asserting `do_not_mix_mini_and_micro_batches` and `max_concurrent_roots`.
* Manifest validation rejecting mixed mini/micro request sets.
* Claude Opus review of batch separation.

### Mitigation
Mini (`ES/NQ/RTY`) and micro (`MES/MNQ/M2K`) are separate batches, never mixed; micros are
a secondary path; concurrency capped at 3 roots; parity checks declared separately.

### Owner
Codex (batch plan/policy + tests) / Claude Opus (batch-separation review).

### Related Phases
DATA-P10, DATA-P19.

### Blocking Condition
A single batch or manifest mixes mini and micro roots, or exceeds `max_concurrent_roots`.

---

## R-019 — Optional BID_ASK requests explode pacing/storage

### Description
The optional `BID_ASK` / spread-proxy pilot issues heavy `BID_ASK` requests that explode
pacing budgets and local storage beyond the conservative limits.

### Impact
Pacing budgets and local storage are blown by heavier `BID_ASK` volume, jeopardizing the
primary `TRADES` panel. S2.

### Likelihood
L2 — `BID_ASK` is heavier and easy to over-request without explicit bounds.

### Detection
* Pacing-policy `bid_ask_counts_double` accounting; pilot-plan tests bounding scope.
* Storage/scope assertions in the pilot plan; resume/error ledgers track pilot requests.
* Claude Opus review of the optional pilot scope.

### Mitigation
`BID_ASK` is an optional, clearly-bounded pilot track; pacing counts it heavier; request
scope and local storage are explicitly bounded and configurable; pilot stays secondary to
the `TRADES` panel.

### Owner
Codex (pilot plan + pacing accounting) / Claude Opus (pilot-scope review).

### Related Phases
DATA-P20.

### Blocking Condition
The `BID_ASK` pilot runs without bounded pacing/storage scope or jeopardizes the primary panel.

---

## R-020 — DatasetVersion not reproducible

### Description
A `DatasetVersion` omits or mis-binds manifest, code, config, or quality hashes, so the
canonical dataset it references cannot be reproduced or audited.

### Impact
Datasets cannot be reproduced or audited, breaking the reproducibility guarantee for
downstream research. S1.

### Likelihood
L2 — hash binding is easy to get partially wrong without explicit validation.

### Detection
* `DatasetVersion` validation requiring `manifest_hash`, `code_hash`, `config_hash`, `quality_report_hash`.
* Reproducibility tests asserting hashes bind to the referenced canonical dataset.
* `VERSIONED` requires coverage report + manifest/code/config hashes.
* Claude Opus review of version reproducibility.

### Mitigation
`DatasetVersion` records reproducible manifest/code/config/quality hashes plus source,
universe, bar size, what_to_show, start/end, contract universe, and roll policy; versioning
fails closed without complete hashes.

### Owner
Codex (dataset-version + reproducibility tests) / Claude Opus (reproducibility review).

### Related Phases
DATA-P17.

### Blocking Condition
A `DatasetVersion` is accepted without complete, correctly-bound reproducibility hashes.

---

## R-021 — Governance bypass: data used for alpha search before quality accepted

### Description
Real or canonical data is used for alpha/factor/label search or strategy work before its
quality and coverage status are accepted and before Governance metadata is attached.

### Impact
Out-of-scope alpha search proceeds on un-accepted data, bypassing the governance gates the
prior campaign installed. S1.

### Likelihood
L2 — the temptation to "just try it" on fresh data is strong without an explicit gate.

### Detection
* Scope audit: no alpha/factor/label/strategy code in this campaign (forbidden global changes).
* `READY_FOR_RESEARCH` requires dataset version + non-blocking quality + coverage + artifact pass.
* Merge global-blockers on real alpha search / factor-label/strategy scope.
* Claude Opus review and semantic done-check.

### Mitigation
Data foundation layer is explicitly not alpha search; `READY_FOR_RESEARCH` is the only
research-eligible state and requires accepted quality/coverage; alpha/factor/label/strategy
scope is forbidden in every phase.

### Owner
Ralph (scope/stop enforcement) / Claude Opus (scope + done-check review).

### Related Phases
DATA-P18, all phases.

### Blocking Condition
Data is used for alpha/factor/label/strategy work before reaching `READY_FOR_RESEARCH` with accepted quality.

---

## R-022 — Locked-test contamination begins at data foundation stage

### Description
The locked-test partition (`2025-01-01 → as_of_run`) is touched or used without
contamination metadata at the data-foundation stage, silently contaminating the held-out
window before any research begins.

### Impact
The locked-test window loses its held-out meaning before research starts, weakening future
validation. S2.

### Likelihood
L2 — partition QA may inadvertently use locked data without recording contamination.

### Detection
* `DatasetPartitionPlan` contamination-metadata rules; partition/contamination metadata checks.
* Tests asserting locked-partition use creates contamination metadata.
* Claude Opus review of partition handling.

### Mitigation
Define development/validation/locked partitions; data QA may inspect coverage across
partitions, but any use of the locked partition requires contamination metadata; no
locked-partition research use without Governance metadata.

### Owner
Codex (partition + contamination metadata) / Claude Opus (partition review).

### Related Phases
DATA-P18.

### Blocking Condition
The locked-test partition is used without recorded contamination metadata.

---

## R-023 — Real-time/live feed creep

### Description
A real-time L1 quote stream, live market-data loop, or real-time signal path is introduced
under the guise of historical-data work.

### Impact
Real-time/live feed scope enters the read-only historical foundation, crossing the campaign
boundary. S1.

### Likelihood
L2 — the same API exposes live feeds, so real-time creep is plausible without explicit
prohibition.

### Detection
* Forbidden-scope audit for real-time/live feed code; `real_time_feed_forbidden` policy.
* Read-only boundary tests; merge global-blocker on real-time scope.
* Claude Opus review; stop-and-escalate on real-time scope.

### Mitigation
Historical data only; no L1 live quote stream, live market-data loop, or real-time signal
loop; `real_time_feed_forbidden: true`; real-time scope triggers STOP/escalation.

### Owner
Ralph (scope/stop enforcement) / Claude Opus (boundary review).

### Related Phases
DATA-P04, all phases.

### Blocking Condition
Any real-time quote, live feed, or real-time signal-loop scope appears.

---

## R-024 — Paper/live/broker scope creep

### Description
Broker integration, paper trading, live trading, order routing, order placement, account
trading, or a production execution adapter is introduced.

### Impact
Forbidden trading/broker scope enters the data foundation, the highest-risk boundary
violation for this campaign. S1.

### Likelihood
L2 — the broker/order surface is adjacent in the same API and explicitly out of scope.

### Detection
* Global forbidden paths (`execution/broker|live|paper|order_router`, `broker/**`, `live/**`).
* Dependency/forbidden-path audit; merge global-blocker on broker/live/paper/order-routing scope.
* Claude Opus review; stop-and-escalate on trading scope.

### Mitigation
Global forbidden paths and forbidden global changes block broker/paper/live/order/account
scope in every lane; RED here authorizes read-only IBKR pulls and heavy local writes only,
never trading; trading scope triggers STOP/escalation.

### Owner
Ralph (scope/stop enforcement + merge gating) / Claude Opus (boundary review).

### Related Phases
DATA-P04, all phases.

### Blocking Condition
Any broker, paper, live, order-routing, order-placement, account-trading, or execution-adapter scope appears.

---

## R-025 — Human authorization bypassed for external data pulls

### Description
An external IBKR historical pull is attempted without the required RED-lane scope and
data-pull authorization, or such a pull is attempted in CI.

### Impact
An external provider call runs without human authorization or in CI, violating the RED-lane
and external-call policy. S1.

### Likelihood
L2 — automation may attempt a convenient external call without the authorization gate.

### Detection
* RED-lane authorization checks: `PROJECT_OP_AUTHORIZED` / `PROJECT_OP_SCOPE` / `PROJECT_OP_EXPIRES` present, scope-matched, unexpired.
* Data-pull authorization: `ALPHA_DATA_PULL_AUTHORIZED` and `ALPHA_ALLOW_EXTERNAL_IBKR` required; never in CI.
* Merge global-blocker on external IBKR pull attempted without authorization; `real_data_pull_forbidden_in_ci`.
* Claude Opus review; RED auto-merge disabled (human gate).

### Mitigation
External IBKR pulls require scoped RED authorization plus data-pull env, run local-only,
never in CI, with `auto_merge: false` for RED; the human owns the final external-pull
decision; missing authorization fails closed.

### Owner
Ralph (RED authorization + merge gating) / Human (final external-pull judgment).

### Related Phases
DATA-P22, DATA-P23.

### Blocking Condition
An external IBKR pull is attempted without scoped + data-pull authorization, or any external pull runs in CI.

---

## Blocking Risk Summary

The following are hard STOP/merge-block conditions: R-001, R-002, R-005, R-006, R-008,
R-011, R-015, R-016, R-020, R-021, R-023, R-024, R-025. Any of these makes the affected
phase ineligible for merge until resolved or truthfully blocked.

## Risk Review Cadence

* Per phase: Claude Opus review checks the risks tied to that phase's Related Phases.
* Per gate: the acceptance gate re-checks all blocking risks for its phases.
* RED phases (DATA-P22, DATA-P23): authorization and CI-exclusion blockers (R-025) are re-verified before any external call.
* Campaign closeout (DATA-P24): full register reviewed in the semantic done-check.

## Risk Ownership Summary

* **Ralph** — artifact policy, scope/stop enforcement, RED authorization, and merge gating (R-015, R-016, R-021, R-023, R-024, R-025).
* **Codex** — fail-closed validation, ledgers, parsers, quality/coverage, and contract economics (R-001, R-002, R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-012, R-013, R-014, R-017, R-018, R-019, R-020, R-022).
* **Claude Opus** — semantic review of boundary, provenance, timestamps, claims, and done-check (R-006, R-011, and the semantic review side of every risk).
* **Human** — direction and final external-pull and capital/live judgment (R-025).
