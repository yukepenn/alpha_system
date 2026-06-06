# ALPHA_RESEARCH_RUNTIME_MVP Risk Register

## Purpose

This register records the campaign-specific risks for the **Research Runtime MVP**: the
executable, local, deterministic **research loop layer** that sits between the
Feature/Label substrate (`ALPHA_FEATURE_LABEL_FOUNDATION_V1`, COMPLETE 32/32
COMPLETE_WITH_WARNINGS) and the future Agent Factory. The runtime turns an approved
`AlphaSpec` + `StudySpec` into a bounded pipeline — resolve accepted `DatasetVersion` +
Feature/Label packs → Tier 0 factor diagnostics → label diagnostics → simple signal probe →
cost stress → bounded variant budget → `EvidenceDraft` → `ReferenceCandidateHandoff`, **or**
`REJECTED` / `INCONCLUSIVE` / `BLOCKED`. It does this by **orchestrating existing primitives**
(`alpha_system.research.*`, `alpha_system.backtest.costs`/`slippage`,
`alpha_system.experiments.*`, `alpha_system.governance.*`,
`alpha_system.data.foundation.version_registry.resolve_dataset_version`,
`alpha_system.features.*` / `labels.*`) inside the **new** package
`src/alpha_system/runtime/` plus an additive `alpha runtime ...` CLI surface. It does **not**
re-implement those primitives.

This campaign is **runtime orchestration construction only**. It does **not** run alpha
search, does **not** promote a factor, does **not** build a `FactorLibrary`, a Portfolio
AlphaBook, or a Strategy Reference Validation, does **not** call Databento/IBKR, and does
**not** introduce any order/account/paper/live/broker scope. Most risks here are therefore
about **orchestration discipline, no-lookahead safety at runtime, primitive/governance reuse,
fast-path-vs-Reference scope honesty, cost/anti-overfit rigor, parallel-DAG correctness, and
artifact discipline** — the runtime drifting into ad hoc alpha search, bypassing the
`DatasetVersion` boundary, overclaiming a probe or a draft, hiding a failed run, or committing
forbidden values — rather than market risk.

A diagnostic PASS is **not** alpha validation. A signal probe is **not** a strategy
candidate. A bounded grid is **not** promotion. An `EvidenceDraft` is **not** a candidate. A
`ReferenceCandidateHandoff` is **not** Reference validation. The fast path is **not**
Reference truth. The register reflects that framing: every "Blocking condition" below is a
hard STOP/merge-block that Ralph must enforce through the serial merge queue, and most map
directly to the `merge_policy.global_blockers` and `stop_conditions` lists in `campaign.yaml`.

## Severity Scale

* **S1 Critical** — bakes lookahead/leakage into the runtime, exposes forbidden
  trading/broker/order/alpha-search/factor-promotion scope, makes an unsupported
  alpha/tradability/profitability claim, reads raw provider data, calls an external provider,
  or commits forbidden raw/canonical/value/heavy/DB artifacts; the campaign cannot be
  accepted.
* **S2 High** — materially weakens a runtime guard, the primitive/governance-reuse boundary,
  the fast-path-vs-Reference scope honesty, cost/anti-overfit rigor, the agent-facing tool
  contract, or a parallel-DAG/merge-queue invariant.
* **S3 Medium** — local correctness, performance, or clarity issue with contained impact.
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

| ID | Name | Severity | Likelihood | Blocking? |
| -- | ---- | -------- | ---------- | --------- |
| R-001 | Runtime becomes ad hoc alpha search | S1 | L2 | Yes |
| R-002 | Runtime bypasses DatasetVersion | S1 | L2 | Yes |
| R-003 | Runtime reads raw provider data | S1 | L2 | Yes |
| R-004 | Diagnostics run without AlphaSpec / StudySpec | S2 | L2 | Yes |
| R-005 | Fast path mistaken for Reference truth | S2 | L2 | Yes |
| R-006 | Signal probe mistaken for strategy validation | S2 | L2 | Yes |
| R-007 | Evidence draft mistaken for candidate | S2 | L2 | Yes |
| R-008 | Grid / variant explosion | S2 | L3 | Yes |
| R-009 | Locked-test contamination | S1 | L2 | Yes |
| R-010 | Cost stress omitted or weak | S2 | L2 | Yes |
| R-011 | BBO cost/slippage proxy overclaimed | S2 | L2 | No |
| R-012 | Session / RTH / ETH split omitted | S2 | L2 | No |
| R-013 | Cross-market timestamp misalignment | S2 | L2 | No |
| R-014 | No-lookahead runtime audit incomplete | S1 | L2 | Yes |
| R-015 | Failed / inconclusive runs hidden | S2 | L2 | Yes |
| R-016 | Runtime reports claim alpha / profitability | S1 | L2 | Yes |
| R-017 | Tool output exposes raw / heavy data | S2 | L2 | Yes |
| R-018 | Runtime artifacts committed accidentally | S1 | L2 | Yes |
| R-019 | Agent Factory later cannot consume tool outputs | S2 | L2 | No |
| R-020 | CLI surface diverges from repo conventions | S3 | L2 | No |
| R-021 | Runtime too slow for Agent Factory | S3 | L2 | No |
| R-022 | Runtime overbuilt into distributed platform prematurely | S2 | L2 | No |
| R-023 | DAG scheduler metadata wrong | S2 | L2 | Yes |
| R-024 | Parallel phase path conflict | S2 | L2 | Yes |
| R-025 | Reference handoff lacks required versions / manifests | S2 | L2 | No |
| R-026 | Governance / primitive objects bypassed or duplicated | S2 | L3 | Yes |
| R-027 | Research state machine lacks reject / inconclusive / block distinction | S2 | L2 | Yes |

---

# Detailed Risk Entries

## R-001 — Runtime becomes ad hoc alpha search

### Description
The runtime drifts from "execute one approved `AlphaSpec` + `StudySpec` through a bounded
pipeline" into broad, undirected alpha discovery — sweeping factor families, mining
combinations, ranking candidates, or promoting a survivor — turning the executable research
loop into an unbounded search engine and a de facto `FactorLibrary`/promotion path.

### Impact
The runtime exceeds its charter as the orchestration layer (it is **not** Agent Factory,
**not** alpha search, **not** a `FactorLibrary`), re-creating a factor zoo and a promotion
path the MVP explicitly forbids, and inviting the prohibited states `ALPHA_VALIDATED` /
`FACTOR_PROMOTED`. S1.

### Likelihood
L2 — once diagnostics and a bounded grid exist, "just sweep a few more variants" is a natural
slide into search unless the per-run `AlphaSpec`/`StudySpec` scope and the `VariantBudget` are
hard limits.

### Detection
* `runtime_policy`: `no_alpha_search: true`, `no_factor_promotion: true`,
  `no_strategy_wrappers_as_research_products: true`; every run is bound to one approved
  `AlphaSpec` + `StudySpec` (`alpha_spec_required` / `study_spec_required`).
* `BoundedGridSpec` + `VariantBudget` (RT-P13) consume `alpha_system.experiments.limits`;
  unbounded grids fail closed.
* `risk_controls.runtime_not_alpha_search` (scope audit, import audit, Claude review);
  `merge_policy.global_blockers`: `factor promotion or alpha search scope introduced`.
* Claude Opus review of RT-P12/RT-P13 scope and the semantic done-check (RT-P26).

### Mitigation
The runtime executes a single approved spec pair per run; `no_alpha_search` /
`no_factor_promotion` are policy; the `VariantBudget` bounds every grid; prohibited MVP states
(`ALPHA_VALIDATED`, `FACTOR_PROMOTED`) are unreachable by any transition; the most advanced
survivor state is `REFERENCE_HANDOFF_READY`.

### Owner
Codex (spec-bound runs + bounded grid) / Claude Opus (scope review) / Ralph (scope/stop
enforcement + merge gating).

### Related Phases
RT-P04, RT-P12, RT-P13, RT-P15, RT-P26.

### Blocking Condition
Broad alpha search, factor promotion, or candidate-promotion scope appears, or a run executes
outside its approved `AlphaSpec`/`StudySpec` budget.

---

## R-002 — Runtime bypasses DatasetVersion

### Description
Runtime input resolution produces feature/label/diagnostic inputs without resolving an
**accepted** `DatasetVersion` through the sanctioned
`alpha_system.data.foundation.version_registry.resolve_dataset_version` boundary — e.g.
reading a registry table directly, hard-coding a path, or accepting a non-admissible version
state.

### Impact
The single sanctioned consumption boundary is broken: the runtime consumes data that has not
passed quality/coverage/admissibility gating, so every downstream diagnostic, probe, and
handoff inherits ungated, possibly contaminated inputs. S1.

### Likelihood
L2 — convenience access to a known registry/path is plausible in the input resolver unless the
only sanctioned API is enforced and admissibility is checked.

### Detection
* `dataset_consumption_policy`: `accepted_dataset_versions_required: true`,
  `sanctioned_consumption_api: ...resolve_dataset_version`, admissible states limited to
  `{VERSIONED, READY_FOR_RESEARCH}`; RT-P03 input-resolver tests assert resolution goes only
  through the sanctioned API.
* `risk_controls.accepted_dataset_version_required` (input resolver tests, Claude review);
  `merge_policy.global_blockers`: `accepted DatasetVersion bypassed`.
* `forbidden_paths` block `src/alpha_system/data/**` edits from runtime phases.
* Claude Opus review of RT-P03 resolution semantics.

### Mitigation
`resolve_dataset_version` is the only resolution path; only `VERSIONED`/`READY_FOR_RESEARCH`
versions are admissible; Databento and IBKR versions are never merged
(`no_merge_of_databento_and_ibkr_versions: true`); bypass is fail-closed and merge-blocking.

### Owner
Codex (input resolver + admissibility checks) / Claude Opus (boundary review).

### Related Phases
RT-P01, RT-P03, RT-P21, RT-P25.

### Blocking Condition
Runtime inputs are produced without resolving an admissible `DatasetVersion` through
`resolve_dataset_version`.

---

## R-003 — Runtime reads raw provider data

### Description
Runtime code reads raw provider files directly (`.dbn`, `.zst`, parquet, arrow, feather, or
any provider response) instead of consuming canonical records
(`CanonicalBarRecord`/`CanonicalBBORecord`/`DenseGridBarRecord`) from an accepted
`DatasetVersion`, bypassing the no-lookahead and admissibility guarantees that ride on
canonical records.

### Impact
The runtime consumes provider artifacts and possible lookahead that canonical gating exists to
remove, corrupting every diagnostic and probe built on top — the most direct raw-bypass
failure mode for an orchestration layer. S1.

### Likelihood
L2 — raw provider files are already local and convenient, so a shortcut into them is plausible
without an explicit forbidden-path guard and import audit.

### Detection
* `dataset_consumption_policy`: `raw_provider_access_forbidden: true`, `canonical_records_only`
  limited to the three canonical record types.
* Forbidden-path globs in every phase (`data/raw/**`, `data/canonical/**`, `**/*.dbn`,
  `**/*.zst`, `**/*.parquet`, `**/*.arrow`, `**/*.feather`); import/source-path audit asserts
  no runtime module imports a provider reader or opens raw files.
* `risk_controls.no_raw_provider_access` (source path audit, import audit, Claude review);
  `merge_policy.global_blockers`: `raw provider data read by runtime code`;
  `stop_conditions`: `raw provider data read by runtime code`.
* Claude Opus review of RT-P03 input loaders.

### Mitigation
Runtime consumes only canonical records resolved from accepted `DatasetVersions`; raw provider
files are forbidden paths; provider readers are never imported by runtime code; raw access is
fail-closed and merge-blocking.

### Owner
Codex (canonical-only loaders + import guards) / Claude Opus (boundary review).

### Related Phases
RT-P03, RT-P07, RT-P08, RT-P21.

### Blocking Condition
Any runtime code reads a raw provider file or opens `.dbn`/`.zst`/parquet/arrow/feather
directly.

---

## R-004 — Diagnostics run without AlphaSpec / StudySpec

### Description
A diagnostics, signal-probe, or grid run is executed without a bound, approved `AlphaSpec` and
`StudySpec` reference, so a runtime study runs ungoverned, untraceable to a hypothesis, and
outside the governance scope the runtime is meant to honor.

### Impact
Ungoverned runs enter the runtime, defeating the spec-gate the campaign installs, breaking
provenance from hypothesis to evidence, and re-opening an ad hoc-search path (cross-links
R-001). S2.

### Likelihood
L2 — wiring the spec requirement is easy to forget for a "quick" diagnostic, and one bypass
normalizes more.

### Detection
* `runtime_policy`: `alpha_spec_required: true`, `study_spec_required: true`;
  `consumes_study_input_pack: true` (consumes `alpha_system.governance.study_input_pack`).
* `RuntimeRequest`/`StudyRunSpec` contracts (RT-P04) require `AlphaSpec` + `StudySpec`
  references; tests prove fail-closed behavior when either is absent.
* `risk_controls.alpha_spec_and_study_spec_required` (runtime request contract tests, Claude
  review); `stop_conditions`: `runtime study run without AlphaSpec or StudySpec`.
* Claude Opus review of RT-P04 request contracts and RT-P07/RT-P12 entry points.

### Mitigation
No runtime study run without an approved `AlphaSpec` + `StudySpec`; the `RuntimeRequest`
contract binds both and consumes the governance `StudyInputPack`; missing specs fail closed
and are merge-blocking.

### Owner
Codex (spec-bound request contracts) / Claude Opus (spec-gate review).

### Related Phases
RT-P01, RT-P04, RT-P07, RT-P12.

### Blocking Condition
A diagnostics, probe, or grid run is executed without a bound, approved `AlphaSpec` and
`StudySpec`.

---

## R-005 — Fast path mistaken for Reference truth

### Description
A fast-path runtime result (the local, deterministic, bounded diagnostics/probe pipeline) is
presented or recorded as Reference truth — i.e. as completed Strategy Reference Validation —
conflating the cheap, fast screening layer with the slower, authoritative Reference process
the runtime explicitly does not perform.

### Impact
Downstream consumers treat a fast screening result as validated Reference truth, overstating
the runtime's authority (the fast path is **not** Reference truth; the runtime is **not**
Strategy Reference Validation) and corrupting the evidence chain to the Agent Factory. S2.

### Likelihood
L2 — a clean fast-path PASS is easy to describe as if it were the final word unless the
fast-path-vs-Reference distinction is enforced in contracts and language.

### Detection
* `runtime_policy`: `fast_path_not_reference_truth: true`,
  `reference_handoff_not_reference_validation: true`.
* `risk_controls.fast_path_not_reference_truth` (evidence/handoff tests, doc grep, Claude
  review); `merge_policy.global_blockers` / `stop_conditions`:
  `fast path treated as Reference truth`.
* `RuntimeReportCard` / `RuntimeRunSummary` and `EvidenceDraft` carry explicit
  fast-path/non-Reference labels (RT-P16, RT-P23).
* Claude Opus review of RT-P16/RT-P17 wording and the semantic done-check.

### Mitigation
Fast-path results are labeled fast-path screening, never Reference truth; the
`ReferenceCandidateHandoff` is explicitly a handoff, not Reference validation; contracts and
docs carry the distinction; a fast-path-as-Reference claim is fail-closed and merge-blocking.

### Owner
Codex (fast-path labeling in contracts/reports) / Claude Opus (scope-honesty review).

### Related Phases
RT-P12, RT-P16, RT-P17, RT-P23, RT-P26.

### Blocking Condition
A fast-path runtime result is presented or recorded as Reference truth / completed Reference
validation.

---

## R-006 — Signal probe mistaken for strategy validation

### Description
A `SignalProbeReport` (a deliberately simple, cost-aware signal screen) is presented as
strategy validation, a tradable strategy candidate, or a backtest result — overstating what a
probe establishes and edging into forbidden strategy/backtest scope.

### Impact
A cheap directional/IC-style probe is misread as a validated strategy, fabricating downstream
confidence and crossing into strategy/backtest scope the campaign forbids (a signal probe is
**not** a strategy candidate). S2.

### Likelihood
L2 — probe outputs resemble mini-backtests, so describing one as a "strategy result" is an
easy overstatement without an explicit guard.

### Detection
* `runtime_policy`: `signal_probe_not_strategy_validation: true`;
  `strategy_backtest_portfolio_in_scope: false`.
* RT-P12 `SignalProbeSpec`/`SignalProbeReport` are labeled probe-only; tests assert no
  strategy/candidate framing.
* `risk_controls.no_strategy_scope` (source path audit, dependency audit, Claude review);
  `stop_conditions`: `signal probe called strategy validation`;
  `merge_policy.global_blockers`: `signal probe called strategy validation`.
* Claude Opus review of RT-P12 probe semantics and report language.

### Mitigation
The signal probe is a simple, cost-aware screen labeled as such; it is never strategy
validation or a candidate; no strategy/backtest/portfolio wrapper is introduced; a
probe-as-strategy claim is fail-closed and merge-blocking.

### Owner
Codex (probe-only contracts/reports) / Claude Opus (probe-scope review).

### Related Phases
RT-P12, RT-P16, RT-P23.

### Blocking Condition
A signal probe is presented as strategy validation, a tradable candidate, or a backtest
result.

---

## R-007 — Evidence draft mistaken for candidate

### Description
An `EvidenceDraft` (a structured summary of diagnostics/probe/cost results feeding the
governance `EvidenceBundle`) is presented as a promoted candidate, a validated alpha, or a
completed `EvidenceBundle`, conflating draft assembly with promotion.

### Impact
A draft is read as a candidate, overstating the runtime's output (an `EvidenceDraft` is **not**
a candidate) and inviting the prohibited states `FACTOR_PROMOTED` / `ALPHA_VALIDATED`. S2.

### Likelihood
L2 — "evidence" language invites a promotion reading unless the draft-vs-candidate distinction
is enforced in contracts and language.

### Detection
* `runtime_policy`: `evidence_draft_not_candidate: true`,
  `feeds_governance_evidence_bundle: true` (RT-P16 feeds
  `alpha_system.governance.evidence_bundle`, does not finalize it).
* `risk_controls.fast_path_not_reference_truth` (evidence/handoff tests, doc grep, Claude
  review); `merge_policy.global_blockers` / `stop_conditions`:
  `EvidenceDraft treated as candidate`.
* Prohibited MVP states (`FACTOR_PROMOTED`, `ALPHA_VALIDATED`) are unreachable (RT-P15).
* Claude Opus review of RT-P16 draft semantics and the semantic done-check.

### Mitigation
The `EvidenceDraft` is explicitly a draft input to the governance `EvidenceBundle`, never a
candidate or a finalized bundle; promotion states are unreachable; a draft-as-candidate claim
is fail-closed and merge-blocking.

### Owner
Codex (draft-only builder feeding governance) / Claude Opus (draft-scope review).

### Related Phases
RT-P15, RT-P16, RT-P17, RT-P26.

### Blocking Condition
An `EvidenceDraft` is presented as a promoted candidate, validated alpha, or completed
`EvidenceBundle`.

---

## R-008 — Grid / variant explosion

### Description
A bounded grid runs without an enforced `VariantBudget`, or exceeds it — sweeping too many
parameter combinations, re-running variants until something passes, or selecting on the
locked-test partition — so the runtime overfits by search and re-creates a tuning factory.

### Impact
Unbounded or budget-exceeding grids manufacture spurious passes through multiplicity,
defeating the anti-overfit discipline the runtime is meant to enforce (a bounded grid is
**not** promotion) and biasing every downstream `EvidenceDraft`. S2.

### Likelihood
L3 — expanding a grid "just a little" is the path of least resistance once the grid runner
exists, so explosion is expected unless the `VariantBudget` is a hard, recorded limit.

### Detection
* `anti_overfit_policy`: `variant_budget_required: true`, `no_unbounded_grid: true`,
  `no_selection_on_locked_test: true`, `repeated_run_records_required: true`; RT-P13
  consumes `alpha_system.experiments.limits` / `experiments.overfit_controls` /
  `experiments.splits` / `experiments.survivors`.
* `risk_controls.variant_budget_required` (bounded grid tests, experiments.limits
  enforcement, Claude review); `merge_policy.global_blockers` / `stop_conditions`:
  `bounded grid unbounded or variant budget exceeded`.
* Claude Opus review of RT-P13 budget enforcement and repeated-run records.

### Mitigation
Every grid is bound by a `VariantBudget` enforced via `experiments.limits`; unbounded grids
and locked-test selection fail closed; repeated runs are recorded; the bounded grid is never
treated as promotion.

### Owner
Codex (bounded grid + budget enforcement) / Claude Opus (anti-overfit review).

### Related Phases
RT-P13, RT-P14, RT-P15, RT-P25.

### Blocking Condition
A grid runs without a `VariantBudget`, exceeds the configured budget, or selects on the
locked-test partition.

---

## R-009 — Locked-test contamination

### Description
The locked-test partition (`locked_test_candidate` `2025-01-01 → as_of_run`, or a
`latest_shadow_candidate` rolling window) is consumed for diagnostics, normalization, probe
fitting, or grid selection without recording governance contamination metadata, silently
contaminating the held-out window the runtime is meant to protect.

### Impact
The locked-test window loses its held-out meaning at the runtime stage, weakening future
out-of-sample validation for everything the runtime feeds into the Agent Factory and Reference
process. S1.

### Likelihood
L2 — partition handling and any normalization/fit step can inadvertently touch locked data
without recording contamination, especially across diagnostics and the bounded grid.

### Detection
* `partition_policy`: `locked_test_metadata_required: true`,
  `locked_test_use_requires_governance_metadata: true`,
  `partition_contamination_must_be_recorded: true`; partitions are development 2018–2022,
  validation 2023–2024, locked_test_candidate 2025–as_of_run.
* `dataset_consumption_policy`: `locked_partition_use_requires_governance_metadata: true`;
  `anti_overfit_policy`: `no_selection_on_locked_test: true`,
  `locked_test_contamination_metadata_required: true`.
* `merge_policy.global_blockers` / `stop_conditions`:
  `locked-test partition used without contamination metadata`.
* Claude Opus review of partition handling in RT-P03 and the diagnostics/grid phases.

### Mitigation
Any locked-partition use flows through the governance contamination gate and records metadata;
normalization/fit/selection default to development/validation partitions; locked-test
selection is forbidden; uncontrolled locked use is fail-closed and merge-blocking.

### Owner
Codex (partition gating + contamination metadata) / Claude Opus (partition review).

### Related Phases
RT-P03, RT-P13, RT-P14, RT-P25.

### Blocking Condition
The locked-test (or shadow) partition is consumed without recorded governance contamination
metadata, or is used for selection.

---

## R-010 — Cost stress omitted or weak

### Description
A signal probe or `ReferenceCandidateHandoff` is produced without cost stress, or with weak
cost stress — missing the double-cost stress, omitting a `CostModelVersion`, or using a
zero-cost result as a promotion basis — so a result looks favorable only before transaction
costs.

### Impact
Cost-blind or weakly cost-stressed results overstate signal quality, biasing the runtime's
evidence toward signals that survive only at zero cost — the cost-unaware-backtest failure
mode the runtime exists to prevent. S2.

### Likelihood
L2 — base-case (or zero-cost) results are the simplest to produce and tend to dominate unless
double-cost stress and a `CostModelVersion` are required for every probe/handoff.

### Detection
* `cost_policy`: `cost_model_version_required: true`, `base_stress_required: true`,
  `double_cost_required: true`, `bbo_spread_crossing_required_if_available: true`,
  `session_specific_cost_required: true`, `zero_cost_not_promotion_basis: true`; RT-P11
  consumes `alpha_system.backtest.costs` / `backtest.slippage`.
* `risk_controls.cost_stress_required` (cost stress tests, Claude review);
  `merge_policy.global_blockers` / `stop_conditions`: `cost stress omitted for probe or
  handoff`, `zero-cost result used as promotion basis`.
* Claude Opus review of RT-P11/RT-P12/RT-P17 cost coverage.

### Mitigation
Every probe and handoff carries a `CostStressSpec` with base + double cost and a
`CostModelVersion`; session-specific costs apply; slippage is a labeled proxy; zero-cost is
never a promotion basis; omitted/weak cost stress is fail-closed and merge-blocking.

### Owner
Codex (cost stress runtime + coverage) / Claude Opus (cost-rigor review).

### Related Phases
RT-P11, RT-P12, RT-P17, RT-P25.

### Blocking Condition
A signal probe or `ReferenceCandidateHandoff` is produced without double-cost stress / a
`CostModelVersion`, or a zero-cost result is used as a promotion basis.

---

## R-011 — BBO cost/slippage proxy overclaimed

### Description
The BBO-spread-crossing cost model and the slippage proxy used in cost stress are described or
treated as a realistic/validated execution cost rather than as a labeled proxy, overstating
the precision of the runtime's cost adjustment.

### Impact
Cost-stressed results are read as if they reflect realized execution costs, overstating
confidence in cost-survivability (a proxy is not a validated cost). S2.

### Likelihood
L2 — a concrete spread/slippage number invites a realism claim unless it is explicitly labeled
a proxy in contracts and reports.

### Detection
* `cost_policy`: `slippage_proxy_must_be_labeled_proxy: true`,
  `bbo_spread_crossing_required_if_available: true`; `risk_controls.cost_stress_required`
  rule `slippage_labeled_proxy: true`.
* `CostSensitivityReport` (RT-P11) labels slippage as a proxy; doc grep for unqualified cost
  realism claims.
* Claude Opus review of RT-P11 cost/slippage wording.

### Mitigation
`CostModelVersion` and the slippage component are labeled proxies; the
`CostSensitivityReport` states the proxy nature and uses BBO spread crossing when available;
no realized-execution-cost claim is made. (Descriptive cost stress only — no tradability
claim.)

### Owner
Codex (proxy-labeled cost contracts) / Claude Opus (cost-claim review).

### Related Phases
RT-P11, RT-P12, RT-P17.

### Blocking Condition
None on its own (S2, non-blocking); escalates to R-016 if the proxy is presented as a
validated/realistic execution cost or used to support a tradability/profitability claim.

---

## R-012 — Session / RTH / ETH split omitted

### Description
Diagnostics are reported only in aggregate, omitting the required session / RTH / ETH and
regime splits, so a result that is concentrated in one session or regime is presented as if it
held uniformly.

### Impact
Aggregate-only diagnostics hide session/regime concentration, overstating the breadth of a
result and weakening the descriptive picture the runtime is meant to provide. S2.

### Likelihood
L2 — aggregate reporting is the simplest default and easy to ship without the session/regime
breakdowns unless they are required.

### Detection
* `diagnostics_policy`: `session_split_required: true`, `rth_eth_split_required: true`,
  `regime_split_required: true`; RT-P09 produces `SessionSplitReport` /
  `RegimeSplitReport` (orchestrating `alpha_system.research.regimes`).
* RT-P09 tests assert splits are present; the diagnostics gate requires
  `split_diagnostics_runtime_present`.
* Claude Opus review of RT-P09 split coverage.

### Mitigation
Session/RTH/ETH and regime splits are first-class outputs of the split-diagnostics runtime;
diagnostics are descriptive and non-promotional; the diagnostics acceptance gate requires the
split runtime.

### Owner
Codex (split diagnostics runtime) / Claude Opus (split-coverage review).

### Related Phases
RT-P09, RT-P25.

### Blocking Condition
None on its own (S2, non-blocking); flagged in the diagnostics gate review when required
session/RTH/ETH/regime splits are absent.

---

## R-013 — Cross-market timestamp misalignment

### Description
Cross-market ES/NQ/RTY diagnostics align series on the wrong timestamp (mixing `event_ts`
across instruments or ignoring per-instrument `available_ts`), so a cross-market
spread/correlation is computed across non-contemporaneous or future-peeking bars.

### Impact
Cross-market diagnostics are computed over misaligned bars, producing spurious cross-market
signal and possible lookahead in the multi-instrument reports. S2.

### Likelihood
L2 — aligning three instruments correctly on `available_ts` is error-prone, and a naive join
can silently peek forward on the slower-arriving instrument.

### Detection
* `diagnostics_policy`: `cross_market_diagnostics_required_for_multi_instrument: true`; RT-P10
  aligns strictly on `available_ts` (orchestrating `alpha_system.research.correlation`); tests
  assert contemporaneous, no-lookahead alignment.
* `dataset_consumption_policy`: `no_merge_of_databento_and_ibkr_versions: true`; the
  no-lookahead runtime audit (RT-P14) covers the cross-market join.
* Claude Opus review of RT-P10 alignment semantics.

### Mitigation
Cross-market diagnostics align on common `available_ts`; no cross-instrument forward peeking;
ES/NQ/RTY are drawn from a single accepted `DatasetVersion` family, never a Databento+IBKR
merge.

### Owner
Codex (cross-market alignment + tests) / Claude Opus (alignment review).

### Related Phases
RT-P10, RT-P14.

### Blocking Condition
None on its own (S2, non-blocking); escalates to R-014 (blocking) if the misalignment
introduces lookahead or a missing `available_ts`.

---

## R-014 — No-lookahead runtime audit incomplete

### Description
The `NoLookaheadRuntimeAudit` omits a required check — `available_ts` on feature inputs,
`label_available_ts` on label inputs, same-bar fill semantics in the signal probe, or
locked-test contamination metadata — so the runtime's central leakage guard does not actually
prove no-lookahead.

### Impact
Lookahead can ride into diagnostics, the probe, or the evidence draft unnoticed because the
audit that is supposed to catch it is incomplete — the highest-risk leakage failure mode for
the runtime. S1.

### Likelihood
L2 — a partial audit (covering only some of the four checks) looks complete but silently
leaves a leakage path open.

### Detection
* `risk_controls.no_lookahead_runtime_audit` rule
  `available_ts_label_available_ts_same_bar_fill_locked_test_metadata_checked: true`
  (no_lookahead runtime audit, no_lookahead test suite, Claude review).
* RT-P14 `NoLookaheadRuntimeAudit` covers all four checks; `tests/no_lookahead/research_runtime`
  exercises the input resolver, signal-probe fills, and locked-test metadata.
* `stop_conditions`: `feature input without available_ts`, `label input without
  label_available_ts`; `available_ts_required` and `no_label_as_feature` controls.
* Claude Opus review of RT-P14 audit completeness.

### Mitigation
The `NoLookaheadRuntimeAudit` checks `available_ts`, `label_available_ts`, same-bar fills, and
locked-test metadata; the no-lookahead test suite proves each; missing checks fail closed and
are merge-blocking.

### Owner
Codex (complete audit + no-lookahead tests) / Claude Opus (audit-completeness review).

### Related Phases
RT-P03, RT-P12, RT-P14, RT-P20.

### Blocking Condition
The `NoLookaheadRuntimeAudit` omits `available_ts`, `label_available_ts`, same-bar-fill, or
locked-test-metadata coverage; or any feature/label input lacks its availability timestamp.

---

## R-015 — Failed / inconclusive runs hidden

### Description
A failed or inconclusive runtime run is silently dropped, retried until it passes, or omitted
from the run record instead of being recorded with a `RejectionReasonRecord` and a terminal
`REJECTED` / `INCONCLUSIVE` / `BLOCKED` state, hiding negative results.

### Impact
Hidden failures bias the visible evidence toward survivors, manufacturing apparent success and
defeating the anti-overfit honesty the runtime depends on (negative results must stay
visible). S2.

### Likelihood
L2 — dropping or re-running a disappointing result is a natural temptation unless rejection
recording is required and retries are bounded/recorded.

### Detection
* `runtime_policy`: `failed_and_inconclusive_runs_visible: true`; `diagnostics_policy`:
  `rejection_reason_required_for_fail: true`; `anti_overfit_policy`: `failed_runs_visible:
  true`, `repeated_run_records_required: true`.
* RT-P15 `RejectionReasonRecord` + terminal decision states (`REJECTED`/`INCONCLUSIVE`/
  `BLOCKED`); tests assert failures are recorded, not dropped.
* `risk_controls.failed_runs_visible` (decision state tests, Claude review);
  `merge_policy.global_blockers` / `stop_conditions`: `failed or inconclusive run hidden`.
* Claude Opus review of RT-P15 decision-state semantics.

### Mitigation
Every fail/inconclusive run produces a `RejectionReasonRecord` and a terminal decision state;
repeated runs are recorded; hiding a failed/inconclusive run is fail-closed and
merge-blocking.

### Owner
Codex (rejection records + decision states) / Claude Opus (visibility review).

### Related Phases
RT-P13, RT-P14, RT-P15, RT-P25.

### Blocking Condition
A failed or inconclusive run is hidden, dropped, or retried-to-pass instead of recorded with a
`RejectionReasonRecord` and terminal state.

---

## R-016 — Runtime reports claim alpha / profitability

### Description
Runtime reports, `RuntimeReportCard`s, `EvidenceDraft`s, docs, templates, or handoffs assert
alpha validity, profitability, tradability, market-beating, or strategy/production/live/broker
readiness — or reach a prohibited MVP state (`ALPHA_VALIDATED`, `STRATEGY_READY`, `LIVE_READY`,
`PROFITABLE`, `TRADABLE`, `PRODUCTION_READY`).

### Impact
The runtime falsely signals downstream readiness it has not earned — the highest-risk semantic
boundary violation for an orchestration-only campaign (a diagnostic PASS is not alpha
validation). S1.

### Likelihood
L2 — convenience and aspirational language make alpha/profitability claims easy to introduce
in reports and docs.

### Detection
* `diagnostics_policy`: `descriptive_non_promotional_only: true`; `runtime_policy`:
  `diagnostic_pass_not_alpha_validation: true`;
  `alpha_tradability_claims_allowed_without_evidence: false`.
* `risk_controls.no_alpha_claims` (prohibited claim tests, doc grep, Claude review);
  `RESEARCH_INTERPRETATION_POLICY.md` governs language; prohibited MVP states are unreachable
  (RT-P15).
* `merge_policy.global_blockers` / `stop_conditions`: `unsupported alpha/tradability claim
  introduced` / `alpha/profitability/tradability claim detected`.
* Claude Opus review of all committed reports/docs and the semantic done-check (RT-P26).

### Mitigation
Reports and docs are explicitly descriptive (distribution, coverage, availability, cost
sensitivity), never promotional; the no-claims policy governs all committed text; prohibited
MVP states are unreachable; a diagnostic PASS is not alpha validation; any such claim is
fail-closed and merge-blocking.

### Owner
Codex (descriptive reports/docs) / Claude Opus (claims/no-claims review) / Ralph (scope/claims
enforcement + merge gating).

### Related Phases
RT-P15, RT-P16, RT-P23, RT-P26.

### Blocking Condition
Any committed report/draft/doc claims or implies alpha/profitability/tradability/strategy/
production/live/broker readiness, or any prohibited MVP state is introduced.

---

## R-017 — Tool output exposes raw / heavy data

### Description
An agent-facing `RuntimeToolResult` (or `RuntimeRunSummary`) embeds raw or heavy data — full
feature/label value arrays, canonical bars, provider responses, parquet/arrow payloads, or
large logs — instead of compact, structured, referenced summaries safe for an agent to
consume.

### Impact
The tool surface leaks raw/heavy data into agent context (and risks committing it), defeating
the agent-facing contract the runtime prepares for the Agent Factory and the artifact policy.
S2.

### Likelihood
L2 — returning "everything" is the simplest tool implementation, and large payloads slip into
tool results without an explicit no-raw-data contract.

### Detection
* `tool_policy`: `structured_outputs_required: true`, `agent_facing_contracts_required: true`,
  `raw_data_in_tool_response_forbidden: true`, `heavy_artifact_commit_forbidden: true`.
* RT-P22 `RuntimeToolResult` tests assert no raw/heavy data is embedded;
  `risk_controls.tool_output_no_raw_data` (tool result tests, Claude review).
* `merge_policy.global_blockers` / `stop_conditions`: `tool result exposes raw or heavy data`.
* Claude Opus review of RT-P22 tool-result contracts.

### Mitigation
Tool results are compact, structured, and carry references/handles rather than raw or heavy
data; raw data in a tool response is forbidden; the contract is enforced by tests; a raw/heavy
tool result is fail-closed and merge-blocking.

### Owner
Codex (no-raw-data tool contracts) / Claude Opus (tool-contract review).

### Related Phases
RT-P18, RT-P22, RT-P23.

### Blocking Condition
An agent-facing tool result embeds raw or heavy data instead of a compact, referenced summary.

---

## R-018 — Runtime artifacts committed accidentally

### Description
Runtime-produced heavy outputs — materialized diagnostic/probe/grid values, canonical/feature/
label values, provider responses, parquet/arrow/feather/`.dbn`/`.zst`/`.npy`/`.npz`, local
DB/registry files (sqlite/db/wal), logs, caches, or anything under `runs/**` — are staged or
committed instead of remaining local-only.

### Impact
Forbidden data/heavy artifacts enter git, violating the artifact policy and risking data
exposure; the campaign cannot be accepted. S1.

### Likelihood
L2 — runtime runs produce heavy outputs near the repo (and `runs/**` state) that are easy to
stage without explicit, path-by-path staging.

### Detection
* `git ls-files runs` returns empty (a per-phase check); artifact audit before every merge
  gate; `find data -type f ...` and `find artifacts -type f -size +1M` checks at closeout.
* `artifact_policy.never_commit` globs (`data/raw/**`, `data/canonical/**`, `data/factors/**`,
  `data/labels/**`, `**/*.parquet|*.arrow|*.feather|*.dbn|*.zst|*.npy|*.npz`,
  `metadata/*.sqlite|*.db|*.wal`, `runs/**`); explicit staging only (`git add .` / `git add
  -A` forbidden).
* `risk_controls.no_raw_heavy_artifacts` (git status audit, git ls-files audit, artifact
  policy checks); `merge_policy.global_blockers` / `stop_conditions`: raw/heavy/value/DB
  staged.
* Claude Opus review of the staged set; explicit-staging confirmation in every handoff.

### Mitigation
Runtime values and heavy outputs are `local_only` and never committed; `runs/**` is
local-only; explicit staging only; `never_commit` globs enforced; artifact audit before merge;
tiny synthetic fixtures only under `tests/fixtures/**`.

### Owner
Ralph (artifact policy + merge gating) / Codex (local-only writes + explicit staging).

### Related Phases
RT-P19, RT-P20, RT-P21, RT-P25, RT-P26.

### Blocking Condition
Any raw/canonical/feature/label/runtime value, provider response, heavy artifact, local DB, or
`runs/**` path is staged.

---

## R-019 — Agent Factory later cannot consume tool outputs

### Description
The `RuntimeToolResult`, `RuntimeRunSummary`, `EvidenceDraft`, and `ReferenceCandidateHandoff`
contracts are shaped such that the future Agent Factory (AI Alpha Researchers driving the
runtime as a tool) cannot cleanly consume the runtime's outputs — missing stable handles,
versioning, or a consistent agent-facing schema.

### Impact
The runtime fails its core purpose as a tool layer for downstream agents, forcing rework
before the Agent Factory can consume it (the runtime exists to prepare agent-facing tool
contracts without creating agents). S2.

### Likelihood
L2 — without an explicit consumer contract, tool-result/summary schemas drift from what an
agent consumer needs.

### Detection
* `tool_policy`: `prepares_agent_factory_tool_contracts_without_creating_agents: true`,
  `agent_facing_contracts_required: true`; RT-P22 tool-result contracts and RT-P17 handoff
  expose stable, versioned, referenced handles.
* RT-P25 end-to-end dry run exercises the agent-facing surface; RT-P26 acceptance audit checks
  next-campaign (Agent Factory) readiness.
* Claude Opus review of the consumer-facing surface.

### Mitigation
Tool results, run summaries, and handoffs expose stable, versioned, referenced contracts
without creating agents; the dry run and acceptance audit validate the consumer path; the
contracts are additive and consistent.

### Owner
Codex (agent-facing contracts) / Claude Opus (consumer-contract review) / ChatGPT (roadmap
framing for the Agent Factory consumer).

### Related Phases
RT-P17, RT-P22, RT-P25, RT-P26.

### Blocking Condition
None on its own (S2, non-blocking); flagged in the RT-P26 acceptance audit if the agent-facing
consumer path is not demonstrably clean.

---

## R-020 — CLI surface diverges from repo conventions

### Description
The new `alpha runtime ...` CLI subcommands diverge from the repo's existing CLI conventions —
inconsistent command naming, non-additive registration that mutates other command groups,
non-CI-safe defaults, or commands that trigger heavy/network work — instead of an additive,
local-only, CI-safe surface under `src/alpha_system/cli/`.

### Impact
A divergent CLI is harder to use and maintain and risks breaking the existing command surface
or CI; the runtime's tool entry points become inconsistent with the rest of `alpha`. S3.

### Likelihood
L2 — adding a new command group without re-checking conventions easily produces drift,
especially around registration and defaults.

### Detection
* RT-P18 registers `alpha runtime ...` additively (`src/alpha_system/cli/runtime.py` +
  additive wiring in `cli/main.py`); checks include `python -m alpha_system runtime --help`
  and CLI tests; `docs/research_runtime/CLI.md` documents the surface.
* `docs/CLI_REFERENCE.md` is the convention reference for the supported `alpha` command
  surface.
* Claude Opus review of RT-P18 CLI conventions and additive registration.

### Mitigation
The CLI is additive, local-only, and CI-safe; it follows existing `alpha` conventions; it does
not mutate other command groups or trigger heavy/network work; `--help` and tests confirm the
surface.

### Owner
Codex (additive, convention-following CLI) / Claude Opus (CLI-convention review).

### Related Phases
RT-P18, RT-P22, RT-P23.

### Blocking Condition
None on its own (S3, non-blocking); becomes blocking via R-018 if a CLI command triggers a
heavy/value commit, or via R-003 if it triggers raw provider access.

---

## R-021 — Runtime too slow for Agent Factory

### Description
The fast-path runtime pipeline (resolve → diagnostics → probe → cost stress → bounded grid →
draft) is too slow or resource-heavy to serve as the cheap screening layer the Agent Factory
will call repeatedly, undermining the "fast path" premise.

### Impact
A slow fast path defeats its purpose as a quick, cheap screen, making the runtime impractical
for agent-driven iteration and tempting heavy-output caching/commits to compensate. S3.

### Likelihood
L2 — diagnostics + bounded grid over multiple instruments/partitions naturally grows expensive
without explicit local-only, bounded, deterministic scope and a cache policy.

### Detection
* `compute_policy`: `local_only: true`, `deterministic: true`, `heavy_outputs_local_only:
  true`, `no_distributed_compute_required: true`, `no_ray_cluster: true`,
  `heavy_dependencies_require_justification: true`.
* `RuntimeCachePolicy` (RT-P19) and `RuntimeConcurrencyPolicy` bound local cost; RT-P21 small
  real smoke and RT-P25 dry run record runtime/size; truthful `PASS_WITH_WARNINGS` allowed if
  slow.
* Claude Opus review of scope/perf bounds in RT-P19/RT-P21/RT-P25.

### Mitigation
The fast path is deterministic, local-only, and bounded; a `RuntimeCachePolicy` keeps cached
outputs local-only; performance is a documented, non-blocking concern resolved by scope and
caching, not by committing heavy outputs.

### Owner
Codex (bounded fast path + cache policy) / Claude Opus (scope/perf review) / ChatGPT (Agent
Factory throughput framing).

### Related Phases
RT-P19, RT-P21, RT-P25.

### Blocking Condition
None on its own (S3, non-blocking); becomes blocking via R-018 if heavy cached outputs are
staged, or via R-022 if distributed/cluster compute is introduced to compensate.

---

## R-022 — Runtime overbuilt into distributed platform prematurely

### Description
The runtime is built into a distributed compute platform, ML experiment platform, or
service/daemon — introducing a Ray cluster, a job scheduler, an ML-experiment-tracking
platform, or an always-on service — far beyond the local, deterministic MVP scope.

### Impact
The MVP balloons into infrastructure it does not need, adding heavy dependencies, breaking the
local-first/deterministic/CI-safe property, and delaying the actual research loop. S2.

### Likelihood
L2 — "we'll need scale eventually" is a common over-engineering impulse once the pipeline
works locally.

### Detection
* `compute_policy`: `no_distributed_compute_required: true`, `no_ray_cluster: true`,
  `no_ml_experiment_platform: true`, `heavy_dependencies_require_justification: true`,
  `local_only: true`, `deterministic: true`.
* `forbidden_global_changes` includes `ML/DL training beyond authorized scope` and
  `real-time market data loop`; `risk_controls.no_strategy_scope` blocks
  `ML training beyond authorized scope` and `L2 replay`.
* Claude Opus review of dependencies and runtime architecture across phases.

### Mitigation
The runtime stays local-only, deterministic, and dependency-light; no Ray cluster, ML
platform, distributed scheduler, or always-on service; heavy dependencies require explicit
justification; scale is deferred to future campaigns.

### Owner
Codex (local-only, dependency-light runtime) / Claude Opus (architecture/dependency review) /
ChatGPT (roadmap scoping).

### Related Phases
RT-P02, RT-P19, RT-P21, RT-P25.

### Blocking Condition
None on its own (S2, non-blocking); becomes blocking via R-018 (heavy artifact commit) or the
forbidden-scope blockers if distributed/ML-platform/service scope or unjustified heavy
dependencies are introduced.

---

## R-023 — DAG scheduler metadata wrong

### Description
A phase declares incorrect or missing DAG metadata — `parallel_safe`, `must_run_alone`,
`allowed_paths`, `merge_group`, `conflicts_with`, or `dependencies` — so the DAG wave
scheduler either parallelizes a phase that should run alone or mis-orders the waves
(W0 sequential RT-P00..P06; W1 parallel RT-P07..P11; W2 sequential RT-P12..P19; W3 parallel
RT-P20/P22/P23; W4 sequential RT-P21/P24/P25/P26).

### Impact
The scheduler builds an unsafe wave (e.g. a run-alone integration phase running concurrently
with a diagnostics phase), risking path/resource conflicts and incorrect merge ordering. S2.

### Likelihood
L2 — DAG metadata is easy to get subtly wrong, and an omission defaults a phase into the wrong
parallel posture.

### Detection
* `workflow2.requirements`: `run_frontier_plan_before_execution`,
  `run_parallel_mock_before_first_live_parallel_run`; RT-P24 runs `ralph_driver.py plan-dag`
  and documents the parallel plan.
* Default posture is conservative: omitting `parallel_safe`/`allowed_paths` means run-alone
  (`default_parallel_safe: false`, `default_must_run_alone: true`).
* `risk_controls.dag_parallel_requires_allowed_paths` and `acceptance_gate_coverage_required`
  (plan-dag preview, dag_scheduler validation, campaign.yaml validation script);
  `stop_conditions`: `parallel phase lacks allowed_paths`, `PHASE_PLAN / campaign.yaml
  mismatch`, `acceptance gates missing phases`.
* Claude Opus review of DAG metadata correctness (explicit `review_must_check` item).

### Mitigation
Parallel-safe phases (RT-P07..P11, RT-P20/P22/P23) declare disjoint `allowed_paths`,
`must_run_alone: false`, and no global/coordinator file; everything else runs alone by
default; plan-dag and the parallel mock run before live parallel execution; PHASE_PLAN and
campaign.yaml are kept in agreement.

### Owner
Ralph (DAG scheduler + plan/mock gating) / Claude Opus (DAG-metadata review).

### Related Phases
RT-P07, RT-P08, RT-P09, RT-P10, RT-P11, RT-P20, RT-P22, RT-P23, RT-P24.

### Blocking Condition
A parallel-safe phase lacks disjoint `allowed_paths`, DAG metadata schedules a run-alone phase
concurrently, or PHASE_PLAN and campaign.yaml DAG metadata disagree.

---

## R-024 — Parallel phase path conflict

### Description
Two phases in the same parallel wave write overlapping paths (e.g. a shared
`runtime/diagnostics/__init__.py`, a shared contract/report module, or the same config/doc),
so concurrent worktrees produce conflicting edits in a single wave.

### Impact
The parallel build produces a path/resource conflict within a wave (W1 diagnostics or W3
tests/contracts/docs), breaking the build-in-isolation guarantee and risking merge
corruption. S2.

### Likelihood
L2 — the five concurrent diagnostics phases (W1) and three concurrent W3 phases can collide on
a shared diagnostics-core file unless `allowed_paths` are strictly disjoint and shared core is
forbidden.

### Detection
* Diagnostics phases write only their own `runtime/diagnostics/<name>/**`,
  `tests/.../<name>/**`, `docs/.../<name>.md`, `configs/.../<name>/**`; shared diagnostics core
  (`diagnostics/__init__.py`, `contracts.py`, `report.py`) and `cli/main.py` /
  `ACTIVE_CAMPAIGN.md` are in their `forbidden_paths`.
* `workflow2.requirements`: `parallel_safe_phases_require_disjoint_allowed_paths`; plan-dag /
  parallel mock detect conflicts before live runs; isolated worktrees per phase.
* `merge_policy.global_blockers` / `stop_conditions`: `parallel wave has path/resource
  conflict`.
* Claude Opus review of disjointness across each parallel wave.

### Mitigation
Each parallel phase writes only its own disjoint family/module dirs; shared core and global
files are forbidden to parallel phases; conflicts are detected by plan-dag/mock and are
merge-blocking; the merge queue is serial.

### Owner
Ralph (conflict detection + serial merge) / Codex (additive, disjoint writes) / Claude Opus
(disjointness review).

### Related Phases
RT-P07, RT-P08, RT-P09, RT-P10, RT-P11, RT-P20, RT-P22, RT-P23.

### Blocking Condition
Two phases in the same parallel wave declare or write overlapping `allowed_paths` or a shared
resource.

---

## R-025 — Reference handoff lacks required versions / manifests

### Description
A `ReferenceCandidateHandoff` is produced without the required provenance — the resolved
`DatasetVersion`, Feature/Label pack versions, `CostModelVersion`, `StudyRunManifest` /
`RuntimeArtifactManifest`, and the `AlphaSpec`/`StudySpec` references — so the downstream
Reference process cannot reproduce or trust the screened result.

### Impact
The handoff is not reproducible and cannot be trusted or re-run by the Reference process,
breaking the evidence chain the runtime exists to produce (the handoff is a handoff, not
Reference validation, but it must be complete). S2.

### Likelihood
L2 — assembling a handoff without every version/manifest is easy when the underlying objects
are scattered across diagnostics/probe/cost phases.

### Detection
* `StudyRunManifest` / `RuntimeArtifactManifest` (RT-P05) capture inputs, versions, and
  reproducibility metadata; `runtime_contracts` gate requires `reproducibility_manifest_present`.
* RT-P17 `ReferenceCandidateHandoff` must reference the `DatasetVersion`, pack versions,
  `CostModelVersion`, manifests, and spec pair; tests assert completeness.
* RT-P25 dry run exercises a complete handoff; RT-P26 acceptance audit checks handoff
  completeness.
* Claude Opus review of RT-P17 handoff provenance.

### Mitigation
The `ReferenceCandidateHandoff` bundles the resolved `DatasetVersion`, Feature/Label pack
versions, `CostModelVersion`, `StudyRunManifest`/`RuntimeArtifactManifest`, and the
`AlphaSpec`/`StudySpec` references; the dry run and acceptance audit confirm completeness.

### Owner
Codex (complete handoff + manifests) / Claude Opus (provenance-completeness review).

### Related Phases
RT-P05, RT-P11, RT-P17, RT-P25, RT-P26.

### Blocking Condition
None on its own (S2, non-blocking); flagged in the RT-P26 acceptance audit if the handoff
omits the required `DatasetVersion`/pack/cost-model versions or manifests.

---

## R-026 — Governance / primitive objects bypassed or duplicated

### Description
The runtime re-implements existing primitives or governance objects — duplicating
`research.ic`/`buckets`/`regimes`/`correlation`/`feature_label_diagnostics`,
`backtest.costs`/`slippage`, `experiments.limits`/`overfit_controls`/`splits`/`survivors`, or
governance objects (`alpha_spec`, `study_spec`, `study_input_pack`, `evidence_bundle`,
`feature_request`, `label_spec`, `duplicate_exposure`, `label_leakage_guard`, `trial_ledger`)
— inside `src/alpha_system/runtime/` instead of orchestrating the existing modules.

### Impact
Two divergent sources of truth appear, so diagnostics/cost/anti-overfit/governance logic can be
silently bypassed through the runtime's duplicate, undermining the primitives the runtime is
meant to orchestrate (the runtime orchestrates; it does not duplicate). S2.

### Likelihood
L3 — re-defining a "small" local diagnostic or a local spec is a tempting shortcut, and the
campaign explicitly flags this as the prime duplication risk for an orchestration layer.

### Detection
* `runtime_policy`: `orchestrates_existing_primitives_not_duplicates: true`;
  `risk_controls.consume_not_duplicate` (source path audit, import audit, Claude review).
* `forbidden_paths` block editing `src/alpha_system/{research,experiments,backtest,governance,
  features,labels,data}/**` from runtime phases — they must be consumed, not modified.
* `merge_policy.global_blockers` / `stop_conditions`: `duplicate of an existing
  governance/research/experiments/backtest primitive` introduced.
* Claude Opus review that primitives/governance are consumed, not re-implemented (explicit
  `review_must_check` item).

### Mitigation
The runtime imports and orchestrates the existing `research`/`backtest`/`experiments`/
`governance`/`features`/`labels`/`data` modules; those packages are forbidden-to-edit from
runtime phases; no parallel re-implementation; orchestration adapters only.

### Owner
Codex (orchestration adapters, no re-implementation) / Claude Opus (duplication review).

### Related Phases
RT-P07, RT-P08, RT-P09, RT-P10, RT-P11, RT-P13, RT-P16.

### Blocking Condition
Any existing primitive or governance object is re-implemented inside `src/alpha_system/runtime/`
instead of orchestrated.

---

## R-027 — Research state machine lacks reject / inconclusive / block distinction

### Description
The runtime state machine collapses or omits the terminal outcome distinctions — treating
`REJECTED`, `INCONCLUSIVE`, and `BLOCKED` as a single "failed" bucket, or allowing a run to end
in a non-terminal/ambiguous state — so the lifecycle cannot honestly express why a run did not
produce a handoff.

### Impact
Outcomes lose their meaning: a hypothesis that failed on evidence (`REJECTED`), one that needs
more data (`INCONCLUSIVE`), and one stopped by a guard/authorization (`BLOCKED`) are
conflated, weakening anti-overfit honesty and the evidence chain; it also risks reaching a
prohibited MVP state. S2.

### Likelihood
L2 — a single generic "fail" path is the simplest implementation and easy to ship without the
three distinct terminal states and their reason records.

### Detection
* `runtime_state_model` lists distinct terminal states `REJECTED` / `INCONCLUSIVE` / `BLOCKED`
  and forbids the prohibited MVP states; RT-P15 implements the decision states + a
  `RejectionReasonRecord` per terminal outcome.
* `runtime_state_model.prohibited_mvp_states` are unreachable; tests assert each terminal state
  is distinct and reason-recorded, and that prohibited states cannot be set.
* `risk_controls.failed_runs_visible` (decision state tests, Claude review); the most advanced
  survivor state is `REFERENCE_HANDOFF_READY`.
* Claude Opus review of RT-P15 state-machine semantics and the semantic done-check.

### Mitigation
The lifecycle implements distinct `REJECTED` / `INCONCLUSIVE` / `BLOCKED` terminals, each with
a `RejectionReasonRecord`; non-terminal/ambiguous endings and prohibited MVP states are
unreachable; the three outcomes are first-class and tested.

### Owner
Codex (decision-state machine + reason records) / Claude Opus (state-distinction review).

### Related Phases
RT-P04, RT-P15, RT-P25, RT-P26.

### Blocking Condition
The state machine collapses `REJECTED`/`INCONCLUSIVE`/`BLOCKED` into one bucket, allows a
non-terminal/ambiguous ending, or makes a prohibited MVP state reachable.

---

## Blocking Risk Summary

The following are hard STOP/merge-block conditions (each maps to a
`merge_policy.global_blockers` entry, a `stop_conditions` entry, or a fail-closed gate):
**R-001, R-002, R-003, R-004, R-005, R-006, R-007, R-008, R-009, R-010, R-014, R-015, R-016,
R-017, R-018, R-023, R-024, R-026, R-027**. Any one of these makes the affected phase
ineligible for merge until resolved or truthfully blocked.

The remaining risks (**R-011, R-012, R-013, R-019, R-020, R-021, R-022, R-025**) are
non-blocking on their own (S2/S3) but are reviewed at their related phases and several escalate
into a blocking condition when they cross into a leakage, claim, artifact, duplication, or
out-of-scope violation (noted in each entry).

## Risk Review Cadence

* **Per phase**: Claude Opus review checks the risks tied to that phase's Related Phases (the
  `review_must_check` list in `campaign.yaml` covers orchestration-not-duplication, AlphaSpec/
  StudySpec requirement, accepted-DatasetVersion/no-raw-access, `available_ts`/
  `label_available_ts`/no-label-as-feature, no-lookahead audit coverage, cost stress + double
  cost + labeled slippage proxy, variant budget / no unbounded grid / no locked-test
  selection, fast-path-vs-Reference and EvidenceDraft/Handoff scope, failed/inconclusive
  visibility, agent-facing tool results without raw data, DAG metadata, serial merge, artifact
  policy, and no alpha/strategy claims).
* **Per gate**: each acceptance gate re-checks all blocking risks for its phases
  (`campaign_bootstrap` → R-004/R-016/R-018/R-026; `runtime_contracts` → R-002/R-004/R-014/
  R-025/R-026/R-027; `diagnostics_runtime` → R-003/R-010/R-011/R-012/R-013/R-023/R-024/R-026;
  `runtime_integration` → R-001/R-005/R-006/R-007/R-008/R-014/R-015/R-016/R-017; `tests_tools_docs`
  → R-017/R-018/R-019/R-020/R-023/R-024; `workflow_and_closeout` → R-009/R-016/R-018/R-019/
  R-023/R-025/R-026/R-027).
* **Per parallel wave**: before each live parallel run (W1 diagnostics, W3 tests/contracts/
  docs), `run_frontier_plan_before_execution` and `run_parallel_mock_before_first_live_parallel_run`
  re-verify R-023/R-024 and serial-merge ordering.
* **Campaign closeout (RT-P26)**: the full register is reviewed in the acceptance audit and
  semantic done-check, including the no-claims/no-leakage audit (R-014/R-016), scope honesty
  (R-001/R-005/R-006/R-007), failed-run visibility and decision states (R-015/R-027), handoff
  completeness (R-025), and Agent Factory next-campaign readiness (R-019/R-021).

## Risk Ownership Summary

* **Ralph** — scope/stop enforcement, artifact policy + merge gating, DAG scheduler and serial
  merge queue, coordinator-only `ACTIVE_CAMPAIGN.md`, and external-call prevention (primary on
  R-018, R-023, R-024; merge-gate enforcement of the scope/claims blockers R-001/R-016).
* **Codex** — orchestration adapters (no duplication), accepted-DatasetVersion/canonical-only
  consumption, AlphaSpec/StudySpec-bound runs, `available_ts`/`label_available_ts` wiring and
  the no-lookahead runtime audit, cost stress (double cost + labeled slippage proxy), bounded
  grid / variant budget, decision states and rejection records, fast-path/draft/handoff
  labeling, agent-facing tool contracts, CLI surface, cache policy, fail-closed/no-lookahead
  tests, and local-only writes (R-002, R-003, R-004, R-008, R-010, R-011, R-012, R-013, R-014,
  R-015, R-020, R-021, R-025, R-026, R-027).
* **Claude Opus** — semantic review of the orchestration/duplication boundary, the
  DatasetVersion/raw-access boundary, no-lookahead/availability, cost rigor, anti-overfit
  discipline, fast-path-vs-Reference and EvidenceDraft/Handoff scope honesty, claims/no-claims,
  DAG metadata, serial merge, and the final done-check (the semantic review side of every risk;
  primary on R-005, R-006, R-007, R-016).
* **ChatGPT** — roadmap framing and consumer prioritization for the downstream Agent Factory
  and Reference process (R-019, R-021), scoping against premature platform build (R-022), and
  post-run reasoning.
* **Human (repo owner)** — direction and capital/live judgment; this campaign is local-only
  with no RED-lane phases and no external provider calls, so no per-operation human
  authorization is required, but the human owns final acceptance of the runtime layer.

---

*This file is a campaign contract describing the intended risks, controls, and boundaries of
ALPHA_RESEARCH_RUNTIME_MVP; it makes no claim that any alpha is validated, tradable,
profitable, or production-ready, and no claim that any factor is promoted.*
