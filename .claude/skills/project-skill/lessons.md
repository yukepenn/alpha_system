# Lessons

Project-specific lessons for `alpha_system`.

Add concise entries only after they are validated by real work.

## Workflow 2 — parallel dag_wave execution

- **Serialize all git/gh in parallel mode.** In `dag_wave` parallel mode the build
  workers run as threads sharing one repo. A `gh pr merge` can transiently flip the
  shared repo to `core.bare=true`, which makes a sibling phase's concurrent `git`
  fail with `fatal: this operation must be run in a work tree`. Hold a process-wide
  RLock around every `git()` and every gh call, and restore `core.bare=false` after
  each gh call (`tools/frontier/git_utils.GIT_SERIAL_LOCK`,
  `github_utils._run_gh`). Validated by 4 clean parallel waves on
  `ALPHA_FEATURE_LABEL_FOUNDATION_V1`.

- **The coordinator owns git; the executor must not.** In worktree mode the shared
  `.git` is effectively read-only to the executor — it leaves all changes UNSTAGED
  and the unsandboxed driver stages/commits per curated path on its behalf. A git
  failure on the executor side is expected and is not a phase blocker.

- **Union-merge README only — never `**/*.md`.** A blanket markdown union-merge in
  `.git/info/attributes` silently concatenates conflicting same-region edits in
  load-bearing docs (`specs/`, `ACCEPTANCE.md`, `decisions/`, `handoffs/`) and
  defeats the pre-merge base-sync conflict detection (which relies on a non-zero
  merge return to block truthfully). Only the append-only README snapshot is safe
  to union-merge.

- **Branch deletion is driver-owned in both modes.** `merge_pr` does not pass
  `--delete-branch` (it can flip `core.bare` while a branch is checked out in a
  worktree). The driver deletes the branch after merge: worktree mode via
  `WorktreeManager.cleanup_after_merge`; in-tree mode via
  `cleanup_phase_worktree_after_merge` (guarded to `auto/` branches). Forgetting
  the in-tree path leaks remote branches in the default serial mode.

## Validation environment

- **Run authoritative `verify.py --all` in a clean shell.** Inherited Workflow-2
  control env vars (`FRONTIER_CREATE_PR`, `FRONTIER_ALLOW_AUTOMERGE`,
  `FRONTIER_MERGE_DRY_RUN`, `FRONTIER_PARALLEL`, `FRONTIER_MAX_PARALLEL_PHASES`)
  force PR/merge/parallel driver paths during tests and fail exactly 13 driver
  tests (`tests/test_ralph_driver.py`, `tests/test_github_utils.py`) on otherwise
  green main — a false negative with zero substrate tests affected. This wrongly
  `BLOCKED` the `FLF-P31` closeout (re-validated clean: `2120 passed`) and recurred
  identically at the `RT-P26` (`ALPHA_RESEARCH_RUNTIME_MVP`) closeout (`13 failed`
  vs clean `2439 passed`). **Now fixed permanently**: an autouse fixture in
  `tests/conftest.py` clears `FRONTIER_*` before each test, so the suite is
  hermetic regardless of ambient env (PR #178). Tests run via `PYTHONPATH=src`
  (the bare `python -c "import alpha_system..."` smoke commands in specs only
  resolve with it).

- **Manual gh ops from a worktree need a core.bare check.** A manual
  `gh pr merge` / push from a worktree can leave the shared root repo with
  `core.bare=true` and may error `'main' is already used by worktree` on gh's local
  branch cleanup — but the **remote merge still succeeds**. Always
  `git config core.bare false` afterward (safe only when no driver is running, as
  the in-process git-lock does not cover external shells).

## Verdict artifacts

- **Specific review warnings live in `review.md`, not `verdict.json`.** The verdict
  parser often writes the placeholder *"Review passed with warnings but did not
  enumerate warning bullets"* and may set `external_providers_called`/`network_used`
  to `true` by default; these contradict the review prose and the no-external-call
  contract. Read the `review.md` narrative for the real residual warnings, and
  treat the boolean flags as parser defaults, not evidence of provider calls.

## Workflow 2 — live run recovery (ALPHA_RESEARCH_RUNTIME_MVP, 27/27)

- **The live loop is sound; failures are content/external, not the parallel loop.**
  The first real `frontier-run-parallel` run (27 phases) stopped four times — all
  from per-phase content or a provider blip, never the dag_wave coordinator, which
  correctly isolated each bad phase (stalled it, never merged broken code, resumed
  cleanly). Single-phase waves fail identically to parallel ones for these causes.

- **pytest needs `--import-mode=importlib` for duplicate test basenames.** Phases
  add `tests/.../test_contracts.py` etc.; two same-basename files under packages
  without `__init__.py` abort collection with *"import file mismatch"* under the
  default `prepend` mode, failing only `frontier-ci` (local phase checks run a
  scoped subset and miss it). Fixed repo-wide via `addopts="--import-mode=importlib"`
  in `pyproject.toml` (PR #157).

- **Runtime subpackage `__init__.__all__` stays empty.** The RT-P02 skeleton test
  `test_created_subpackage_surfaces_are_empty_until_later_phases` asserts the
  runtime subpackages keep `__all__ == []`; a later phase that populates it
  (`splits`/RT-P09, `cost`/RT-P11) breaks CI and **cannot edit the skeleton test**
  (boundary). Conform the phase: keep `__all__ = []`, re-export symbols via plain
  imports or a lazy `__getattr__` (callers/tests import from the package root,
  which works regardless of `__all__`).

- **Authorized resume head-mismatch — recover, don't hand-edit.** After a manual
  fix changes a phase branch head, resume hits `RESUME_PRECONDITION_FAILED`; arm
  `FRONTIER_ALLOW_RESUME_HEAD_MISMATCH=1` **only after** verifying the PR diff ==
  the reviewed files. The drain now treats that stranded status as drainable when
  the override is armed (PR #178); previously it dropped out of the gate-blocked
  set, dag_wave `SCHEDULE_DEADLOCK`ed, and needed a `state.json` edit restoring
  `CI_BLOCKED`.

- **Re-run a mid-build stage (e.g. review after a transient 529) sequentially.**
  In a `dag_wave` campaign the coordinator only schedules `PENDING`/gate-blocked
  phases, so `--from-stage review` deadlocks. Force
  `FRONTIER_SCHEDULER_MODE=sequential` with `--run-dir --phase-id --from-stage
  review` (no `--no-provider-replay`, so the provider is actually re-called). A
  gate-drain recovery also targeted-stops after the one phase ("no later phases
  started") — resume again to continue.

- **Promote reviewer records at closeout.** The driver keeps Opus reviews run-local
  (`runs/<run>/phases/<phase>/{review.md,verdict.json}`); the
  `yellow_phase_reviews_present` acceptance gate wants them committed under
  `reviews/<campaign>/<phase>/`. Use `just frontier-promote-reviews <run_id>
  <campaign>` (PR #178) at closeout, then stage explicitly. RT-P26's executor
  correctly reported `BLOCKED` for this coordinator-owned gap; the coordinator
  resolved it and recorded `COMPLETE_WITH_WARNINGS`.

## Workflow 2 — live run recovery (ALPHA_AGENT_FACTORY_MVP, 26/26)

- **The verdict parser must tolerate Markdown-decorated verdict lines.** A phase
  done-check that rendered its verdict in **bold** — `**DONE_CHECK:
  PASS_WITH_WARNINGS**` — was mis-parsed as `BLOCKED` because `DONE_CHECK_RE`
  (and the identical `VERDICT_RE`) in `tools/frontier/verdict.py` required the
  verdict to be the *entire* line (`^\s*DONE_CHECK:\s*(...)\s*$`); the leading and
  trailing `**` produced zero matches and the parser defaulted to `BLOCKED`
  ("missing or ambiguous"). This stopped the live run at `AGENT-P16` even though
  the phase passed review and every check. **Fixed (PR #198):** both regexes now
  allow leading decoration (`[\s>#*_`-]*`) and emphasis/backtick padding around
  the colon and verdict, while staying anchored to a single line so prose can't
  false-match. The 16 prior phases passed only because they happened to emit
  plain `DONE_CHECK:` lines — pure formatting non-determinism, so this *will*
  recur without the fix. The dag_wave coordinator handled the false-negative
  correctly (isolated the phase, merged nothing, STOP + clean exit at 16/26).

- **Resuming `--from-stage done_check` reuses `done_check.json` — re-parsing the
  `.md` is NOT enough.** When a done-check is "fresh" (`done_check.json` mtime ≥
  `executor_output.md`), the driver reuses the stored `verdict` from the JSON
  (event `DONE_CHECK_REUSED`) without re-parsing the markdown. So after fixing
  the parser, regenerate the cached JSON from the real `done_check.md`
  (`parse_done_check_text` → rewrite `done_check.json` with the same
  `frontier-done-check-v1` shape) before resuming; otherwise the stale `BLOCKED`
  shadows the fix. `--no-provider-replay` only permits `from_stage ∈
  {ci, branch_protection, merge_gate, merge, complete}`, so a pre-PR `done_check`
  stall can't use the deterministic stage-resume — regenerate-the-artifact +
  `FRONTIER_SCHEDULER_MODE=sequential ... --from-stage done_check` (provider
  replay on) is the path. `AGENT-P16` recovered this way and merged (PR #199).

- **Don't write `.log` console captures under `runs/`.**
  `tests/unit/test_l2_artifact_policy.py::test_no_l2_db_or_columnar_artifacts_are_present`
  `rglob`s the whole tree (only `.git`/`__pycache__` excluded) for
  `.log/.sqlite/.db/.parquet/...`, so operator console logs like
  `runs/_live_console_*.log` fail the closeout `verify --all` even though they are
  gitignored. Capture live-run console to a path outside the repo (or a non-matching
  suffix), or delete it before the closeout verify.

- **Supervisor PRs to `main` need an explicit merge permission.** The Claude Code
  auto-mode classifier blocks a direct `gh pr merge` to the default branch even
  under a general "full access" grant; add a `Bash(gh pr merge:*)` allow-rule
  (`.claude/settings.local.json`) once, with the user's standing authorization.
  Driver-internal phase merges (armed via `FRONTIER_ALLOW_AUTOMERGE=1`) are
  unaffected — only the coordinator's own out-of-band merges are gated.

## Workflow 2 — keystone re-lock + honest substrate gaps (ALPHA_FUTURES_CORE_ALPHA_PILOT_V1, 31/31 COMPLETE_WITH_WARNINGS)

- **Feature identity must be content-addressed over the computational contract
  only.** A `feature_version_id` that includes `feature_request_id` (whose freq
  the duplicate-exposure gate regenerates from live registry population) makes
  identical features hash differently by registry state/order → committed locks
  become unreproducible/unresolvable. Fix = `FeatureSpec.to_identity_dict()`
  (contract minus request-id) in `FeatureVersion.derive` (PR #234). It is
  backward-INCOMPATIBLE: `FeatureLineageRecord.__post_init__` re-derives and
  raises on stored old-identity records, so clean + re-materialize the registry
  after the change. Verify the full round-trip: dry-run identity preview ==
  execute == registry record == StudySpec lock == runtime resolver.

- **Re-locking after an identity change is BOUNDED, not a full regen.** AlphaSpec
  `factor_inputs` fvers are pure provenance (never resolved at runtime) BUT are
  hashed into `alpha_spec_id` — so DO NOT edit alpha_specs in place (it cascades
  every id). Only re-run the lock-bearing phases: P03 (input_pack_lock) → P13
  (audit) → P14 (study_specs), which re-resolve against the live registry. The
  runtime resolver matches feature_version_id STRICTLY (no
  feature_id/feature_set fallback) and fails closed (`feature_pack_not_found` /
  INPUTS_BLOCKED) — never substitute.

- **`must_run_alone` + topological order safely serializes two reset phases**
  without editing the DAG. `dag_scheduler.compute_waves` builds the ready set in
  phase-list order and gives a non-parallel-safe phase its own wave, so e.g.
  P03 merges before P13 builds off updated `main` even though P13's only declared
  dep is P12. Use `resume --max-phases N` to cap a chain and insert a manual gate
  (e.g. a resolver-smoke) before the next wave.

- **Diagnostics runtime modules are pure functions over caller-supplied
  `observations`.** The phase executor loads locked feature/label VALUES from
  `study_specs.dataset_scope.feature_pack_locks` and builds the rows; the runtime
  only summarizes. So a materialized-but-unlocked feature is invisible, and the
  governed resolver rejects un-locked features (`feature_pack_not_governed_by_
  study_input_pack`). Making a blocked family real therefore needs
  materialize AND re-lock (P03→P14) AND re-run — a full second cascade, not just
  materialization.

- **Honest INCONCLUSIVE / DEPENDENCY_GAP / DATA_GAP flows through review.** When
  locked packs lack the derived features a family needs (regime trendiness/
  compression, liquidity sweep/breakout) or the dataset lacks the modality (BBO
  on an OHLCV-only DatasetVersion), the executor should load whatever real rows
  exist, return runtime status INCONCLUSIVE, name the missing inputs, and
  fabricate nothing. These pass PASS_WITH_WARNINGS — treat substrate gaps as a
  coverage finding, not an alpha failure, and hand the missing substrate to a
  follow-up campaign rather than force it inside the pilot.

- **The autonomous closeout will correctly BLOCK on a red required verifier; the
  accept-vs-fix call is the coordinator's.** A Yellow `must_run_alone` closeout
  cannot self-grant COMPLETE while `verify.py --all` is red. When the red is
  local-only (the phase branch is 0 commits ahead of `main` and the campaign's
  PRs are all CI-green), triage it: `test_cache_policy` fails purely because
  `ALPHA_DATA_ROOT` is exported (passes unset); duckdb/polars fixtures drift with
  research-venv library versions; databento canonicalize needs a local offline
  fixture. Resolve via a coordinator closeout PR that documents the triage,
  accepts the failures as out-of-scope environmental exceptions, and records
  COMPLETE_WITH_WARNINGS — do not edit source/tests to force local green.

## Workflow 2 — reference-label parallel closeout

- **NOT_RELEASED still needs a durable resume handoff.** RLPC-P03 delivered the
  opt-in reference-worker path but measured only 2.14x at workers=8 on the
  bounded real `cost_adjusted` ES/2024 grid, below the 3.0x release gate, so
  RLPC-P04 left FUTSUB policy unchanged and documented a resume on default
  workers=1. Close the backlog as delivered-engineering / NOT_RELEASED-policy,
  and point the coordinator to a resume handoff rather than quietly flipping
  worker counts.

- **Registration can become the parallel ceiling.** In the RLPC-P03 sweep,
  worker compute fell from 526.587762 s to 157.706309 s between workers=1 and
  workers=8, but parent-side serial registration rose from 3.515340 s to
  90.097791 s. Future cost-label throughput work should account for registry /
  registration overhead before assuming more compute parallelism will clear a
  release gate.
