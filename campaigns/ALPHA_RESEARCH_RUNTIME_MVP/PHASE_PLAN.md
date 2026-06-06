# ALPHA_RESEARCH_RUNTIME_MVP Phase Plan

## Purpose

This phase plan is the human-readable contract for `ALPHA_RESEARCH_RUNTIME_MVP`, the
**executable research loop layer** between the Feature/Label substrate and the future
Agent Factory. It turns an approved `AlphaSpec` + `StudySpec` into reproducible
diagnostics, cost stress, bounded probes, an `EvidenceDraft`, rejection reasons, and a
`ReferenceCandidateHandoff` — by **orchestrating existing primitives**
(`alpha_system.research.*`, `alpha_system.backtest.costs/slippage`,
`alpha_system.experiments.limits/overfit_controls`,
`alpha_system.governance.study_input_pack/evidence_bundle`), never re-implementing them.
It does **not** conduct broad alpha search, promote factors, validate strategies, or make
any alpha/tradability/profitability claim. Every structured field below is derived from
`campaign.yaml`; the two files must agree.

## Campaign Invariants

- No `AlphaSpec` / `StudySpec` → no runtime run.
- No accepted DatasetVersion → no runtime execution; raw provider access is forbidden; no external provider calls.
- Feature inputs carry `available_ts`; label inputs carry `label_available_ts`; no label-as-feature.
- Cost stress (including a `double_cost` profile) is required for any signal probe or handoff; slippage is labeled a proxy; zero-cost is never a promotion basis.
- Bounded grids only — a `VariantBudget` is required; no unbounded grid; no selection on the locked test without contamination metadata.
- Failed and inconclusive runs stay visible via `RejectionReasonRecord`.
- A diagnostic PASS is not alpha validation; a signal probe is not a strategy candidate; a bounded grid is not promotion; an `EvidenceDraft` is not a candidate; a `ReferenceCandidateHandoff` is not Reference validation; the fast path is not Reference truth.
- Runtime **orchestrates** existing research/experiments/governance/backtest primitives and never duplicates them.
- Local-only and deterministic; no broker/live/paper/order/account scope; no committed raw/canonical/feature/label/runtime values, heavy artifacts, or local DBs.

## Global Phase Rules

### Workflow Rules

- Workflow 2 strict order: `RUN_INIT → CAMPAIGN_LOAD → PHASE_SELECT → SPEC_GENERATE → SPEC_VALIDATE → WORKTREE_CREATE → CODEX_EXECUTE → CHECKS_RUN → HANDOFF_VALIDATE → CLAUDE_REVIEW → VERDICT_PARSE → PR_CREATE → CI_WAIT → MERGE_GATE → MERGE → DONE_CHECK → NEXT_PHASE → CAMPAIGN_DONE_CHECK → RUN_SUMMARY`.
- Each phase requires a spec, runs its checks, writes a handoff, and (YELLOW) a fresh Claude review with `verdict.json`.

### DAG Wave Scheduler Rules

- `mode: dag_wave`, `parallel_execution: true`, `max_parallel_phases: 3`, `merge_queue: serial`, `update_active_campaign: coordinator_only`.
- A phase is parallel-safe **only** if it sets `parallel_safe: true`, declares disjoint `allowed_paths`, sets `must_run_alone: false`, declares no global/coordinator file, and is not RED. Otherwise it runs alone.
- Phase branches never write `ACTIVE_CAMPAIGN.md` in parallel mode; the pointer is coordinator-owned.
- Preview with `just frontier-plan ALPHA_RESEARCH_RUNTIME_MVP`; mock with `just frontier-run-parallel-mock ALPHA_RESEARCH_RUNTIME_MVP 3` before the first live parallel run.

### Repo Path Rules

- The active repo and worktrees run under the WSL2 Linux filesystem at `~/projects/alpha_system`; `/mnt/c`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temp dirs are forbidden.

### Git Rules

- Explicit staging only; `git add .` / `git add -A` forbidden; no force push; commit format `<campaign_id>/<phase_id>: <summary>`.

### Artifact Rules

- `runs/**` is local-only and never staged. Never commit raw/canonical/feature/label/runtime values, parquet/arrow/feather/dbn/zst, provider responses, local DBs, logs, caches, or heavy artifacts. Tiny synthetic documented fixtures under `tests/fixtures/**` are the only data-like exception.

### Domain Boundary Rules

- Runtime consumes `research.*`, `experiments.*`, `governance.*`, `backtest.costs/slippage`, `features.*`, `labels.*`, and `data.foundation.*`; it must not edit those packages (they are in each phase's `forbidden_paths`). No broker/live/paper/order/account scope; no alpha search; no factor/strategy promotion.

### Review Rules

- YELLOW phases require a fresh Claude Opus 4.8 xhigh review and a `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} to merge. The implementer cannot self-approve.

### Repair Rules

- Bounded repair, max 2 attempts; repair attempts recorded under `runs/<run_id>/phases/<phase_id>/repair_attempts/`; fake completion forbidden.

### Validation Rules

- Run the narrowest meaningful check first, broaden when shared behavior changes, and record skipped checks with the reason. Default commands: `python tools/verify.py --smoke` / `--all`, `python tools/hooks/canary_runner.py`.

## Phase Table Summary

| Phase | Name | Lane | Deps | Parallel-safe | Merge group |
| --- | --- | --- | --- | --- | --- |
| `RT-P00` | Research Runtime Campaign Bootstrap | GREEN | — | false | bootstrap |
| `RT-P01` | Runtime Entry Contract After Feature/Label | YELLOW | RT-P00 | false | foundation |
| `RT-P02` | Runtime Package Skeleton and Naming | YELLOW | RT-P01 | false | foundation |
| `RT-P03` | Runtime Input Resolver: DatasetVersion and Feature/Label Packs | YELLOW | RT-P02 | false | foundation |
| `RT-P04` | StudyRunSpec and RuntimePlan Contracts | YELLOW | RT-P03 | false | foundation |
| `RT-P05` | StudyRunRecord, Manifest, and Runtime Artifact Contract | YELLOW | RT-P04 | false | foundation |
| `RT-P06` | Diagnostics Report Contracts | YELLOW | RT-P05 | false | foundation |
| `RT-P07` | Factor Diagnostics Runtime | YELLOW | RT-P06 | true | diagnostics |
| `RT-P08` | Label Diagnostics Runtime | YELLOW | RT-P06 | true | diagnostics |
| `RT-P09` | Session / Regime / RTH / ETH Split Diagnostics | YELLOW | RT-P06 | true | diagnostics |
| `RT-P10` | Cross-Market Diagnostics Runtime | YELLOW | RT-P06 | true | diagnostics |
| `RT-P11` | CostModelVersion and Cost Stress Runtime | YELLOW | RT-P06 | true | diagnostics |
| `RT-P12` | Simple Signal Probe Runtime | YELLOW | RT-P07, RT-P08, RT-P11 | false | integration |
| `RT-P13` | Bounded Grid / Variant Budget Guard | YELLOW | RT-P12 | false | integration |
| `RT-P14` | No-Lookahead Runtime Audit | YELLOW | RT-P12 | false | integration |
| `RT-P15` | RejectionReasonRecord and Runtime Decision States | YELLOW | RT-P13, RT-P14 | false | integration |
| `RT-P16` | EvidenceBundle Draft Builder | YELLOW | RT-P15 | false | integration |
| `RT-P17` | Reference Candidate Handoff Builder | YELLOW | RT-P16 | false | integration |
| `RT-P18` | Runtime CLI / Tool Surface | YELLOW | RT-P17 | false | integration |
| `RT-P19` | Runtime Cache and Local Artifact Policy | YELLOW | RT-P18 | false | integration |
| `RT-P20` | Synthetic Runtime Fixtures and Fail-Closed Tests | YELLOW | RT-P19 | true | tests_tools_docs |
| `RT-P21` | Small Real FLF DatasetVersion Runtime Smoke | YELLOW | RT-P20, RT-P22, RT-P23 | false | closeout |
| `RT-P22` | Agent-Facing Tool Result Contracts | YELLOW | RT-P19 | true | tests_tools_docs |
| `RT-P23` | Runtime Reports, Docs, and Templates | YELLOW | RT-P19 | true | tests_tools_docs |
| `RT-P24` | Workflow 2 DAG Integration and Parallel Plan | YELLOW | RT-P21 | false | closeout |
| `RT-P25` | End-to-End Runtime Dry Run | YELLOW | RT-P24 | false | closeout |
| `RT-P26` | Acceptance Audit and Closeout | YELLOW | RT-P25 | false | closeout |

## Parallel Wave Summary

Waves are computed by the DAG scheduler from dependencies plus DAG metadata; the shape below is the intended plan (`just frontier-plan` previews exact waves):

- **Wave 0 — sequential bootstrap + contracts (run-alone):** RT-P00 → RT-P01 → RT-P02 → RT-P03 → RT-P04 → RT-P05 → RT-P06.
- **Wave 1 — parallel diagnostics (disjoint `allowed_paths`):** RT-P07, RT-P08, RT-P09, RT-P10, RT-P11.
- **Wave 2 — sequential integration (run-alone):** RT-P12 → RT-P13 → RT-P14 → RT-P15 → RT-P16 → RT-P17 → RT-P18 → RT-P19.
- **Wave 3 — parallel tests / contracts / docs (disjoint `allowed_paths`):** RT-P20, RT-P22, RT-P23.
- **Wave 4 — sequential closeout (run-alone):** RT-P21 → RT-P24 → RT-P25 → RT-P26.

## Acceptance Gate Summary

Each of the 27 phases belongs to exactly one acceptance gate:

| Gate | Phases |
| --- | --- |
| `campaign_bootstrap` | RT-P00, RT-P01, RT-P02 |
| `runtime_contracts` | RT-P03, RT-P04, RT-P05, RT-P06 |
| `diagnostics_runtime` | RT-P07, RT-P08, RT-P09, RT-P10, RT-P11 |
| `runtime_integration` | RT-P12, RT-P13, RT-P14, RT-P15, RT-P16, RT-P17, RT-P18, RT-P19 |
| `tests_tools_docs` | RT-P20, RT-P21, RT-P22, RT-P23 |
| `workflow_and_closeout` | RT-P24, RT-P25, RT-P26 |

Final verdict ∈ {`COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`}.

# Detailed Phase Specs

## RT-P00 — Research Runtime Campaign Bootstrap

### Phase ID

`RT-P00`

### Phase Name

Research Runtime Campaign Bootstrap

### Lane

GREEN

### Dependencies

None

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `bootstrap`

### Purpose

Lay down the campaign control surface and the research-runtime docs root so Workflow 2 can load and schedule the campaign.

### Scope

- Create the six campaign contract files and the docs/research_runtime README + OVERVIEW.
- Confirm the root ACTIVE_CAMPAIGN.md points to this campaign and no campaign-local pointer exists.

### Non-Goals

- No runtime code.
- No diagnostics.
- No data access.

### Expected Files / Directories

- `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/**`
- `docs/research_runtime/README.md`
- `docs/research_runtime/OVERVIEW.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P00.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P00/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/GOAL.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACCEPTANCE.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RISK_REGISTER.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RUNBOOK.md
test '!' -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACTIVE_CAMPAIGN.md
test -f handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P00.md
grep -q "ALPHA_RESEARCH_RUNTIME_MVP" ACTIVE_CAMPAIGN.md
python tools/verify.py --smoke
git ls-files runs
```

### Artifact Policy

Commit only: campaign control + overview docs; commit-eligible handoff. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- All six campaign files present and campaign.yaml parses.
- No campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACTIVE_CAMPAIGN.md exists.
- Bootstrap handoff present; artifact audit clean.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P00.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

GREEN: Claude review optional unless the phase requires it; checks + handoff + artifact audit still required.

### Auto-Merge Eligibility

Auto-PR + auto-merge when checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P01 — Runtime Entry Contract After Feature/Label

### Phase ID

`RT-P01`

### Phase Name

Runtime Entry Contract After Feature/Label

### Lane

YELLOW

### Dependencies

`RT-P00`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `foundation`

### Purpose

Establish the single sanctioned runtime entry contract: how an approved AlphaSpec/StudySpec plus accepted DatasetVersions and the registered FeatureStore/LabelStore enter the runtime.

### Scope

- Add alpha_system.runtime.entry_contract consuming resolve_dataset_version, StudyInputPack, and the Feature/Label stores.
- Define INPUTS_RESOLVED / INPUTS_BLOCKED / INPUTS_INCONCLUSIVE outcomes before any diagnostics run.

### Non-Goals

- No diagnostics execution.
- No raw provider access.
- No governance re-implementation.

### Expected Files / Directories

- `src/alpha_system/runtime/__init__.py`
- `src/alpha_system/runtime/entry_contract.py`
- `tests/unit/runtime/test_entry_contract.py`
- `docs/research_runtime/ENTRY_CONTRACT.md`
- `configs/runtime/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P01.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P01/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.entry_contract"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime -q
test -f docs/research_runtime/ENTRY_CONTRACT.md
git ls-files runs
```

### Artifact Policy

Commit only: runtime entry contract; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.entry_contract imports.
- Entry contract requires AlphaSpec + StudySpec + accepted DatasetVersion.
- ENTRY_CONTRACT.md present; tests pass.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P01.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P01/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P02 — Runtime Package Skeleton and Naming

### Phase ID

`RT-P02`

### Phase Name

Runtime Package Skeleton and Naming

### Lane

YELLOW

### Dependencies

`RT-P01`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `foundation`

### Purpose

Create the importable runtime package skeleton and naming conventions that all later phases extend additively.

### Scope

- Lay out src/alpha_system/runtime/ subpackage structure and __init__ surface.
- Document naming conventions for runtime objects, states, and report cards.

### Non-Goals

- No diagnostics logic.
- No CLI.
- No duplication of research/experiments/governance code.

### Expected Files / Directories

- `src/alpha_system/runtime/**`
- `tests/unit/runtime/**`
- `docs/research_runtime/NAMING.md`
- `configs/runtime/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P02.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P02/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime -q
test -f docs/research_runtime/NAMING.md
git ls-files runs
```

### Artifact Policy

Commit only: runtime package skeleton; naming conventions; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime imports.
- NAMING.md present.
- Skeleton additive; tests pass.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P02.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P02/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P03 — Runtime Input Resolver: DatasetVersion and Feature/Label Packs

### Phase ID

`RT-P03`

### Phase Name

Runtime Input Resolver: DatasetVersion and Feature/Label Packs

### Lane

YELLOW

### Dependencies

`RT-P02`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `foundation`

### Purpose

Build the RuntimeInputPack resolver that turns references into a resolved, versioned input bundle (DatasetVersion + feature/label packs) with availability discipline.

### Scope

- Resolve accepted DatasetVersion, canonical input views, FeatureStore/LabelStore handles, partition + session scope.
- Enforce feature available_ts and label label_available_ts at resolution time; no raw provider path.

### Non-Goals

- No materialization.
- No external provider calls.
- No diagnostics.

### Expected Files / Directories

- `src/alpha_system/runtime/input_resolver.py`
- `tests/unit/runtime/test_input_resolver.py`
- `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
- `docs/research_runtime/INPUT_RESOLVER.md`
- `configs/runtime/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P03.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P03/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.input_resolver"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime tests/no_lookahead/research_runtime -q
test -f docs/research_runtime/INPUT_RESOLVER.md
git ls-files runs
```

### Artifact Policy

Commit only: RuntimeInputPack resolver; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.input_resolver imports.
- available_ts/label_available_ts enforced.
- INPUT_RESOLVER.md + no-lookahead test present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P03.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P03/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P04 — StudyRunSpec and RuntimePlan Contracts

### Phase ID

`RT-P04`

### Phase Name

StudyRunSpec and RuntimePlan Contracts

### Lane

YELLOW

### Dependencies

`RT-P03`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `foundation`

### Purpose

Define the StudyRunSpec and RuntimePlan (plus RuntimeRequest) contracts that describe and validate a bounded runtime job before it executes.

### Scope

- RuntimeRequest, RuntimePlan, StudyRunSpec dataclasses with validation.
- Require bounded grid and cost stress when a signal probe is included; require locked-test contamination metadata for locked partitions.

### Non-Goals

- No execution.
- No promotion semantics.
- No alpha approval implied by a request.

### Expected Files / Directories

- `src/alpha_system/runtime/contracts/__init__.py`
- `src/alpha_system/runtime/contracts/run_spec.py`
- `src/alpha_system/runtime/contracts/plan.py`
- `tests/unit/runtime/contracts/test_run_spec.py`
- `tests/unit/runtime/contracts/test_plan.py`
- `docs/research_runtime/RUN_SPEC_AND_PLAN.md`
- `configs/runtime/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P04.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P04/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.contracts.run_spec, alpha_system.runtime.contracts.plan"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime -q
test -f docs/research_runtime/RUN_SPEC_AND_PLAN.md
git ls-files runs
```

### Artifact Policy

Commit only: StudyRunSpec / RuntimePlan / RuntimeRequest contracts; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- run_spec and plan modules import.
- Validation rejects unbounded plans.
- RUN_SPEC_AND_PLAN.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P04.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P04/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P05 — StudyRunRecord, Manifest, and Runtime Artifact Contract

### Phase ID

`RT-P05`

### Phase Name

StudyRunRecord, Manifest, and Runtime Artifact Contract

### Lane

YELLOW

### Dependencies

`RT-P04`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `foundation`

### Purpose

Define the durable StudyRunRecord, the reproducibility StudyRunManifest, and the RuntimeArtifactManifest contracts.

### Scope

- StudyRunRecord (status/result_state/rejection_reasons), StudyRunManifest (dataset/feature/label/code/config hashes), RuntimeArtifactManifest (local-only, commit_allowed flags).
- Bind manifests to versions for reproducibility.

### Non-Goals

- No heavy artifact commit.
- No values embedded in records.

### Expected Files / Directories

- `src/alpha_system/runtime/contracts/run_record.py`
- `src/alpha_system/runtime/contracts/manifest.py`
- `src/alpha_system/runtime/contracts/artifacts.py`
- `tests/unit/runtime/contracts/test_run_record.py`
- `tests/unit/runtime/contracts/test_manifest.py`
- `tests/unit/runtime/contracts/test_artifacts.py`
- `docs/research_runtime/RUN_RECORD_AND_MANIFEST.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P05.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P05/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.contracts.run_record, alpha_system.runtime.contracts.manifest"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime -q
test -f docs/research_runtime/RUN_RECORD_AND_MANIFEST.md
git ls-files runs
```

### Artifact Policy

Commit only: StudyRunRecord / StudyRunManifest / RuntimeArtifactManifest; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- run_record and manifest modules import.
- Manifest carries version + hash lineage.
- RUN_RECORD_AND_MANIFEST.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P05.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P05/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P06 — Diagnostics Report Contracts

### Phase ID

`RT-P06`

### Phase Name

Diagnostics Report Contracts

### Lane

YELLOW

### Dependencies

`RT-P05`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `foundation`

### Purpose

Define the shared diagnostics report contracts (DiagnosticsRunSpec/DiagnosticsRunRecord + report shape) that the parallel diagnostics runtimes implement.

### Scope

- Shared runtime/diagnostics/__init__.py, contracts.py, report.py.
- Descriptive, non-promotional report schema with limitations and status.

### Non-Goals

- No family-specific diagnostics yet.
- No promotion language.

### Expected Files / Directories

- `src/alpha_system/runtime/diagnostics/__init__.py`
- `src/alpha_system/runtime/diagnostics/contracts.py`
- `src/alpha_system/runtime/diagnostics/report.py`
- `tests/unit/runtime/diagnostics/test_contracts.py`
- `tests/unit/runtime/diagnostics/test_report.py`
- `docs/research_runtime/DIAGNOSTICS_CONTRACTS.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P06.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P06/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.diagnostics.contracts"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/diagnostics -q
test -f docs/research_runtime/DIAGNOSTICS_CONTRACTS.md
git ls-files runs
```

### Artifact Policy

Commit only: DiagnosticsRunSpec / DiagnosticsRunRecord / report contracts; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.diagnostics.contracts imports.
- Report schema descriptive only.
- DIAGNOSTICS_CONTRACTS.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P06.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P06/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P07 — Factor Diagnostics Runtime

### Phase ID

`RT-P07`

### Phase Name

Factor Diagnostics Runtime

### Lane

YELLOW

### Dependencies

`RT-P06`

### DAG Scheduling

- `parallel_safe`: `true`
- `must_run_alone`: `false`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `diagnostics`

### Purpose

Implement the Factor Diagnostics runtime by orchestrating existing research primitives (IC/RankIC, bucket returns, monotonicity, decay) into a FactorDiagnosticsReport.

### Scope

- runtime/diagnostics/factor/ orchestrating alpha_system.research.ic and research.buckets.
- Coverage, missingness, outlier rate, decay curve, limitations.

### Non-Goals

- No new IC/bucket math (consume research.*).
- No promotion.
- No signal probe.

### Expected Files / Directories

- `src/alpha_system/runtime/diagnostics/factor/**`
- `tests/unit/runtime/diagnostics/factor/**`
- `docs/research_runtime/diagnostics/factor.md`
- `configs/runtime/diagnostics/factor/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P07.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P07/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`. In parallel mode this phase additionally must not touch the shared diagnostics contracts, `cli/main.py`, or `ACTIVE_CAMPAIGN.md`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.diagnostics.factor"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/diagnostics/factor -q
test -f docs/research_runtime/diagnostics/factor.md
git ls-files runs
```

### Artifact Policy

Commit only: Factor diagnostics runtime (orchestrates research.ic/buckets); tests on synthetic fixtures; docs; configs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.diagnostics.factor imports.
- Report orchestrates research.ic/buckets.
- diagnostics/factor.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P07.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P07/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P08 — Label Diagnostics Runtime

### Phase ID

`RT-P08`

### Phase Name

Label Diagnostics Runtime

### Lane

YELLOW

### Dependencies

`RT-P06`

### DAG Scheduling

- `parallel_safe`: `true`
- `must_run_alone`: `false`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `diagnostics`

### Purpose

Implement the Label Diagnostics runtime producing a LabelDiagnosticsReport (distribution, horizon coverage, class balance, MFE/MAE, path ambiguity, label_available_ts validity, cost-adjustment sanity).

### Scope

- runtime/diagnostics/label/ orchestrating existing research/label diagnostics primitives.

### Non-Goals

- No label materialization.
- No promotion.

### Expected Files / Directories

- `src/alpha_system/runtime/diagnostics/label/**`
- `tests/unit/runtime/diagnostics/label/**`
- `docs/research_runtime/diagnostics/label.md`
- `configs/runtime/diagnostics/label/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`. In parallel mode this phase additionally must not touch the shared diagnostics contracts, `cli/main.py`, or `ACTIVE_CAMPAIGN.md`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.diagnostics.label"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/diagnostics/label -q
test -f docs/research_runtime/diagnostics/label.md
git ls-files runs
```

### Artifact Policy

Commit only: Label diagnostics runtime (orchestrates research diagnostics); tests on synthetic fixtures; docs; configs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.diagnostics.label imports.
- label_available_ts validity checked.
- diagnostics/label.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P09 — Session / Regime / RTH / ETH Split Diagnostics

### Phase ID

`RT-P09`

### Phase Name

Session / Regime / RTH / ETH Split Diagnostics

### Lane

YELLOW

### Dependencies

`RT-P06`

### DAG Scheduling

- `parallel_safe`: `true`
- `must_run_alone`: `false`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `diagnostics`

### Purpose

Implement Session / Regime / RTH / ETH split diagnostics producing RegimeSplitReport and SessionSplitReport.

### Scope

- runtime/diagnostics/splits/ orchestrating alpha_system.research.regimes and session metadata.
- RTH/ETH, session segment, volatility/spread/liquidity buckets, trend/range.

### Non-Goals

- No strategy conditioning claims.
- No promotion.

### Expected Files / Directories

- `src/alpha_system/runtime/diagnostics/splits/**`
- `tests/unit/runtime/diagnostics/splits/**`
- `docs/research_runtime/diagnostics/splits.md`
- `configs/runtime/diagnostics/splits/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P09.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P09/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`. In parallel mode this phase additionally must not touch the shared diagnostics contracts, `cli/main.py`, or `ACTIVE_CAMPAIGN.md`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.diagnostics.splits"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/diagnostics/splits -q
test -f docs/research_runtime/diagnostics/splits.md
git ls-files runs
```

### Artifact Policy

Commit only: Session/regime/RTH/ETH split diagnostics (orchestrates research.regimes); tests on synthetic fixtures; docs; configs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.diagnostics.splits imports.
- RTH/ETH + regime splits present.
- diagnostics/splits.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P09.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P09/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P10 — Cross-Market Diagnostics Runtime

### Phase ID

`RT-P10`

### Phase Name

Cross-Market Diagnostics Runtime

### Lane

YELLOW

### Dependencies

`RT-P06`

### DAG Scheduling

- `parallel_safe`: `true`
- `must_run_alone`: `false`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `diagnostics`

### Purpose

Implement Cross-Market ES/NQ/RTY diagnostics producing a CrossMarketDiagnosticsReport (alignment, timestamp sync, lead/lag, correlation regime, residual, per-symbol missingness).

### Scope

- runtime/diagnostics/cross_market/ orchestrating alpha_system.research.correlation/cross_sectional.

### Non-Goals

- No multi-asset strategy.
- No promotion.

### Expected Files / Directories

- `src/alpha_system/runtime/diagnostics/cross_market/**`
- `tests/unit/runtime/diagnostics/cross_market/**`
- `docs/research_runtime/diagnostics/cross_market.md`
- `configs/runtime/diagnostics/cross_market/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P10.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P10/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`. In parallel mode this phase additionally must not touch the shared diagnostics contracts, `cli/main.py`, or `ACTIVE_CAMPAIGN.md`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.diagnostics.cross_market"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/diagnostics/cross_market -q
test -f docs/research_runtime/diagnostics/cross_market.md
git ls-files runs
```

### Artifact Policy

Commit only: Cross-market ES/NQ/RTY diagnostics (orchestrates research.correlation); tests on synthetic fixtures; docs; configs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.diagnostics.cross_market imports.
- alignment + timestamp sync reported.
- diagnostics/cross_market.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P10.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P10/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P11 — CostModelVersion and Cost Stress Runtime

### Phase ID

`RT-P11`

### Phase Name

CostModelVersion and Cost Stress Runtime

### Lane

YELLOW

### Dependencies

`RT-P06`

### DAG Scheduling

- `parallel_safe`: `true`
- `must_run_alone`: `false`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `diagnostics`

### Purpose

Implement CostModelVersion and the cost-stress runtime producing a CostSensitivityReport across base / stress_1 / stress_2 / double_cost profiles.

### Scope

- runtime/cost/ consuming alpha_system.backtest.costs and backtest.slippage.
- BBO spread crossing where available; slippage labeled proxy; session/ETH penalties.

### Non-Goals

- No live execution.
- No venue guarantees.
- Zero-cost is diagnostic only.

### Expected Files / Directories

- `src/alpha_system/runtime/cost/**`
- `tests/unit/runtime/cost/**`
- `docs/research_runtime/COST_STRESS.md`
- `configs/runtime/cost/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P11.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P11/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`. In parallel mode this phase additionally must not touch the shared diagnostics contracts, `cli/main.py`, or `ACTIVE_CAMPAIGN.md`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.cost"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/cost -q
test -f docs/research_runtime/COST_STRESS.md
git ls-files runs
```

### Artifact Policy

Commit only: CostModelVersion / CostStressSpec / CostSensitivityReport (consumes backtest.costs/slippage); tests on synthetic fixtures; docs; configs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.cost imports.
- double_cost profile present; slippage labeled proxy.
- COST_STRESS.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P11.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P11/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P12 — Simple Signal Probe Runtime

### Phase ID

`RT-P12`

### Phase Name

Simple Signal Probe Runtime

### Lane

YELLOW

### Dependencies

`RT-P07`, `RT-P08`, `RT-P11`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `integration`

### Purpose

Implement the simple Signal Probe runtime (SignalProbeSpec/SignalProbeReport): convert a diagnostic relationship into a long/short/flat probe and check survival under cost, turnover, and stability — explicitly not strategy validation.

### Scope

- runtime/probe/ with threshold probes, trade count, turnover, cost-aware expectancy proxy, drawdown proxy, parameter-neighborhood stability.
- No same-bar optimistic fill.

### Non-Goals

- No final strategy validation.
- No management grid.
- No portfolio claim.
- No promotion.

### Expected Files / Directories

- `src/alpha_system/runtime/probe/**`
- `tests/unit/runtime/probe/**`
- `tests/no_lookahead/research_runtime/test_signal_probe_fills.py`
- `docs/research_runtime/SIGNAL_PROBE.md`
- `configs/runtime/probe/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P12.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P12/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.probe"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/probe tests/no_lookahead/research_runtime -q
test -f docs/research_runtime/SIGNAL_PROBE.md
git ls-files runs
```

### Artifact Policy

Commit only: SignalProbeSpec / SignalProbeReport (fast-path probe, not strategy validation); tests; docs; configs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.probe imports.
- no same-bar fill enforced; cost stress required.
- SIGNAL_PROBE.md + no-lookahead fill test present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P12.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P12/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P13 — Bounded Grid / Variant Budget Guard

### Phase ID

`RT-P13`

### Phase Name

Bounded Grid / Variant Budget Guard

### Lane

YELLOW

### Dependencies

`RT-P12`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `integration`

### Purpose

Implement the bounded-grid / VariantBudget guard that caps variants, grid points, and compute and forbids selection on the locked test — consuming the existing experiments limits/overfit controls.

### Scope

- runtime/grid/ consuming alpha_system.experiments.limits and experiments.overfit_controls.
- Record variant count; block unbounded grids and locked-test selection.

### Non-Goals

- No new grid engine.
- No promotion.

### Expected Files / Directories

- `src/alpha_system/runtime/grid/**`
- `tests/unit/runtime/grid/**`
- `docs/research_runtime/BOUNDED_GRID.md`
- `configs/runtime/grid/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P13.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P13/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.grid"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/grid -q
test -f docs/research_runtime/BOUNDED_GRID.md
git ls-files runs
```

### Artifact Policy

Commit only: BoundedGridSpec / VariantBudget guard (consumes experiments.limits/overfit_controls); tests; docs; configs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.grid imports.
- unbounded grid rejected; variant budget enforced.
- BOUNDED_GRID.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P13.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P13/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P14 — No-Lookahead Runtime Audit

### Phase ID

`RT-P14`

### Phase Name

No-Lookahead Runtime Audit

### Lane

YELLOW

### Dependencies

`RT-P12`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `integration`

### Purpose

Implement the NoLookaheadRuntimeAudit that fails closed on availability, same-bar fill, label-as-feature, centered/future windows, and locked-test contamination.

### Scope

- runtime/audit/ checks: available_ts, label_available_ts, no label-as-feature, no centered/future live window, no same-bar optimistic fill, locked-test metadata.

### Non-Goals

- No promotion.
- No strategy validation.

### Expected Files / Directories

- `src/alpha_system/runtime/audit/**`
- `tests/unit/runtime/audit/**`
- `docs/research_runtime/NO_LOOKAHEAD_AUDIT.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P14.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P14/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.audit"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/audit -q
test -f docs/research_runtime/NO_LOOKAHEAD_AUDIT.md
git ls-files runs
```

### Artifact Policy

Commit only: NoLookaheadRuntimeAudit; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.audit imports.
- audit fails closed on each violation class.
- NO_LOOKAHEAD_AUDIT.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P14.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P14/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P15 — RejectionReasonRecord and Runtime Decision States

### Phase ID

`RT-P15`

### Phase Name

RejectionReasonRecord and Runtime Decision States

### Lane

YELLOW

### Dependencies

`RT-P13`, `RT-P14`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `integration`

### Purpose

Implement RejectionReasonRecord and the runtime decision states so failed/inconclusive/blocked runs stay visible (REJECTED / INCONCLUSIVE / BLOCKED, never hidden).

### Scope

- runtime/decisions/ with reason categories (data_unavailable, leakage_risk, weak_diagnostics, cost_fragile, low_sample, variant_budget_exceeded, duplicate_exposure, blocked_by_policy, inconclusive).

### Non-Goals

- No silent failure.
- No promotion.

### Expected Files / Directories

- `src/alpha_system/runtime/decisions/**`
- `tests/unit/runtime/decisions/**`
- `docs/research_runtime/DECISION_STATES.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P15.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P15/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.decisions"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/decisions -q
test -f docs/research_runtime/DECISION_STATES.md
git ls-files runs
```

### Artifact Policy

Commit only: RejectionReasonRecord + runtime decision states (REJECTED/INCONCLUSIVE/BLOCKED); tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.decisions imports.
- rejection reasons recorded for fail/inconclusive.
- DECISION_STATES.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P15.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P15/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P16 — EvidenceBundle Draft Builder

### Phase ID

`RT-P16`

### Phase Name

EvidenceBundle Draft Builder

### Lane

YELLOW

### Dependencies

`RT-P15`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `integration`

### Purpose

Implement the EvidenceDraft builder that bundles diagnostics + cost summaries + limitations + rejection/handoff state to feed the existing governance EvidenceBundle — an evidence-input, not a candidate.

### Scope

- runtime/evidence/ producing EvidenceDraft consumable by alpha_system.governance.evidence_bundle.

### Non-Goals

- No candidate creation.
- No promotion.
- No EvidenceBundle re-implementation.

### Expected Files / Directories

- `src/alpha_system/runtime/evidence/**`
- `tests/unit/runtime/evidence/**`
- `docs/research_runtime/EVIDENCE_DRAFT.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P16.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P16/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.evidence"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/evidence -q
test -f docs/research_runtime/EVIDENCE_DRAFT.md
git ls-files runs
```

### Artifact Policy

Commit only: EvidenceDraft builder (feeds governance.evidence_bundle; not a candidate); tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.evidence imports.
- EvidenceDraft feeds governance.evidence_bundle; not a candidate.
- EVIDENCE_DRAFT.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P16.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P16/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P17 — Reference Candidate Handoff Builder

### Phase ID

`RT-P17`

### Phase Name

Reference Candidate Handoff Builder

### Lane

YELLOW

### Dependencies

`RT-P16`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `integration`

### Purpose

Implement the ReferenceCandidateHandoff builder that packages a survivor (report, manifest, versions, cost profile, limitations, required next gate) for conservative Reference validation — handoff only, never Reference validation itself.

### Scope

- runtime/handoff/ producing ReferenceCandidateHandoff with strategy_not_validated_flag and reference_requirements.

### Non-Goals

- No Reference backtest execution.
- No promotion.
- No tradability claim.

### Expected Files / Directories

- `src/alpha_system/runtime/handoff/**`
- `tests/unit/runtime/handoff/**`
- `docs/research_runtime/REFERENCE_HANDOFF.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P17.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P17/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.handoff"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/handoff -q
test -f docs/research_runtime/REFERENCE_HANDOFF.md
git ls-files runs
```

### Artifact Policy

Commit only: ReferenceCandidateHandoff builder (handoff only; not Reference validation); tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.handoff imports.
- handoff marks strategy_not_validated and next_required_gate=REFERENCE_VALIDATION_REQUIRED.
- REFERENCE_HANDOFF.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P17.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P17/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P18 — Runtime CLI / Tool Surface

### Phase ID

`RT-P18`

### Phase Name

Runtime CLI / Tool Surface

### Lane

YELLOW

### Dependencies

`RT-P17`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `integration`

### Purpose

Add the local-only, CI-safe alpha runtime CLI / tool surface, registered additively in the existing CLI shell.

### Scope

- src/alpha_system/cli/runtime.py + additive registration in cli/main.py.
- Subcommands: plan, validate-inputs, run-diagnostics, run-label-diagnostics, run-signal-probe, run-cost-stress, build-evidence-draft, build-reference-handoff, summarize, inspect, replay-summary.

### Non-Goals

- No network.
- No provider calls.
- No autonomous agents.

### Expected Files / Directories

- `src/alpha_system/cli/runtime.py`
- `src/alpha_system/cli/main.py`
- `tests/unit/cli/test_runtime.py`
- `docs/research_runtime/CLI.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P18.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P18/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.cli.runtime"
python -m alpha_system runtime --help
python tools/verify.py --smoke
python -m pytest tests/unit/cli/test_runtime.py -q
test -f docs/research_runtime/CLI.md
git ls-files runs
```

### Artifact Policy

Commit only: alpha runtime CLI surface (local-only, CI-safe, additive registration); tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.cli.runtime imports; `alpha runtime --help` works.
- CLI local-only and CI-safe.
- CLI.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P18.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P18/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P19 — Runtime Cache and Local Artifact Policy

### Phase ID

`RT-P19`

### Phase Name

Runtime Cache and Local Artifact Policy

### Lane

YELLOW

### Dependencies

`RT-P18`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `integration`

### Purpose

Define the RuntimeCachePolicy and the local-only runtime artifact policy (small curated summaries committable; heavy outputs local-only).

### Scope

- runtime/cache/ + runtime/artifact_policy.py with commit_allowed flags and a derived-summary cache policy.

### Non-Goals

- No heavy artifact commit.
- No distributed compute.

### Expected Files / Directories

- `src/alpha_system/runtime/cache/**`
- `src/alpha_system/runtime/artifact_policy.py`
- `tests/unit/runtime/cache/**`
- `tests/unit/runtime/test_artifact_policy.py`
- `docs/research_runtime/CACHE_AND_ARTIFACTS.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.artifact_policy"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime -q
test -f docs/research_runtime/CACHE_AND_ARTIFACTS.md
git ls-files runs
```

### Artifact Policy

Commit only: RuntimeCachePolicy + local-only artifact policy; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.artifact_policy imports.
- heavy outputs marked local-only.
- CACHE_AND_ARTIFACTS.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P19/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P20 — Synthetic Runtime Fixtures and Fail-Closed Tests

### Phase ID

`RT-P20`

### Phase Name

Synthetic Runtime Fixtures and Fail-Closed Tests

### Lane

YELLOW

### Dependencies

`RT-P19`

### DAG Scheduling

- `parallel_safe`: `true`
- `must_run_alone`: `false`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `tests_tools_docs`

### Purpose

Add tiny synthetic runtime fixtures and the fail-closed test suite that exercises every prohibited shortcut.

### Scope

- tests/fixtures/runtime/ (tiny, synthetic, documented), tests/unit/runtime/fail_closed/, tests/no_lookahead/research_runtime/.

### Non-Goals

- No real market data.
- No alpha evidence in fixtures.

### Expected Files / Directories

- `tests/fixtures/runtime/**`
- `tests/unit/runtime/fail_closed/**`
- `tests/no_lookahead/research_runtime/**`
- `docs/research_runtime/FIXTURES.md`
- `docs/research_runtime/TESTING.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P20.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P20/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`. In parallel mode this phase additionally must not touch the shared diagnostics contracts, `cli/main.py`, or `ACTIVE_CAMPAIGN.md`.

### Validation Commands

```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/fail_closed tests/no_lookahead/research_runtime -q
test -f docs/research_runtime/FIXTURES.md
git ls-files runs
find tests/fixtures/runtime -type f -size +1M -print
```

### Artifact Policy

Commit only: tiny synthetic runtime fixtures; fail-closed test suite; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- fail-closed + no-lookahead suites pass.
- fixtures tiny (<1MB) and documented.
- FIXTURES.md + TESTING.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P20.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P20/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P21 — Small Real FLF DatasetVersion Runtime Smoke

### Phase ID

`RT-P21`

### Phase Name

Small Real FLF DatasetVersion Runtime Smoke

### Lane

YELLOW

### Dependencies

`RT-P20`, `RT-P22`, `RT-P23`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `closeout`

### Purpose

Run a small real FLF DatasetVersion runtime smoke (local-only) end to end through resolve → diagnostics → cost stress → evidence draft.

### Scope

- src/alpha_system/runtime/smoke.py + integration test against a small accepted DatasetVersion (local-only).

### Non-Goals

- No external provider call.
- No data commit.
- No alpha claim.

### Expected Files / Directories

- `src/alpha_system/runtime/smoke.py`
- `tests/integration/runtime/test_smoke.py`
- `docs/research_runtime/REAL_SMOKE.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P21.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P21/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.smoke"
python tools/verify.py --smoke
python -m pytest tests/integration/runtime -q
test -f docs/research_runtime/REAL_SMOKE.md
git ls-files runs
```

### Artifact Policy

Commit only: small real DatasetVersion runtime smoke harness (local-only); integration test; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.smoke imports.
- smoke passes or records a truthful PASS_WITH_WARNINGS.
- REAL_SMOKE.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P21.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P21/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P22 — Agent-Facing Tool Result Contracts

### Phase ID

`RT-P22`

### Phase Name

Agent-Facing Tool Result Contracts

### Lane

YELLOW

### Dependencies

`RT-P19`

### DAG Scheduling

- `parallel_safe`: `true`
- `must_run_alone`: `false`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `tests_tools_docs`

### Purpose

Define the agent-facing RuntimeToolResult / RuntimeRunSummary structured-output contracts for the future Agent Factory — without creating any autonomous agent.

### Scope

- runtime/tool_results.py with status/run_id/version ids/diagnostics_summary/cost_summary/rejection_reasons/artifacts/next_required_gate.
- Raw/heavy data forbidden in tool responses.

### Non-Goals

- No autonomous agents.
- No raw data in tool output.

### Expected Files / Directories

- `src/alpha_system/runtime/tool_results.py`
- `tests/unit/runtime/test_tool_results.py`
- `docs/research_runtime/TOOL_RESULTS.md`
- `configs/runtime/tool_results/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P22.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P22/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`. In parallel mode this phase additionally must not touch the shared diagnostics contracts, `cli/main.py`, or `ACTIVE_CAMPAIGN.md`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.tool_results"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/test_tool_results.py -q
test -f docs/research_runtime/TOOL_RESULTS.md
git ls-files runs
```

### Artifact Policy

Commit only: RuntimeToolResult / RuntimeRunSummary agent-facing contracts; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.tool_results imports.
- tool results carry no raw/heavy data.
- TOOL_RESULTS.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P22.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P22/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P23 — Runtime Reports, Docs, and Templates

### Phase ID

`RT-P23`

### Phase Name

Runtime Reports, Docs, and Templates

### Lane

YELLOW

### Dependencies

`RT-P19`

### DAG Scheduling

- `parallel_safe`: `true`
- `must_run_alone`: `false`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `tests_tools_docs`

### Purpose

Add the RuntimeReportCard renderer plus report/markdown templates for human-readable runtime summaries.

### Scope

- runtime/reports.py + docs/research_runtime/templates/ and report_cards/.

### Non-Goals

- No heavy report bundles committed.
- No promotion language.

### Expected Files / Directories

- `src/alpha_system/runtime/reports.py`
- `tests/unit/runtime/test_reports.py`
- `docs/research_runtime/REPORTS.md`
- `docs/research_runtime/templates/**`
- `docs/research_runtime/report_cards/**`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P23.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P23/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`. In parallel mode this phase additionally must not touch the shared diagnostics contracts, `cli/main.py`, or `ACTIVE_CAMPAIGN.md`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.reports"
python tools/verify.py --smoke
python -m pytest tests/unit/runtime/test_reports.py -q
test -f docs/research_runtime/REPORTS.md
git ls-files runs
```

### Artifact Policy

Commit only: RuntimeReportCard + report/markdown templates; tests; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.reports imports.
- templates present; reports non-promotional.
- REPORTS.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P23.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P23/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P24 — Workflow 2 DAG Integration and Parallel Plan

### Phase ID

`RT-P24`

### Phase Name

Workflow 2 DAG Integration and Parallel Plan

### Lane

YELLOW

### Dependencies

`RT-P21`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `closeout`

### Purpose

Document the Workflow 2 DAG integration and parallel plan for the runtime campaign (waves, parallel-safe phases, serial merge).

### Scope

- docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md + RT-P24 handoff; confirm plan-dag waves.

### Non-Goals

- No scheduler code change (consume WF2_PARALLEL_DAG_SCHEDULER_MVP).

### Expected Files / Directories

- `docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python tools/verify.py --smoke
python tools/frontier/ralph_driver.py plan-dag --campaign-id ALPHA_RESEARCH_RUNTIME_MVP
test -f docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md
git ls-files runs
```

### Artifact Policy

Commit only: Workflow 2 DAG integration notes + parallel plan; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- plan-dag runs clean.
- DAG integration documented.
- handoff present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P25 — End-to-End Runtime Dry Run

### Phase ID

`RT-P25`

### Phase Name

End-to-End Runtime Dry Run

### Lane

YELLOW

### Dependencies

`RT-P24`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `closeout`

### Purpose

Run the end-to-end runtime dry run: a governed AlphaSpec/StudySpec flows resolve → diagnostics → probe → cost stress → evidence draft → reference handoff on synthetic fixtures.

### Scope

- src/alpha_system/runtime/dry_run.py + integration test; full pipeline on fixtures.

### Non-Goals

- No alpha search.
- No promotion.
- No data commit.

### Expected Files / Directories

- `src/alpha_system/runtime/dry_run.py`
- `tests/integration/runtime/test_dry_run.py`
- `docs/research_runtime/E2E_DRY_RUN.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P25.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P25/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python -c "import alpha_system.runtime.dry_run"
python tools/verify.py --all
python -m pytest tests/integration/runtime -q
test -f docs/research_runtime/E2E_DRY_RUN.md
git ls-files runs
```

### Artifact Policy

Commit only: end-to-end runtime dry-run harness (local-only); integration test; docs. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- alpha_system.runtime.dry_run imports.
- verify.py --all passes; e2e dry run passes or truthful warnings.
- E2E_DRY_RUN.md present.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P25.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P25/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## RT-P26 — Acceptance Audit and Closeout

### Phase ID

`RT-P26`

### Phase Name

Acceptance Audit and Closeout

### Lane

YELLOW

### Dependencies

`RT-P25`

### DAG Scheduling

- `parallel_safe`: `false`
- `must_run_alone`: `true`
- `conflicts_with`: `[]`
- `resource_class`: `[]`
- `merge_group`: `closeout`

### Purpose

Run the acceptance audit + semantic done-check and write the closeout with a final verdict and Agent Factory next-campaign readiness.

### Scope

- campaigns/ALPHA_RESEARCH_RUNTIME_MVP/CLOSEOUT.md + docs/research_runtime/ACCEPTANCE_AUDIT.md + RT-P26 handoff.

### Non-Goals

- No new runtime scope.
- No alpha claim.

### Expected Files / Directories

- `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/CLOSEOUT.md`
- `docs/research_runtime/ACCEPTANCE_AUDIT.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P26.md` (commit-eligible handoff)
- `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P26/**` (review artifacts when YELLOW)

### Forbidden Changes

Out-of-scope domains, all data/heavy-artifact paths, and the consumed primitive packages (`src/alpha_system/governance/**`, `experiments/**`, `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`). The full `forbidden_paths` list is in `campaign.yaml`.

### Validation Commands

```bash
git status --short
python tools/verify.py --all
python tools/hooks/canary_runner.py
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/CLOSEOUT.md
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
```

### Artifact Policy

Commit only: acceptance audit; closeout doc with final verdict and next-campaign readiness. Explicit staging only. Never commit raw/canonical/feature/label/runtime values, heavy artifacts, provider responses, local DBs, logs, caches, or `runs/**`.

### Done Criteria

- verify.py --all + canaries pass.
- acceptance gates satisfied; artifact audit clean.
- CLOSEOUT.md records final verdict and readiness.

### Handoff Requirements

Write `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P26.md` with the exact staged file list, `git status --short`, commands run with results, checks, artifact-audit confirmation, and any caveats.

### Review Requirements

YELLOW: fresh Claude Opus 4.8 xhigh review with `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P26/**review.md` and `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`} required before merge.

### Auto-Merge Eligibility

Auto-PR + auto-merge after a fresh Claude Opus review with `verdict.json` ∈ {`PASS`, `PASS_WITH_WARNINGS`}, checks pass, handoff valid, artifact policy passes, no forbidden paths, no STOP file, and the semantic done-check passes.

## Campaign-Wide Done Criteria

- All 27 phases (RT-P00 … RT-P26) complete; every acceptance gate satisfied.
- An approved AlphaSpec/StudySpec runs end to end through resolve → diagnostics → cost stress → (optional) probe → EvidenceDraft → ReferenceCandidateHandoff on synthetic fixtures and a small real local DatasetVersion.
- `python tools/verify.py --all` and `python tools/hooks/canary_runner.py` pass (or a truthful PASS_WITH_WARNINGS is recorded).
- Artifact audit clean: `git ls-files runs` empty; no raw/canonical/feature/label/runtime values, heavy artifacts, or local DBs committed.
- DAG metadata correct: parallel-safe phases have disjoint `allowed_paths`; no phase branch writes `ACTIVE_CAMPAIGN.md`; merge is serial.
- No alpha/tradability/profitability/strategy/paper/live/broker/production claim anywhere; no prohibited runtime state reachable.
- CLOSEOUT.md records the final verdict and Agent Factory next-campaign readiness.

## Scope Boundaries

See GOAL.md (What this campaign does not build) and campaign.yaml (`stop_conditions`, `risk_controls`, `phase_defaults.forbidden_global_changes`). The runtime is the controlled local runtime that makes approved specs runnable into diagnostics and evidence drafts — it is not Agent Factory, not alpha search, not a FactorLibrary, not Strategy Reference Validation, not a Portfolio AlphaBook, and not paper/live/broker.

## Review and Merge Rules

- YELLOW merges require a fresh Claude review verdict ∈ {`PASS`, `PASS_WITH_WARNINGS`}; serial merge queue; CI must pass if configured; artifact audit must be clean; no STOP file. See `merge_policy` and `review_policy` in campaign.yaml.

