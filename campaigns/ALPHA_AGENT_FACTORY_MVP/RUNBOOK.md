# ALPHA_AGENT_FACTORY_MVP Runbook

## Runbook purpose

This runbook is the operator manual for executing the `ALPHA_AGENT_FACTORY_MVP`
campaign under Frontier Harness Generic v3.0 Workflow 2 with the DAG-wave
parallel scheduler. It covers preflight, the contracts-only posture, the four
preflight gates, the accepted-DatasetVersion consumption boundary, the
no-raw-data / no-external-provider boundary, the DAG wave plan, the
parallel-mock-then-parallel-live protocol, the serial merge queue, the role /
permission-matrix / tool-contract / separation-of-duties / research-queue /
runtime-bridge validations, the bounded non-alpha dry-run, the
memory / rejected-idea validation, handoff validation, Claude review, the bounded
repair loop, STOP and resume in parallel mode, blocked-phase handling, the
artifact audit, closeout, and next-campaign readiness for
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`.

This campaign builds the **controlled AI Alpha Research Team contract layer** over
the completed Governance + Feature/Label + Research Runtime stack
(`ALPHA_RESEARCH_GOVERNANCE_MVP`, `ALPHA_FEATURE_LABEL_FOUNDATION_V1` 32/32
`COMPLETE_WITH_WARNINGS`, `ALPHA_RESEARCH_RUNTIME_MVP` 27/27
`COMPLETE_WITH_WARNINGS`, and `POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1`).
It defines, as **contracts only**, the agent role model, permission matrix, tool
contracts, research queue, separation-of-duties enforcement, agent/decision/
handoff records, rejected-idea memory, prompt assets, a runtime tool integration
bridge, and a bounded non-alpha dry-run harness — by **driving existing
primitives** (`alpha_system.runtime.tool_results`, `alpha_system.cli.runtime`,
`alpha_system.governance.*`, `alpha_system.data.foundation.version_registry.resolve_dataset_version`),
never re-implementing or editing them. It does **not** instantiate any autonomous
agent, does **not** start a continuous research runner, does **not** conduct
alpha search, does **not** promote a factor, does **not** validate a strategy,
does **not** call Databento or IBKR, and does **not** pull or commit
raw/canonical/feature/label/runtime/agent values. State it plainly and keep it
true: an agent dry-run success is not alpha; an agent-drafted `AlphaSpec` is not
implementation approval; a runtime diagnostic PASS is not factor promotion; an
`EvidenceDraft` is not a candidate; a `ReferenceCandidateHandoff` is not Reference
validation; validated research is not paper/live approval. Agent Factory is
**not** Core Alpha Pilot, **not** the Agent Research Runner, **not** a Factor
Library, **not** Strategy Reference Validation, **not** a Portfolio AlphaBook, and
**not** paper/live/broker execution.

This campaign has **exactly 26 phases** `AGENT-P00 … AGENT-P25`. `AGENT-P00` is
GREEN (campaign bootstrap / docs, no Claude review). The other 25 are YELLOW
(material Agent Factory contract engineering with fresh Claude Opus 4.8 xhigh
review and auto-merge through the serial merge queue). This campaign has **no
RED-lane phases** and makes **no external provider calls**: all consumption is
local-only against accepted DatasetVersions, the seed FeaturePack/LabelPack, and
runtime structured outputs. The RED lane definition is retained for harness
completeness only.

The contracts this campaign defines must enforce the agent-research lifecycle
`RESEARCH_TASK_QUEUED → DIRECTOR_SCOPED → HYPOTHESIS_DRAFTED → ALPHASPEC_DRAFTED
→ ALPHASPEC_CRITIQUED (→ ALPHASPEC_REVISION_REQUESTED / ALPHASPEC_REJECTED) →
DATA_CONTRACT_AUDITED (→ INPUTS_BLOCKED) → IMPLEMENTATION_SCOPED →
DIAGNOSTICS_REQUESTED → DIAGNOSTICS_COMPLETE → NO_LOOKAHEAD_AUDITED →
STATISTICAL_REVIEW_{PASS|WATCH|REJECT|INCONCLUSIVE} → EVIDENCE_DRAFT_RECORDED →
REFERENCE_HANDOFF_RECORDED → LIBRARIAN_MEMORY_RECORDED`, with terminal `REJECTED`,
`INCONCLUSIVE`, and `BLOCKED`. `REFERENCE_HANDOFF_RECORDED` is the most advanced
forward state any dry-run survivor may reach. The states `ALPHA_VALIDATED`,
`FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`, `CANDIDATE_PROMOTED`,
`LIVE_READY`, `PAPER_READY`, `PROFITABLE`, `TRADABLE`, `PRODUCTION_READY`, and
`AUTONOMOUS_RESEARCH_RUNNING` are **prohibited MVP states** and must never be
reachable by any transition the contracts define.

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
  cover every phase (`AGENT-P00 … AGENT-P25`) in exactly one acceptance gate? If
  not, block.
* Is this campaign **contracts only**? No autonomous agent may be instantiated
  and no continuous research runner may be created. If a phase introduces an
  agent loop or a continuous runner, STOP and escalate.
* Do `ALPHA_RESEARCH_RUNTIME_MVP` (the runtime + agent-facing
  `RuntimeToolResult` / `RuntimeRunSummary`) and the governance primitives exist
  on `main`? Agent Factory **drives** them; it does not rebuild them. If a
  baseline item is not-on-`main`, treat it as a dependency warning and proceed
  only against the on-`main` state; the contract is still valid.
* Is any forbidden artifact already staged (raw/canonical data, feature or label
  values, runtime/agent heavy outputs, parquet/arrow/feather/dbn/zst, DB/WAL,
  provider response)? If so, unstage before starting.
* Is any broker / order / account / paper / live / strategy / backtest /
  portfolio / alpha-search / factor-promotion / autonomous-runner scope present
  anywhere? If so, STOP and escalate.
* Has `just frontier-plan` been run for this campaign, and has a
  `frontier-run-parallel-mock` completed before any first live parallel run? If
  not, do those first (DAG wave plan + parallel mock sections below).

### Smoke preflight

```bash
cd ~/projects/alpha_system
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
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
present, the root `ACTIVE_CAMPAIGN.md` must point to this campaign, and there must
be **no** campaign-local `ACTIVE_CAMPAIGN.md` (the pointer is coordinator-owned).

```bash
cd ~/projects/alpha_system
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/GOAL.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/ACCEPTANCE.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/RISK_REGISTER.md
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/RUNBOOK.md
test '!' -f campaigns/ALPHA_AGENT_FACTORY_MVP/ACTIVE_CAMPAIGN.md
grep -q "ALPHA_AGENT_FACTORY_MVP" ACTIVE_CAMPAIGN.md
```

The six `test -f` campaign-file checks above are the `AGENT-P00` bootstrap gate.
The `test '!' -f` assertion guarantees no campaign-local `ACTIVE_CAMPAIGN.md`
exists, and the `grep -q` confirms the root pointer references this campaign.

## YAML parse

The campaign YAML must parse, identify itself, list 26 phases `AGENT-P00 …
AGENT-P25`, declare the DAG-wave scheduler, and cover the phase set with its six
acceptance gates exactly once. The assertion below also confirms there is no RED
phase and that the lane shape is `AGENT-P00` GREEN with the rest YELLOW.

```bash
cd ~/projects/alpha_system
python - <<'PY'
from pathlib import Path
import yaml
data = yaml.safe_load(
    Path("campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml").read_text()
)
assert data["campaign_id"] == "ALPHA_AGENT_FACTORY_MVP"
phases = data["phases"]
assert phases, "no phases"
assert "acceptance_gates" in data and data["acceptance_gates"], "no acceptance_gates"
wf2 = data["workflow2"]
assert wf2["scheduler"]["mode"] == "dag_wave", "scheduler.mode must be dag_wave"
assert wf2["scheduler"]["parallel_execution"] is True
assert wf2["scheduler"]["merge_queue"] == "serial"
assert wf2["scheduler"]["max_parallel_phases"] == 3
assert wf2["scheduler"]["update_active_campaign"] == "coordinator_only"
phase_ids = [ph["id"] for ph in phases]
expected = [f"AGENT-P{n:02d}" for n in range(26)]
assert phase_ids == expected, f"expected AGENT-P00..AGENT-P25, found {phase_ids}"
assert len(phase_ids) == 26, f"expected 26 phases, found {len(phase_ids)}"
# lanes: AGENT-P00 GREEN, all others YELLOW, no RED
lanes = {ph["id"]: ph["lane"] for ph in phases}
assert lanes["AGENT-P00"] == "GREEN", "AGENT-P00 must be GREEN"
assert all(lanes[p] == "YELLOW" for p in phase_ids if p != "AGENT-P00"), "non-P00 must be YELLOW"
red = {ph["id"] for ph in phases if ph["lane"] == "RED"}
assert red == set(), f"unexpected RED phases: {red}"
# acceptance-gate coverage: each phase in exactly one gate
gates = data["acceptance_gates"]
expected_gates = {
    "bootstrap_and_entry": ["AGENT-P00", "AGENT-P01", "AGENT-P02"],
    "core_contracts": ["AGENT-P03", "AGENT-P04", "AGENT-P05", "AGENT-P06"],
    "agent_roles": ["AGENT-P07", "AGENT-P08", "AGENT-P09", "AGENT-P10",
                    "AGENT-P11", "AGENT-P12", "AGENT-P13", "AGENT-P14", "AGENT-P15"],
    "enforcement_and_records": ["AGENT-P16", "AGENT-P17", "AGENT-P18"],
    "assets_and_bridge": ["AGENT-P19", "AGENT-P20", "AGENT-P21"],
    "dry_run_and_closeout": ["AGENT-P22", "AGENT-P23", "AGENT-P24", "AGENT-P25"],
}
covered = []
for name, spec in gates.items():
    covered.extend(spec.get("phases", []))
assert set(phase_ids) == set(covered), "acceptance gate coverage mismatch"
assert len(covered) == len(set(covered)), "phase covered by more than one gate"
for name, want in expected_gates.items():
    assert name in gates, f"missing acceptance gate: {name}"
    assert gates[name]["phases"] == want, f"gate {name} phases mismatch"
assert set(gates) == set(expected_gates), "acceptance gate set mismatch"
print(
    f"OK: {len(phase_ids)} phases AGENT-P00..AGENT-P25; dag_wave + serial merge "
    f"(max_parallel=3, coordinator_only); P00 GREEN, rest YELLOW, no RED; "
    f"{len(gates)} gates cover phase set exactly once"
)
PY
```

## DAG wave plan check (frontier-plan)

Before any execution, run the read-only DAG plan. It prints the dependency graph,
ready waves, run-alone phases, and any path / resource conflict. A phase is
parallel-safe only if `parallel_safe: true` **and** `must_run_alone: false`
**and** it has disjoint `allowed_paths` **and** touches no global/coordinator file
(`ACTIVE_CAMPAIGN.md`, shared `roles/__init__.py`, `roles/registry.py`) **and** is
not RED. A phase that omits `parallel_safe: true` or `allowed_paths` runs alone.

```bash
cd ~/projects/alpha_system
just frontier-plan ALPHA_AGENT_FACTORY_MVP
```

Intended wave shape for this campaign (waves w0–w4; `just frontier-plan` previews
the exact computed waves, and at `max_parallel_phases: 3` each parallel group is
split into sub-waves of three):

```text
w0  AGENT-P00..AGENT-P06  sequential bootstrap + core contracts (each runs alone)
w1  AGENT-P07..AGENT-P15  PARALLEL role contracts (disjoint allowed_paths)
w2  AGENT-P16..AGENT-P18  sequential enforcement / records / memory (each runs alone)
w3  AGENT-P19,AGENT-P20,AGENT-P21  PARALLEL assets + runtime bridge (disjoint allowed_paths)
w4  AGENT-P22..AGENT-P25  sequential dry-run + closeout (each runs alone)
```

Only `AGENT-P07..AGENT-P15` and `AGENT-P19,AGENT-P20,AGENT-P21` are parallel-safe;
all other phases run alone. Parallel waves build concurrently in isolated
worktrees, capped at `max_parallel_phases = 3`. Verify in the plan output that
every parallel phase in a wave has disjoint `allowed_paths`, that the role phases
do not edit `roles/__init__.py` or `roles/registry.py`, and that no parallel phase
writes a global file. If the plan reports a path or resource conflict, that wave
does not run in parallel.

## Parallel mock run

Run the parallel mock at least once before the first live parallel run. The mock
exercises the DAG-wave scheduler, worktree isolation, and the serial merge queue
with **no providers, no network, and no merge** (`FRONTIER_MOCK_PROVIDERS`).

```bash
cd ~/projects/alpha_system
just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3
```

Confirm from the mock output that waves form as expected (w0 sequential; w1 the
nine role phases in parallel sub-waves of three; w2 sequential; w3 the three
assets/bridge phases in parallel; w4 sequential), that parallel phases build
concurrently in separate worktrees, and that merges are serialized one PR at a
time. The mock must not call Databento or IBKR and must not create real PRs or
merges.

## Parallel live run

After a clean plan and a successful mock, the live parallel run executes
concurrently in isolated worktrees with a serial merge queue. This is the default
execution path for this campaign.

```bash
cd ~/projects/alpha_system
# Live DAG-wave parallel run (concurrent build in isolated worktrees, serial merge).
# Run only after `just frontier-plan` is clean and a parallel mock has passed.
# just frontier-run-parallel ALPHA_AGENT_FACTORY_MVP 3
```

The live run still makes **no external provider calls** — every phase consumes
local accepted DatasetVersions, the local seed packs, or synthetic fixtures.
`max_parallel = 3` matches `workflow2.scheduler.max_parallel_phases`. Phase
branches use the `auto/` branch prefix. Build is parallel; **merge is always
serial** (`merge_queue: serial`). The coordinator merges one PR at a time,
re-validating the merge gate against the freshly updated `main` before each merge,
and **only the coordinator updates `ACTIVE_CAMPAIGN.md`**
(`update_active_campaign: coordinator_only`). A phase branch that writes
`ACTIVE_CAMPAIGN.md` in parallel mode, or a merge outside the serial queue, is a
global blocker.

## Preflight gate checks

The Agent Factory entry contract (`AGENT-P01`,
`alpha_system.agent_factory.entry_contract`) encodes **four** preflight gates and
fails closed on missing prerequisites, returning a structured
`PREFLIGHT_PASS` / `PREFLIGHT_WARN` / `PREFLIGHT_BLOCKED`. The seed packs and
local registries are local-only under `$ALPHA_DATA_ROOT`; absent in a clean
checkout / CI, so the entry contract degrades to a truthful warning rather than a
hard crash.

1. **Seed FeaturePack/LabelPack exists** — a real seed FeaturePack/LabelPack is
   registered locally under `$ALPHA_DATA_ROOT/registry/{features,labels}.sqlite`.
2. **Runtime real smoke PASS** — `real_dataset_version_smoke_ran: true`, proven
   by `POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1` over the Databento
   canonical TRADES ES/NQ/RTY 1-min 2024 seed window
   (`dsv_databento_ohlcv_05404069799decb0`), seed features `returns` /
   `log_returns` / `rolling_volatility` / `rolling_range` / `volume_zscore` /
   `range_position`, seed labels `fwd_ret_5m` / `fwd_ret_10m` / `fwd_ret_30m`.
3. **`FEATURE_LABEL_PARQUET_SINK_V1` status** — named follow-up (ADR-0006 /
   `decisions/0006-feature-label-value-storage.md`); large-scale value-consuming
   studies are blocked until it lands or a human explicitly approves.
4. **`SESSION_LABEL_GUARD_FIX_V1` status** — named follow-up; session-context
   features (`rth_flag` / `eth_flag` / `session_minute`) are blocked because the
   runtime guard `_reject_label_as_live_feature` in `runtime/input_resolver.py`
   false-positives on the canonical `session_label` field.

```bash
cd ~/projects/alpha_system
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
python -c "import alpha_system.agent_factory.entry_contract"   # AGENT-P01
python -m pytest tests/unit/agent_factory/test_entry_contract.py -q
test -f docs/agent_factory/PREFLIGHT_GATES.md

# Heuristic local checks for gate 1 (seed FeaturePack/LabelPack registries):
ls "$ALPHA_DATA_ROOT/registry/features.sqlite" 2>/dev/null \
  || echo "note: no local FeaturePack registry; entry contract degrades to PREFLIGHT_WARN"
ls "$ALPHA_DATA_ROOT/registry/labels.sqlite" 2>/dev/null \
  || echo "note: no local LabelPack registry; entry contract degrades to PREFLIGHT_WARN"

# TARGET: alpha agent preflight                                 (AGENT-P01 entry surface, not yet built)
# TARGET: alpha agent preflight --gate seed-packs
# TARGET: alpha agent preflight --gate runtime-real-smoke
# TARGET: alpha agent preflight --gate parquet-sink
# TARGET: alpha agent preflight --gate session-label-guard
```

The entry contract must fail closed (`PREFLIGHT_BLOCKED`) on a genuinely
unsatisfiable prerequisite and must never report a gate as satisfied when it is
not. A large-scale value-consuming study before `FEATURE_LABEL_PARQUET_SINK_V1`,
or a session-context feature before `SESSION_LABEL_GUARD_FIX_V1`, is a global
merge blocker.

## Accepted DatasetVersion check

Agents consume **only accepted DatasetVersions**, never raw provider files.
Admissibility is a DatasetVersion lifecycle state in
`{VERSIONED, READY_FOR_RESEARCH}`. The sanctioned consumption API is
`alpha_system.data.foundation.version_registry.resolve_dataset_version`, which
returns DatasetVersion metadata; canonical records are reconstructed through
`CanonicalBarRecord`, `CanonicalBBORecord`, and `DenseGridBarRecord`. Databento is
the primary deep-history research source; IBKR is broker-source recent validation
only; the two are never merged. The dataset registry is local-only under
`$ALPHA_DATA_ROOT/registry/datasets.sqlite`, and it persists report **hashes**,
not full report objects (the rehydration gap in `docs/STRUCTURAL_BACKLOG.md`);
agents must use registry/runtime tools and respect that gap, not bypass
accepted-DatasetVersion policy.

```bash
cd ~/projects/alpha_system
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
# registry DB is local-only under $ALPHA_DATA_ROOT/registry/datasets.sqlite
ls "$ALPHA_DATA_ROOT/registry/datasets.sqlite" 2>/dev/null \
  || echo "note: no local dataset registry yet; agent_factory tests use synthetic fixtures"
python -c "import alpha_system.data.foundation.version_registry as vr; print(vr.resolve_dataset_version.__name__)"

# TARGET: alpha agent resolve-dataset-version --id <dsv_id>     (Data Contract Auditor surface, not yet built)
```

The Data Contract Auditor role contract (`AGENT-P10`) resolves inputs through
`resolve_dataset_version` and must report inputs available/blocked; it must never
access raw provider data, write registries, or bypass accepted-DatasetVersion
policy. An agent input produced without resolving an admissible DatasetVersion is
a global merge blocker.

## No raw data / no external provider check

It is forbidden for any `agent_factory` code to read `.dbn`, `.zst`, parquet,
arrow, or feather files directly, to import a data provider, or to call Databento
or IBKR. Diagnostics are reached **only** through the runtime tool surface; the
single bridge (`runtime_bridge.py`) imports the runtime and never edits it.

```bash
cd ~/projects/alpha_system
# heuristic scan: no provider imports or raw/file readers in agent_factory code
grep -REn "\.dbn|\.zst|read_parquet|to_parquet|pyarrow|databento|ib_insync|ibapi|\.feather|\.arrow" \
  src/alpha_system/agent_factory 2>/dev/null \
  | grep -v "resolve_dataset_version\|from_mapping" \
  || echo "no direct provider/file readers found in agent_factory code"

# heuristic scan: agent_factory does not edit the consumed primitive packages
grep -REn "^from alpha_system\.(runtime|governance|research|experiments|backtest|features|labels|data)|^import alpha_system\.(runtime|governance|research|experiments|backtest|features|labels|data)" \
  src/alpha_system/agent_factory 2>/dev/null \
  | head -20 \
  || echo "note: agent_factory imports (consumes) primitives; it must not EDIT those packages"
```

`agent_factory` **imports** (consumes) `runtime.*`, `governance.*`, `research.*`,
`experiments.*`, `backtest.*`, `features.*`, `labels.*`, and `data.foundation.*`,
but must never **edit** them — they sit in every phase's `forbidden_paths`. If
`agent_factory` code reads raw provider data, calls an external provider, bypasses
`resolve_dataset_version` or the runtime input resolver, or edits a consumed
package, that is a global merge blocker: `block_merge_and_escalate` /
`block_merge_and_repair`.

## Role contract / permission matrix / tool contract validation

The core contracts (`AGENT-P03`–`AGENT-P05`) define the `AgentRole` model +
discovery-based registry, the fail-closed permission matrix
(`ToolPermission` / `DataPermission` / `WritePermission` / `ReviewPermission` /
`PromotionPermission` / `HumanApprovalRequired` / `RedLaneRequired`), and the
agent-facing tool contract registry whose `AgentToolResult` carries only
structured, value-free fields. Every roster role must have an explicit
permission-matrix entry; default-deny / fail-closed.

```bash
cd ~/projects/alpha_system
# Role contract model + registry (AGENT-P03)
python -c "import alpha_system.agent_factory.roles.contracts, alpha_system.agent_factory.roles.registry"
python -m pytest tests/unit/agent_factory/roles -q
# Permission matrix (AGENT-P04)
python -c "import alpha_system.agent_factory.permissions.model, alpha_system.agent_factory.permissions.matrix"
python -m pytest tests/unit/agent_factory/permissions -q
# Tool contract registry + structured outputs (AGENT-P05)
python -c "import alpha_system.agent_factory.tools.contracts, alpha_system.agent_factory.tools.registry, alpha_system.agent_factory.tools.results"
python -m pytest tests/unit/agent_factory/tools -q
test -f docs/agent_factory/ROLES.md
test -f docs/agent_factory/PERMISSIONS.md
test -f docs/agent_factory/TOOLS.md
```

The permission matrix tests must assert: every roster role
(Research Director, Hypothesis Scout, AlphaSpec Critic, Data Contract Auditor,
Feature Engineer, Label Engineer, No-Lookahead Auditor, Diagnostics Runner,
Statistical Reviewer, Librarian) has explicit
`ToolPermission`/`DataPermission`/`WritePermission`/`ReviewPermission`/`PromotionPermission`
entries; no role may receive raw data; no role may write a registry directly; and
`HumanApprovalRequired`/`RedLaneRequired` flags are respected. The
`AgentToolResult` carries only `status`, `role`, `request_id`, `alpha_spec_id`,
`study_spec_id`, `dataset_version_id`, `feature_pack_refs`, `label_pack_refs`,
`runtime_run_id`, `diagnostics_summary`, `cost_summary`, `rejection_reasons`,
`blocking_findings`, `next_required_gate`, `artifacts`, and `limitations`, and
**rejects** raw or heavy payloads. A role without a permission-matrix entry, or a
tool result that embeds raw/heavy data, is a global merge blocker.

The ten MVP role contracts (`AGENT-P07`–`AGENT-P15`) each register additively via
the `AGENT-P03` registry in disjoint files (no edits to `roles/__init__.py` or
`roles/registry.py`):

```bash
cd ~/projects/alpha_system
for role in research_director hypothesis_scout alpha_spec_critic data_contract_auditor \
            feature_engineer label_engineer no_lookahead_auditor diagnostics_runner \
            statistical_reviewer librarian; do
  python -c "import alpha_system.agent_factory.roles.$role" \
    && echo "role import OK: $role" \
    || echo "role import MISSING: $role (not yet built)"
done
python -m pytest tests/unit/agent_factory/roles -q
```

## Separation-of-duties validation

`AGENT-P16` assembles all role contracts into the registry + permission matrix
(`separation/wiring.py`, the only module that imports all roles) and enforces
separation of duties in code, fail-closed (`separation/enforcement.py`). The
rules: **generator cannot approve** (the drafter cannot approve its own
`AlphaSpec`); **implementer cannot review** its own work; **diagnostics runner
cannot promote**; **reviewer is not the implementer**; **librarian cannot write a
registry without a reviewer verdict**; and the human owns risk/capital/live
judgment.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.agent_factory.separation.enforcement, alpha_system.agent_factory.separation.wiring"
python -m pytest tests/unit/agent_factory/separation -q
test -f docs/agent_factory/SEPARATION_OF_DUTIES.md
```

The enforcement tests must prove each separation rule **fails closed** and that
wiring registers all ten roles. A generator approving its own spec, an
implementer reviewing its own work, a diagnostics runner promoting, a reviewer
who is the implementer, or a librarian writing a registry without a verdict is a
global merge blocker (`block_merge_and_rework`).

## Research queue validation

`AGENT-P06` defines the bounded research-queue / work-item contracts that scope
agent work **without** becoming a continuous autonomous runner (that is
`ALPHA_AGENT_RESEARCH_RUNNER_V1`): `ResearchQueue`, `ResearchTask`,
`AgentAssignment`, `ResearchBudget`, `VariantBudget`, `ComputeBudget`,
`ReviewRequirement`, `BlockerRecord`, `QueuePriorityPolicy`, `FamilyBudgetPolicy`
(task status, allowed alpha family, allowed DatasetVersion/FeaturePack/LabelPack,
allowed/blocked partitions, max variants, max runtime budget, required reviews,
retry policy, rejection reason, next action).

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.agent_factory.queue.models"
python -m pytest tests/unit/agent_factory/queue -q
test -f docs/agent_factory/RESEARCH_QUEUE.md
test -f templates/agent_factory/research_task.template.yaml
```

The contract must be **single-task-bounded** (no daily/weekly loop), bound
variants and runtime via budgets, and carry allowed/blocked partitions plus
required reviews. A continuous-runner / autonomous-loop shape introduced here is a
global blocker (`block_merge_and_escalate`).

## Runtime bridge validation

`AGENT-P21` implements the single `runtime_bridge.py` — the **only** place that
imports the runtime tool surface. It adapts
`alpha_system.runtime.tool_results.RuntimeToolResult` /
`RuntimeRunSummary` into the value-free `AgentToolResult` shape, resolves inputs
through `resolve_dataset_version`, embeds no raw/heavy data, and **imports** the
runtime — never edits it.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.runtime.tool_results"          # consumed contract surface
python -c "import alpha_system.agent_factory.runtime_bridge"  # AGENT-P21
python -m pytest tests/unit/agent_factory/test_runtime_bridge.py -q
test -f docs/agent_factory/RUNTIME_BRIDGE.md
# TARGET: alpha agent run-diagnostics --study <study_spec_id>  (Diagnostics Runner via bridge, not yet built)
```

The bridge tests must assert that mapped `AgentToolResult`s contain no raw/heavy
data and that `src/alpha_system/runtime/**` is not modified. Agent code that
performs diagnostics directly instead of through the runtime tool surface, or that
edits the runtime package, is a global merge blocker.

## Dry-run procedure

The dry-run proves **machinery, not alpha**: role routing, tool contracts,
permissions, handoffs, and rejection memory. It uses synthetic fixtures (and the
local seed packs when present); a seed-pack/synthetic dry-run is **not** alpha
evidence.

The bounded non-alpha dry-run harness (`AGENT-P22`,
`dry_run/harness.py`) orchestrates the lifecycle on synthetic fixtures: Director
scopes a tiny `ResearchTask` → Hypothesis Scout drafts 3–5 `AlphaSpec` drafts →
AlphaSpec Critic rejects/revises most → Data Contract Auditor checks seed
availability → Feature/Label Engineer reference a bounded approved input →
Diagnostics Runner invokes the runtime **via the bridge** → No-Lookahead Auditor
reviews → Statistical Reviewer issues REJECT/WATCH/INCONCLUSIVE → Librarian
records rejection memory. **No promotion** is reachable.

```bash
cd ~/projects/alpha_system
# Synthetic dry-run unit harness (AGENT-P22)
python -c "import alpha_system.agent_factory.dry_run.harness"
python -m pytest tests/unit/agent_factory/dry_run -q
test -f docs/agent_factory/DRY_RUN.md

# Seed-pack / synthetic integration dry run (AGENT-P23) — degrades to synthetic
# fixtures when $ALPHA_DATA_ROOT / seed registries are absent.
export ALPHA_DATA_ROOT=~/alpha_data/alpha_system
python tools/verify.py --all
python -m pytest tests/integration/agent_factory -q
test -f docs/agent_factory/DRY_RUN_RESULTS.md

# TARGET: alpha agent dry-run --task <task_id> --synthetic        (not yet built)
# TARGET: alpha agent dry-run --task <task_id> --seed-pack <pack_id>
```

`DRY_RUN.md` and `DRY_RUN_RESULTS.md` must state explicitly that the run is **not
alpha evidence**, record limitations, and record a truthful `PASS_WITH_WARNINGS`
when local seed registries are absent. A dry-run treated as alpha evidence, an
`EvidenceDraft` treated as a candidate, or a `ReferenceCandidateHandoff` treated
as Reference validation is a global merge blocker (`block_merge_and_rework`).

## Memory / rejected-idea validation

`AGENT-P17` defines the agent record contracts (`AgentRunRecord`,
`AgentDecisionRecord`, `AgentHandoff`, `ToolInvocationRecord`, `AgentAuditLog`,
`AgentPromptVersion`, `AgentRoleVersion`, `AgentPermissionVersion`). `AGENT-P18`
defines rejected-idea + research memory (`RejectedIdeaMemoryRecord`,
`ResearchMemoryRecord`) that consume `governance.rejected_idea` /
`ResearchGraveyardLedger`, keep failures visible, avoid duplicate idea churn, and
surface prior rejection reasons.

```bash
cd ~/projects/alpha_system
# Records (AGENT-P17)
python -c "import alpha_system.agent_factory.records.models"
python -m pytest tests/unit/agent_factory/records -q
test -f docs/agent_factory/HANDOFFS.md
# Rejected-idea + research memory (AGENT-P18)
python -c "import alpha_system.agent_factory.memory.models"
python -c "import alpha_system.governance.rejected_idea"   # consumed (RejectedIdeaRecord/ResearchGraveyardLedger)
python -m pytest tests/unit/agent_factory/memory -q
test -f docs/agent_factory/REJECTION_MEMORY.md
```

The memory contracts must **consume** (not duplicate) the governance graveyard,
detect duplicate ideas on synthetic fixtures, and surface prior rejection reasons.
A failed or rejected idea hidden instead of recorded with a
`RejectedIdeaMemoryRecord`/`RejectionReasonRecord` is a global merge blocker.

## Handoff validation

Every phase writes a commit-eligible handoff under
`handoffs/ALPHA_AGENT_FACTORY_MVP/<PHASE_ID>.md` plus a local-only
`runs/<run_id>/phases/<phase_id>/handoff.md`. The handoff must list explicit
staged paths, record `git status --short`, document any skipped checks with the
reason, and state the artifact-policy result. A handoff that omits the explicit
file list or hides forbidden paths fails validation.

```bash
cd ~/projects/alpha_system
cat handoffs/ALPHA_AGENT_FACTORY_MVP/<PHASE_ID>.md
ls runs/<run_id>/phases/<phase_id>/
```

A `BLOCKED` verdict, missing authorization, contradictory scope, or impossible
validation produces a **truthful** blocked handoff; dependent phases are blocked;
fake completion is forbidden.

## Claude review

Every YELLOW phase requires a fresh Claude Opus 4.8 xhigh review before merge; the
implementer cannot self-approve. The GREEN phase (`AGENT-P00`) does not require
review unless the phase requests it. The review writes
`runs/<run_id>/phases/<phase_id>/review.md` and `verdict.json` for local audit,
and a commit-eligible review under `reviews/ALPHA_AGENT_FACTORY_MVP/<PHASE_ID>/**`
when commit-eligible. Allowed verdicts: `PASS`, `PASS_WITH_WARNINGS`, `REWORK`,
`BLOCKED`. Only `PASS` or `PASS_WITH_WARNINGS` are merge-eligible.

Review must check: phase scope; that `agent_factory` contracts **drive** the
existing runtime/governance/registry primitives and do not duplicate or edit them;
that **no autonomous agent is instantiated** and no continuous research runner is
created (contracts only); that every agent role has explicit
`ToolPermission`/`DataPermission`/`WritePermission`/`ReviewPermission`/`PromotionPermission`
entries; that separation of duties holds (generator cannot approve, implementer
cannot review, diagnostics runner cannot promote, reviewer is not the
implementer, librarian cannot write a registry without a verdict); that all
agent-facing tool contracts produce structured, value-free outputs and never
embed raw or heavy data; that tools consume the runtime via
`RuntimeToolResult`/`RuntimeRunSummary` and `resolve_dataset_version` with no raw
provider access and no external provider calls; that the four preflight gates are
present (seed FeaturePack/LabelPack exists, runtime real smoke PASS,
`FEATURE_LABEL_PARQUET_SINK_V1` status, `SESSION_LABEL_GUARD_FIX_V1` status); that
large-scale value-consuming studies are blocked until
`FEATURE_LABEL_PARQUET_SINK_V1` and session-context features until the session
guard fix; that the dry-run uses synthetic fixtures or seed packs only and is not
alpha evidence, an `EvidenceDraft` is not a candidate, and a
`ReferenceCandidateHandoff` is not Reference validation; that failed/rejected
ideas remain visible; that DAG metadata is correct (parallel phases have disjoint
`allowed_paths`, no global files); that the serial merge queue is respected and no
phase branch writes `ACTIVE_CAMPAIGN.md` in parallel mode; artifact-policy
compliance; no broker/live/paper/order/account scope; no
alpha/profitability/tradability claim and no strategy/backtest/portfolio/
alpha-search/factor-promotion/continuous-runner scope; no test weakening; and
handoff completeness and semantic done criteria.

```bash
cd ~/projects/alpha_system
ls reviews/ALPHA_AGENT_FACTORY_MVP/
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

Create `runs/<run_id>/STOP` with a short reason. Ralph checks STOP before provider
calls, phase selection, Codex execution, validation, review, PR creation, CI
waiting, the merge gate, merge, the done-check, and next-phase selection.

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

Remove or resolve the STOP condition, then resume. Ralph resumes from recorded run
state and does not regenerate completed, merged work. In parallel mode it
re-derives ready waves from the DAG and the merge ledger rather than restarting
the campaign.

```bash
cd ~/projects/alpha_system
rm runs/<run_id>/STOP
# resume the live parallel run (only after a clean plan and prior mock):
# just frontier-run-parallel ALPHA_AGENT_FACTORY_MVP 3
```

For a partially merged wave, resume continues from the serial merge queue
position; already-merged phases are not rebuilt.

## Blocked phase handling

A phase blocks on contradictory scope, repeated failure beyond the repair limit,
missing authorization, impossible validation, or a hard boundary violation
(external provider call attempted, raw provider data read by `agent_factory` code,
accepted DatasetVersion bypassed, runtime bypassed instead of called via the tool
surface, a consumed primitive edited, an autonomous agent instantiated or
continuous research runner introduced, a role without a permission-matrix entry, a
self-review/self-promotion, a prohibited MVP state introduced, or
broker/live/paper/order/account or strategy/backtest/portfolio/alpha-search scope
introduced). The phase writes a **truthful** blocked handoff with the exact
command, failure, and reason; its verdict is `BLOCKED`; and its dependents are
blocked. Fake completion is never allowed. A truthful `BLOCKED` is an acceptable
terminal outcome and must not be masked as a pass.

```bash
cd ~/projects/alpha_system
cat handoffs/ALPHA_AGENT_FACTORY_MVP/<PHASE_ID>.md   # records BLOCKED reason
cat runs/<run_id>/phases/<phase_id>/verdict.json     # verdict == BLOCKED
```

## Artifact audit

`runs/**` is local-only runtime state and must never be staged or committed. Raw,
canonical, feature, label, runtime, and agent values stay local-only under
`$ALPHA_DATA_ROOT`. Run this audit at preflight, before every merge, after the
integration dry run (`AGENT-P23`), and at closeout.

```bash
cd ~/projects/alpha_system
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find metadata -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/*/fixtures/*" -not -path "./tests/fixtures/*" -print
# reject committed DB/log/heavy formats outside fixtures
git ls-files | grep -E '\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|dbn|zst|pkl|pickle|joblib|onnx|npy|npz|log)$' \
  | grep -v '^tests/.*fixtures/' || echo "no committed heavy/db/log artifacts"
```

`git ls-files runs` must return empty. If any forbidden path is staged, unstage it
and repair the handoff before merge. Stage explicit paths only; never `git add .`
/ `git add -A`. Never force push. Tiny synthetic documented fixtures under
`tests/**/fixtures/**` (`tests/fixtures/**`,
`tests/unit/agent_factory/fixtures/**`, `tests/integration/agent_factory/fixtures/**`)
are the only data-like exception, and they must be tiny, synthetic, documented,
not real market data, and never alpha evidence.

## Final closeout

Closeout runs in wave w4 sequentially: `AGENT-P22` (Agent Dry-Run Harness, runs
alone), `AGENT-P23` (Seed-Pack and Synthetic Dry Run, runs alone), `AGENT-P24`
(Workflow 2 DAG Integration and Parallel Plan, runs alone), and `AGENT-P25`
(Acceptance Audit and Closeout, runs alone). The dry runs make **no external
provider call** — they run on synthetic fixtures and, when present, the local seed
packs.

```bash
cd ~/projects/alpha_system
python -c "import alpha_system.agent_factory.dry_run.harness"   # AGENT-P22
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/integration/agent_factory -q            # AGENT-P23
python tools/hooks/canary_runner.py
test -f docs/agent_factory/DRY_RUN.md
test -f docs/agent_factory/DRY_RUN_RESULTS.md
test -f docs/agent_factory/WORKFLOW2_DAG.md                     # AGENT-P24
test -f docs/agent_factory/ACCEPTANCE_AUDIT.md                  # AGENT-P25
test -f campaigns/ALPHA_AGENT_FACTORY_MVP/CLOSEOUT.md           # AGENT-P25
git ls-files runs
find data -type f ! -name README.md ! -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/*/fixtures/*" -not -path "./tests/fixtures/*" -print
# TARGET: alpha agent dry-run --task <task_id> --report          (closeout summary surface, not yet built)
```

At closeout: run the synthetic dry-run harness and the seed-pack/synthetic
integration dry run (Director → Scout → Critic → Data Contract Auditor →
Feature/Label Engineer → Diagnostics Runner via the bridge → No-Lookahead
Auditor → Statistical Reviewer → Librarian; no promotion); document the Workflow 2
DAG integration and parallel plan; run the acceptance audit across all six gates
(`bootstrap_and_entry`, `core_contracts`, `agent_roles`,
`enforcement_and_records`, `assets_and_bridge`, `dry_run_and_closeout` — see
`ACCEPTANCE.md`); run the final semantic done-check; write
`campaigns/ALPHA_AGENT_FACTORY_MVP/CLOSEOUT.md` with the final verdict
(`COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`); update `ACTIVE_CAMPAIGN.md`
(coordinator-only); and add durable lessons to `project-skill` when applicable.
The campaign is done only when all gates pass (or a truthful `BLOCKED` is
recorded), the artifact audit is clean, no autonomous agent is instantiated, no
prohibited MVP state is reachable, and no alpha/tradability/profitability/
strategy/paper/live/broker/production claim exists.

## Next campaign readiness for ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

This campaign is the controlled AI Alpha Research Team **contract layer** that the
future `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` consumes: the Core Alpha Pilot will run
*real* studies through the runtime, driven by these role / permission / tool /
queue / separation / memory contracts, under its own explicitly authorized
campaign. The program roadmap is: Data Foundation → Feature/Label Foundation →
Research Runtime → Seed Packs / Real Smoke → **Agent Factory (this)** → Core Alpha
Pilot → Validation Governance → Factor Library → Strategy Reference Validation →
Portfolio AlphaBook → Agent Research Runner → Monitoring/Decay → ML Meta-Labeling
→ L1 Eventstream → L2/Execution → Paper → Live Canary.

Readiness for the Core Alpha Pilot means the controlled-team contract layer exists
and is wired to drive the executable runtime safely: roles, a fail-closed
permission matrix, structured value-free tool contracts, a bounded research queue,
separation-of-duties enforcement, agent/decision/handoff records, rejected-idea
memory, a runtime bridge, and a non-alpha dry-run all exist as contracts. It does
**not** mean any signal is alpha, profitable, tradable, strategy-ready,
production-ready, or paper/live/broker-ready. Three known follow-ups still
constrain the next campaign and are carried forward as preflight gates /
future-blockers, not work this campaign performs:

* **`FEATURE_LABEL_PARQUET_SINK_V1`** (ADR-0006 /
  `decisions/0006-feature-label-value-storage.md`) must land before any
  large-scale, value-consuming Agent Factory study.
* **`SESSION_LABEL_GUARD_FIX_V1`** must land before session-context features
  (`rth_flag` / `eth_flag` / `session_minute`) can be used; the runtime guard in
  `runtime/input_resolver.py` currently false-positives on `session_label`.
* **Dataset registry report rehydration** (`docs/STRUCTURAL_BACKLOG.md`):
  `datasets.sqlite` persists report hashes, not full report objects; agents must
  use registry/runtime tools and respect this gap, not bypass
  accepted-DatasetVersion policy.

Each downstream campaign proceeds only under its own authorized contract; the
human owns risk/capital/live judgment. Use precise wording: an agent dry-run
success is not alpha, an agent-drafted `AlphaSpec` is not implementation approval,
a runtime diagnostic PASS is not factor promotion, an `EvidenceDraft` is not a
candidate, a `ReferenceCandidateHandoff` is not Reference validation, and
validated research is not paper/live approval. `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
is a separate, separately-authorized later campaign; Agent Factory only prepares
its readiness.

---

*This file is a campaign contract describing the intended Workflow 2 operating
procedure and boundaries for `ALPHA_AGENT_FACTORY_MVP`; it instantiates no
autonomous agent and makes no alpha, tradability, profitability, production, or
live claim.*
