# ALPHA_FEATURE_LABEL_FOUNDATION_V1 Phase Plan

## Purpose

This is the human-readable, phase-by-phase contract for **ALPHA_FEATURE_LABEL_FOUNDATION_V1**, the campaign that builds the
**research substrate layer** future AI Alpha Researchers consume: a versioned, no-lookahead-safe,
deduplicated, cost-aware, BBO-aware FeatureStore and LabelStore over **accepted DatasetVersions**.

It is the bridge from `accepted DatasetVersion` to `research-ready FeatureStore / LabelStore substrate`.
It is **not** alpha research, **not** strategy work, and **not** a feature/label dumping ground. A feature
is not alpha; a label is not alpha; a materialized FeatureSet is not a promoted candidate.

This campaign runs under **Workflow 2 with the DAG wave scheduler**: dependency-ready phase selection,
concurrent build of conflict-free parallel-safe waves in isolated worktrees, and a **serial merge queue**
that merges one PR at a time. `ACTIVE_CAMPAIGN.md` is coordinator-owned and is never written by a phase
branch in parallel mode.

## Campaign Invariants

* Consume only **accepted DatasetVersions** via `resolve_dataset_version`; never read raw provider files.
* Databento is the **primary deep-history research source**; IBKR is **broker-source recent validation only**.
* Every feature value carries `available_ts`; every label value carries `label_available_ts`.
* No `FeatureRequest` → no feature; no `FeatureSpec` → no feature values; no `LabelSpec` → no label values.
* No label-as-feature; no future/centered rolling windows in live features.
* Governance objects (`FeatureRequest`, `LabelSpec`, `StudySpec`, `AlphaSpec`) are **consumed, not duplicated**.
* BBO missingness is flagged (`missing_bbo` / `bbo_quarantined`); no silent forward-fill. Synthetic dense-grid
  no-trade rows are flagged (`has_trade=false`, `synthetic=true`, `no_trade`) and never treated as trade bars.
* Locked-test partition use requires governance contamination metadata.
* Feature/label values, raw/canonical data, heavy artifacts, and local registries are **local-only**, never committed.
* No external provider calls; no broker/live/paper/order/account scope; no alpha/tradability/profitability claims.

## Global Phase Rules

### Workflow Rules
Workflow 2 strict autonomous loop with the DAG wave scheduler. State order:
`RUN_INIT -> CAMPAIGN_LOAD -> PHASE_SELECT -> SPEC_GENERATE -> SPEC_VALIDATE -> WORKTREE_CREATE ->
CODEX_EXECUTE -> CHECKS_RUN -> HANDOFF_VALIDATE -> CLAUDE_REVIEW -> VERDICT_PARSE -> PR_CREATE -> CI_WAIT ->
MERGE_GATE -> MERGE -> DONE_CHECK -> NEXT_PHASE -> CAMPAIGN_DONE_CHECK -> RUN_SUMMARY`.

### DAG Wave Scheduler Rules
* `workflow2.scheduler.mode: dag_wave`, `parallel_execution: true`, `max_parallel_phases: 3`,
  `merge_queue: serial`, `update_active_campaign: coordinator_only`.
* A phase is parallel-safe **only** if it sets `parallel_safe: true`, declares disjoint `allowed_paths`,
  sets `must_run_alone: false`, declares no global/coordinator file, and is not RED.
* Bootstrap, core contracts, materialization engines, stores/registries, CLI, dry runs, and closeout
  **run alone**. Feature-family and label-family phases parallelize because they write disjoint paths.
* Run `just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1` (read-only) and `just frontier-run-parallel-mock ALPHA_FEATURE_LABEL_FOUNDATION_V1 3` before the first
  live parallel run. Merge always proceeds **serially**, one PR at a time.

### Repo Path Rules
Active repo and worktrees must live under `~/projects/alpha_system` on the WSL2 Linux filesystem. `/mnt/c`,
OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temp dirs are forbidden.

### Git Rules
Explicit staging only. `git add .` / `git add -A` forbidden. No force push. Confirm the staged set has no
`runs/` path and no raw/canonical/value/DB/heavy artifact before any commit or merge-gate evaluation.

### Artifact Rules
Commit only source, configs, schemas, docs, tests, tiny synthetic fixtures, templates, handoffs, reviews, and
curated row-free summaries. Never commit feature/label values, raw/canonical data, provider responses, local
registries/DBs, or heavy artifacts. `git ls-files runs` must be empty.

### Domain Boundary Rules
Consume accepted DatasetVersions only; no raw provider access; no external provider calls; no order/account/
broker/paper/live scope; no alpha search/strategy/backtest/portfolio scope; no ML beyond authorized scope; no
L2/event-stream ingestion.

### Review Rules
YELLOW phases require fresh Claude Opus review with a `verdict.json` (`PASS`/`PASS_WITH_WARNINGS` to merge).
GREEN phases (docs/mechanical) may skip review. The reviewer is independent; implementers cannot self-approve.

### Repair Rules
Bounded repair loop (max 2 attempts by default) on `REWORK`/`FAIL`; repair attempts are recorded under
`runs/<run_id>/phases/<phase_id>/repair_attempts/`. Fake completion is forbidden. `BLOCKED` writes a truthful
blocked handoff and stops.

### Validation Rules
Run the narrowest meaningful test first, broaden when shared behavior changes, and record skipped checks with
the reason. Default validation: `python tools/verify.py --smoke` / `--all`, `python tools/hooks/canary_runner.py`.

## Phase Table Summary

| Phase ID | Phase Name | Lane | Dependencies | Parallel-safe | Merge Group |
| -------- | ---------- | ---- | ------------ | ------------- | ----------- |
| FLF-P00 | Feature/Label Campaign Bootstrap | GREEN | none | no | `foundation` |
| FLF-P01 | Entry Contract and DatasetVersion Consumption | YELLOW | FLF-P00 | no | `foundation` |
| FLF-P02 | Feature/Label Package Skeleton and Naming | YELLOW | FLF-P01 | no | `foundation` |
| FLF-P03 | Canonical Input Views for OHLCV and BBO | YELLOW | FLF-P02 | no | `foundation` |
| FLF-P04 | Dense Grid / No-Trade / BBO Missingness Semantics | YELLOW | FLF-P03 | no | `foundation` |
| FLF-P05 | FeatureRequest Gate and Duplicate Exposure Guard | YELLOW | FLF-P04 | no | `foundation` |
| FLF-P06 | FeatureSpec and FeatureVersion Contracts | YELLOW | FLF-P05 | no | `foundation` |
| FLF-P07 | Transform / Window / Normalization Primitives | YELLOW | FLF-P06 | no | `foundation` |
| FLF-P08 | Base OHLCV Feature Families | YELLOW | FLF-P06, FLF-P07 | yes | `feature_families` |
| FLF-P09 | BBO Tradability Feature Families | YELLOW | FLF-P06, FLF-P07 | yes | `feature_families` |
| FLF-P10 | Session / Calendar / Roll Feature Families | YELLOW | FLF-P06, FLF-P07 | yes | `feature_families` |
| FLF-P11 | Cross-Market ES/NQ/RTY Feature Families | YELLOW | FLF-P06, FLF-P07 | yes | `feature_families` |
| FLF-P12 | Liquidity Sweep / Structure Primitive Features | YELLOW | FLF-P06, FLF-P07 | yes | `feature_families` |
| FLF-P13 | Feature Materialization Engine | YELLOW | FLF-P08, FLF-P09, FLF-P10, FLF-P11, FLF-P12 | no | `feature_integration` |
| FLF-P14 | FeatureStore / FeatureRegistry Integration | YELLOW | FLF-P13 | no | `feature_integration` |
| FLF-P15 | Feature Quality and Coverage Reports | YELLOW | FLF-P14 | no | `feature_integration` |
| FLF-P16 | LabelSpec and LabelVersion Contracts | YELLOW | FLF-P07 | no | `label_families` |
| FLF-P17 | Fixed-Horizon and Midprice Forward Labels | YELLOW | FLF-P16 | yes | `label_families` |
| FLF-P18 | Cost-Adjusted / Spread-Adjusted Labels | YELLOW | FLF-P16 | yes | `label_families` |
| FLF-P19 | Path Labels: MFE / MAE / Triple Barrier | YELLOW | FLF-P16 | yes | `label_families` |
| FLF-P20 | Strategy-Agnostic Event Labels | YELLOW | FLF-P16 | yes | `label_families` |
| FLF-P21 | Label Materialization Engine | YELLOW | FLF-P17, FLF-P18, FLF-P19, FLF-P20 | no | `label_integration` |
| FLF-P22 | LabelStore / LabelRegistry Integration | YELLOW | FLF-P21 | no | `label_integration` |
| FLF-P23 | Label Leakage and Availability Audits | YELLOW | FLF-P22 | no | `label_integration` |
| FLF-P24 | Feature/Label Diagnostics Reports | YELLOW | FLF-P15, FLF-P23 | yes | `diagnostics_and_packaging` |
| FLF-P25 | Synthetic Fixtures and Fail-Closed Tests | YELLOW | FLF-P15, FLF-P23 | yes | `diagnostics_and_packaging` |
| FLF-P26 | Small Real Databento DatasetVersion Dry Run | YELLOW | FLF-P25 | no | `diagnostics_and_packaging` |
| FLF-P27 | Governance Integration: StudySpec Input Packs | YELLOW | FLF-P15, FLF-P23 | yes | `diagnostics_and_packaging` |
| FLF-P28 | CLI / Tooling Surface | YELLOW | FLF-P15, FLF-P23, FLF-P27 | no | `diagnostics_and_packaging` |
| FLF-P29 | Docs, Templates, and Agent Guide | GREEN | FLF-P15, FLF-P23 | yes | `diagnostics_and_packaging` |
| FLF-P30 | End-to-End Feature/Label Dry Run | YELLOW | FLF-P26, FLF-P28, FLF-P29 | no | `closeout` |
| FLF-P31 | Workflow 2 Acceptance Audit and Closeout | YELLOW | FLF-P30 | no | `closeout` |

## Parallel Wave Summary

- **Wave 0 — Sequential bootstrap and core contracts (run-alone)**: FLF-P00, FLF-P01, FLF-P02, FLF-P03, FLF-P04, FLF-P05, FLF-P06, FLF-P07. All run-alone.
- **Wave 1 — Parallel feature families (disjoint allowed_paths)**: FLF-P08, FLF-P09, FLF-P10, FLF-P11, FLF-P12. Parallel-safe: FLF-P08, FLF-P09, FLF-P10, FLF-P11, FLF-P12.
- **Wave 2 — Sequential feature integration (run-alone)**: FLF-P13, FLF-P14, FLF-P15. All run-alone.
- **Wave 3 — Label contracts (run-alone) then parallel label families**: FLF-P16, FLF-P17, FLF-P18, FLF-P19, FLF-P20. Parallel-safe: FLF-P17, FLF-P18, FLF-P19, FLF-P20.
- **Wave 4 — Sequential label integration (run-alone)**: FLF-P21, FLF-P22, FLF-P23. All run-alone.
- **Wave 5 — Partial-parallel diagnostics / fixtures / governance / docs**: FLF-P24, FLF-P25, FLF-P26, FLF-P27, FLF-P28, FLF-P29. Parallel-safe: FLF-P24, FLF-P25, FLF-P27, FLF-P29.
- **Wave 6 — Sequential dry run and closeout (run-alone)**: FLF-P30, FLF-P31. All run-alone.

Waves are computed by the DAG scheduler from dependencies + DAG metadata, not hard-coded; the lists above are
the intended shape. After the canonical input layer (FLF-P04/FLF-P07) the **feature track** and **label track**
fan out and interleave. Run `just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1` to preview the exact waves.

## Acceptance Gate Summary

Every phase belongs to exactly one acceptance gate. Gates have no gaps and no overlaps.

| Gate | Phases | Exit Requirement |
| ---- | ------ | ---------------- |
| `campaign_bootstrap` | FLF-P00 … FLF-P02 | Campaign control files present; no campaign-local ACTIVE_CAMPAIGN.md; features package imports; DatasetVersion consumption adapter present and accepted-only; package skeleton + naming present; handoffs/reviews present; artifact audit clean; no forbidden scope or claims. |
| `canonical_inputs` | FLF-P03 … FLF-P04 | Canonical OHLCV/BBO input views key off available_ts; dense-grid/no-trade and BBO-missingness semantics present with synthetic rows flagged and no silent forward-fill. |
| `feature_contracts` | FLF-P05 … FLF-P07 | FeatureRequest gate + duplicate-exposure guard wired to governance; FeatureSpec/FeatureVersion contracts present with available_ts required; transform/window/normalization primitives causal and no-lookahead. |
| `feature_families` | FLF-P08 … FLF-P12 | Five feature families implemented additively in disjoint family dirs with available_ts on every value; unit-tested on synthetic fixtures; no shared-core or cross-family edits. |
| `feature_materialization` | FLF-P13 … FLF-P15 | Feature materialization engine + FeatureStore/registry (local-only) + quality/coverage reports present; values never committed; no dumping ground. |
| `label_contracts` | FLF-P16 … FLF-P20 | LabelVersion contracts bind to governance LabelSpec; four label families implemented additively with label_available_ts; future data legal only for labels; no label-as-feature. |
| `label_materialization` | FLF-P21 … FLF-P23 | Label materialization engine + LabelStore/registry (local-only) + leakage/availability audits present; values never committed; leakage audits pass. |
| `diagnostics_and_tests` | FLF-P24 … FLF-P26 | Feature/Label diagnostics (descriptive, non-promotional) + synthetic fixtures + fail-closed test suite present; small local-only Databento dry run passes or truthful PASS_WITH_WARNINGS. |
| `workflow_and_closeout` | FLF-P27 … FLF-P31 | StudySpec Input Pack integrates with existing governance; CLI surface local-only and CI-safe; durable guide/templates present; end-to-end dry run passes; acceptance audit + semantic done-check pass with a recorded final verdict and next-campaign readiness. |

---

# Detailed Phase Specs

---

## FLF-P00 — Feature/Label Campaign Bootstrap

### Phase ID
`FLF-P00`

### Phase Name
Feature/Label Campaign Bootstrap

### Lane
GREEN

### Dependencies
None.

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `foundation`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/**`
  * `docs/feature_label_foundation/README.md`
  * `docs/feature_label_foundation/OVERVIEW.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P00.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P00/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Create the implementation entry point for the Feature/Label Foundation campaign: the documentation root and a high-level overview of the feature/label research substrate, while confirming the campaign contract bundle is present and self-consistent. Makes the repository ready to execute the remaining phases. The ACTIVE_CAMPAIGN.md pointer is coordinator-owned and is NOT written by any phase branch.

### Scope
* Confirm the campaign contract bundle under campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/ is present and consistent.
* Create docs/feature_label_foundation/README.md and docs/feature_label_foundation/OVERVIEW.md describing the research substrate, the hard rules, the Feature/Label object families, the lifecycle state models, and the DatasetVersion entry contract at a high level.
* Create the commit-eligible handoff handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P00.md.

### Non-Goals
* Do not create feature or label source code.
* Do not write ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).
* Do not create a campaign-local ACTIVE_CAMPAIGN.md.
* Do not pull data or call any provider API.

### Expected Files / Directories
* `docs/feature_label_foundation/README.md`
* `docs/feature_label_foundation/OVERVIEW.md`
* `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P00.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/GOAL.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/campaign.yaml
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/RUNBOOK.md
test '!' -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/ACTIVE_CAMPAIGN.md
test -f handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P00.md
grep -q "ALPHA_FEATURE_LABEL_FOUNDATION_V1" ACTIVE_CAMPAIGN.md
python tools/verify.py --smoke
git ls-files runs
```

### Artifact Policy
Commit only: campaign overview docs, commit-eligible handoff. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Feature/Label docs root exists with an overview of the substrate and lifecycle models.
* ACTIVE_CAMPAIGN.md points to ALPHA_FEATURE_LABEL_FOUNDATION_V1 (written by the coordinator).
* No campaign-local ACTIVE_CAMPAIGN.md exists.
* Commit-eligible handoff exists and records validation results.
* No feature/label source, tests, or forbidden scope introduced.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P00.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Optional (GREEN docs/mechanical lane). Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P01 — Entry Contract and DatasetVersion Consumption

### Phase ID
`FLF-P01`

### Phase Name
Entry Contract and DatasetVersion Consumption

### Lane
YELLOW

### Dependencies
`FLF-P00`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `foundation`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/__init__.py`
  * `src/alpha_system/features/consumption.py`
  * `tests/unit/features/test_consumption.py`
  * `docs/feature_label_foundation/ENTRY_CONTRACT_CONSUMPTION.md`
  * `configs/features/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P01.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P01/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Establish the single sanctioned path by which the Feature/Label layer consumes an ACCEPTED DatasetVersion. Wrap resolve_dataset_version and the canonical record loaders so that NO feature/label code ever reads raw provider files. Encode the accepted-DatasetVersion admissibility check (lifecycle state in {VERSIONED, READY_FOR_RESEARCH} with non-blocking quality + coverage).

### Scope
* Create the features package root src/alpha_system/features/__init__.py.
* Create src/alpha_system/features/consumption.py exposing a thin, read-only consumption adapter over alpha_system.data.foundation.version_registry.resolve_dataset_version and the canonical record from_mapping loaders (CanonicalBarRecord, CanonicalBBORecord, DenseGridBarRecord).
* Encode accepted/admissible gating: refuse to materialize unless the DatasetVersion is admissible; surface partition + locked-test gating via require_governance_metadata_for_locked_partition_use.
* Document the entry contract in docs/feature_label_foundation/ENTRY_CONTRACT_CONSUMPTION.md (consumes docs/FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md).

### Non-Goals
* Do not read raw Databento/IBKR files; canonical records only.
* Do not materialize any feature or label values.
* Do not call any external provider API.
* Do not merge Databento and IBKR DatasetVersions.

### Expected Files / Directories
* `src/alpha_system/features/__init__.py`
* `src/alpha_system/features/consumption.py`
* `tests/unit/features/test_consumption.py`
* `docs/feature_label_foundation/ENTRY_CONTRACT_CONSUMPTION.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.consumption"
python tools/verify.py --smoke
python -m pytest tests/unit/features -q
test -f docs/feature_label_foundation/ENTRY_CONTRACT_CONSUMPTION.md
git ls-files runs
```

### Artifact Policy
Commit only: DatasetVersion consumption adapter, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* alpha_system.features imports cleanly.
* The consumption adapter resolves only accepted DatasetVersions and exposes canonical records, never raw provider data.
* Locked-test partition use is gated by governance contamination metadata.
* No raw provider access, materialization, or external call introduced.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P01.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P02 — Feature/Label Package Skeleton and Naming

### Phase ID
`FLF-P02`

### Phase Name
Feature/Label Package Skeleton and Naming

### Lane
YELLOW

### Dependencies
`FLF-P01`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `foundation`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/**`
  * `src/alpha_system/labels/families/**`
  * `tests/unit/features/**`
  * `tests/unit/labels/families/**`
  * `tests/no_lookahead/feature_label/**`
  * `configs/features/**`
  * `configs/labels/**`
  * `docs/feature_label_foundation/NAMING.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P02.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P02/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Establish the importable features package skeleton, the label-families subpackage skeleton under the existing labels package, the test/config/doc roots, and the canonical naming conventions for all Feature/Label objects, IDs, files, and directories — so every later phase has disjoint, additive write targets.

### Scope
* Create src/alpha_system/features/ subpackage stubs (families/, primitives/, engine/) with __init__.py placeholders.
* Create src/alpha_system/labels/families/__init__.py (additive subpackage; do not edit existing labels/*.py).
* Create tests/unit/features/, tests/unit/labels/families/, tests/no_lookahead/feature_label/ roots with import smoke tests.
* Create configs/features/ and configs/labels/ roots with documented placeholders.
* Create docs/feature_label_foundation/NAMING.md defining object names, ID prefixes (e.g. freq_/lspec_ reuse from governance), file naming, and directory layout.

### Non-Goals
* Do not implement object validation logic yet.
* Do not edit existing labels/*.py modules or governance modules.
* Do not materialize values.

### Expected Files / Directories
* `src/alpha_system/features/{families,primitives,engine}/__init__.py`
* `src/alpha_system/labels/families/__init__.py`
* `tests/unit/features/test_package_skeleton.py`
* `configs/features/, configs/labels/ (with .gitkeep/README.md)`
* `docs/feature_label_foundation/NAMING.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features"
python tools/verify.py --smoke
python -m pytest tests/unit/features -q
test -f docs/feature_label_foundation/NAMING.md
git ls-files runs
```

### Artifact Policy
Commit only: package skeletons, tests, configs placeholders, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* alpha_system.features and alpha_system.labels.families import cleanly.
* Skeleton, test, config, and doc roots exist with passing import smoke tests.
* Canonical naming documented; existing labels/*.py and governance modules untouched.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P02.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P03 — Canonical Input Views for OHLCV and BBO

### Phase ID
`FLF-P03`

### Phase Name
Canonical Input Views for OHLCV and BBO

### Lane
YELLOW

### Dependencies
`FLF-P02`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `foundation`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/input_views.py`
  * `tests/unit/features/test_input_views.py`
  * `tests/no_lookahead/feature_label/test_input_views_available_ts.py`
  * `docs/feature_label_foundation/INPUT_VIEWS.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P03.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P03/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Provide provider-agnostic, no-lookahead input views over CanonicalBarRecord and CanonicalBBORecord that every feature and label family consumes. Views key strictly off available_ts, expose the five distinct timestamps, and never expose raw provider fields.

### Scope
* Create src/alpha_system/features/input_views.py building aligned OHLCV and BBO views from canonical records.
* Expose available_ts-ordered access; forbid use of event_ts/provider_ts/ingested_at for usability ordering.
* Surface BBO fields (bid, ask, bid_size, ask_size, mid, spread, optional spread_ticks/microprice/bid_order_count/ask_order_count) and quality_flags tokens.
* Document timestamp + alignment semantics in docs/feature_label_foundation/INPUT_VIEWS.md.

### Non-Goals
* No feature computation.
* No raw provider access.
* No materialization.

### Expected Files / Directories
* `src/alpha_system/features/input_views.py`
* `tests/unit/features/test_input_views.py`
* `tests/no_lookahead/feature_label/test_input_views_available_ts.py`
* `docs/feature_label_foundation/INPUT_VIEWS.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.input_views"
python tools/verify.py --smoke
python -m pytest tests/unit/features tests/no_lookahead/feature_label -q
test -f docs/feature_label_foundation/INPUT_VIEWS.md
git ls-files runs
```

### Artifact Policy
Commit only: input view layer, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Input views expose canonical OHLCV/BBO keyed off available_ts.
* No-lookahead tests prove usability never keys off event_ts/provider_ts/ingested_at.
* No raw provider access or materialization introduced.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P03.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P04 — Dense Grid / No-Trade / BBO Missingness Semantics

### Phase ID
`FLF-P04`

### Phase Name
Dense Grid / No-Trade / BBO Missingness Semantics

### Lane
YELLOW

### Dependencies
`FLF-P03`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `foundation`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/semantics.py`
  * `tests/unit/features/test_semantics.py`
  * `docs/feature_label_foundation/DENSE_GRID_AND_BBO_SEMANTICS.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P04.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P04/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Encode the canonical policy that preserves provider trade-truth while allowing a flagged dense 1-minute research grid. Synthetic no-trade rows and missing/abnormal BBO must be explicitly flagged and never treated as actual trade bars or executable quotes.

### Scope
* Create src/alpha_system/features/semantics.py mediating sparse OHLCV truth vs DenseGridBarRecord (has_trade, synthetic, fill_method, provider_bar_ref, no_trade flag).
* Encode BBO missingness handling using the missing_bbo and bbo_quarantined quality-flag tokens; no silent forward-fill.
* Provide predicates feature/label families use to exclude or flag synthetic / missing-BBO rows.
* Document the policy in docs/feature_label_foundation/DENSE_GRID_AND_BBO_SEMANTICS.md.

### Non-Goals
* No feature computation.
* No silent forward-fill.
* No treating synthetic rows as trades.

### Expected Files / Directories
* `src/alpha_system/features/semantics.py`
* `tests/unit/features/test_semantics.py`
* `docs/feature_label_foundation/DENSE_GRID_AND_BBO_SEMANTICS.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.semantics"
python tools/verify.py --smoke
python -m pytest tests/unit/features -q
test -f docs/feature_label_foundation/DENSE_GRID_AND_BBO_SEMANTICS.md
git ls-files runs
```

### Artifact Policy
Commit only: dense-grid / no-trade / BBO-missingness semantics, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Synthetic no-trade rows are detectable via has_trade/synthetic/no_trade flags and never treated as trade bars.
* Missing/abnormal BBO is flagged (missing_bbo/bbo_quarantined) with no silent forward-fill.
* Policy documented and tested.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P04.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P05 — FeatureRequest Gate and Duplicate Exposure Guard

### Phase ID
`FLF-P05`

### Phase Name
FeatureRequest Gate and Duplicate Exposure Guard

### Lane
YELLOW

### Dependencies
`FLF-P04`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `foundation`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/request_gate.py`
  * `tests/unit/features/test_request_gate.py`
  * `docs/feature_label_foundation/FEATURE_REQUEST_GATE.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P05.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P05/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Wire the existing governance FeatureRequest + duplicate-exposure guard into the feature layer so NO feature may be implemented without an approved FeatureRequest and a duplicate/equivalent-exposure check. This consumes governance objects; it does not re-implement them (R-022).

### Scope
* Create src/alpha_system/features/request_gate.py adapting alpha_system.governance.feature_request.FeatureRequest and alpha_system.governance.duplicate_exposure.
* Enforce: no FeatureRequest (freq_) -> no feature implementation; approval_status gating; duplicate/equivalent exposure recorded.
* Define DuplicateExposureReport / EquivalentFeatureGroup views over the governance guard output.
* Document the gate in docs/feature_label_foundation/FEATURE_REQUEST_GATE.md.

### Non-Goals
* Do not re-implement FeatureRequest or the duplicate-exposure guard (consume governance).
* Do not implement any concrete feature.

### Expected Files / Directories
* `src/alpha_system/features/request_gate.py`
* `tests/unit/features/test_request_gate.py`
* `docs/feature_label_foundation/FEATURE_REQUEST_GATE.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.request_gate"
python tools/verify.py --smoke
python -m pytest tests/unit/features -q
test -f docs/feature_label_foundation/FEATURE_REQUEST_GATE.md
git ls-files runs
```

### Artifact Policy
Commit only: FeatureRequest gate adapter, duplicate-exposure views, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* No feature implementation is reachable without an approved governance FeatureRequest.
* Duplicate/equivalent exposure is checked and recorded via the governance guard (not re-implemented).
* Gate documented and tested fail-closed.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P05.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P06 — FeatureSpec and FeatureVersion Contracts

### Phase ID
`FLF-P06`

### Phase Name
FeatureSpec and FeatureVersion Contracts

### Lane
YELLOW

### Dependencies
`FLF-P05`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `foundation`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/contracts.py`
  * `tests/unit/features/test_contracts.py`
  * `docs/feature_label_foundation/FEATURE_CONTRACTS.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P06.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P06/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Define the immutable feature contract objects the families and engine consume: FeatureSpec, FeatureFamily, FeatureInputSpec, TransformSpec, WindowSpec, NormalizationSpec, FeatureSetSpec, FeatureVersion, FeatureLineageRecord. Every feature value must carry available_ts; no FeatureSpec -> no feature values.

### Scope
* Create src/alpha_system/features/contracts.py with frozen dataclasses for the feature contract family and a deterministic FeatureVersion id.
* Require available_ts on FeatureValueRecord; forbid future/centered windows for live features at the contract level.
* Avoid colliding with the pre-existing experiments/feature_sets.py FeatureSetSpec — name-namespace under features/.
* Document the contracts in docs/feature_label_foundation/FEATURE_CONTRACTS.md.

### Non-Goals
* No concrete feature families.
* No materialization.
* No registry persistence.

### Expected Files / Directories
* `src/alpha_system/features/contracts.py`
* `tests/unit/features/test_contracts.py`
* `docs/feature_label_foundation/FEATURE_CONTRACTS.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.contracts"
python tools/verify.py --smoke
python -m pytest tests/unit/features -q
test -f docs/feature_label_foundation/FEATURE_CONTRACTS.md
git ls-files runs
```

### Artifact Policy
Commit only: feature contract objects, FeatureVersion, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* FeatureSpec/FeatureVersion and the contract family exist as immutable, hashable objects.
* available_ts is required on feature values; future/centered live windows are contract-forbidden.
* No collision with experiments/feature_sets.py; no materialization.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P06.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P07 — Transform / Window / Normalization Primitives

### Phase ID
`FLF-P07`

### Phase Name
Transform / Window / Normalization Primitives

### Lane
YELLOW

### Dependencies
`FLF-P06`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `foundation`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/primitives/**`
  * `tests/unit/features/test_primitives.py`
  * `tests/no_lookahead/feature_label/test_primitives_causal.py`
  * `docs/feature_label_foundation/PRIMITIVES.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P07.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P07/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Provide the shared, no-lookahead transform/window/normalization primitives that both feature families and label families build on: causal rolling windows, z-scores, returns, ATR-style ranges, session-aware resets. Centered/future windows are offline-only and blocked from live features.

### Scope
* Create src/alpha_system/features/primitives/ with causal window, normalization, and return primitives keyed off available_ts.
* Make centered/future windows explicitly offline-only and unavailable to live-feature contracts.
* Provide deterministic, dependency-light implementations (stdlib + numpy/pandas as already used).
* Document primitives in docs/feature_label_foundation/PRIMITIVES.md.

### Non-Goals
* No concrete features.
* No live use of centered/future windows.
* No materialization.

### Expected Files / Directories
* `src/alpha_system/features/primitives/**`
* `tests/unit/features/test_primitives.py`
* `tests/no_lookahead/feature_label/test_primitives_causal.py`
* `docs/feature_label_foundation/PRIMITIVES.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.primitives"
python tools/verify.py --smoke
python -m pytest tests/unit/features tests/no_lookahead/feature_label -q
test -f docs/feature_label_foundation/PRIMITIVES.md
git ls-files runs
```

### Artifact Policy
Commit only: transform/window/normalization primitives, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Causal primitives exist and are proven no-lookahead by tests.
* Centered/future windows are offline-only and blocked from live-feature contracts.
* Primitives are shared by feature and label families.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P07.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P08 — Base OHLCV Feature Families

### Phase ID
`FLF-P08`

### Phase Name
Base OHLCV Feature Families

### Lane
YELLOW

### Dependencies
`FLF-P06`, `FLF-P07`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `feature_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/families/ohlcv/**`
  * `tests/unit/features/families/ohlcv/**`
  * `docs/feature_label_foundation/features/ohlcv.md`
  * `configs/features/families/ohlcv/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P08.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P08/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement the base OHLCV feature families that the broadest set of intraday studies depend on, derived from sparse trade-truth bars with no-lookahead causality.

### Scope
* Implement the Base OHLCV Feature Families under src/alpha_system/features/families/ohlcv/ as additive modules only.
* Each feature consumes input views + primitives, carries available_ts, and is registered via an approved FeatureRequest.
* Cover at least: returns, log returns, rolling volatility, rolling range, ATR, volume z-score, rolling volume, session minute, RTH/ETH flags, opening range, overnight range, VWAP, anchored VWAP, distance to VWAP, range position, trendiness.
* Document the family in docs/feature_label_foundation/features/ohlcv.md.

### Non-Goals
* Do not edit shared feature-core files (contracts, store, engine, primitives, registry).
* Do not edit any other feature family or any label module.
* Do not materialize values to disk; produce feature definitions + unit-tested logic on synthetic fixtures.
* Do not introduce future/centered live windows.

### Expected Files / Directories
* `src/alpha_system/features/families/ohlcv/**`
* `tests/unit/features/families/ohlcv/**`
* `docs/feature_label_foundation/features/ohlcv.md`
* `configs/features/families/ohlcv/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.families.ohlcv"
python tools/verify.py --smoke
python -m pytest tests/unit/features/families/ohlcv -q
test -f docs/feature_label_foundation/features/ohlcv.md
git ls-files runs
```

### Artifact Policy
Commit only: Base OHLCV Feature Families (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The Base OHLCV Feature Families are implemented additively under families/ohlcv/ with available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No materialization, no future/centered live windows, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P08.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P09 — BBO Tradability Feature Families

### Phase ID
`FLF-P09`

### Phase Name
BBO Tradability Feature Families

### Lane
YELLOW

### Dependencies
`FLF-P06`, `FLF-P07`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `feature_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/families/bbo/**`
  * `tests/unit/features/families/bbo/**`
  * `docs/feature_label_foundation/features/bbo.md`
  * `configs/features/families/bbo/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P09.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P09/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement the BBO tradability feature families — the first full-history L1-lite tradability layer — with explicit missing/abnormal-quote handling and no silent forward-fill.

### Scope
* Implement the BBO Tradability Feature Families under src/alpha_system/features/families/bbo/ as additive modules only.
* Each feature consumes input views + primitives, carries available_ts, and is registered via an approved FeatureRequest.
* Cover at least: mid, spread, spread_ticks, spread_bps, spread_zscore, bid size, ask size, top_book_depth, top_book_imbalance, microprice, microprice_minus_mid, missing_bbo_flag, bad_quote_flag, wide_spread_flag, low_depth_flag.
* Document the family in docs/feature_label_foundation/features/bbo.md.

### Non-Goals
* Do not edit shared feature-core files (contracts, store, engine, primitives, registry).
* Do not edit any other feature family or any label module.
* Do not materialize values to disk; produce feature definitions + unit-tested logic on synthetic fixtures.
* Do not introduce future/centered live windows.

### Expected Files / Directories
* `src/alpha_system/features/families/bbo/**`
* `tests/unit/features/families/bbo/**`
* `docs/feature_label_foundation/features/bbo.md`
* `configs/features/families/bbo/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.families.bbo"
python tools/verify.py --smoke
python -m pytest tests/unit/features/families/bbo -q
test -f docs/feature_label_foundation/features/bbo.md
git ls-files runs
```

### Artifact Policy
Commit only: BBO Tradability Feature Families (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The BBO Tradability Feature Families are implemented additively under families/bbo/ with available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No materialization, no future/centered live windows, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P09.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P10 — Session / Calendar / Roll Feature Families

### Phase ID
`FLF-P10`

### Phase Name
Session / Calendar / Roll Feature Families

### Lane
YELLOW

### Dependencies
`FLF-P06`, `FLF-P07`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `feature_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/families/session/**`
  * `tests/unit/features/families/session/**`
  * `docs/feature_label_foundation/features/session.md`
  * `configs/features/families/session/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P10.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P10/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement session, calendar, and roll feature families using the canonical session/calendar/roll metadata from the data foundation, with explicit handling of halts/status where available.

### Scope
* Implement the Session / Calendar / Roll Feature Families under src/alpha_system/features/families/session/ as additive modules only.
* Each feature consumes input views + primitives, carries available_ts, and is registered via an approved FeatureRequest.
* Cover at least: session_id, minutes_from_rth_open, minutes_to_rth_close, ETH/RTH segment, day_of_week, roll proximity, expiration proximity (where available), status/halt flags (where available).
* Document the family in docs/feature_label_foundation/features/session.md.

### Non-Goals
* Do not edit shared feature-core files (contracts, store, engine, primitives, registry).
* Do not edit any other feature family or any label module.
* Do not materialize values to disk; produce feature definitions + unit-tested logic on synthetic fixtures.
* Do not introduce future/centered live windows.

### Expected Files / Directories
* `src/alpha_system/features/families/session/**`
* `tests/unit/features/families/session/**`
* `docs/feature_label_foundation/features/session.md`
* `configs/features/families/session/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.families.session"
python tools/verify.py --smoke
python -m pytest tests/unit/features/families/session -q
test -f docs/feature_label_foundation/features/session.md
git ls-files runs
```

### Artifact Policy
Commit only: Session / Calendar / Roll Feature Families (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The Session / Calendar / Roll Feature Families are implemented additively under families/session/ with available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No materialization, no future/centered live windows, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P10.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P11 — Cross-Market ES/NQ/RTY Feature Families

### Phase ID
`FLF-P11`

### Phase Name
Cross-Market ES/NQ/RTY Feature Families

### Lane
YELLOW

### Dependencies
`FLF-P06`, `FLF-P07`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `feature_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/families/cross_market/**`
  * `tests/unit/features/families/cross_market/**`
  * `docs/feature_label_foundation/features/cross_market.md`
  * `configs/features/families/cross_market/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P11.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P11/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement cross-market ES/NQ/RTY feature families with strict timestamp alignment on available_ts so no synthetic look-ahead is introduced across instruments.

### Scope
* Implement the Cross-Market ES/NQ/RTY Feature Families under src/alpha_system/features/families/cross_market/ as additive modules only.
* Each feature consumes input views + primitives, carries available_ts, and is registered via an approved FeatureRequest.
* Cover at least: synchronized ES/NQ/RTY returns, NQ-minus-ES return spread, RTY-minus-ES return spread, rolling beta residual, rolling correlation, confirmation/divergence flags, risk-on/risk-off rotation proxies.
* Document the family in docs/feature_label_foundation/features/cross_market.md.

### Non-Goals
* Do not edit shared feature-core files (contracts, store, engine, primitives, registry).
* Do not edit any other feature family or any label module.
* Do not materialize values to disk; produce feature definitions + unit-tested logic on synthetic fixtures.
* Do not introduce future/centered live windows.

### Expected Files / Directories
* `src/alpha_system/features/families/cross_market/**`
* `tests/unit/features/families/cross_market/**`
* `docs/feature_label_foundation/features/cross_market.md`
* `configs/features/families/cross_market/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.families.cross_market"
python tools/verify.py --smoke
python -m pytest tests/unit/features/families/cross_market -q
test -f docs/feature_label_foundation/features/cross_market.md
git ls-files runs
```

### Artifact Policy
Commit only: Cross-Market ES/NQ/RTY Feature Families (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The Cross-Market ES/NQ/RTY Feature Families are implemented additively under families/cross_market/ with available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No materialization, no future/centered live windows, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P11.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P12 — Liquidity Sweep / Structure Primitive Features

### Phase ID
`FLF-P12`

### Phase Name
Liquidity Sweep / Structure Primitive Features

### Lane
YELLOW

### Dependencies
`FLF-P06`, `FLF-P07`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `feature_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/families/structure/**`
  * `tests/unit/features/families/structure/**`
  * `docs/feature_label_foundation/features/structure.md`
  * `configs/features/families/structure/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P12.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P12/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement liquidity-sweep and market-structure primitive features as strategy-agnostic descriptors (not signals), derived causally from OHLCV and BBO.

### Scope
* Implement the Liquidity Sweep / Structure Primitive Features under src/alpha_system/features/families/structure/ as additive modules only.
* Each feature consumes input views + primitives, carries available_ts, and is registered via an approved FeatureRequest.
* Cover at least: prior high/low distance, opening range high/low distance, sweep high/low flags, failed breakout flags, close location value, wick rejection score, compression / range contraction.
* Document the family in docs/feature_label_foundation/features/structure.md.

### Non-Goals
* Do not edit shared feature-core files (contracts, store, engine, primitives, registry).
* Do not edit any other feature family or any label module.
* Do not materialize values to disk; produce feature definitions + unit-tested logic on synthetic fixtures.
* Do not introduce future/centered live windows.

### Expected Files / Directories
* `src/alpha_system/features/families/structure/**`
* `tests/unit/features/families/structure/**`
* `docs/feature_label_foundation/features/structure.md`
* `configs/features/families/structure/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.families.structure"
python tools/verify.py --smoke
python -m pytest tests/unit/features/families/structure -q
test -f docs/feature_label_foundation/features/structure.md
git ls-files runs
```

### Artifact Policy
Commit only: Liquidity Sweep / Structure Primitive Features (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The Liquidity Sweep / Structure Primitive Features are implemented additively under families/structure/ with available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No materialization, no future/centered live windows, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P12.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P13 — Feature Materialization Engine

### Phase ID
`FLF-P13`

### Phase Name
Feature Materialization Engine

### Lane
YELLOW

### Dependencies
`FLF-P08`, `FLF-P09`, `FLF-P10`, `FLF-P11`, `FLF-P12`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `feature_integration`
* `conflicts_with`: none
* `resource_class`: `materialization_engine`
* `allowed_paths`:
  * `src/alpha_system/features/engine/**`
  * `tests/unit/features/test_feature_engine.py`
  * `tests/integration/features/**`
  * `docs/feature_label_foundation/FEATURE_MATERIALIZATION.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P13.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P13/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Build the FeatureMaterializationPlan + engine that turns an approved FeatureSetSpec into FeatureValueRecords for an accepted DatasetVersion + partition — local-only, deterministic, no-lookahead, idempotent. Values are never committed.

### Scope
* Create src/alpha_system/features/engine/ implementing FeatureMaterializationPlan execution over consumption views.
* Enforce available_ts propagation and partition/locked-test gating; write outputs only under $ALPHA_DATA_ROOT.
* Provide a dry-run mode that plans without writing.
* Document the engine in docs/feature_label_foundation/FEATURE_MATERIALIZATION.md.

### Non-Goals
* No committed feature values.
* No external provider calls.
* No alpha search.

### Expected Files / Directories
* `src/alpha_system/features/engine/**`
* `tests/unit/features/test_feature_engine.py`
* `tests/integration/features/test_feature_materialize.py`
* `docs/feature_label_foundation/FEATURE_MATERIALIZATION.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.engine"
python tools/verify.py --smoke
python -m pytest tests/unit/features tests/integration/features -q
test -f docs/feature_label_foundation/FEATURE_MATERIALIZATION.md
git ls-files runs
```

### Artifact Policy
Commit only: feature materialization engine, tests on synthetic fixtures, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The engine materializes FeatureValueRecords deterministically with available_ts, local-only.
* Dry-run planning works; locked-test gating enforced; no committed values.
* No external call, no alpha search.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P13.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P14 — FeatureStore / FeatureRegistry Integration

### Phase ID
`FLF-P14`

### Phase Name
FeatureStore / FeatureRegistry Integration

### Lane
YELLOW

### Dependencies
`FLF-P13`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `feature_integration`
* `conflicts_with`: none
* `resource_class`: `feature_registry`
* `allowed_paths`:
  * `src/alpha_system/features/store.py`
  * `src/alpha_system/features/registry.py`
  * `tests/unit/features/test_feature_store.py`
  * `tests/integration/features/**`
  * `docs/feature_label_foundation/FEATURE_STORE.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P14.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P14/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Integrate a FeatureStore + FeatureRegistry (FeatureRegistryRecord, FeatureLineageRecord, FeatureDeprecationRecord) so materialized features are versioned, lineage-tracked, and discoverable — with the registry DB local-only and never committed.

### Scope
* Create src/alpha_system/features/store.py and src/alpha_system/features/registry.py.
* Persist FeatureRegistryRecord/lineage to a local-only registry under $ALPHA_DATA_ROOT (sqlite), mirroring data-foundation registry patterns.
* Record duplicate-exposure status and deprecation; no FeatureStore dumping ground.
* Document the store/registry in docs/feature_label_foundation/FEATURE_STORE.md.

### Non-Goals
* No committed registry DB.
* No dumping-ground feature accumulation.
* No alpha search.

### Expected Files / Directories
* `src/alpha_system/features/store.py`
* `src/alpha_system/features/registry.py`
* `tests/unit/features/test_feature_store.py`
* `tests/integration/features/test_feature_registry_tempdb.py`
* `docs/feature_label_foundation/FEATURE_STORE.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.registry"
python tools/verify.py --smoke
python -m pytest tests/unit/features tests/integration/features -q
test -f docs/feature_label_foundation/FEATURE_STORE.md
git ls-files runs
```

### Artifact Policy
Commit only: FeatureStore/registry code, tests against temp DB, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Features are versioned + lineage-tracked in a local-only registry, never committed.
* Duplicate-exposure and deprecation are recorded; no dumping ground.
* Tests run against a temp DB with no real data.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P14.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P15 — Feature Quality and Coverage Reports

### Phase ID
`FLF-P15`

### Phase Name
Feature Quality and Coverage Reports

### Lane
YELLOW

### Dependencies
`FLF-P14`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `feature_integration`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/features/reports.py`
  * `src/alpha_system/reports/feature_card.py`
  * `tests/unit/features/test_feature_reports.py`
  * `tests/unit/reports/test_feature_card.py`
  * `docs/feature_label_foundation/FEATURE_REPORTS.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P15.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P15/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Produce FeatureQualityReport + FeatureCoverageReport (and a FeatureCard) so every registered feature has fail-closed quality and coverage evidence — non-blocking metrics vs blocking defects clearly separated.

### Scope
* Create src/alpha_system/features/reports.py and a reports/feature_card.py card renderer.
* Report coverage by symbol/session/partition and quality (nan rates, constant features, missing-BBO exposure) with blocking vs non-blocking status.
* Document the reports in docs/feature_label_foundation/FEATURE_REPORTS.md.

### Non-Goals
* No alpha/IC ranking.
* No committed report bundles.
* No tradability claims.

### Expected Files / Directories
* `src/alpha_system/features/reports.py`
* `src/alpha_system/reports/feature_card.py`
* `tests/unit/features/test_feature_reports.py`
* `docs/feature_label_foundation/FEATURE_REPORTS.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.features.reports"
python tools/verify.py --smoke
python -m pytest tests/unit/features tests/unit/reports -q
test -f docs/feature_label_foundation/FEATURE_REPORTS.md
git ls-files runs
```

### Artifact Policy
Commit only: feature quality/coverage reports, feature card, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Every registered feature can produce quality + coverage reports with blocking/non-blocking status.
* FeatureCard renders without claiming alpha/tradability.
* No committed report bundles.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P15.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P16 — LabelSpec and LabelVersion Contracts

### Phase ID
`FLF-P16`

### Phase Name
LabelSpec and LabelVersion Contracts

### Lane
YELLOW

### Dependencies
`FLF-P07`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `label_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/labels/version.py`
  * `src/alpha_system/labels/families/__init__.py`
  * `tests/unit/labels/test_label_contracts.py`
  * `docs/feature_label_foundation/LABEL_CONTRACTS.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P16.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P16/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Define the label-layer contract objects (LabelVersion, LabelInputSpec, LabelHorizonSpec, LabelPathSpec, BarrierSpec, CostAdjustmentSpec, LabelAvailabilityPolicy, LabelLineageRecord) that CONSUME the existing governance LabelSpec (lspec_). Every label carries label_available_ts; labels are never usable as live features.

### Scope
* Create src/alpha_system/labels/version.py and additive label-foundation contract modules under labels/ (without editing existing labels/spec.py/contracts.py/generation.py/store.py).
* Bind labels to governance LabelSpec via lspec_ id; require label_available_ts and forbidden_feature_overlap.
* Define the LabelAvailabilityPolicy that makes future-data use legal ONLY for labels, never for features.
* Document the contracts in docs/feature_label_foundation/LABEL_CONTRACTS.md.

### Non-Goals
* Do not re-implement the governance LabelSpec or its leakage checks (consume them).
* Do not edit existing labels/*.py core modules.
* Do not materialize label values.

### Expected Files / Directories
* `src/alpha_system/labels/version.py`
* `tests/unit/labels/test_label_contracts.py`
* `docs/feature_label_foundation/LABEL_CONTRACTS.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.labels.version"
python tools/verify.py --smoke
python -m pytest tests/unit/labels -q
test -f docs/feature_label_foundation/LABEL_CONTRACTS.md
git ls-files runs
```

### Artifact Policy
Commit only: label contract objects, LabelVersion, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* LabelVersion + label contract family exist and bind to governance LabelSpec (lspec_).
* label_available_ts is required; future-data use is legal only for labels.
* Existing labels/*.py core and governance modules untouched.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P16.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P17 — Fixed-Horizon and Midprice Forward Labels

### Phase ID
`FLF-P17`

### Phase Name
Fixed-Horizon and Midprice Forward Labels

### Lane
YELLOW

### Dependencies
`FLF-P16`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `label_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/labels/families/fixed_horizon/**`
  * `tests/unit/labels/families/fixed_horizon/**`
  * `docs/feature_label_foundation/labels/fixed_horizon.md`
  * `configs/labels/families/fixed_horizon/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P17.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P17/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement fixed-horizon forward-return labels (trade-price and midprice based) with explicit label_available_ts at horizon end.

### Scope
* Implement the Fixed-Horizon and Midprice Forward Labels under src/alpha_system/labels/families/fixed_horizon/ as additive modules only.
* Each label binds to a governance LabelSpec, carries label_available_ts, and never becomes a live feature.
* Cover at least: fwd_ret_1m / 3m / 5m / 10m / 30m, mid_fwd_ret_1m / 3m / 5m / 10m / 30m.
* Document the family in docs/feature_label_foundation/labels/fixed_horizon.md.

### Non-Goals
* Do not edit shared labels/*.py core (spec, contracts, generation, store, path_metrics, version, engine, registry).
* Do not edit any other label family, any feature module, or governance.
* Do not materialize values to disk; provide definitions + unit-tested logic on synthetic fixtures.
* Do not expose label values as features.

### Expected Files / Directories
* `src/alpha_system/labels/families/fixed_horizon/**`
* `tests/unit/labels/families/fixed_horizon/**`
* `docs/feature_label_foundation/labels/fixed_horizon.md`
* `configs/labels/families/fixed_horizon/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.labels.families.fixed_horizon"
python tools/verify.py --smoke
python -m pytest tests/unit/labels/families/fixed_horizon -q
test -f docs/feature_label_foundation/labels/fixed_horizon.md
git ls-files runs
```

### Artifact Policy
Commit only: Fixed-Horizon and Midprice Forward Labels (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The Fixed-Horizon and Midprice Forward Labels are implemented additively under families/fixed_horizon/ with label_available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No label-as-feature, no materialization, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P17.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P18 — Cost-Adjusted / Spread-Adjusted Labels

### Phase ID
`FLF-P18`

### Phase Name
Cost-Adjusted / Spread-Adjusted Labels

### Lane
YELLOW

### Dependencies
`FLF-P16`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `label_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/labels/families/cost_adjusted/**`
  * `tests/unit/labels/families/cost_adjusted/**`
  * `docs/feature_label_foundation/labels/cost_adjusted.md`
  * `configs/labels/families/cost_adjusted/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P18.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P18/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement cost-adjusted and spread-adjusted forward-return labels using BBO spread/mid so that label targets reflect realistic frictions; cost assumptions are explicit and auditable.

### Scope
* Implement the Cost-Adjusted / Spread-Adjusted Labels under src/alpha_system/labels/families/cost_adjusted/ as additive modules only.
* Each label binds to a governance LabelSpec, carries label_available_ts, and never becomes a live feature.
* Cover at least: cost_adjusted_fwd_ret, spread_adjusted_fwd_ret (parameterized by BBO spread and a documented cost model).
* Document the family in docs/feature_label_foundation/labels/cost_adjusted.md.

### Non-Goals
* Do not edit shared labels/*.py core (spec, contracts, generation, store, path_metrics, version, engine, registry).
* Do not edit any other label family, any feature module, or governance.
* Do not materialize values to disk; provide definitions + unit-tested logic on synthetic fixtures.
* Do not expose label values as features.

### Expected Files / Directories
* `src/alpha_system/labels/families/cost_adjusted/**`
* `tests/unit/labels/families/cost_adjusted/**`
* `docs/feature_label_foundation/labels/cost_adjusted.md`
* `configs/labels/families/cost_adjusted/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.labels.families.cost_adjusted"
python tools/verify.py --smoke
python -m pytest tests/unit/labels/families/cost_adjusted -q
test -f docs/feature_label_foundation/labels/cost_adjusted.md
git ls-files runs
```

### Artifact Policy
Commit only: Cost-Adjusted / Spread-Adjusted Labels (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The Cost-Adjusted / Spread-Adjusted Labels are implemented additively under families/cost_adjusted/ with label_available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No label-as-feature, no materialization, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P18.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P19 — Path Labels: MFE / MAE / Triple Barrier

### Phase ID
`FLF-P19`

### Phase Name
Path Labels: MFE / MAE / Triple Barrier

### Lane
YELLOW

### Dependencies
`FLF-P16`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `label_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/labels/families/path/**`
  * `tests/unit/labels/families/path/**`
  * `docs/feature_label_foundation/labels/path.md`
  * `configs/labels/families/path/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P19.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P19/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement path-dependent labels (maximum favorable/adverse excursion, target-before-stop, triple-barrier) with explicit barrier specs and availability at barrier resolution time.

### Scope
* Implement the Path Labels: MFE / MAE / Triple Barrier under src/alpha_system/labels/families/path/ as additive modules only.
* Each label binds to a governance LabelSpec, carries label_available_ts, and never becomes a live feature.
* Cover at least: MFE, MAE, target_before_stop, triple_barrier.
* Document the family in docs/feature_label_foundation/labels/path.md.

### Non-Goals
* Do not edit shared labels/*.py core (spec, contracts, generation, store, path_metrics, version, engine, registry).
* Do not edit any other label family, any feature module, or governance.
* Do not materialize values to disk; provide definitions + unit-tested logic on synthetic fixtures.
* Do not expose label values as features.

### Expected Files / Directories
* `src/alpha_system/labels/families/path/**`
* `tests/unit/labels/families/path/**`
* `docs/feature_label_foundation/labels/path.md`
* `configs/labels/families/path/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.labels.families.path"
python tools/verify.py --smoke
python -m pytest tests/unit/labels/families/path -q
test -f docs/feature_label_foundation/labels/path.md
git ls-files runs
```

### Artifact Policy
Commit only: Path Labels: MFE / MAE / Triple Barrier (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The Path Labels: MFE / MAE / Triple Barrier are implemented additively under families/path/ with label_available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No label-as-feature, no materialization, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P19.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P20 — Strategy-Agnostic Event Labels

### Phase ID
`FLF-P20`

### Phase Name
Strategy-Agnostic Event Labels

### Lane
YELLOW

### Dependencies
`FLF-P16`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `label_families`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/labels/families/event/**`
  * `tests/unit/labels/families/event/**`
  * `docs/feature_label_foundation/labels/event.md`
  * `configs/labels/families/event/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P20.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P20/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Implement strategy-agnostic event-outcome labels (breakout/VWAP/sweep outcomes) as neutral outcome descriptors, not promoted strategy signals.

### Scope
* Implement the Strategy-Agnostic Event Labels under src/alpha_system/labels/families/event/ as additive modules only.
* Each label binds to a governance LabelSpec, carries label_available_ts, and never becomes a live feature.
* Cover at least: breakout_success, return_to_vwap, sweep outcome, liquidity_quality_future label (where appropriate).
* Document the family in docs/feature_label_foundation/labels/event.md.

### Non-Goals
* Do not edit shared labels/*.py core (spec, contracts, generation, store, path_metrics, version, engine, registry).
* Do not edit any other label family, any feature module, or governance.
* Do not materialize values to disk; provide definitions + unit-tested logic on synthetic fixtures.
* Do not expose label values as features.

### Expected Files / Directories
* `src/alpha_system/labels/families/event/**`
* `tests/unit/labels/families/event/**`
* `docs/feature_label_foundation/labels/event.md`
* `configs/labels/families/event/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.labels.families.event"
python tools/verify.py --smoke
python -m pytest tests/unit/labels/families/event -q
test -f docs/feature_label_foundation/labels/event.md
git ls-files runs
```

### Artifact Policy
Commit only: Strategy-Agnostic Event Labels (additive), tests on synthetic fixtures, docs, configs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The Strategy-Agnostic Event Labels are implemented additively under families/event/ with label_available_ts on every value.
* Unit tests on synthetic fixtures pass; no shared-core or cross-family edits.
* No label-as-feature, no materialization, no alpha/tradability claims.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P20.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P21 — Label Materialization Engine

### Phase ID
`FLF-P21`

### Phase Name
Label Materialization Engine

### Lane
YELLOW

### Dependencies
`FLF-P17`, `FLF-P18`, `FLF-P19`, `FLF-P20`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `label_integration`
* `conflicts_with`: none
* `resource_class`: `materialization_engine`
* `allowed_paths`:
  * `src/alpha_system/labels/engine.py`
  * `tests/unit/labels/test_label_engine.py`
  * `tests/integration/labels/**`
  * `docs/feature_label_foundation/LABEL_MATERIALIZATION.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P21.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P21/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Build the LabelMaterializationPlan + engine that turns an approved LabelSpec into LabelValueRecords for an accepted DatasetVersion + partition — local-only, deterministic, leakage-safe. Label values are never committed and never exposed as features.

### Scope
* Create src/alpha_system/labels/engine.py implementing label materialization over consumption views.
* Enforce label_available_ts propagation and partition/locked-test gating; outputs only under $ALPHA_DATA_ROOT.
* Provide a dry-run planning mode.
* Document the engine in docs/feature_label_foundation/LABEL_MATERIALIZATION.md.

### Non-Goals
* No committed label values.
* No label-as-feature.
* No external provider calls.

### Expected Files / Directories
* `src/alpha_system/labels/engine.py`
* `tests/unit/labels/test_label_engine.py`
* `tests/integration/labels/test_label_materialize.py`
* `docs/feature_label_foundation/LABEL_MATERIALIZATION.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.labels.engine"
python tools/verify.py --smoke
python -m pytest tests/unit/labels tests/integration/labels -q
test -f docs/feature_label_foundation/LABEL_MATERIALIZATION.md
git ls-files runs
```

### Artifact Policy
Commit only: label materialization engine, tests on synthetic fixtures, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The engine materializes LabelValueRecords deterministically with label_available_ts, local-only.
* Dry-run planning works; locked-test gating enforced; no committed values.
* No label-as-feature, no external call.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P21.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P22 — LabelStore / LabelRegistry Integration

### Phase ID
`FLF-P22`

### Phase Name
LabelStore / LabelRegistry Integration

### Lane
YELLOW

### Dependencies
`FLF-P21`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `label_integration`
* `conflicts_with`: none
* `resource_class`: `label_registry`
* `allowed_paths`:
  * `src/alpha_system/labels/registry.py`
  * `tests/unit/labels/test_label_store.py`
  * `tests/integration/labels/**`
  * `docs/feature_label_foundation/LABEL_STORE.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P22.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P22/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Integrate a LabelStore + LabelRegistry (LabelRegistryRecord, LabelLineageRecord) so materialized labels are versioned and lineage-tracked, with the registry DB local-only and never committed.

### Scope
* Create src/alpha_system/labels/registry.py (and extend labels/store.py usage read-only or additively) for label versioning + lineage.
* Persist LabelRegistryRecord to a local-only registry under $ALPHA_DATA_ROOT.
* Document the store/registry in docs/feature_label_foundation/LABEL_STORE.md.

### Non-Goals
* No committed registry DB.
* No label-as-feature.
* No alpha search.

### Expected Files / Directories
* `src/alpha_system/labels/registry.py`
* `tests/unit/labels/test_label_store.py`
* `tests/integration/labels/test_label_registry_tempdb.py`
* `docs/feature_label_foundation/LABEL_STORE.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.labels.registry"
python tools/verify.py --smoke
python -m pytest tests/unit/labels tests/integration/labels -q
test -f docs/feature_label_foundation/LABEL_STORE.md
git ls-files runs
```

### Artifact Policy
Commit only: LabelStore/registry code, tests against temp DB, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Labels are versioned + lineage-tracked in a local-only registry, never committed.
* Tests run against a temp DB with no real data.
* No label-as-feature, no alpha search.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P22.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P23 — Label Leakage and Availability Audits

### Phase ID
`FLF-P23`

### Phase Name
Label Leakage and Availability Audits

### Lane
YELLOW

### Dependencies
`FLF-P22`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `label_integration`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/labels/leakage_audit.py`
  * `tests/no_lookahead/feature_label/test_label_leakage_guard.py`
  * `tests/no_lookahead/feature_label/test_label_available_ts.py`
  * `docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P23.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P23/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Build LabelLeakageAuditReport + availability audits that prove no label leaks into features and that every label respects label_available_ts. Consumes the existing governance label-leakage guard (read-only).

### Scope
* Create src/alpha_system/labels/leakage_audit.py producing LabelLeakageAuditReport via the governance label_leakage_guard (label_as_feature + availability_time checks).
* Audit forbidden_feature_overlap and availability ordering for every registered label.
* Document the audits in docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md.

### Non-Goals
* Do not edit the governance leakage guard (consume it).
* No label-as-feature path.

### Expected Files / Directories
* `src/alpha_system/labels/leakage_audit.py`
* `tests/no_lookahead/feature_label/test_label_leakage_guard.py`
* `tests/no_lookahead/feature_label/test_label_available_ts.py`
* `docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.labels.leakage_audit"
python tools/verify.py --smoke
python -m pytest tests/no_lookahead/feature_label -q
test -f docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md
git ls-files runs
```

### Artifact Policy
Commit only: label leakage/availability audit, no-lookahead tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Leakage audits prove no label-as-feature and correct label_available_ts for every label.
* Governance leakage guard is consumed, not re-implemented.
* Fail-closed tests pass.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P23.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P24 — Feature/Label Diagnostics Reports

### Phase ID
`FLF-P24`

### Phase Name
Feature/Label Diagnostics Reports

### Lane
YELLOW

### Dependencies
`FLF-P15`, `FLF-P23`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `diagnostics_and_packaging`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/research/feature_label_diagnostics.py`
  * `tests/unit/research/test_feature_label_diagnostics.py`
  * `docs/feature_label_foundation/diagnostics.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P24.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P24/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Produce strategy-agnostic Feature/Label diagnostics (alignment, coverage overlap, feature-label availability consistency) as a NEW module that does not edit the shared research/diagnostics.py. Diagnostics are descriptive, never alpha/IC promotion.

### Scope
* Create src/alpha_system/research/feature_label_diagnostics.py (new, additive).
* Report feature/label availability alignment, coverage overlap, and missingness exposure; clearly non-promotional.
* Document the diagnostics in docs/feature_label_foundation/diagnostics.md.

### Non-Goals
* Do not edit research/diagnostics.py.
* No IC/alpha ranking or promotion.
* No tradability claims.

### Expected Files / Directories
* `src/alpha_system/research/feature_label_diagnostics.py`
* `tests/unit/research/test_feature_label_diagnostics.py`
* `docs/feature_label_foundation/diagnostics.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.research.feature_label_diagnostics"
python tools/verify.py --smoke
python -m pytest tests/unit/research/test_feature_label_diagnostics.py -q
test -f docs/feature_label_foundation/diagnostics.md
git ls-files runs
```

### Artifact Policy
Commit only: feature/label diagnostics module, tests, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Diagnostics report feature/label alignment + coverage descriptively, never as alpha promotion.
* Shared research/diagnostics.py untouched.
* Tests pass on synthetic fixtures.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P24.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P25 — Synthetic Fixtures and Fail-Closed Tests

### Phase ID
`FLF-P25`

### Phase Name
Synthetic Fixtures and Fail-Closed Tests

### Lane
YELLOW

### Dependencies
`FLF-P15`, `FLF-P23`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `diagnostics_and_packaging`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `tests/fixtures/feature_label/**`
  * `tests/no_lookahead/feature_label/**`
  * `configs/features/examples/**`
  * `configs/labels/examples/**`
  * `docs/feature_label_foundation/fixtures.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P25.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P25/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Add tiny synthetic fixtures and the cross-cutting fail-closed test suite for the Feature/Label layer: no FeatureRequest -> blocked, no FeatureSpec -> blocked, no LabelSpec -> blocked, missing available_ts -> blocked, label-as-feature -> blocked, raw-provider access -> blocked, locked-test without metadata -> blocked.

### Scope
* Create tiny synthetic deterministic fixtures under tests/fixtures/feature_label/ (no real market data).
* Add fail-closed tests under tests/no_lookahead/feature_label/ covering the prohibited shortcuts.
* Add example configs under configs/features/examples/ and configs/labels/examples/.
* Document fixtures in docs/feature_label_foundation/fixtures.md.

### Non-Goals
* No real market data fixtures.
* No happy-path-only coverage.
* No materialization.

### Expected Files / Directories
* `tests/fixtures/feature_label/**`
* `tests/no_lookahead/feature_label/**`
* `configs/features/examples/**`
* `configs/labels/examples/**`
* `docs/feature_label_foundation/fixtures.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/no_lookahead/feature_label -q
test -f docs/feature_label_foundation/fixtures.md
git ls-files runs
```

### Artifact Policy
Commit only: tiny synthetic fixtures, fail-closed tests, example configs, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Fail-closed tests cover every prohibited shortcut and pass.
* Fixtures are tiny, synthetic, deterministic, documented, and not real market data.
* No happy-path-only coverage.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P25.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P26 — Small Real Databento DatasetVersion Dry Run

### Phase ID
`FLF-P26`

### Phase Name
Small Real Databento DatasetVersion Dry Run

### Lane
YELLOW

### Dependencies
`FLF-P25`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `diagnostics_and_packaging`
* `conflicts_with`: none
* `resource_class`: `local_dataset_registry`
* `allowed_paths`:
  * `docs/feature_label_foundation/DRY_RUN_DATABENTO.md`
  * `tests/integration/feature_label/**`
  * `src/alpha_system/features/engine/**`
  * `src/alpha_system/labels/engine.py`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P26.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P26/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Run a small, local-only dry run that materializes a handful of features and labels from an ACCEPTED Databento DatasetVersion (e.g. a single dev-partition slice) to prove end-to-end consumption works — with NO external provider call and NO committed values.

### Scope
* Drive the feature + label engines over one accepted Databento DatasetVersion slice using resolve_dataset_version (local registry).
* Produce a curated, row-free summary (counts, coverage, quality status) — no raw rows, no values committed.
* Record the dry run in docs/feature_label_foundation/DRY_RUN_DATABENTO.md and the handoff.

### Non-Goals
* No external Databento/IBKR call.
* No committed feature/label values.
* No alpha search.

### Expected Files / Directories
* `docs/feature_label_foundation/DRY_RUN_DATABENTO.md`
* `tests/integration/feature_label/test_small_databento_dryrun.py`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/integration/feature_label -q
test -f docs/feature_label_foundation/DRY_RUN_DATABENTO.md
git ls-files runs
```

### Artifact Policy
Commit only: curated row-free dry-run summary, integration test (CI-safe, no real data), docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* A local-only dry run materializes a small feature+label set from an accepted DatasetVersion.
* Only a curated, row-free summary is committed; no values, no raw rows, no external call.
* PASS_WITH_WARNINGS acceptable if the local registry/data is absent on the runner, with the exact operator command documented.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P26.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P27 — Governance Integration: StudySpec Input Packs

### Phase ID
`FLF-P27`

### Phase Name
Governance Integration: StudySpec Input Packs

### Lane
YELLOW

### Dependencies
`FLF-P15`, `FLF-P23`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `diagnostics_and_packaging`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/governance/study_input_pack.py`
  * `tests/unit/governance/test_study_input_pack.py`
  * `configs/governance/feature_label_pack/**`
  * `docs/feature_label_foundation/governance_integration.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P27.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P27/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Produce a StudySpec Input Pack: a NEW additive governance helper that bundles the FeatureRequest (freq_) + LabelSpec (lspec_) handles a study consumes, so the existing StudySpec can reference them. Does NOT modify the StudySpec schema or existing governance modules (R-022).

### Scope
* Create src/alpha_system/governance/study_input_pack.py (new, additive) assembling freq_/lspec_/aspec_ id handles + dataset_scope for a StudySpec.
* Validate the pack against the existing StudySpec/LabelSpec/FeatureRequest contracts (consume, do not edit).
* Document the integration in docs/feature_label_foundation/governance_integration.md.

### Non-Goals
* Do not edit governance/study_spec.py, label_spec.py, feature_request.py, or duplicate_exposure.py.
* Do not add a parallel study/experiment spec.

### Expected Files / Directories
* `src/alpha_system/governance/study_input_pack.py`
* `tests/unit/governance/test_study_input_pack.py`
* `configs/governance/feature_label_pack/**`
* `docs/feature_label_foundation/governance_integration.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.governance.study_input_pack"
python tools/verify.py --smoke
python -m pytest tests/unit/governance/test_study_input_pack.py -q
test -f docs/feature_label_foundation/governance_integration.md
git ls-files runs
```

### Artifact Policy
Commit only: StudySpec input-pack helper (new, additive), tests, configs, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* A StudySpec Input Pack bundles freq_/lspec_/aspec_ handles + dataset_scope and validates against existing governance contracts.
* No existing governance module is edited; no parallel study spec introduced.
* Tests pass.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P27.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P28 — CLI / Tooling Surface

### Phase ID
`FLF-P28`

### Phase Name
CLI / Tooling Surface

### Lane
YELLOW

### Dependencies
`FLF-P15`, `FLF-P23`, `FLF-P27`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `diagnostics_and_packaging`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `src/alpha_system/cli/feature.py`
  * `src/alpha_system/cli/label.py`
  * `src/alpha_system/cli/main.py`
  * `tests/unit/cli/test_feature_cli.py`
  * `tests/unit/cli/test_label_cli.py`
  * `docs/CLI_REFERENCE.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P28.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P28/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Expose a thin, local-only CLI surface for the Feature/Label layer (plan/list/materialize-dry-run/report) wired into the existing cli/main.py subparser registry. Edits the shared cli/main.py, so it runs alone.

### Scope
* Create src/alpha_system/cli/feature.py and src/alpha_system/cli/label.py and register them in cli/main.py.
* Commands are local-only, read accepted DatasetVersions, and never call external providers; default to dry-run/report.
* Append a Feature/Label section to docs/CLI_REFERENCE.md.

### Non-Goals
* No external provider calls from the CLI.
* No order/account/broker commands.
* No alpha search command.

### Expected Files / Directories
* `src/alpha_system/cli/feature.py`
* `src/alpha_system/cli/label.py`
* `tests/unit/cli/test_feature_cli.py`
* `tests/unit/cli/test_label_cli.py`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python -c "import alpha_system.cli.main"
python tools/verify.py --smoke
python -m pytest tests/unit/cli/test_feature_cli.py tests/unit/cli/test_label_cli.py -q
git ls-files runs
```

### Artifact Policy
Commit only: feature/label CLI, cli/main.py wiring, tests, CLI_REFERENCE update. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* Feature/Label CLI commands exist (plan/list/dry-run/report), local-only and CI-safe.
* No external provider, broker, or alpha-search command introduced.
* CLI reference updated; tests pass.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P28.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P29 — Docs, Templates, and Agent Guide

### Phase ID
`FLF-P29`

### Phase Name
Docs, Templates, and Agent Guide

### Lane
GREEN

### Dependencies
`FLF-P15`, `FLF-P23`

### DAG Scheduling
* `parallel_safe`: true
* `must_run_alone`: false
* `merge_group`: `diagnostics_and_packaging`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `docs/feature_label_foundation/guide/**`
  * `docs/feature_label_foundation/AGENT_GUIDE.md`
  * `docs/feature_label_foundation/templates/**`
  * `templates/feature_label/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P29.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P29/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, shared feature/label core, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Author the durable Feature/Label Foundation guide + templates an AI Alpha Researcher consumes — kept in a disjoint docs subtree so it can be authored in parallel. Strategy-agnostic, no alpha claims.

### Scope
* Create docs/feature_label_foundation/guide/** (researcher guide + how-to), docs/feature_label_foundation/AGENT_GUIDE.md, docs/feature_label_foundation/templates/**.
* Provide FeatureRequest/FeatureSpec/LabelSpec request templates under templates/feature_label/.
* Cross-reference the entry contract, governance objects, and DatasetVersion consumption path.

### Non-Goals
* No alpha/tradability/profitability claims.
* No edits to shared root docs (closeout handles cross-refs).

### Expected Files / Directories
* `docs/feature_label_foundation/guide/**`
* `docs/feature_label_foundation/AGENT_GUIDE.md`
* `docs/feature_label_foundation/templates/**`
* `templates/feature_label/**`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No edits to shared feature/label core or other families (additive-only, disjoint allowed_paths).

### Validation Commands
```bash
git status --short
test -f docs/feature_label_foundation/AGENT_GUIDE.md
python tools/verify.py --smoke
git ls-files runs
```

### Artifact Policy
Commit only: researcher/agent guide, templates, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* A durable Feature/Label researcher + agent guide and request templates exist in a disjoint docs subtree.
* Docs are strategy-agnostic with no alpha/tradability claims.
* No source/test edits; shared root docs untouched.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P29.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Optional (GREEN docs/mechanical lane). Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P30 — End-to-End Feature/Label Dry Run

### Phase ID
`FLF-P30`

### Phase Name
End-to-End Feature/Label Dry Run

### Lane
YELLOW

### Dependencies
`FLF-P26`, `FLF-P28`, `FLF-P29`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `closeout`
* `conflicts_with`: none
* `resource_class`: `local_dataset_registry`
* `allowed_paths`:
  * `docs/feature_label_foundation/E2E_DRY_RUN.md`
  * `tests/integration/feature_label/**`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P30.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P30/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Run the full Feature/Label substrate end-to-end on a small accepted DatasetVersion slice via the CLI: FeatureRequest -> FeatureSpec -> materialize (dry/local) -> reports -> LabelSpec -> materialize (dry/local) -> leakage audit -> StudySpec Input Pack. Local-only, no committed values, no external call.

### Scope
* Exercise the CLI/engines over one accepted DatasetVersion slice end to end, local-only.
* Verify lifecycle states, available_ts/label_available_ts, leakage audit pass, and a valid StudySpec Input Pack.
* Produce a curated, row-free end-to-end summary in docs/feature_label_foundation/E2E_DRY_RUN.md.

### Non-Goals
* No external provider call.
* No committed values.
* No alpha/tradability claim.

### Expected Files / Directories
* `docs/feature_label_foundation/E2E_DRY_RUN.md`
* `tests/integration/feature_label/test_e2e_dryrun.py`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/integration/feature_label -q
test -f docs/feature_label_foundation/E2E_DRY_RUN.md
git ls-files runs
```

### Artifact Policy
Commit only: curated row-free end-to-end summary, CI-safe integration test, docs. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* The full Feature/Label pipeline runs end-to-end on an accepted DatasetVersion slice, local-only.
* Lifecycle, availability, leakage audit, and StudySpec Input Pack all validate.
* Only a curated, row-free summary is committed; PASS_WITH_WARNINGS acceptable with a documented operator command if local data is absent on the runner.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P30.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---
## FLF-P31 — Workflow 2 Acceptance Audit and Closeout

### Phase ID
`FLF-P31`

### Phase Name
Workflow 2 Acceptance Audit and Closeout

### Lane
YELLOW

### Dependencies
`FLF-P30`

### DAG Scheduling
* `parallel_safe`: false
* `must_run_alone`: true
* `merge_group`: `closeout`
* `conflicts_with`: none
* `resource_class`: none
* `allowed_paths`:
  * `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md`
  * `docs/feature_label_foundation/CLOSEOUT_NOTES.md`
  * `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P31.md`
  * `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P31/**`
  * `runs/**`
* `forbidden_paths`: broker/live/paper/order scope, raw/canonical/value data, heavy artifacts, local DBs, and the per-phase exclusions listed in `campaign.yaml`.

### Purpose
Final acceptance audit + closeout: verify every acceptance gate, run the semantic done-check, reconcile docs/status, record the final verdict and the readiness note for ALPHA_AGENT_FACTORY_MVP / ALPHA_FUTURES_CORE_ALPHA_PILOT_V1. The ACTIVE_CAMPAIGN.md pointer is updated by the coordinator, not this phase branch.

### Scope
* Audit all acceptance gates and confirm coverage of all 32 phases.
* Run the semantic done-check and the artifact audit; reconcile PROJECT_STATUS/PROGRESS references via the closeout doc.
* Write campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md with the final verdict and next-campaign readiness.

### Non-Goals
* Do not write ACTIVE_CAMPAIGN.md (coordinator-only).
* No alpha/tradability/profitability claims.
* No new feature/label scope.

### Expected Files / Directories
* `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md`
* `docs/feature_label_foundation/CLOSEOUT_NOTES.md`

### Forbidden Changes
* No broker/live/paper/order-routing/account scope.
* No external Databento/IBKR provider calls; no raw provider data access from feature/label code.
* No committed feature/label values, raw/canonical data, heavy artifacts, or local DB files.
* No alpha/profitability/tradability claims; no strategy/backtest/portfolio scope.
* No writes to ACTIVE_CAMPAIGN.md (coordinator-only in dag_wave mode).

### Validation Commands
```bash
git status --short
python tools/verify.py --all
python tools/hooks/canary_runner.py
test -f campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md
git ls-files runs
```

### Artifact Policy
Commit only: closeout doc with final verdict, closeout notes. Never commit: runs/**, raw/canonical market data, provider
responses, materialized feature/label values, heavy artifacts (parquet/arrow/feather), or local DB/registry
files. Explicit staging only.

### Done Criteria
* All acceptance gates verified; semantic done-check passes or a truthful BLOCKED is recorded.
* CLOSEOUT.md records the final verdict (COMPLETE / COMPLETE_WITH_WARNINGS / BLOCKED) and next-campaign readiness.
* No alpha/tradability claims; no new scope; ACTIVE_CAMPAIGN.md left to the coordinator.

### Handoff Requirements
`handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P31.md` must summarize the change, exact staged files, validation results,
artifact-policy confirmation, explicit-staging confirmation, DAG-metadata confirmation (disjoint paths for
parallel phases), and statements that no forbidden scope/claims/data were added.

### Review Requirements
Claude Opus review required. Must verify scope compliance, no raw-provider access, accepted-DatasetVersion-only consumption,
available_ts / label_available_ts presence, no label-as-feature, BBO/no-trade flagging, DAG-metadata
correctness, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph through the **serial merge queue** only when checks pass, handoff validates,
verdict is `PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden
paths are staged, no STOP file, CI passes if configured, and the semantic done-check passes. Parallel-safe
phases build concurrently in isolated worktrees but always merge one at a time.

---

## Campaign-Wide Done Criteria

* All 32 phases (`FLF-P00` … `FLF-P31`) complete with passing reviews and clean gates.
* The FeatureStore and LabelStore substrate is versioned, no-lookahead-safe, deduplicated, cost-aware, and
  BBO-aware, consuming only accepted DatasetVersions.
* Fail-closed tests cover every prohibited shortcut; the small Databento dry run and the end-to-end dry run
  pass (or record truthful `PASS_WITH_WARNINGS`).
* The StudySpec Input Pack integrates with existing governance without duplicating governance objects.
* `CLOSEOUT.md` records the final verdict and the readiness note for `ALPHA_AGENT_FACTORY_MVP` and
  `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`.

## Scope Boundary Reminders

This campaign generates the research substrate. It does **not** implement alpha, run alpha search, build
strategy wrappers, run backtests, allocate a portfolio, call Databento/IBKR APIs, pull data, or commit raw/
canonical/value data. A good diagnostic is not production readiness; an accepted DatasetVersion is not alpha
validated; a materialized FeatureSet is not a promoted candidate.

## Forbidden Path Reminders

`src/alpha_system/execution/broker|live|paper|order_router*`, `src/alpha_system/broker|live`, `data/raw|canonical|
factors|labels|cache`, `metadata/*.sqlite|*.db|*.wal`, `**/*.parquet|*.arrow|*.feather|*.dbn|*.zst`, and
`runs/**` are never staged. The existing governance contract modules
(`governance/study_spec.py`, `feature_request.py`, `label_spec.py`, `duplicate_exposure.py`,
`label_leakage_guard.py`) are **consumed, never edited**.

## Review and Merge Rules

YELLOW phases merge only after a fresh Claude Opus review verdict of `PASS`/`PASS_WITH_WARNINGS`, clean checks,
clean artifact audit, no STOP file, and a passing semantic done-check — through the **serial merge queue**.
Parallel-safe phases build concurrently in isolated worktrees but never merge concurrently.
