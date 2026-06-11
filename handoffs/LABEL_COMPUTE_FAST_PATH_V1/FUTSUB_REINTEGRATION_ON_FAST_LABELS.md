# FUTSUB Reintegration On Fast Labels

This is an executable coordinator handoff for after
`LABEL_COMPUTE_FAST_PATH_V1` closes. It is not an instruction for any LCFP phase
branch to amend FUTSUB, edit run state, clear STOP, remove worktrees, mutate
registries, write values, create a PR, or merge.

## Evidence Basis

Read these committed LCFP files before acting:

- `research/label_compute_fast_path_v1/parity/parity_report.md`
- `research/label_compute_fast_path_v1/benchmark/benchmark_summary.md`
- `research/label_compute_fast_path_v1/integration/integration_report.md`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_PAUSE_STATE.md`
- `research/label_compute_fast_path_v1/closeout/CLOSEOUT.md`

The benchmark-selected engine policy is per family, not fast everywhere:

| FUTSUB phase | LCFP benchmark family | Config | Engine after LCFP acceptance | Requested workers | Notes |
| --- | --- | --- | --- | ---: | --- |
| `FUTSUB-P16` | `fixed_base` | `configs/labels/scaleout/fixed_horizon.json` | `v1` fast label path | 8 | P08 measured 1.03x at requested workers 8, effective 6. |
| `FUTSUB-P17` | `fixed_extended` | `configs/labels/scaleout/extended_horizon.json` | `reference` | n/a | P08 best fast cell was 0.55x; reference remains faster. |
| `FUTSUB-P18` | `close_out` | `configs/labels/scaleout/session_close_maintenance_flat.json` | `reference` | n/a | P08 best fast cell was 0.40x; reference remains faster. |
| `FUTSUB-P19` | `cost_adjusted` | `configs/labels/scaleout/cost_adjusted.json` | `reference` | n/a | P08 best fast cell was 0.72x; preserve valid checkpointed reference progress. |
| `FUTSUB-P20` | `path` | `configs/labels/scaleout/path.json` | `v1` fast label path | 8 | P08 measured 10.23x at requested workers 8, effective 7. |

Thread controls for fast reruns:

```bash
export POLARS_MAX_THREADS=2
export OMP_NUM_THREADS=2
export RAYON_NUM_THREADS=2
export NUMBA_NUM_THREADS=2
export ALPHA_LABEL_CPU_WORKERS=8
```

Prefer an explicit `--workers 8` on fast `alpha scaleout label-pack` invocations;
the environment variable is the fallback. `ALPHA_LABEL_CPU_WORKERS` takes
precedence over `ALPHA_CPU_WORKERS` for label scaleout when `--workers` is not
provided.

## Amend FUTSUB Text

Apply these amendments only after LCFP is accepted. In this worktree, there are
no committed generated FUTSUB spec files under
`specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`; if the coordinator has
generated or run-local specs for `FUTSUB-P16` through `FUTSUB-P20`, amend or
regenerate those specs with the same text below before rerunning.

### `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/GOAL.md`

Replace the `Producer Engine Policy (post-FCFP)` label bullet that says labels
materialize on the per-row reference label engine and that a V1 fast label path
is out of scope with:

```markdown
- **Labels -> LCFP accepted per-family engine policy.** Governed LabelPacks
  materialize through the official label scaleout path using the
  `LABEL_COMPUTE_FAST_PATH_V1` accepted engine policy:
  `fixed_base` and `path` use the V1 fast label producer path with requested
  workers 8 and thread controls `POLARS_MAX_THREADS=2`, `OMP_NUM_THREADS=2`,
  `RAYON_NUM_THREADS=2`, and `NUMBA_NUM_THREADS=2`; `fixed_extended`,
  `close_out`, and `cost_adjusted` use the reference engine because the P08
  benchmark measured the reference engine faster for those families. Both
  engines are parity-gated, emit the same governed `label_version_id`
  identities, and write only through the official serial label registry path.
  Existing valid reference-produced labels are preserved as the parity oracle
  and are not deleted.
- **Reference engine = oracle forever.** The per-row reference label engine is
  retained as the correctness oracle for parity checks and for families where it
  remains the selected materialization engine. Producer provenance
  (`producer_engine_id`) and `value_schema_version` are registry/value metadata;
  they never enter `label_version_id`.
```

### `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml`

Amend the campaign-level `project_profile.description` and `workflow2.notes`
where they describe label materialization as reference-engine-only. Use this
replacement text inside the existing scalar/list fields being edited; do not add
an unknown top-level YAML key:

```text
After LABEL_COMPUTE_FAST_PATH_V1 acceptance, FUTSUB P16-P20 use the LCFP-P08
accepted per-family engine policy: V1 fast labels for fixed_base and path at
requested workers 8 with thread controls, and reference labels for
fixed_extended, close_out, and cost_adjusted because reference remains faster
for those families. The reference label engine remains the correctness oracle
and no existing reference outputs are deleted.
```

For `FUTSUB-P16`, replace the scope sentence beginning
`ENGINE POLICY (post-FCFP, see GOAL.md): labels materialize on the per-row
REFERENCE label engine...` with:

```yaml
  - 'ENGINE POLICY (post-LCFP acceptance, see GOAL.md and
    handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md):
    fixed_base labels use the V1 fast label producer path selected by
    LCFP-P08. Invoke the official label scaleout path with --engine v1,
    requested --workers 8, and thread controls POLARS_MAX_THREADS=2,
    OMP_NUM_THREADS=2, RAYON_NUM_THREADS=2, NUMBA_NUM_THREADS=2. The reference
    label engine remains the parity oracle; label_version_id identity,
    label_available_ts, roll/maintenance guards, checkpoint/restart,
    Parquet-first values, and serial registry writes remain mandatory.'
```

For `FUTSUB-P17`, add this scope bullet after the materialize/register bullet:

```yaml
  - 'ENGINE POLICY (post-LCFP acceptance): fixed_extended labels stay on the
    reference engine because LCFP-P08 measured the reference engine faster
    (best fast speedup 0.55x). Do not force the fast path for this family.
    Correctness remains parity-gated and engine-independent.'
```

For `FUTSUB-P18`, add this scope bullet and retire any generated-spec non-goal
that says labels must stay reference-engine-only:

```yaml
  - 'ENGINE POLICY (post-LCFP acceptance): close_out labels
    (session_close/maintenance_flat) stay on the reference engine because
    LCFP-P08 measured the reference engine faster (best fast speedup 0.40x).
    The old reference-engine-only non-goal is retired as a blanket policy; this
    phase uses reference by per-family benchmark selection, not because fast
    labels are globally out of scope.'
```

For `FUTSUB-P19`, add this scope bullet and retire any generated-spec non-goal
that says labels must stay reference-engine-only:

```yaml
  - 'ENGINE POLICY (post-LCFP acceptance): cost_adjusted labels stay on the
    reference engine because LCFP-P08 measured the reference engine faster
    (best fast speedup 0.72x). Preserve valid checkpointed reference-engine
    progress and let checkpoint + registry truth skip completed valid units.
    Do not force-recompute unless the coordinator documents a specific
    supersession, corruption, or schema-version reason.'
```

For `FUTSUB-P20`, add this scope bullet after the materialize/register bullet:

```yaml
  - 'ENGINE POLICY (post-LCFP acceptance): path labels use the V1 fast label
    producer path selected by LCFP-P08. Invoke the official label scaleout path
    with --engine v1, requested --workers 8, and thread controls
    POLARS_MAX_THREADS=2, OMP_NUM_THREADS=2, RAYON_NUM_THREADS=2,
    NUMBA_NUM_THREADS=2. The reference label engine remains the parity oracle;
    same-bar policy, label_available_ts, roll/maintenance guards, and identity
    parity remain mandatory.'
```

Remove `runs/**` from FUTSUB P16-P20 allowed paths when regenerating specs if
the generator still emits it as commit-eligible. `runs/**` is local-only runtime
state and must not be staged.

### `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/PHASE_PLAN.md`

Add a short note before the FUTSUB-P16 section:

```markdown
**Post-LCFP label engine policy:** FUTSUB-P16 through P20 use the
`LABEL_COMPUTE_FAST_PATH_V1` accepted per-family policy. P16 fixed-base and P20
path labels run on the V1 fast label producer path with requested workers 8 and
the LCFP thread controls. P17 fixed-extended, P18 close-out, and P19
cost-adjusted labels remain on the reference engine because P08 measured the
reference engine faster for those families. The reference engine remains the
oracle; existing valid reference outputs are preserved.
```

### `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/ACCEPTANCE.md`

Replace the `label_materialization` gate paragraph with:

```markdown
### Gate `label_materialization` - FUTSUB-P16...P20
Diagnostic/primary/extended/session-close/maintenance-flat/cost-adjusted/path
LabelPacks are materialized and registered with `label_available_ts`,
roll-splice + maintenance-crossing guards, horizon coverage, and
N_eff/overlap metadata. Engine selection follows the LCFP accepted per-family
policy: V1 fast for `fixed_base` and `path`; reference for `fixed_extended`,
`close_out`, and `cost_adjusted`. Cost-adjusted labels use documented
cost/fee/slippage assumptions with BBO as a proxy. Coverage summaries are
value-free; no value/SQLite payload is committed; registry writes are serial.
```

### `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RUNBOOK.md`

Replace the label materialization workflow command note with:

````markdown
- **Label materialization workflow** - `FUTSUB-P16...P20` (serialized):

  ```bash
  # values are local-only under $ALPHA_DATA_ROOT; never staged
  # P16 fixed_base and P20 path after LCFP acceptance:
  POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 \
    alpha scaleout label-pack --execute --engine v1 --workers 8 ...

  # P17 fixed_extended, P18 close_out, P19 cost_adjusted:
  alpha scaleout label-pack --execute --engine reference ...

  alpha label list
  ```
````

### Generated Specs

For `specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P16.md`
through `FUTSUB-P20.md`, if present or regenerated, apply the same phase-specific
engine policy bullets above. For P18 and P19 specifically, replace any non-goal
wording equivalent to `a V1 fast label path is out of scope` or `labels stay
reference-engine-only` with:

```markdown
Building a new label engine or changing label semantics is out of scope. Engine
selection is inherited from the accepted LCFP per-family benchmark policy:
this phase uses the reference engine because reference remains faster for this
family; other FUTSUB label phases may use the V1 fast label producer where P08
selected it. Correctness is parity-gated and identity is engine-independent.
```

## Reset P16-P20 State

### Coordinator deviation note (2026-06-10)

The coordinator deliberately did NOT apply this section's P16-P18 reset.
P16/P17/P18 remain merged PASS: their full-window reference-produced values are
valid and parity-equivalent, so recomputing them would destroy harness-recorded
success only to reproduce identical values. Under the accepted per-family
policy, P17 (`fixed_extended`) and P18 (`close_out`) stay on the reference
engine anyway, and P16's `fixed_base` v1 selection (1.03x) applies to future
appends/recomputes only - it does not invalidate the existing reference-produced
substrate. Resetting them would violate preserve-valid-work (the
Preserve-Don't-Delete rules below) and the Compass v3 minimum-substrate
principle (do the minimum work that yields a valid substrate; do not rebuild
valid substrate for engine symmetry). Only `FUTSUB-P19` (resume reference from
its ~60% durable checkpoint) and `FUTSUB-P20` (fresh on the V1 fast path) are
reset/resumed. The state-surgery recipe below therefore applies with
`targets = {"FUTSUB-P19", "FUTSUB-P20"}` and an expected pending order of
`FUTSUB-P19`, `FUTSUB-P20`; everything else in this handoff (backups, STOP
removal ordering, preserve rules, rerun commands for P19/P20) stands.

Coordinator-only steps:

1. Back up the stopped run state before editing:

   ```bash
   cp runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/state.json \
      runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/state.json.bak_lcfp_reintegration
   ```

2. Reset only `FUTSUB-P16` through `FUTSUB-P20` to the clean pending key set.
   The clean key set is the one observed on the existing pending `FUTSUB-P20`
   entry:

   ```text
   allowed_paths
   artifact_paths
   conflicts_with
   dependencies
   execution_mode
   forbidden_paths
   lane
   merge_group
   must_run_alone
   name
   parallel_safe
   phase_id
   resource_class
   status
   ```

   Remove lifecycle keys from those phase dicts, including `branch`,
   `worktree_path`, `started_at`, `updated_at`, `completed_at`,
   `completed_stages`, `current_stage`, `last_completed_stage`, `status`
   values other than `PENDING`, `merged`, `commit_sha`, `pr_number`,
   `ci_status`, `merge_gate_status`, and any resume/block/provider fields.
   Set `status` to `PENDING`.

Coordinator script, from the repo root after the backup:

```bash
python - <<'PY'
import json
from pathlib import Path

run_dir = Path("runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1")
state_path = run_dir / "state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))

targets = {"FUTSUB-P16", "FUTSUB-P17", "FUTSUB-P18", "FUTSUB-P19", "FUTSUB-P20"}
clean_keys = [
    "allowed_paths",
    "artifact_paths",
    "conflicts_with",
    "dependencies",
    "execution_mode",
    "forbidden_paths",
    "lane",
    "merge_group",
    "must_run_alone",
    "name",
    "parallel_safe",
    "phase_id",
    "resource_class",
    "status",
]

for index, phase in enumerate(state["phases"]):
    if phase.get("phase_id") not in targets:
        continue
    missing = [key for key in clean_keys if key not in phase]
    if missing:
        raise SystemExit(f"{phase.get('phase_id')} missing clean keys: {missing}")
    reset = {key: phase[key] for key in clean_keys}
    reset["status"] = "PENDING"
    state["phases"][index] = reset

state["status"] = "RUNNING"
state["current_phase_id"] = None
state.pop("current_stage", None)

pending_order = [
    phase["phase_id"]
    for phase in state["phases"]
    if phase.get("phase_id") in targets and phase.get("status") == "PENDING"
]
expected = ["FUTSUB-P16", "FUTSUB-P17", "FUTSUB-P18", "FUTSUB-P19", "FUTSUB-P20"]
if pending_order != expected:
    raise SystemExit(f"unexpected pending order: {pending_order}")

state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
PY
```

3. Reset run-level stale current-phase pointers so Ralph selects the first
   dependency-satisfied pending phase:

   ```json
   {
     "status": "RUNNING",
     "current_phase_id": null,
     "current_stage": null
   }
   ```

   If `current_stage` is absent, leave it absent. Do not alter completed
   feature phases, run ledgers, costs, or event history except through the
   explicit backup and state reset.

4. Verify the resulting pending order is `FUTSUB-P16`, `FUTSUB-P17`,
   `FUTSUB-P18`, `FUTSUB-P19`, `FUTSUB-P20` before resuming. Because all five
   share `resource_class: materialization_registry`, the scheduler must run the
   registry-touching work serially.

## Registry Backup Before Rerun

Before the first rerun that may touch the label registry, create a local-only
backup under `ALPHA_DATA_ROOT`:

```bash
cp "$ALPHA_DATA_ROOT/registry/labels.sqlite" \
   "$ALPHA_DATA_ROOT/registry/labels.sqlite.bak_futsub_lcfp_reintegration_$(date -u +%Y%m%dT%H%M%SZ)"
```

This backup is local-only. Do not stage or commit it.

## Rerun Commands

Use the amended/generated FUTSUB specs and existing scaleout configs. The
examples below omit dataset registry, canonical root, symbols, years, and
dataset-version filters because those must come from the accepted FUTSUB P05
batch plan and current DatasetVersion acceptance locks.

```bash
# FUTSUB-P16: fast fixed_base
POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 \
  alpha scaleout label-pack \
    --config configs/labels/scaleout/fixed_horizon.json \
    --execute --rollout bounded-then-full --engine v1 --workers 8 ...

# FUTSUB-P17: reference fixed_extended
alpha scaleout label-pack \
  --config configs/labels/scaleout/extended_horizon.json \
  --execute --rollout bounded-then-full --engine reference ...

# FUTSUB-P18: reference close_out
alpha scaleout label-pack \
  --config configs/labels/scaleout/session_close_maintenance_flat.json \
  --execute --rollout bounded-then-full --engine reference ...

# FUTSUB-P19: reference cost_adjusted; preserve valid checkpointed progress
alpha scaleout label-pack \
  --config configs/labels/scaleout/cost_adjusted.json \
  --execute --rollout bounded-then-full --engine reference ...

# FUTSUB-P20: fast path
POLARS_MAX_THREADS=2 OMP_NUM_THREADS=2 RAYON_NUM_THREADS=2 NUMBA_NUM_THREADS=2 \
  alpha scaleout label-pack \
    --config configs/labels/scaleout/path.json \
    --execute --rollout bounded-then-full --engine v1 --workers 8 ...
```

Do not pass `--force` or `--force-recompute` by default. Checkpoint and registry
truth skip completed valid units. For the paused P19 cost-adjusted work, the
P00 pause handoff and this executor's read-only recheck observed 181 Parquet
files, 181 JSON sidecars, 181 checkpoint unit JSON files, and
`completed_units.jsonl`; those completed valid units should be skipped, not
recomputed, unless the coordinator documents a specific corruption,
supersession, or value-schema reason.

## Resume Stopped FUTSUB Run

Observed pause state rechecked by LCFP-P09:

- Run directory exists:
  `/home/yuke_zhang/projects/alpha_system/runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.
- STOP file is present.
- `state.json` reports `status=RUNNING`, `current_phase_id=FUTSUB-P19`,
  `phase_count=34`, counts `PASS=1`, `PASS_WITH_WARNINGS=18`, `PENDING=14`,
  `SPEC_READY=1`, and `updated_at=2026-06-10T00:38:26Z`.
- `FUTSUB-P19` is `SPEC_READY` on branch
  `auto/alpha_futures_research_substrate_scaleout_v1/futsub-p19-cost-adjusted-labelpack-scaleout`.
- Preserved FUTSUB worktree directories exist for P14 and P19:
  `/home/yuke_zhang/projects/alpha_system-alpha_futures_research_substrate_scaleout_v1-futsub-p14`
  and
  `/home/yuke_zhang/projects/alpha_system-alpha_futures_research_substrate_scaleout_v1-futsub-p19`.

Resume sequence:

1. Apply and review the FUTSUB text/spec amendments above.
2. Back up `state.json` and `labels.sqlite`.
3. Reset P16-P20 phase dicts to clean `PENDING` and clear stale run-level
   current-phase pointers as described above.
4. Verify local value/checkpoint directories under `ALPHA_DATA_ROOT` are still
   present. Do not remove or rewrite checkpoint-bearing state.
5. Remove the STOP file only after the backup and reset are complete.
6. Repoint `ACTIVE_CAMPAIGN.md` to
   `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.
7. Resume the exact stopped run:

   ```bash
   just frontier-resume-run 2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
   ```

Worktree cleanup is coordinator-owned. Use the Frontier worktree cleanup path
only after confirming no checkpoint-bearing or uncommitted value-free evidence
exists only in the worktree. Do not delete the P19 worktree until its paused
spec/handoff/context are either intentionally obsolete because P19 was reset or
preserved elsewhere. Removing a source worktree must not remove
`ALPHA_DATA_ROOT` value, checkpoint, or registry state.

## Preserve-Don't-Delete Registry Rules

- Default action is preserve. Do not delete reference-label registry rows,
  values, checkpoint files, or sidecars merely because a fast path now exists.
- Supersede only when the old row/value is superseded and verified: same
  governed `label_version_id`, same intended value series, parity within the
  documented tolerance, and an official resolver/registry path that can select
  one producer unambiguously.
- Provenance must remain explicit via `producer_engine_id` and
  `value_schema_version`. Expected fast provenance from LCFP is
  `alpha_system.labels.fast.pack_materializer.v1` with
  `alpha_system.labels.fast.values.v1`.
- Never silently mix reference and fast producers in one value series. If the
  existing registry rejects a fast registration because a reference row already
  owns the identity, treat that as a correct fail-closed condition. Do not patch
  SQLite manually.
- Keep existing valid reference outputs as the parity reference. The reference
  engine is never deleted or weakened.
- If fast-vs-reference values differ beyond the documented tolerance, treat the
  difference as a fast-path bug or a schema-versioning issue. Do not overwrite
  reference outputs to force convergence.
- If the value layout or provenance semantics change, version the value schema
  explicitly and materialize through the official path. Do not reuse a schema
  version for incompatible values.
- No raw/canonical data, label values, Parquet payloads, SQLite files, logs,
  caches, or run artifacts may be staged or committed.

## Explicit Non-Execution Statement

Everything in this file is a coordinator action after LCFP closes. LCFP-P09 did
not execute the FUTSUB amendment, reset P16-P20, clear STOP, remove worktrees,
resume the run, mutate registry rows, write label values, call a broker, create
a PR, run a reviewer, merge, or mark the phase PASS.
