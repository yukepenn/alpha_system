# RUNBOOK — ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1

Operational runbook for the Workflow 2 (`dag_wave`) Substrate Scaleout. All
paths are relative to `~/projects/alpha_system`. The active repo and worktrees
must stay on the WSL2 Linux filesystem; never run from `/mnt/c`, `/mnt/d`,
`/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced, network, or temp
paths.

## 0. Preflight

```bash
cd ~/projects/alpha_system
git status --short
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Confirm the consumed stack imports:

```bash
python -c "import alpha_system.runtime, alpha_system.features, alpha_system.labels, alpha_system.experiments.splits, alpha_system.data.foundation.rolls, alpha_system.core.value_store"
```

## 1. Environment checks (Core Pilot lesson)

```bash
echo "ALPHA_DATA_ROOT=${ALPHA_DATA_ROOT:?set ALPHA_DATA_ROOT to the local data root}"
test -d "$ALPHA_DATA_ROOT"                       # local-only data + registries live here
source ~/.venvs/alpha_system_research/bin/activate   # research venv
python -c "import polars, pyarrow"               # Parquet stack (and duckdb where used)
python -c "import duckdb" 2>/dev/null || echo "duckdb optional; skip if unused"
```

- For Codex execution, ensure `shell_environment_policy.inherit = all` so
  `ALPHA_DATA_ROOT`, the research venv, and `FRONTIER_*` env vars reach the
  executor (a direct lesson from the Core Pilot: a missing/empty inherited
  `FRONTIER_*` env produced false-negative blocks).
- Entry gates recorded in `FUTSUB-P01`: consumed primitives import; resolver-smoke
  discipline intact; the inherited boundary (4 `REJECT` / 6 `INCONCLUSIVE` /
  0 `WATCH` / 0 `CANDIDATE_RESEARCH`) recorded.

## 2. Campaign file checks

```bash
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/GOAL.md
test -f campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml
test -f campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RUNBOOK.md
test '!' -f campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/ACTIVE_CAMPAIGN.md
grep -q "ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1" ACTIVE_CAMPAIGN.md
```

## 3. YAML parse + consistency

```bash
python -c "import yaml; yaml.safe_load(open('campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml'))"
```

Consistency expectations (also enforced by stop_conditions):

- phase ids/names/lanes/dependencies/DAG fields match between `PHASE_PLAN.md` and
  `campaign.yaml`;
- `acceptance_gates` cover all 34 phases exactly once;
- no phase is `parallel_safe` (materialization is serialized by the shared
  `resource_class: materialization_registry`); `must_run_alone` phases are not
  `parallel_safe`; no phase declares a global/coordinator path while parallel.

## 4. Repo clean check

```bash
git status --short
git ls-files runs                                   # must be empty
git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst' '**/*.arrow' '**/*.feather'   # must be empty
```

## 5. Plan the DAG (read-only)

```bash
just frontier-plan ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
```

Expected shape: a serial DAG (no `parallel_safe` phases). Materialization phases
appear in the `materialization_registry` resource group and are never
co-scheduled. No `conflicts`, no `blocked`.

## 6. Mock run (no providers, no merges)

```bash
just frontier-run-parallel-mock ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1 3
```

Confirms phase ordering, STOP checks, the registry resource serialization, and
the serial merge queue end-to-end with mocked providers before any live cost.

## 7. Live run

```bash
just frontier-run-parallel ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1 3
# or, sequential / next / overnight:
just frontier-run      ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
just frontier-next     ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1 1
just frontier-overnight ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
```

Ralph builds each phase in an isolated worktree, runs checks, routes Claude
review, parses verdicts, opens PRs, waits for CI, evaluates the merge gate, and
merges one PR at a time.

STOP / resume / heartbeat / tail / summary / promote-reviews:

```bash
just frontier-stop      <run_id>
just frontier-resume    ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
just frontier-heartbeat <run_id>
just frontier-tail      <run_id>
just frontier-summary   <run_id>
just frontier-promote-reviews <run_id> ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
```

## 8. Per-stage substrate workflows (what each phase does)

- **DatasetVersion inventory + acceptance-lock** — `FUTSUB-P02`. Inspect via
  `alpha registry status` / registry tools; persist accept/block/warn + coverage.
- **Roll-boundary dry run** — `FUTSUB-P03`. Compute the analytic CME quarterly
  calendar via `data/foundation/rolls.py`; persist `RollCalendarRecord`s
  (local-only); add the roll-splice guard; test on a known roll week.
- **Keystone identity preflight** — `FUTSUB-P04`. Verify
  `dry-run == execute == record == lock == resolver` on a slice.
- **Materialization batch plan** — `FUTSUB-P05`. Bounded/chunked/restart-safe
  plan + serial registry resource guard; dry-run identity preview only.
- **Dry-run identity preview** (per family) before execute:

  ```bash
  alpha feature plan   --help     # inspect plan/preview args for the family
  alpha label   plan   --help
  ```

- **Feature materialization workflow** — `FUTSUB-P06…P13` (serialized):

  ```bash
  # values are local-only under $ALPHA_DATA_ROOT; never staged
  alpha feature materialize --execute   # with the family/dataset/registry args from the P05 plan
  alpha feature list                    # confirm registered metadata
  ```

- **Feature integration + resolver smoke** — `FUTSUB-P14`; coverage matrix
  `FUTSUB-P15`.
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

- **Roll-splice + maintenance-crossing guard audit** — `FUTSUB-P21`.
- **Label integration + resolver smoke** — `FUTSUB-P22`; coverage matrices
  `FUTSUB-P23`.
- **Walk-forward / purge / embargo smoke** — `FUTSUB-P24` (wire
  `experiments/splits.py` into the runtime diagnostics path).
- **N_eff reporting smoke** — `FUTSUB-P25`.
- **BBO quality + cross-market alignment matrices** — `FUTSUB-P26`.
- **Core Pilot StudySpec re-lock + rerun** — `FUTSUB-P27…P29` (re-lock,
  re-run via runtime tools, refresh honest verdicts).
- **Artifact audit** — `FUTSUB-P30`. **Handoffs** — `FUTSUB-P31` (Validation
  Governance), `FUTSUB-P32` (FactorLibrary / Multi-Horizon Mining).
- **Closeout** — `FUTSUB-P33`.

## 9. Registry backup / restore policy

Local SQLite registries (`registry/datasets.sqlite`, `registry/features.sqlite`,
`registry/labels.sqlite`) under `ALPHA_DATA_ROOT` are **local-only and never
committed**. Before a large materialization wave, copy the registry files to a
local-only backup (outside git, under `ALPHA_DATA_ROOT`) so a corrupted parallel
write can be restored; the campaign serializes registry writes
(`resource_class: materialization_registry`) to avoid corruption in the first
place.

## 10. Artifact audit (before every merge)

```bash
git status --short
git diff --cached --name-only
git ls-files runs
git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'
```

Stage explicit paths only. Never `git add .` / `git add -A`. Never force-push.
Values, registries, and roll-calendar data stay local-only (gitignored +
never-commit globs). Only value-free summaries / code / tests / docs / handoffs /
reviews are commit-eligible.

## 11. STOP / Resume

A `runs/<run_id>/STOP` file is an active stop request. Ralph checks it before
phase selection, Codex execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. To resume, remove/resolve the STOP and re-run
`frontier-resume`; Ralph continues from recorded run state.

## 12. Closeout + handoffs

`FUTSUB-P33` runs the acceptance audit + semantic done-check, writes
`campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/CLOSEOUT.md` with a
verdict in `{COMPLETE, COMPLETE_WITH_WARNINGS, BLOCKED}`, updates the coordinator
`ACTIVE_CAMPAIGN.md`, and confirms the downstream handoffs from `FUTSUB-P31/P32`.
Final gates:

```bash
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Handoffs flow to `ALPHA_VALIDATION_GOVERNANCE_V1` (multiple-testing / locked-test
/ contamination ledger / DSR-PBO-PSR + the N_eff/fold metadata produced here),
`ALPHA_FACTOR_LIBRARY_V1` (FactorCard/EvidenceBundle ingestion), and
`ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1` (the materialized substrate +
coverage matrices as the consumable mining base).
