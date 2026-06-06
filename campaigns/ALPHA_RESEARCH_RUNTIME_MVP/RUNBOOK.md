# ALPHA_RESEARCH_RUNTIME_MVP Runbook

## Runbook purpose

This runbook is the operator manual for executing the
`ALPHA_RESEARCH_RUNTIME_MVP` campaign under Frontier Harness Generic v3.0
Workflow 2 with the DAG-wave parallel scheduler. It covers preflight, the
accepted-DatasetVersion consumption posture, the Feature/Label substrate
dependency, the no-raw-data boundary, the DAG wave plan, the parallel-mock then
parallel-live protocol, the serial merge queue, the runtime input/StudyRunSpec
workflows, the diagnostics / label-diagnostics / signal-probe / cost-stress /
bounded-grid workflows, the no-lookahead runtime audit, the EvidenceDraft and
ReferenceCandidateHandoff workflows, runtime artifact and structured-tool-output
inspection, handoff validation, Claude review, the bounded repair loop, STOP and
resume in parallel mode, blocked-phase handling, the artifact audit, closeout,
and next-campaign readiness for the Agent Factory.

This campaign builds the **executable research loop layer** between the
Feature/Label substrate (`ALPHA_FEATURE_LABEL_FOUNDATION_V1`, complete 32/32,
`COMPLETE_WITH_WARNINGS`) and the future Agent Factory. It builds the local,
deterministic runtime that turns an approved `AlphaSpec` + `StudySpec` into
reproducible diagnostics, cost stress, a bounded signal probe, an
`EvidenceDraft`, rejection reasons, and a `ReferenceCandidateHandoff` — by
**orchestrating existing primitives**, never re-implementing them. It does
**not** run broad alpha search, promote factors, validate strategies, call
Databento or IBKR, pull data, or commit raw/canonical/feature/label/runtime
values. State it plainly and keep it true: a diagnostic PASS is not alpha
validation; a signal probe is not a strategy candidate; a bounded grid is not
promotion; an `EvidenceDraft` is not a candidate; a `ReferenceCandidateHandoff`
is not Reference validation; the fast path is not Reference truth. Research
Runtime is **not** Agent Factory, **not** alpha search, **not** a FactorLibrary,
**not** Strategy Reference Validation, **not** a Portfolio AlphaBook, and
**not** paper/live/broker.

All 27 phases `RT-P00 … RT-P26` are GREEN or YELLOW. `RT-P00` is GREEN
(campaign bootstrap / docs, no Claude review). The other 26 are YELLOW (material
engineering with fresh Claude Opus 4.8 xhigh review and auto-merge through the
serial merge queue). This campaign has **no RED-lane phases** and makes **no
external provider calls**: the runtime consumes only local accepted
DatasetVersions and the registered FeatureStore/LabelStore. The RED lane
definition is retained for harness completeness only.

The runtime objects this campaign builds enforce a research-run lifecycle:
`RUNTIME_REQUESTED → INPUTS_RESOLVED → PLAN_VALIDATED → DIAGNOSTICS_READY →
DIAGNOSTICS_RUNNING → DIAGNOSTICS_COMPLETE (/ DIAGNOSTICS_FAILED) →
SIGNAL_PROBE_READY → SIGNAL_PROBE_COMPLETE → COST_STRESS_COMPLETE →
EVIDENCE_DRAFT_READY → REFERENCE_HANDOFF_READY`, with terminal `REJECTED`,
`INCONCLUSIVE`, and `BLOCKED`. The states `ALPHA_VALIDATED`, `FACTOR_PROMOTED`,
`STRATEGY_READY`, `PORTFOLIO_READY`, `LIVE_READY`, `PAPER_READY`, `PROFITABLE`,
`TRADABLE`, and `PRODUCTION_READY` are **prohibited MVP states** and must never
be reachable by any transition implemented here. `REFERENCE_HANDOFF_READY` is the
most advanced state any survivor may reach.

## Preflight checklist

### Required repo path

The active repo and all Workflow 2 worktrees must be under
`~/projects/alpha_system` on the WSL2 Linux filesystem. Forbidden active
locations: `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive,
Windows-synced folders, network drives, and temporary directories.

```bash
cd ~/projects/alpha_system
pwd                 # must be /home/<user>/projects/alpha_system
git status -sb
```

### Non-negotiable preflight questions

* Is the worktree under the WSL2 path? If not, STOP at `RUN_INIT`.
* Does `campaign.yaml` parse, declare `workflow2.scheduler.mode == dag_wave`, and
  cover every phase (`RT-P00 … RT-P26`) in exactly one acceptance gate? If not,
  block.
* Is `ALPHA_FEATURE_LABEL_FOUNDATION_V1` complete and its FeatureStore/LabelStore
  substrate available? The runtime consumes that substrate; it does not rebuild
  it. If the substrate is missing, block (runtime has nothing admissible to
  resolve).
* Is any forbidden artifact already staged (raw/canonical data, feature or label
  values, runtime heavy outputs, parquet/arrow/feather/dbn/zst, DB/WAL, provider
  response)? If so, unstage before starting.
* Is any broker / order / account / paper / live / strategy / backtest /
  portfolio / alpha-search / factor-promotion scope present anywhere? If so, STOP
  and escalate.
* Has `just frontier-plan` been run for this campaign, and has a
  `frontier-run-parallel-mock` completed before any first live parallel run?
  If not, do those first (DAG wave plan + parallel mock sections below).

### Smoke preflight

```bash
cd ~/projects/alpha_system
python tools/verify.py --smoke
ls runs/*/STOP 2>/dev/null || echo "no active STOP file"
```

## Repo clean check

```bash
cd ~/projects/alpha_system
git status --short
git status -sb
```

A non-clean baseline before `RUN_INIT` should be reconciled or explained before
starting. Stage explicit paths only; never `git add .` / `git add -A`. Never
force push. `runs/**` is local-only and must never appear in `git status` as a
staged path.

## Campaign file checks

The campaign contract is the source of truth. All six control files must be
present, and there must be no campaign-local `ACTIVE_CAMPAIGN.md`.

```bash
cd ~/projects/alpha_system
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/GOAL.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACCEPTANCE.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RISK_REGISTER.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RUNBOOK.md
test '!' -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACTIVE_CAMPAIGN.md
grep -q "ALPHA_RESEARCH_RUNTIME_MVP" ACTIVE_CAMPAIGN.md
```

## YAML parse

The campaign YAML must parse, identify itself, list phases and acceptance gates,
and declare the DAG-wave scheduler. The assertion below also confirms gate
coverage is complete and unique and that no RED phase exists.

```bash
cd ~/projects/alpha_system
python - <<'PY'
from pathlib import Path
import yaml
data = yaml.safe_load(
    Path("campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml").read_text()
)
assert data["campaign_id"] == "ALPHA_RESEARCH_RUNTIME_MVP"
phases = data["phases"]
assert phases, "no phases"
assert "acceptance_gates" in data and data["acceptance_gates"], "no acceptance_gates"
wf2 = data["workflow2"]
assert wf2["scheduler"]["mode"] == "dag_wave", "scheduler.mode must be dag_wave"
assert wf2["scheduler"]["parallel_execution"] is True
assert wf2["scheduler"]["merge_queue"] == "serial"
assert wf2["scheduler"]["max_parallel_phases"] == 3
phase_ids = [ph["id"] for ph in phases]
assert phase_ids[0] == "RT-P00" and phase_ids[-1] == "RT-P26"
assert len(phase_ids) == 27, f"expected 27 phases, found {len(phase_ids)}"
covered = []
for g in data["acceptance_gates"].values():
    covered.extend(g.get("phases", []))
assert set(phase_ids) == set(covered), "acceptance gate coverage mismatch"
assert len(covered) == len(set(covered)), "phase covered by more than one gate"
red = {ph["id"] for ph in phases if ph["lane"] == "RED"}
assert red == set(), f"unexpected RED phases: {red}"
print(
    f"OK: {len(phase_ids)} phases RT-P00..RT-P26; dag_wave + serial merge "
    f"(max_parallel=3); {len(data['acceptance_gates'])} gates cover phase set "
    f"exactly once; no RED phases"
)
PY
```

## DAG wave plan check (frontier-plan)

Before any execution, run the read-only DAG plan. It prints the dependency
graph, ready waves, run-alone phases, and any path / resource conflicts. A phase
is parallel-safe only if `parallel_safe: true` **and** `must_run_alone: false`
**and** it has disjoint `allowed_paths` **and** touches no global/coordinator
file (`ACTIVE_CAMPAIGN.md`, shared `runtime/diagnostics/contracts.py`,
`cli/main.py`) **and** is not RED. A phase that omits `parallel_safe: true` or
`allowed_paths` runs alone.

```bash
cd ~/projects/alpha_system
just frontier-plan ALPHA_RESEARCH_RUNTIME_MVP
```

Intended wave shape for this campaign (waves w0–w4; `just frontier-plan` previews
the exact computed waves):

```text
w0  RT-P00..RT-P06  sequential bootstrap + contracts (each runs alone)
w1  RT-P07..RT-P11  PARALLEL diagnostics (factor, label, splits, cross_market, cost)
w2  RT-P12..RT-P19  sequential integration (probe, grid, audit, decisions,
                    evidence, handoff, CLI, cache) — each runs alone
w3  RT-P20,RT-P22,RT-P23  PARALLEL tests / tool contracts / docs+templates
w4  RT-P21,RT-P24,RT-P25,RT-P26  sequential closeout (real smoke, DAG integration,
                    e2e dry run, acceptance + closeout) — each runs alone
```

Parallel waves (w1 and the parallel subset of w3) build concurrently in isolated
worktrees, capped at `max_parallel_phases = 3`. Verify in the plan output that
every parallel phase in a wave has disjoint `allowed_paths` and that none writes
a global file. If the plan reports a path or resource conflict, that wave does
not run in parallel.

## Parallel mock run (frontier-run-parallel-mock)

Run the parallel mock at least once before the first live parallel run. The mock
exercises the DAG-wave scheduler, worktree isolation, and the serial merge queue
with **no providers, no network, and no merge** (`FRONTIER_MOCK_PROVIDERS`).

```bash
cd ~/projects/alpha_system
just frontier-run-parallel-mock ALPHA_RESEARCH_RUNTIME_MVP 3
```

Confirm from the mock output that waves form as expected, that parallel phases
build concurrently in separate worktrees, and that merges are serialized one PR
at a time. The mock must not call Databento or IBKR and must not create real PRs
or merges.

## Parallel live run (frontier-run-parallel)

After a clean plan and a successful mock, the live parallel run executes
concurrently in isolated worktrees with a serial merge queue. This is the
default execution path for this campaign.

```bash
cd ~/projects/alpha_system
# Live DAG-wave parallel run (concurrent build in isolated worktrees, serial merge).
# Run only after `just frontier-plan` is clean and a parallel mock has passed.
# just frontier-run-parallel ALPHA_RESEARCH_RUNTIME_MVP 3
```

The live run still makes **no external provider calls** — every phase consumes
local accepted DatasetVersions or synthetic fixtures. `max_parallel = 3` matches
`workflow2.scheduler.max_parallel_phases`. Phase branches use the `auto/` branch
prefix. Build is parallel; **merge is always serial**
(`merge_queue: serial`). The coordinator merges one PR at a time, re-validating
the merge gate against the freshly updated `main` before each merge, and only the
coordinator updates `ACTIVE_CAMPAIGN.md` (`update_active_campaign:
coordinator_only`). A phase branch that writes `ACTIVE_CAMPAIGN.md` in parallel
mode, or a merge outside the serial queue, is a global blocker.

## Accepted DatasetVersion check

The runtime consumes **only accepted DatasetVersions**, never raw provider files.
Admissibility is a DatasetVersion lifecycle state in
`{VERSIONED, READY_FOR_RESEARCH}`. The sanctioned consumption API is
`alpha_system.data.foundation.version_registry.resolve_dataset_version`, which
returns DatasetVersion metadata; records are reconstructed through
`CanonicalBarRecord`, `CanonicalBBORecord`, and `DenseGridBarRecord` (their
`from_mapping` constructors). Databento is the primary deep-history research
source; IBKR is broker-source recent validation only. Databento and IBKR
DatasetVersions are **never merged**.

```bash
cd ~/projects/alpha_system
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
# registry DB is local-only under $ALPHA_DATA_ROOT/registry/datasets.sqlite
ls "$ALPHA_DATA_ROOT/registry/datasets.sqlite" 2>/dev/null \
  || echo "note: no local registry yet; runtime consumption uses synthetic fixtures in tests"

# TARGET: resolve and inspect an accepted DatasetVersion (RT-P03 input resolver)
# TARGET: alpha runtime validate-inputs --study <study_run_spec_id>
```

A locked-test partition DatasetVersion may only be consumed with governance
contamination metadata (see no-lookahead runtime audit). The input resolver must
reject any DatasetVersion id that is not in an admissible lifecycle state.

## Feature/Label substrate check

The runtime consumes the registered FeatureStore/LabelStore produced by
`ALPHA_FEATURE_LABEL_FOUNDATION_V1` via
`alpha_system.features.consumption` / `features.store` / `features.registry` and
`alpha_system.labels.store` / `labels.registry`. Feature inputs carry
`available_ts`; label inputs carry `label_available_ts`. A label value must never
be exposed as a live feature.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.features.store, alpha_system.features.registry"
python -c "import alpha_system.labels.store, alpha_system.labels.registry"
python -c "import alpha_system.governance.study_input_pack"   # StudyInputPack consumed by runtime
# TARGET: alpha runtime validate-inputs --study <study_run_spec_id>   (RT-P03/RT-P18 surface)
```

These packages are **consumed, not modified**: `src/alpha_system/features/**`,
`labels/**`, `governance/**`, `experiments/**`, `backtest/**`, `research/**`, and
`data/**` are in every phase's `forbidden_paths`. The runtime orchestrates them
and never duplicates them.

## Local data root check ($ALPHA_DATA_ROOT)

Raw, canonical, feature, label, and runtime values are local-only and live
**outside** the repo. The suggested data root is `~/alpha_data/alpha_system`,
configured via `ALPHA_DATA_ROOT`.

```bash
cd ~/projects/alpha_system
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
case "$ALPHA_DATA_ROOT" in
  "$(pwd)"*) echo "ERROR: data root inside repo" ;;
  /mnt/*|*OneDrive*|*Dropbox*|*"Google Drive"*) echo "ERROR: data root on forbidden/synced path" ;;
  *) echo "data root OK (local, outside repo): $ALPHA_DATA_ROOT" ;;
esac
mkdir -p "$ALPHA_DATA_ROOT"
```

Runtime heavy outputs (diagnostics tables, probe artifacts, cost grids), when
produced, are written under `$ALPHA_DATA_ROOT` or `runs/**`, never into the repo
tree. Only small curated summaries are commit-eligible (see
`RuntimeArtifactManifest` `commit_allowed` flags, RT-P05 / RT-P19).

## No raw data access check

Runtime code must never read `.dbn`, `.zst`, parquet, arrow, feather, or any
provider file directly. The only sanctioned input path is an accepted
DatasetVersion resolved through the registry API plus the registered
FeatureStore/LabelStore.

```bash
cd ~/projects/alpha_system
# no forbidden provider/file readers in runtime code (heuristic scan)
grep -REn "\.dbn|\.zst|read_parquet|pyarrow|databento|ib_insync|\.feather" \
  src/alpha_system/runtime 2>/dev/null \
  | grep -v "from_mapping\|resolve_dataset_version" \
  || echo "no direct provider/file readers found in runtime code"
```

If runtime code reads raw provider data, bypasses `resolve_dataset_version`, or
merges Databento with IBKR DatasetVersions, that is a global merge blocker:
`block_merge_and_escalate`.

## Runtime input validation

The entry contract (`RT-P01`) requires an approved `AlphaSpec` + `StudySpec`
plus accepted DatasetVersions and the registered FeatureStore/LabelStore before
any diagnostics run, yielding `INPUTS_RESOLVED` / `INPUTS_BLOCKED` /
`INPUTS_INCONCLUSIVE`. The input resolver (`RT-P03`) turns references into a
`RuntimeInputPack` (`FeatureLabelPackResolver` + resolved DatasetVersion +
partition/session scope) and enforces `available_ts` / `label_available_ts` at
resolution time. No `AlphaSpec`/`StudySpec` → no runtime run; no accepted
DatasetVersion → no runtime execution.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.entry_contract"        # RT-P01
python -c "import alpha_system.runtime.input_resolver"        # RT-P03
python -m pytest tests/unit/runtime tests/no_lookahead/research_runtime -q
test -f docs/research_runtime/ENTRY_CONTRACT.md
test -f docs/research_runtime/INPUT_RESOLVER.md
# TARGET: alpha runtime validate-inputs --study <study_run_spec_id>
```

A missing `AlphaSpec`/`StudySpec`, a bypassed `resolve_dataset_version`, a
feature input without `available_ts`, or a label input without
`label_available_ts` is a global merge blocker.

## StudyRunSpec workflow

A `RuntimeRequest` is described and validated by a `RuntimePlan` and a
`StudyRunSpec` (`RT-P04`) before it executes. The plan must require a bounded
grid (`VariantBudget`) and cost stress when a signal probe is included, and must
require locked-test contamination metadata for locked partitions. Execution
produces a durable `StudyRunRecord` plus a reproducibility `StudyRunManifest`
(dataset/feature/label/code/config hashes) and a `RuntimeArtifactManifest`
(local-only, `commit_allowed` flags) — `RT-P05`. A request never implies alpha
approval.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.contracts.run_spec, alpha_system.runtime.contracts.plan"   # RT-P04
python -c "import alpha_system.runtime.contracts.run_record, alpha_system.runtime.contracts.manifest"  # RT-P05
python -m pytest tests/unit/runtime -q
test -f docs/research_runtime/RUN_SPEC_AND_PLAN.md
test -f docs/research_runtime/RUN_RECORD_AND_MANIFEST.md
# TARGET: alpha runtime plan --study <study_run_spec_id>
```

`RuntimePlan` validation must reject unbounded plans; `StudyRunManifest` must
carry version + hash lineage. No values are embedded in records.

## Diagnostics workflow

The shared diagnostics report contracts (`DiagnosticsRunSpec`,
`DiagnosticsRunRecord`, report shape — `RT-P06`) are descriptive and
non-promotional. The Factor Diagnostics runtime (`RT-P07`) orchestrates
`alpha_system.research.ic` and `research.buckets` into a
`FactorDiagnosticsReport` (IC/RankIC, bucket returns, monotonicity, decay,
coverage, missingness, outlier rate, limitations). It introduces no new IC/bucket
math and makes no promotion claim.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.diagnostics.contracts"  # RT-P06
python -c "import alpha_system.runtime.diagnostics.factor"     # RT-P07
python -m pytest tests/unit/runtime/diagnostics -q
test -f docs/research_runtime/DIAGNOSTICS_CONTRACTS.md
test -f docs/research_runtime/diagnostics/factor.md
# TARGET: alpha runtime run-diagnostics --study <study_run_spec_id>
```

A diagnostic PASS is **not** alpha validation. Session / Regime / RTH / ETH split
diagnostics (`RT-P09`, orchestrating `research.regimes`) and Cross-Market ES/NQ/
RTY diagnostics (`RT-P10`, orchestrating `research.correlation`) produce
`RegimeSplitReport` / `SessionSplitReport` and `CrossMarketDiagnosticsReport`
respectively.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.diagnostics.splits"        # RT-P09
python -c "import alpha_system.runtime.diagnostics.cross_market"  # RT-P10
python -m pytest tests/unit/runtime/diagnostics/splits tests/unit/runtime/diagnostics/cross_market -q
test -f docs/research_runtime/diagnostics/splits.md
test -f docs/research_runtime/diagnostics/cross_market.md
# TARGET: alpha runtime run-diagnostics --study <study_run_spec_id> --splits --cross-market
```

## Label diagnostics workflow

The Label Diagnostics runtime (`RT-P08`) orchestrates existing research/label
diagnostics primitives into a `LabelDiagnosticsReport` (distribution, horizon
coverage, class balance, MFE/MAE, path ambiguity, `label_available_ts` validity,
cost-adjustment sanity). It materializes no labels and makes no promotion claim.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.diagnostics.label"   # RT-P08
python -m pytest tests/unit/runtime/diagnostics/label -q
test -f docs/research_runtime/diagnostics/label.md
# TARGET: alpha runtime run-label-diagnostics --study <study_run_spec_id>
```

A missing or invalid `label_available_ts`, or any label exposed as a live
feature, is a global merge blocker.

## Signal probe workflow

The simple Signal Probe runtime (`RT-P12`, `SignalProbeSpec` /
`SignalProbeReport`) converts a diagnostic relationship into a long/short/flat
probe and checks survival under cost, turnover, and stability — explicitly
**not** strategy validation. No same-bar optimistic fill is permitted, and cost
stress is required for any probe. A probe is **not** a strategy candidate.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.probe"   # RT-P12
python -m pytest tests/unit/runtime/probe tests/no_lookahead/research_runtime -q
test -f docs/research_runtime/SIGNAL_PROBE.md
# TARGET: alpha runtime run-signal-probe --study <study_run_spec_id>
```

A signal probe called strategy validation, or a same-bar optimistic fill, is a
global merge blocker.

## Cost stress workflow

The `CostModelVersion` and cost-stress runtime (`RT-P11`) consumes
`alpha_system.backtest.costs` and `backtest.slippage` to produce a
`CostSensitivityReport` across `base` / `stress_1` / `stress_2` / `double_cost`
profiles. BBO spread crossing is used where available; slippage is **labeled a
proxy**; session/ETH penalties apply. Zero-cost is diagnostic only and is never a
promotion basis. Cost stress (including the `double_cost` profile) is required
for any signal probe or handoff.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.cost"   # RT-P11
python -m pytest tests/unit/runtime/cost -q
test -f docs/research_runtime/COST_STRESS.md
# TARGET: alpha runtime run-cost-stress --study <study_run_spec_id>
```

Cost stress omitted for a probe or handoff, a slippage value not labeled a proxy,
or a zero-cost result used as a promotion basis, is a global merge blocker.

## Bounded grid workflow

The bounded-grid / `VariantBudget` guard (`RT-P13`) consumes
`alpha_system.experiments.limits` and `experiments.overfit_controls` to cap
variants, grid points, and compute, record the variant count, and forbid
selection on the locked test. A `BoundedGridSpec` with a `VariantBudget` is
required; there is no unbounded grid; a bounded grid is **not** promotion.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.grid"   # RT-P13
python -m pytest tests/unit/runtime/grid -q
test -f docs/research_runtime/BOUNDED_GRID.md
# TARGET: alpha runtime plan --study <study_run_spec_id> --variant-budget <n>
```

An unbounded grid, an exceeded variant budget, or selection on the locked test
without contamination metadata, is a global merge blocker.

## No-lookahead runtime audit

The `NoLookaheadRuntimeAudit` (`RT-P14`) fails closed on availability
(`available_ts`, `label_available_ts`), same-bar optimistic fill,
label-as-feature, centered/future live windows, and locked-test contamination
(locked-test partition use without governance metadata). It is the runtime's
point-in-time safety guard.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.audit"   # RT-P14
python -m pytest tests/unit/runtime/audit tests/no_lookahead/research_runtime -q
test -f docs/research_runtime/NO_LOOKAHEAD_AUDIT.md
# TARGET: alpha runtime run-diagnostics --study <study_run_spec_id> --audit
```

Any audited violation class is a global merge blocker. Locked-test partition use
without contamination metadata is specifically blocked.

## Evidence draft workflow

The `EvidenceDraft` builder (`RT-P16`) bundles diagnostics + cost summaries +
limitations + rejection/handoff state to **feed** the existing governance
`EvidenceBundle` (`alpha_system.governance.evidence_bundle`). It is an
evidence-input, **not** a candidate, and it does not re-implement
`EvidenceBundle`. Decision states and rejection visibility are provided by
`RT-P15` (`RejectionReasonRecord` + `REJECTED` / `INCONCLUSIVE` / `BLOCKED`,
never hidden).

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.decisions"   # RT-P15
python -c "import alpha_system.runtime.evidence"    # RT-P16
python -m pytest tests/unit/runtime/decisions tests/unit/runtime/evidence -q
test -f docs/research_runtime/DECISION_STATES.md
test -f docs/research_runtime/EVIDENCE_DRAFT.md
# TARGET: alpha runtime build-evidence-draft --study <study_run_spec_id>
```

An `EvidenceDraft` treated as a candidate, or a failed/inconclusive run hidden
(no `RejectionReasonRecord`), is a global merge blocker.

## Reference handoff workflow

The `ReferenceCandidateHandoff` builder (`RT-P17`) packages a survivor (report,
manifest, versions, cost profile, limitations, required next gate) for
conservative Reference validation — **handoff only**, never Reference validation
itself. The handoff must mark `strategy_not_validated` and set
`next_required_gate = REFERENCE_VALIDATION_REQUIRED`. The fast path is **not**
Reference truth. `REFERENCE_HANDOFF_READY` is the most advanced state any
survivor may reach.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.handoff"   # RT-P17
python -m pytest tests/unit/runtime/handoff -q
test -f docs/research_runtime/REFERENCE_HANDOFF.md
# TARGET: alpha runtime build-reference-handoff --study <study_run_spec_id>
```

A `ReferenceCandidateHandoff` treated as Reference validation, or the fast path
treated as Reference truth, is a global merge blocker.

## Runtime artifact inspection

`RuntimeArtifactManifest` (`RT-P05`) and `RuntimeCachePolicy` / runtime artifact
policy (`RT-P19`) govern what may be committed. Heavy outputs are local-only;
only small curated summaries are commit-eligible via `commit_allowed` flags.
Inspect that nothing heavy or value-bearing has leaked into the repo.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.artifact_policy"   # RT-P19
python -m pytest tests/unit/runtime/cache tests/unit/runtime/test_artifact_policy.py -q
test -f docs/research_runtime/CACHE_AND_ARTIFACTS.md
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
# TARGET: alpha runtime inspect --run <run_id>
```

A runtime heavy output staged, or any raw/canonical/feature/label/runtime value
committed, is a global merge blocker.

## Structured tool output inspection

The agent-facing `RuntimeToolResult` / `RuntimeRunSummary` contracts (`RT-P22`)
prepare structured outputs for the future Agent Factory **without creating any
autonomous agent**. A tool result carries `status`, `run_id`, version ids,
`diagnostics_summary`, `cost_summary`, `rejection_reasons`, `artifacts`, and
`next_required_gate` — and **no raw or heavy data**.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.tool_results"   # RT-P22
python -m pytest tests/unit/runtime/test_tool_results.py -q
test -f docs/research_runtime/TOOL_RESULTS.md
# TARGET: alpha runtime summarize --run <run_id>
```

Raw or heavy data in a tool response is a global merge blocker. The
`RuntimeReportCard` renderer and templates (`RT-P23`) produce human-readable,
non-promotional summaries; no heavy report bundle is committed.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.reports"   # RT-P23
python -m pytest tests/unit/runtime/test_reports.py -q
test -f docs/research_runtime/REPORTS.md
```

## Handoff validation

Every phase writes a commit-eligible handoff under
`handoffs/ALPHA_RESEARCH_RUNTIME_MVP/<PHASE_ID>.md` plus a local-only
`runs/<run_id>/phases/<phase_id>/handoff.md`. The handoff must list explicit
staged paths, record `git status --short`, document any skipped checks with the
reason, and state the artifact-policy result. A handoff that omits the explicit
file list or hides forbidden paths fails validation.

```bash
cd ~/projects/alpha_system
cat handoffs/ALPHA_RESEARCH_RUNTIME_MVP/<PHASE_ID>.md
ls runs/<run_id>/phases/<phase_id>/
```

A `BLOCKED` verdict, missing authorization, contradictory scope, or impossible
validation produces a **truthful** blocked handoff; dependent phases are blocked;
fake completion is forbidden.

## Claude review

Every YELLOW phase requires a fresh Claude Opus 4.8 xhigh review before merge;
the implementer cannot self-approve. The GREEN phase (`RT-P00`) does not require
review unless the phase requests it. The review writes
`runs/<run_id>/phases/<phase_id>/review.md` and `verdict.json` for local audit,
and a commit-eligible review under
`reviews/ALPHA_RESEARCH_RUNTIME_MVP/<PHASE_ID>/**` when commit-eligible. Allowed
verdicts: `PASS`, `PASS_WITH_WARNINGS`, `REWORK`, `BLOCKED`. Only `PASS` or
`PASS_WITH_WARNINGS` are merge-eligible.

Review must check: phase scope; runtime objects orchestrate existing primitives
and do not duplicate research/experiments/governance/backtest code; `AlphaSpec`
and `StudySpec` required before any runtime study runs; only accepted
DatasetVersions consumed via `resolve_dataset_version` with no raw provider
access; feature inputs carry `available_ts` and label inputs carry
`label_available_ts` with no label-as-feature; the no-lookahead runtime audit
covers `available_ts`, `label_available_ts`, same-bar fills, and locked-test
metadata; cost stress present for any probe or handoff with slippage labeled
proxy and `double_cost` present; variant budget enforced with no unbounded grid
and no locked-test selection; `EvidenceDraft` is not a candidate,
`ReferenceCandidateHandoff` is not Reference validation, and the fast path is not
Reference truth; failed and inconclusive runs remain visible with a
`RejectionReasonRecord`; agent-facing tool results carry no raw or heavy data;
DAG metadata correctness (parallel phases have disjoint `allowed_paths`, no
global files); serial merge queue respected with no phase-branch
`ACTIVE_CAMPAIGN.md` write in parallel mode; artifact policy compliance; no
broker/live/paper/order/account scope; no alpha/tradability/profitability claims
and no strategy/backtest/portfolio/alpha-search scope; no test weakening; handoff
completeness and semantic done criteria.

```bash
cd ~/projects/alpha_system
ls reviews/ALPHA_RESEARCH_RUNTIME_MVP/
cat runs/<run_id>/phases/<phase_id>/verdict.json
```

## Repair loop

A `REWORK` or check `FAIL` routes to the bounded repair loop
(`max_repair_attempts_default = 2`). Each attempt is recorded under
`runs/<run_id>/phases/<phase_id>/repair_attempts/`. Codex repairs only valid,
in-scope findings; it must not weaken tests or fake completion. Exceeding the
repair limit, contradictory scope, or repeated failure produces a truthful
blocked handoff and escalation rather than a fake pass.

```bash
cd ~/projects/alpha_system
ls runs/<run_id>/phases/<phase_id>/repair_attempts/
```

## STOP behavior

Create `runs/<run_id>/STOP` with a short reason. Ralph checks STOP before
provider calls, phase selection, Codex execution, validation, review, PR
creation, CI waiting, the merge gate, merge, the done-check, and next-phase
selection.

```bash
cd ~/projects/alpha_system
echo "operator stop: <reason>" > runs/<run_id>/STOP
```

In parallel mode, a STOP request halts new wave dispatch and pauses the serial
merge queue at the next checkpoint. In-flight worktree builds may finish their
current step, but no new phase is dispatched and no further merge proceeds while
STOP is active. `runs/**` is local-only and must never be staged or committed.
Codex must not ignore an active STOP file inside a Workflow 2 run. A STOP file
present is a global merge blocker.

## Resume behavior

Remove or resolve the STOP condition, then resume. Ralph resumes from recorded
run state and does not regenerate completed, merged work. In parallel mode it
re-derives ready waves from the DAG and the merge ledger rather than restarting
the campaign.

```bash
cd ~/projects/alpha_system
rm runs/<run_id>/STOP
# resume the live parallel run (only after a clean plan and prior mock):
# just frontier-run-parallel ALPHA_RESEARCH_RUNTIME_MVP 3
```

For a partially merged wave, resume continues from the serial merge queue
position; already-merged phases are not rebuilt.

## Blocked phase handling

A phase blocks on contradictory scope, repeated failure beyond the repair limit,
missing authorization, impossible validation, or a hard boundary violation
(external provider call attempted, raw provider data read by runtime code,
accepted DatasetVersion bypassed, runtime study run without `AlphaSpec` or
`StudySpec`, prohibited MVP state introduced, broker/live/paper/order/account or
strategy/backtest/portfolio/alpha-search scope introduced). The phase writes a
**truthful** blocked handoff with the exact command, failure, and reason; its
verdict is `BLOCKED`; and its dependents are blocked. Fake completion is never
allowed. A truthful `BLOCKED` is an acceptable terminal outcome and must not be
masked as a pass.

```bash
cd ~/projects/alpha_system
cat handoffs/ALPHA_RESEARCH_RUNTIME_MVP/<PHASE_ID>.md   # records BLOCKED reason
cat runs/<run_id>/phases/<phase_id>/verdict.json        # verdict == BLOCKED
```

## Artifact audit

`runs/**` is local-only runtime state and must never be staged or committed.
Raw, canonical, feature, label, and runtime values stay local-only under
`$ALPHA_DATA_ROOT`. Run this audit at preflight, before every merge, after the
real smoke (`RT-P21`), and at closeout.

```bash
cd ~/projects/alpha_system
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find metadata -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
# reject committed DB/log/heavy formats outside fixtures
git ls-files | grep -E '\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|dbn|zst|pkl|pickle|joblib|onnx|npy|npz|log)$' \
  | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"
```

If any forbidden path is staged, unstage it and repair the handoff before merge.
Stage explicit paths only; never `git add .` / `git add -A`. Never force push.
Tiny synthetic documented fixtures under `tests/fixtures/runtime/**` are the only
data-like exception, and they must be `<1MB`, synthetic, and never alpha
evidence.

## Final closeout

Closeout runs in wave w4: `RT-P21` (Small Real FLF DatasetVersion Runtime Smoke,
runs alone), `RT-P24` (Workflow 2 DAG Integration and Parallel Plan, runs
alone), `RT-P25` (End-to-End Runtime Dry Run, runs alone), and `RT-P26`
(Acceptance Audit and Closeout, runs alone). The real smoke and the e2e dry run
make **no external provider call** — the DatasetVersion is already local and
accepted, and the e2e path runs on synthetic fixtures.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.smoke"     # RT-P21
python -c "import alpha_system.runtime.dry_run"   # RT-P25
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/integration/runtime -q
python tools/hooks/canary_runner.py
python tools/frontier/ralph_driver.py plan-dag --campaign-id ALPHA_RESEARCH_RUNTIME_MVP   # RT-P24
test -f docs/research_runtime/REAL_SMOKE.md
test -f docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md
test -f docs/research_runtime/E2E_DRY_RUN.md
test -f docs/research_runtime/ACCEPTANCE_AUDIT.md
test -f campaigns/ALPHA_RESEARCH_RUNTIME_MVP/CLOSEOUT.md
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
# TARGET: alpha runtime replay-summary --run <run_id>
```

At closeout: run the small real local DatasetVersion smoke (no external pull);
run the synthetic end-to-end dry run (resolve → diagnostics → probe → cost stress
→ evidence draft → reference handoff); run the acceptance audit across all six
gates (`campaign_bootstrap`, `runtime_contracts`, `diagnostics_runtime`,
`runtime_integration`, `tests_tools_docs`, `workflow_and_closeout` — see
`ACCEPTANCE.md`); run the final semantic done-check; write
`campaigns/ALPHA_RESEARCH_RUNTIME_MVP/CLOSEOUT.md` with the final verdict
(`COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`); update `ACTIVE_CAMPAIGN.md`
(coordinator-only); and add durable lessons to `project-skill` when applicable.
The campaign is done only when all gates pass (or a truthful `BLOCKED` is
recorded), the artifact audit is clean, no prohibited MVP runtime state is
reachable, and no alpha/tradability/profitability/strategy/paper/live/broker/
production claim exists.

## Next campaign readiness for Agent Factory

This campaign is the executable research loop layer that the future
`ALPHA_AGENT_FACTORY_MVP` consumes: future AI Alpha Researchers will drive the
runtime through the agent-facing `RuntimeToolResult` / `RuntimeRunSummary`
contracts (`RT-P22`) and the `alpha runtime` CLI surface (`RT-P18`), turning an
approved `AlphaSpec` + `StudySpec` into diagnostics, cost stress, a bounded
probe, an `EvidenceDraft`, and a `ReferenceCandidateHandoff`. The runtime
**prepares** those tool contracts without creating any autonomous agent.

Roadmap: Data Foundation → Feature/Label Foundation → **Research Runtime** →
Agent Factory → Core Alpha → Strategy/Portfolio. Readiness for the Agent Factory
means the executable, governed, point-in-time-safe research runtime exists and is
wired to consume the Feature/Label substrate; it does **not** mean any signal is
alpha, profitable, tradable, strategy-ready, production-ready, or
paper/live/broker-ready. Each downstream campaign proceeds only under its own
authorized contract. Use precise wording: a diagnostic PASS is not alpha
validation, a signal probe is not a strategy candidate, a bounded grid is not
promotion, an `EvidenceDraft` is not a candidate, a `ReferenceCandidateHandoff`
is not Reference validation, and the fast path is not Reference truth.

---

*This file is a campaign contract describing the intended Workflow 2 operating
procedure and boundaries for `ALPHA_RESEARCH_RUNTIME_MVP`; it makes no alpha,
tradability, profitability, or production claim.*
</content>
</invoke>
