# ALPHA_RESEARCH_RUNTIME_MVP Acceptance Criteria

## Acceptance philosophy

Acceptance for this campaign is **semantic, not mechanical**. Passing tests are necessary but
never sufficient. A phase or gate is accepted only when the Research Runtime genuinely **fails
closed** on a missing prerequisite, the boundaries genuinely **hold** (accepted-DatasetVersion
only, no raw-provider access, no external provider calls, `available_ts` / `label_available_ts`
required, no label-as-feature), the runtime genuinely **orchestrates existing primitives instead
of duplicating them**, cost stress and variant budgets are genuinely **enforced**, failed and
inconclusive runs stay genuinely **visible**, runtime values stay genuinely **local-only**, and
no prohibited scope or claim is present.

This campaign builds the **executable research loop layer** between the Feature/Label substrate
(`ALPHA_FEATURE_LABEL_FOUNDATION_V1`, complete 32/32 `COMPLETE_WITH_WARNINGS`) and the future
Agent Factory. It turns an approved `AlphaSpec` + `StudySpec` into a deterministic, local,
reproducible run: resolve an accepted `DatasetVersion` plus Feature/Label packs, run Tier 0
factor diagnostics, run label diagnostics, run session/regime/RTH/ETH and cross-market splits,
run a simple signal probe, run cost stress, evaluate a bounded variant grid, audit for
lookahead, and emit an `EvidenceDraft` and a `ReferenceCandidateHandoff` — **or** record a
truthful `REJECTED` / `INCONCLUSIVE` / `BLOCKED`. It owns the *runtime that runs approved specs*,
not alpha results.

The framing that acceptance enforces, in its own terms: **Research Runtime is not the Agent
Factory, not broad alpha search, not a FactorLibrary, not Strategy Reference Validation, not a
Portfolio AlphaBook, and not paper/live/broker.** A diagnostic PASS is not alpha validation; a
signal probe is not a strategy candidate; a bounded grid is not promotion; an `EvidenceDraft` is
not a candidate; a `ReferenceCandidateHandoff` is not Reference validation; the fast path is not
Reference truth. Acceptance therefore explicitly rejects any outcome where runtime code reads raw
provider files, where the accepted-DatasetVersion boundary is bypassed, where a diagnostics or
probe run executes without an `AlphaSpec` and `StudySpec`, where a feature input lacks
`available_ts`, where a label input lacks `label_available_ts`, where a label value is exposed as
a live runtime feature, where a grid is unbounded or a variant budget is exceeded, where the
locked-test partition is used without governance contamination metadata, where cost stress is
omitted, where a zero-cost result is used as a promotion basis, where a fast-path result is
treated as Reference truth, where an `EvidenceDraft` is treated as a candidate, where a
`ReferenceCandidateHandoff` is treated as completed Reference validation, where a failed or
inconclusive run is hidden, where the runtime duplicates an existing
research/experiments/governance/backtest primitive, where parallel DAG metadata is unsound,
where a phase branch writes `ACTIVE_CAMPAIGN.md`, where merge escapes the serial merge queue, or
where any alpha/profitability/tradability/strategy/backtest/portfolio claim or scope appears.

This campaign runs under **Workflow 2 with the DAG wave scheduler**: dependency-ready phase
selection, concurrent build of conflict-free parallel-safe waves in isolated worktrees, and a
**serial merge queue** that merges one PR at a time. Ralph owns the strict driver loop, STOP
checks, validation orchestration, review routing, verdict parsing, bounded repair, PR/CI/merge
gates, and run summaries. Codex owns scoped execution of the generated spec and truthful
handoffs. Claude Opus 4.8 xhigh is the fresh semantic reviewer for every YELLOW phase. ChatGPT
owns strategic framing and post-run reasoning.

The final verdict for the campaign is one of `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`.
A truthful `BLOCKED` is acceptable and strongly preferred over a false `COMPLETE`.

## Campaign-level acceptance criteria

The campaign is accepted only when all of the following hold, every phase carries a merged
`PASS` or `PASS_WITH_WARNINGS` verdict (or a truthful `BLOCKED` is recorded), and the artifact
audit is clean:

1. The runtime **consumes only accepted DatasetVersions** through the sanctioned
   `alpha_system.data.foundation.version_registry.resolve_dataset_version` adapter and the
   canonical record types (`CanonicalBarRecord` / `CanonicalBBORecord` / `DenseGridBarRecord`);
   **no runtime code reads raw provider files** (`.dbn` / `.zst` / parquet / arrow / feather /
   provider responses) and **no external Databento or IBKR API call is made** anywhere in the
   campaign. Databento is the primary deep-history research source; IBKR is broker-source recent
   validation only; Databento and IBKR DatasetVersions are never merged into one input.
2. Admissibility is enforced: a DatasetVersion is consumed only in lifecycle state `VERSIONED`
   or `READY_FOR_RESEARCH`; locked-test partition use (`locked_test_candidate`,
   `latest_shadow_candidate`) requires governance contamination metadata. Partitions are honored
   as development `2018-01-01..2022-12-31`, validation `2023-01-01..2024-12-31`, and
   `locked_test_candidate` `2025-01-01..as_of_run`.
3. **No `AlphaSpec` / `StudySpec` → no runtime run.** Every diagnostics, probe, cost-stress, or
   handoff run is bound to an approved `AlphaSpec` and `StudySpec`, consumed through the
   governance `StudyInputPack` and fed back into the governance `EvidenceBundle`; the runtime
   does not introduce a parallel spec or input bundle.
4. **Feature inputs carry `available_ts`; label inputs carry `label_available_ts`; no
   label-as-feature.** A feature input without `available_ts`, a label input without
   `label_available_ts`, or a label value reachable as a runtime feature or signal input is a
   hard blocker. The `NoLookaheadRuntimeAudit` covers `available_ts`, `label_available_ts`,
   same-bar fills, and locked-test metadata.
5. The runtime **orchestrates existing primitives and never duplicates them** — diagnostic math
   from `alpha_system.research.ic` / `research.buckets` / `research.regimes` /
   `research.correlation` / `research.feature_label_diagnostics`; cost and slippage from
   `alpha_system.backtest.costs` / `backtest.slippage`; variant budget, overfit controls, splits,
   and survivors from `alpha_system.experiments.limits` / `experiments.overfit_controls` /
   `experiments.splits` / `experiments.survivors`; governance contracts from
   `alpha_system.governance.study_input_pack` / `governance.evidence_bundle` /
   `governance.alpha_spec` / `governance.study_spec` / `governance.feature_request` /
   `governance.label_spec` / `governance.duplicate_exposure` / `governance.label_leakage_guard` /
   `governance.trial_ledger`; and feature/label consumption from
   `alpha_system.features.consumption` / `features.store` / `features.registry` /
   `labels.store` / `labels.registry`. These packages are in each phase's `forbidden_paths` and
   are never edited.
6. The runtime object model is named and contracted under `src/alpha_system/runtime/`:
   `RuntimeRequest`, `RuntimePlan`, `RuntimeInputPack`, `StudyRunSpec`, `StudyRunRecord`,
   `StudyRunManifest`, `DiagnosticsRunSpec`, `DiagnosticsRunRecord`, `FactorDiagnosticsReport`,
   `LabelDiagnosticsReport`, `SignalProbeSpec`, `SignalProbeReport`, `BoundedGridSpec`,
   `BoundedGridRunRecord`, `VariantBudget`, `CostModelVersion`, `CostStressSpec`,
   `CostSensitivityReport`, `RegimeSplitSpec` / `RegimeSplitReport`, `SessionSplitReport`,
   `CrossMarketDiagnosticsReport`, `NoLookaheadRuntimeAudit`, `RuntimeArtifactManifest`,
   `RejectionReasonRecord`, `EvidenceDraft`, `ReferenceCandidateHandoff`, `RuntimeRunSummary`,
   `RuntimeToolResult`, `FeatureLabelPackResolver`, `RuntimeCachePolicy`,
   `RuntimeConcurrencyPolicy`, `RuntimeReportCard`, `DiagnosticsQualityGate`,
   `RuntimeStopCondition` — consuming `StudyInputPack` from governance, never re-defining it.
7. The runtime decision lifecycle is implemented as `RUNTIME_REQUESTED → INPUTS_RESOLVED →
   PLAN_VALIDATED → DIAGNOSTICS_READY → DIAGNOSTICS_RUNNING → DIAGNOSTICS_COMPLETE
   (/ DIAGNOSTICS_FAILED) → SIGNAL_PROBE_READY → SIGNAL_PROBE_COMPLETE → COST_STRESS_COMPLETE →
   EVIDENCE_DRAFT_READY → REFERENCE_HANDOFF_READY`, with terminal `REJECTED` / `INCONCLUSIVE` /
   `BLOCKED`. `REFERENCE_HANDOFF_READY` is the most advanced state any survivor may reach.
8. The **prohibited MVP states are unreachable** by any implemented transition:
   `ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`, `LIVE_READY`,
   `PAPER_READY`, `PROFITABLE`, `TRADABLE`, `PRODUCTION_READY`.
9. **Cost stress is present** for any signal probe or handoff: a `CostModelVersion` is recorded,
   a base stress and a `double_cost` profile are run, BBO spread-crossing cost is used when
   available, slippage is labeled a **proxy**, session-specific cost is applied, and a zero-cost
   result is never used as a promotion basis.
10. **Variant budget is enforced**: every grid is bounded by a `VariantBudget` (consuming
    `experiments.limits` / `experiments.overfit_controls`); there is no unbounded grid and no
    selection on the locked-test partition.
11. **Failed and inconclusive runs stay visible** via `RejectionReasonRecord`; a hidden failed or
    inconclusive run is a hard failure.
12. **Agent-facing outputs carry no raw or heavy data**: `RuntimeToolResult` / `RuntimeRunSummary`
    are structured contracts that prepare Agent Factory tool surfaces **without creating any
    autonomous agent** and never embed raw or heavy data.
13. No alpha, profitability, tradability, strategy, backtest, portfolio, broker, paper, live,
    order, account, broad-alpha-search, or factor-promotion scope or claim is introduced anywhere.

All 27 phases (`RT-P00` … `RT-P26`) are complete with merged verdicts. `RT-P00` is GREEN
(docs/mechanical bootstrap; review optional); all other phases are YELLOW and require fresh
Claude Opus 4.8 xhigh review and auto-merge through the serial merge queue. There are **no
RED-lane phases** and **no external provider calls** in this campaign: the data is already pulled
locally, and the runtime consumes only local accepted DatasetVersions.

## Runtime-entry-contract-level acceptance

* The runtime entry contract (`alpha_system.runtime.entry_contract`, documented in
  `docs/research_runtime/ENTRY_CONTRACT.md`) defines the single supported way to start a run: an
  approved `AlphaSpec` + `StudySpec` (via the governance `StudyInputPack`) plus a target accepted
  `DatasetVersion` reference. No `AlphaSpec` / `StudySpec` → no runtime run; the entry point is
  **fail-closed**.
* The entry contract refuses to admit any request that names a raw provider source, requests an
  external provider call, or omits a dataset scope; it is the front door and it never opens onto
  raw provider data.
* The entry contract implies neither that a run has executed, nor that any diagnostic passed, nor
  that any alpha exists.

## Input-resolution-level acceptance

* The `RuntimeInputPack` resolver (`alpha_system.runtime.input_resolver`, documented in
  `docs/research_runtime/INPUT_RESOLVER.md`) resolves the accepted `DatasetVersion` only via
  `resolve_dataset_version`, and resolves Feature/Label packs only via the existing
  `features.consumption` / `features.store` / `features.registry` and `labels.store` /
  `labels.registry` surfaces.
* Resolution **refuses to materialize a `RuntimeInputPack`** unless the DatasetVersion is
  admissible (lifecycle state in `{VERSIONED, READY_FOR_RESEARCH}`); a missing or inadmissible
  DatasetVersion blocks the run.
* Every resolved feature input carries `available_ts` and every resolved label input carries
  `label_available_ts`; the `tests/no_lookahead/research_runtime` suite proves availability
  ordering and that no label is exposed as a live feature.
* Databento and IBKR DatasetVersions are never merged; locked-test partitions require governance
  contamination metadata; the resolver never reads raw provider files and never exposes raw
  provider fields.

## StudyRunSpec-level acceptance

* `StudyRunSpec`, `RuntimePlan`, and `RuntimeRequest`
  (`alpha_system.runtime.contracts.run_spec` / `.plan`, documented in
  `docs/research_runtime/RUN_SPEC_AND_PLAN.md`) exist as immutable, hashable contract objects
  that bind a run to its `AlphaSpec` / `StudySpec` / `DatasetVersion` / partition scope and to a
  validated `RuntimePlan`.
* A `RuntimePlan` is validated (`PLAN_VALIDATED`) before any execution; an invalid or
  unauthorized plan blocks the run.
* A `StudyRunSpec` implies no execution, no diagnostic result, and no alpha; it is a request and
  a plan, not an outcome.

## Runtime-manifest-level acceptance

* `StudyRunRecord`, `StudyRunManifest`, and `RuntimeArtifactManifest`
  (`alpha_system.runtime.contracts.run_record` / `.manifest` / `.artifacts`, documented in
  `docs/research_runtime/RUN_RECORD_AND_MANIFEST.md`) provide a deterministic, reproducible
  record of inputs, code/config versions, decision state, and produced artifacts.
* The manifest is **reproducibility evidence, not data**: it references artifact locations and
  hashes under `$ALPHA_DATA_ROOT` / `runs/**` and **never embeds raw or heavy values**; no
  runtime value, heavy artifact, or local DB is committed.
* Decision state on the record is one of the runtime lifecycle states, including the terminal
  `REJECTED` / `INCONCLUSIVE` / `BLOCKED`; the prohibited MVP states are never recorded.

## Factor-diagnostics-level acceptance

* The factor diagnostics runtime (`alpha_system.runtime.diagnostics.factor`, documented in
  `docs/research_runtime/diagnostics/factor.md`) produces a `FactorDiagnosticsReport` by
  **orchestrating** `research.ic` / `research.buckets` (and related research primitives), never
  re-implementing the IC / bucket math.
* Diagnostics are **descriptive and non-promotional**: coverage and quality views, not IC
  rankings presented as alpha scores; a failing condition produces a `RejectionReasonRecord`.
* A factor diagnostic PASS is explicitly **not alpha validation**; the report makes no
  alpha/tradability/profitability claim.

## Label-diagnostics-level acceptance

* The label diagnostics runtime (`alpha_system.runtime.diagnostics.label`, documented in
  `docs/research_runtime/diagnostics/label.md`) produces a `LabelDiagnosticsReport` by
  orchestrating the existing research label-diagnostics primitives
  (`research.feature_label_diagnostics`), never re-implementing them.
* Labels are evaluated only with `label_available_ts` honored; no label value is exposed as a
  live feature; a label whose value would be known before `label_available_ts` is a hard failure.
* A label diagnostic PASS implies no alpha readiness — only that the label is describable and
  leakage-safe.

## Signal-probe-level acceptance

* The signal probe runtime (`SignalProbeSpec` → `SignalProbeReport`,
  `alpha_system.runtime.diagnostics`/probe surface) runs a **simple** probe over an accepted
  DatasetVersion + Feature/Label pack, bound to an `AlphaSpec` / `StudySpec`.
* The probe **requires cost stress**: a `SignalProbeReport` without an accompanying
  `CostSensitivityReport` (base + `double_cost`) is invalid; a zero-cost probe result is never a
  promotion basis.
* The probe is explicitly **not strategy validation and not a candidate**; presenting it as
  either is a hard failure routed to rework.

## Cost-stress-level acceptance

* The cost stress runtime (`CostModelVersion`, `CostStressSpec`, `CostSensitivityReport`,
  `alpha_system.runtime.diagnostics.cost`) consumes `backtest.costs` / `backtest.slippage` and
  records a `CostModelVersion`, a base stress, and a `double_cost` profile; BBO spread-crossing
  cost is used when available and cost is session-specific.
* Slippage is **labeled a proxy**, not a realized fill; zero-cost is never used as a promotion
  basis; cost stress is present for any signal probe or reference handoff.
* The session/regime/RTH/ETH split runtime (`alpha_system.runtime.diagnostics.splits`) and the
  cross-market runtime (`alpha_system.runtime.diagnostics.cross_market`) orchestrate
  `research.regimes` / `research.correlation` and produce `SessionSplitReport` /
  `RegimeSplitReport` / `CrossMarketDiagnosticsReport`; cross-market alignment never introduces
  lookahead (a value at *t* uses only inputs available by `available_ts` for every instrument).

## Bounded-grid-level acceptance

* The bounded grid / variant budget guard (`BoundedGridSpec`, `BoundedGridRunRecord`,
  `VariantBudget`, `alpha_system.runtime.experiments` surface) consumes `experiments.limits` /
  `experiments.overfit_controls` / `experiments.splits` / `experiments.survivors` and **enforces
  a finite variant budget**.
* There is **no unbounded grid** and **no selection on the locked-test partition**; an exceeded
  budget or a locked-test selection is a hard blocker; repeated-run records are kept.
* A bounded grid result is explicitly **not promotion**; surviving a bounded grid does not make a
  variant a candidate.

## No-lookahead-audit-level acceptance

* The `NoLookaheadRuntimeAudit` (`alpha_system.runtime.audit` surface) checks `available_ts`,
  `label_available_ts`, same-bar fills, and locked-test contamination metadata for every run, and
  the `tests/no_lookahead/research_runtime` suite proves these properties on synthetic fixtures.
* A feature input without `available_ts`, a label input without `label_available_ts`, a same-bar
  fill that uses future information, or a locked-test partition consumed without contamination
  metadata is a **hard failure** that blocks merge.
* The audit implies no alpha readiness — only that the run is point-in-time-safe.

## Evidence-draft-level acceptance

* The `EvidenceDraft` builder (`alpha_system.runtime.evidence` surface) assembles the diagnostics,
  split, cost-sensitivity, bounded-grid, and no-lookahead results into a draft that feeds the
  governance `EvidenceBundle`; it consumes `governance.evidence_bundle` and `governance.trial_ledger`,
  never re-implementing them.
* An `EvidenceDraft` is explicitly **not a candidate** and **not Reference truth**; the fast path
  is not Reference truth. Presenting an `EvidenceDraft` as a promoted candidate is a hard failure
  routed to rework.
* Failed and inconclusive runs are represented in the draft via `RejectionReasonRecord`; nothing
  is hidden.

## Reference-handoff-level acceptance

* The `ReferenceCandidateHandoff` builder (`alpha_system.runtime.handoff` surface) emits a handoff
  that records what would be submitted for downstream Reference validation, reaching at most the
  `REFERENCE_HANDOFF_READY` state.
* A `ReferenceCandidateHandoff` is explicitly **not completed Reference validation**, **not a
  promotion**, and **not an alpha/tradability claim**; presenting it as Reference validation is a
  hard failure routed to rework.
* The handoff requires cost stress to be present and the no-lookahead audit to have passed; a
  handoff without these is invalid.

## Tool/CLI-level acceptance

* The runtime CLI surface is added **additively** under `src/alpha_system/cli/` as planned
  `alpha runtime ...` commands; it does not remove or weaken existing CLI behavior and is
  documented in `docs/research_runtime/`.
* The agent-facing `RuntimeToolResult` / `RuntimeRunSummary` contracts are structured outputs that
  **prepare Agent Factory tool surfaces without creating any autonomous agent**, and **carry no
  raw or heavy data**; a tool result embedding raw or heavy data is a hard failure.
* `RuntimeReportCard` and the report/markdown templates under `docs/research_runtime/templates/`
  render human-readable, **non-promotional** summaries that make no alpha/tradability/profitability
  claim.
* The `RuntimeCachePolicy` / `RuntimeConcurrencyPolicy` keep heavy outputs local-only under
  `$ALPHA_DATA_ROOT` / `runs/**` and never commit cached or heavy artifacts.

## DAG-scheduler-level acceptance

* `workflow2.scheduler.mode: dag_wave`, `parallel_execution: true`, `max_parallel_phases: 3`,
  `merge_queue: serial`, `update_active_campaign: coordinator_only`.
* A phase is parallel-safe **only** if it sets `parallel_safe: true`, declares **disjoint
  `allowed_paths`**, sets `must_run_alone: false`, declares no global/coordinator file, and is not
  RED. A phase that omits `parallel_safe: true` or `allowed_paths` **runs alone**.
* Parallel-safe phases are exactly the diagnostics fan-out `RT-P07`–`RT-P11` (`diagnostics` merge
  group) and the tests/contracts/docs fan-out `RT-P20`, `RT-P22`, `RT-P23` (`tests_tools_docs`
  merge group). Bootstrap, the runtime contracts, the integration track (`RT-P12`–`RT-P19`), the
  small real DatasetVersion smoke (`RT-P21`), and the closeout (`RT-P24`–`RT-P26`) **run alone**.
* The intended waves are: **W0** sequential `RT-P00`→…→`RT-P06`; **W1** parallel diagnostics
  `RT-P07`, `RT-P08`, `RT-P09`, `RT-P10`, `RT-P11`; **W2** sequential integration
  `RT-P12`→…→`RT-P19`; **W3** parallel tests/contracts/docs `RT-P20`, `RT-P22`, `RT-P23`; **W4**
  sequential closeout `RT-P21`→`RT-P24`→`RT-P25`→`RT-P26`.
* Parallel-safe phases build concurrently in isolated worktrees but **merge serially** — one PR at
  a time. `ACTIVE_CAMPAIGN.md` is coordinator-owned and **never written by a phase branch** in
  parallel mode.
* `just frontier-plan ALPHA_RESEARCH_RUNTIME_MVP` (read-only) and
  `just frontier-run-parallel-mock ALPHA_RESEARCH_RUNTIME_MVP 3` are run before any live parallel
  run, and the planned waves match the intended shape.

## Artifact-policy-level acceptance

* Runtime values, raw/canonical market data, feature/label values, provider responses, local
  registries/DBs, logs, caches, and heavy artifacts are **local-only** and never committed;
  campaign and docs files may describe paths but never commit data.
* `git ls-files runs` returns empty; run-local `handoff.md` / `review.md` / `verdict.json` /
  `checks.json` / `repair_attempts/` remain under `runs/**` and are never committed.
* No `*.parquet` / `*.arrow` / `*.feather` / `*.dbn` / `*.zst` / `*.sqlite` / `*.db` / `*.wal` /
  `*.log` outside documented tiny synthetic `tests/fixtures/**`; `find artifacts -type f -size +1M`
  returns empty.
* Commit-eligible handoffs live under `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/**` and commit-eligible
  reviews under `reviews/ALPHA_RESEARCH_RUNTIME_MVP/**`. Explicit staging only; **no `git add .` /
  `git add -A`**; no force push. The consumed research/experiments/governance/backtest/features/
  labels/data packages are never edited.

## Review-level acceptance

* Every YELLOW phase has a **fresh Claude Opus 4.8 xhigh review** and a `verdict.json`; merged
  phases are `PASS` or `PASS_WITH_WARNINGS`. `FAIL` / `BLOCKED` / `REWORK` block merge. The GREEN
  bootstrap phase (`RT-P00`) may skip review.
* The reviewer is **independent**; the implementer cannot self-approve.
* Reviews verify: phase-scope compliance; that runtime objects orchestrate existing primitives and
  do not duplicate research/experiments/governance/backtest code; that `AlphaSpec` and `StudySpec`
  are required before any runtime study run; accepted-DatasetVersion-only consumption via
  `resolve_dataset_version` with no raw-provider access and no external provider calls;
  `available_ts` / `label_available_ts` present and no label-as-feature; the no-lookahead runtime
  audit covering `available_ts`, `label_available_ts`, same-bar fills, and locked-test metadata;
  cost stress present for any probe or handoff with slippage labeled a proxy and a `double_cost`
  profile present; variant budget enforced with no unbounded grid and no locked-test selection;
  that the `EvidenceDraft` is not a candidate, the `ReferenceCandidateHandoff` is not Reference
  validation, and the fast path is not Reference truth; that failed and inconclusive runs remain
  visible with a `RejectionReasonRecord`; that agent-facing tool results carry no raw or heavy
  data; **DAG-metadata correctness** (parallel-safe phases have disjoint `allowed_paths` and no
  global files); serial merge queue respected and no phase branch writing `ACTIVE_CAMPAIGN.md`;
  artifact-policy compliance; no broker/live/paper/order-routing/account scope; no
  alpha/profitability/tradability claim and no strategy/backtest/portfolio/alpha-search scope; no
  test weakening or gaming; and handoff completeness with semantic done criteria.

## Prohibited shortcuts

The campaign is **not** accepted if any of the following is true:

* runtime code reads raw Databento/IBKR files (`.dbn` / `.zst` / parquet / arrow / feather)
  directly;
* runtime code calls an external Databento or IBKR provider API;
* diagnostics, probe, cost-stress, or handoff runs without an `AlphaSpec` and `StudySpec`;
* a run executes without an accepted DatasetVersion (accepted-DatasetVersion boundary bypassed);
* feature inputs without `available_ts`;
* label inputs without `label_available_ts`;
* label values used as live runtime features or signal inputs;
* a signal probe presented as strategy validation or as a candidate;
* a grid run unbounded or a variant budget exceeded;
* the locked-test partition used without governance contamination metadata;
* cost stress omitted for a signal probe or reference handoff;
* a zero-cost result used as a promotion basis;
* a fast-path result treated as Reference truth;
* an `EvidenceDraft` treated as a promoted candidate;
* a `ReferenceCandidateHandoff` treated as completed Reference validation;
* `RejectionReasonRecord`s omitted (rejection reasons not recorded);
* failed or inconclusive runs hidden instead of recorded;
* heavy/raw/canonical/feature/label/runtime values or local DBs committed;
* alpha/tradability/profitability (or market-beating / production-ready / live-ready /
  broker-ready) claims introduced;
* strategy/backtest/portfolio/alpha-search/factor-promotion scope introduced;
* paper/live/broker/order/account scope introduced;
* a parallel phase marked safe without disjoint `allowed_paths`;
* a phase branch writes `ACTIVE_CAMPAIGN.md` in parallel mode;
* a merge occurs outside the serial merge queue;
* the runtime duplicates an existing research/experiments/governance/backtest primitive instead of
  orchestrating it;
* an agent-facing tool result embeds raw or heavy data.

## Required final validation commands

```bash
cd ~/projects/alpha_system

# Test + canary validation
python tools/verify.py --all
python tools/hooks/canary_runner.py

# YAML parse + phase-coverage validation of the campaign contract
python -c "import yaml; d=yaml.safe_load(open('campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml')); ids=[p['id'] for p in d['phases']]; assert ids==[f'RT-P{n:02d}' for n in range(27)], ids; gphases=[p for g in d['acceptance_gates'].values() for p in g['phases']]; assert sorted(gphases)==sorted(ids) and len(gphases)==len(ids), gphases; print('campaign.yaml OK:', len(ids), 'phases; every phase in exactly one gate')"

# Run-artifact audit (must be empty)
git status --short
git ls-files runs

# Data / metadata / heavy-artifact audits (must be empty outside tiny synthetic fixtures)
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
find . -name "*.arrow" -not -path "./tests/fixtures/*" -print
find . -name "*.feather" -not -path "./tests/fixtures/*" -print
find . -name "*.dbn" -not -path "./tests/fixtures/*" -print
find . -name "*.zst" -not -path "./tests/fixtures/*" -print

# DAG scheduler read-only plan + mock parallel run (no live merges)
just frontier-plan ALPHA_RESEARCH_RUNTIME_MVP
just frontier-run-parallel-mock ALPHA_RESEARCH_RUNTIME_MVP 3
```

## Required semantic done-check

Beyond passing tests, the final done-check (Claude Opus) must affirm that:

* the runtime **fails closed on a missing prerequisite** — no `AlphaSpec` / `StudySpec`, no
  accepted DatasetVersion, no admissible lifecycle state, no cost stress for a probe/handoff, and
  no variant budget all genuinely block the run;
* the **accepted-DatasetVersion boundary is real** — runtime code never reads raw provider files,
  makes no external Databento/IBKR call, and consumes only admissible DatasetVersions via
  `resolve_dataset_version`, with Databento and IBKR versions never merged;
* **no-lookahead holds** — feature inputs carry `available_ts`, label inputs carry
  `label_available_ts`, no label is exposed as a live feature, same-bar fills are sound, and the
  `NoLookaheadRuntimeAudit` plus `tests/no_lookahead/research_runtime` prove it;
* **cost discipline is real** — a `CostModelVersion`, a base stress, and a `double_cost` profile
  are present for any probe/handoff, slippage is labeled a proxy, and zero-cost is never a
  promotion basis;
* **variant discipline is real** — every grid is bounded by a `VariantBudget`, there is no
  unbounded grid, and there is no selection on the locked-test partition (which itself requires
  contamination metadata);
* **the fast path is not Reference truth** — a diagnostic PASS is not alpha validation, a signal
  probe is not a candidate, a bounded grid is not promotion, an `EvidenceDraft` is not a
  candidate, and a `ReferenceCandidateHandoff` is not completed Reference validation;
* **failed and inconclusive runs stay visible** — every rejection/inconclusive outcome carries a
  `RejectionReasonRecord`; nothing is hidden;
* **the runtime orchestrates, not duplicates** — research, experiments, governance, backtest,
  features, labels, and data foundation primitives are consumed by their real import paths and
  never edited;
* **the DAG metadata is sound** — parallel-safe phases have disjoint `allowed_paths` and no global
  files, merge is serial, and no phase branch writes `ACTIVE_CAMPAIGN.md`;
* **no prohibited scope or claim exists** — no broker/live/paper/order-routing/account, no
  external provider call, no broad alpha search, no factor promotion, no
  alpha/profitability/tradability/strategy/backtest/portfolio scope — and the prohibited MVP
  states (`ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`, `LIVE_READY`,
  `PAPER_READY`, `PROFITABLE`, `TRADABLE`, `PRODUCTION_READY`) are unreachable;
* the **artifact audit is clean** (no `runs/**`, raw, canonical, feature/label value, runtime
  value, heavy, provider, account, or local-DB artifacts committed).

## Final closeout requirements

* `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/CLOSEOUT.md` exists and records the final verdict and any
  warnings (written by `RT-P26`); `docs/research_runtime/ACCEPTANCE_AUDIT.md` records the audit.
* `ACTIVE_CAMPAIGN.md` reflects campaign completion and points at the next campaign or none —
  **updated by the coordinator, never by a phase branch**.
* The end-to-end runtime dry run (`RT-P25`) and the small real FLF DatasetVersion runtime smoke
  (`RT-P21`) are local-only, make **no external provider call**, commit only curated row-free
  summaries, and may record a truthful `PASS_WITH_WARNINGS` (with the exact operator command
  documented) when the local registry/data is absent on the runner.
* Durable lessons are added to `project-skill` when applicable.
* Next-campaign readiness is recorded: the runtime is ready to be consumed by the future **Agent
  Factory** (AI Alpha Researchers driving approved `AlphaSpec` + `StudySpec` through this runtime
  into diagnostics and `EvidenceDraft`s), which may consume this layer only under its own
  authorized contract and the governance + data-admissibility gates this campaign relies on. A
  diagnostic PASS is not alpha validation; a signal probe is not a strategy candidate; an
  `EvidenceDraft` is not a candidate; a `ReferenceCandidateHandoff` is not Reference validation.

## Final acceptance verdicts

### `COMPLETE`
All 27 phases carry merged `PASS` or `PASS_WITH_WARNINGS` verdicts, all campaign-level criteria
are met, the runtime genuinely fails closed on missing prerequisites, the accepted-DatasetVersion
and no-lookahead boundaries hold, cost stress and variant budgets are enforced, failed and
inconclusive runs remain visible, the semantic done-check is clean, the artifact audit is clean,
and no prohibited scope or claims exist.

### `COMPLETE_WITH_WARNINGS`
All hard criteria met, but non-blocking warnings (e.g. documented deferrals, an end-to-end dry run
or small real DatasetVersion smoke that recorded a truthful `PASS_WITH_WARNINGS` because the local
registry/data was absent on the runner, or minor limitations) are recorded in `CLOSEOUT.md`.

### `BLOCKED`
A hard criterion cannot be met (e.g. a gate cannot be made to fail closed, the no-lookahead or
accepted-DatasetVersion boundary cannot be guaranteed, cost stress or the variant budget cannot be
enforced, the runtime cannot be made to orchestrate rather than duplicate a primitive, or a
required object cannot be completed in scope). The blocker is recorded truthfully; fake completion
is forbidden, and a truthful `BLOCKED` is preferred over a false `COMPLETE`.

---

*This file is a campaign contract describing intent and boundaries for the Research Runtime MVP;
it makes no alpha, tradability, profitability, or production-readiness claim.*
