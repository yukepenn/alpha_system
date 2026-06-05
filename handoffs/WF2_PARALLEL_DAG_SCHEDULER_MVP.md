# Handoff: WF2_PARALLEL_DAG_SCHEDULER_MVP

Workflow 1 harness task. Upgrades Workflow 2 from strictly sequential phase
execution to a safe DAG **wave** scheduler: dependency-aware phase selection by
default in `dag_wave` mode, and opt-in concurrent build of conflict-free,
parallel-safe waves in isolated worktrees with a **serial merge queue**. The
existing sequential auto-PR/auto-merge path is unchanged and remains the default.

## Design Summary

- **Scheduling brain (pure, no I/O):** `tools/frontier/dag_scheduler.py` builds
  the dependency graph, rejects cycles / unknown deps / self-deps / unknown
  conflicts, computes the dependency-satisfied ready set, and partitions PENDING
  phases into ordered **waves**. A phase may share a parallel wave only if it is
  conservatively safe: `parallel_safe: true`, has disjoint `allowed_paths`, is not
  `must_run_alone`, is not RED (unless RED scope armed), declares no global file
  (e.g. `ACTIVE_CAMPAIGN.md`, `frontier.yaml`), and does not conflict with another
  member (`conflicts_with`, overlapping paths, shared exclusive `resource_class`).
  Default is run-alone, so omitting all metadata yields one phase per wave.
- **Serial merge queue (pure):** `tools/frontier/merge_queue.py` orders
  build-complete (`MERGE_READY`) phases deterministically — dependencies before
  dependents, `merge_group` members kept adjacent, input order as tiebreaker.
- **Driver integration:** `tools/frontier/ralph_driver.py` parses the new optional
  phase fields and a `workflow2.scheduler` block, persists scheduler metadata in
  run state, selects phases by ready-set in `dag_wave` mode, and runs a parallel
  wave coordinator when parallelism is armed.
- **Merge stays serial** even when builds run concurrently: the merge tail
  (branch protection -> merge gate -> `gh pr merge` -> worktree cleanup) was
  extracted into `finalize_phase_merge` and is invoked one phase at a time by the
  coordinator, re-evaluating the gate against the current base for each PR.
- **Coordinator-owned ACTIVE_CAMPAIGN.md:** in a parallel wave, phase branches do
  not write the pointer (`suppress_active_pointer`), so concurrent branches never
  conflict on it. The coordinator writes the projected pointer to
  `runs/<run_id>/ACTIVE_CAMPAIGN.projected.md`; the tracked pointer is refreshed by
  the next sequential phase / closeout, exactly as the harness already
  reconstructs it from run state.

## Files Changed

New:
- `tools/frontier/dag_scheduler.py` — DAG validation, ready-set, wave partition,
  conflict detection (pure, stdlib only).
- `tools/frontier/merge_queue.py` — serial merge ordering (pure).
- `tests/test_dag_scheduler.py` — 30 cases.
- `tests/test_merge_queue.py` — 8 cases.
- `handoffs/WF2_PARALLEL_DAG_SCHEDULER_MVP.md` — this handoff.

Modified:
- `tools/frontier/ralph_driver.py` — `LedgerPhase` + `parse_campaign_phases` read
  the new fields; `provider_phase_state`/`ledger_phase_state` emit them;
  `SchedulerSettings` + `resolve_scheduler_config`; `next_scheduled_provider_phase`
  / `select_next_phase` / `ready_wave_phases`; `run_dag_wave_parallel` coordinator
  + helpers (`run_wave_build`, `run_wave_merge`, `finalize_merge_for_phase`,
  `coordinator_update_active_campaign`, `wave_integration_verify`,
  `finalize_completed_campaign`); `finalize_phase_merge` extracted from
  `post_phase_git_github` with a `defer_merge` seam; per-run write lock
  (`_RUN_WRITE_LOCK`) on `append_event`/`write_state`/`progress`/`write_heartbeat`/
  `append_cost_record`/summary writes; parallel-local guards on
  `block_provider_run`/`block_provider_gate`/`mark_auto_merge_pending`; coordinator
  guard in `write_active_campaign_for_phase_commit`; `resolve_active_campaign_id`;
  `plan_dag` + CLI subcommand; `--parallel`/`--max-parallel` flags; resume/run
  auto-resolve the active campaign from `ACTIVE_CAMPAIGN.md`.
- `frontier.yaml` — `workflow2.scheduler` block (mode/max_parallel_phases/
  merge_queue/parallel_execution/update_active_campaign), defaults preserve
  sequential behaviour.
- `justfile` — consolidated Workflow 2 recipes (see below).
- `tests/test_ralph_driver.py` — rewrote `test_just_command_semantics_*` for the
  new surface; added scheduler-integration tests (dependency-aware selection,
  deadlock, parallel wave in mock mode, coordinator pointer, plan-dag, auto-resume,
  no-network import guard for the new modules).
- `docs/workflow.md`, `docs/operations.md`, `docs/validation.md`,
  `docs/AI_AGENT_GUIDE.md`, `scripts/ralph/README.md` — scheduling modes,
  consolidated commands, auto-resume, coordinator-only pointer.

## New / Consolidated CLI

`ralph_driver.py` subcommands: `run`, `resume`, **`plan-dag`** (new). `run`/`resume`
gained `--parallel` and `--max-parallel`. `run --provider-wired` and `resume` now
default the campaign id to the `ACTIVE_CAMPAIGN.md` pointer.

Consolidated `just` recipes (LIVE = real PR + auto-merge armed; `*-mock` = safe):

| New | Replaces |
| --- | --- |
| `frontier-run [c]` | `frontier-run-campaign`, `frontier-run-workflow2` |
| `frontier-resume [c]` | `frontier-resume` (run_id), part of `frontier-resume-campaign` |
| `frontier-next [c] [n]` | `frontier-run-next`, `frontier-run-next-x` |
| `frontier-run-parallel [c] [n]` | (new) |
| `frontier-plan [c]` | (new) |
| `frontier-overnight [c]` | `frontier-run-overnight` |
| `frontier-run-mock [c]` | `frontier-run-campaign-mock` |
| `frontier-next-mock [c] [n]` | `frontier-run-next-mock`, `-next-x-mock` |
| `frontier-run-parallel-mock [c] [n]` | (new) |
| `frontier-ledger [c]` | `frontier-run-campaign-ledger` |
| `frontier-resume-run <run_id>` | `frontier-resume` (run_id form) |
| `frontier-resume-stage ...` | `frontier-resume-campaign` |
| `frontier-run-workflow2-toy` | kept (now mock + provider-wired) |

Removed (no replacement): `frontier-run-workflow2-goal` (use `ralph_driver.py run
--goal`). The live/mock safety distinction and the real-PR arming env
(`FRONTIER_CREATE_PR=1 FRONTIER_ALLOW_AUTOMERGE=1 FRONTIER_MERGE_DRY_RUN=0
env -u FRONTIER_DISABLE_AUTOMERGE`) are preserved and asserted by
`test_just_command_semantics_are_provider_wired`.

## Scheduler Metadata

`frontier.yaml` / `campaign.yaml` `workflow2.scheduler`: `mode`
(`sequential`|`dag_wave`), `max_parallel_phases`, `merge_queue` (`serial`),
`parallel_execution`, `update_active_campaign`
(`auto`|`phase_commit`|`coordinator_only`). Per-phase optional fields:
`parallel_safe`, `allowed_paths`, `forbidden_paths`, `conflicts_with`,
`resource_class`, `must_run_alone`, `merge_group`. Env overrides:
`FRONTIER_SCHEDULER_MODE`, `FRONTIER_MAX_PARALLEL_PHASES`,
`FRONTIER_PARALLEL_EXECUTION`, `FRONTIER_PARALLEL` (arms dag_wave + execution).

## What Stays Sequential / What Can Parallelize

- **Default everywhere:** `mode: sequential` — list order, one phase at a time.
- **`dag_wave` (no parallel_execution):** still one phase at a time, but selected
  by dependency-ready set (a correctness improvement — never picks a phase whose
  dependencies have not passed; surfaces `SCHEDULE_DEADLOCK` instead of silently
  "completing").
- **`dag_wave` + parallel:** builds of a conflict-free, parallel-safe wave run
  concurrently; merges run serially. RED, global-file, `must_run_alone`, and
  no-`allowed_paths` phases never parallelize.

## Safety Guarantees

- Sequential behaviour is byte-for-byte preserved unless parallel is explicitly
  armed (verified by the full suite, 1910 passing).
- Merge is always serial; `main` advances one PR at a time, gate re-checked per PR.
- Phase branches never write `ACTIVE_CAMPAIGN.md` in a parallel wave.
- Run-level writes are serialized by a reentrant lock; per-phase blocks in a wave
  are local (one phase blocking does not stop the whole run mid-wave).
- No RED parallelization without `PROJECT_OP_*` scope.
- New modules import only the standard library (no provider/network imports;
  guarded by `test_scheduler_modules_have_no_provider_or_network_imports`).
- `runs/**` stays local-only (`git ls-files runs` empty; artifact audit clean).

## Adversarial Review Findings (fixed)

A 16-agent adversarial review confirmed three real issues (no critical, no
sequential-path break, no race/deadlock); all are fixed and regression-tested:

- **Orphaned `MERGE_READY` on parallel resume (medium).** If a STOP/crash landed
  mid-merge-queue, a built-but-unmerged phase could be silently dropped and the
  run could finalize as COMPLETE. Fix: `run_dag_wave_parallel` now drains leftover
  `MERGE_READY` phases through the serial merge queue at the top of its loop, and
  `finalize_completed_campaign` structurally BLOCKs completion while any phase is
  not passing (covered by `test_finalize_completed_campaign_blocks_on_unmerged_phase`).
- **Coordinator-only suppression gated on wave width (medium/low).**
  `suppress_active_pointer` was set only for width>1 waves, so a width-1 bootstrap
  phase in a parallel run could write `ACTIVE_CAMPAIGN.md` on its branch. Fix:
  suppression is now gated on `update_active_campaign == "coordinator_only"`
  regardless of width (asserted in `test_dag_wave_parallel_runs_wave_in_mock`).

## How ALPHA_FEATURE_LABEL_FOUNDATION_V1 Should Use It

Set `workflow2.scheduler.mode: dag_wave` and `parallel_execution: true` in the
campaign. Declare `parallel_safe: true` with disjoint `allowed_paths` on the
feature-family and label-family phases (e.g. `src/.../features/base/**`,
`.../bbo/**`, `.../session/**`), keep engine/registry/CLI/closeout phases as
`must_run_alone` (or simply without `parallel_safe`), and run
`just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1` to confirm the waves before
`just frontier-run-parallel`.

## Validation

`python tools/verify.py --all` (1910 passed, compileall src/tests/tools),
`python tools/hooks/canary_runner.py` (all pass), `python tools/verify.py
--artifacts` (clean), `ruff check` clean on the new modules and tests,
`ruff check --select F tools/frontier/ralph_driver.py` clean, `git ls-files runs`
empty. CLI smoked: `frontier-run-parallel-mock`, `plan-dag --json`.

## Known Limitations / Next Steps

- True concurrent **provider** execution (live `claude`/`codex`) is newly wired
  and exercised end-to-end only in mock mode (the local test harness cannot drive
  live providers). Watch the first live `frontier-run-parallel` campaign; revert
  to sequential by leaving `parallel_execution: false`.
- Conflict detection is from **declared** metadata, not actual diffs (V2:
  dynamic diff-based conflict detection, auto-rebase/retry between serial merges,
  GitHub-native merge queue, resource-aware scheduling).
- `frontier.yaml` `workflow2.scheduler` is not yet added to
  `REQUIRED_WORKFLOW2_KEYS`; it loads and validates as an optional block.
