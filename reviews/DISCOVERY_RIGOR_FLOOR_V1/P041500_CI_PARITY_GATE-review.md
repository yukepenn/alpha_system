# Fresh Adversarial Review — P041500_CI_PARITY_GATE

- Campaign: DISCOVERY_RIGOR_FLOOR_V1
- Phase: P041500_CI_PARITY_GATE (lane: yellow)
- Reviewer: Claude (fresh adversarial, WF1)
- Date: 2026-06-12
- Worktree: `/home/yuke_zhang/projects/alpha_system-wf1-relock`, branch `harness/ci-parity-gate`, diff UNCOMMITTED
- Worktree HEAD: `e53f456` (origin/main at review time: `80008c5` — branch is 2 commits behind: FUTSUB/P036000 `1141341` #391 and RIGOR-P05 `80008c5` #387, both merged after the branch was cut)
- Spec: `specs/DISCOVERY_RIGOR_FLOOR_V1/P041500_CI_PARITY_GATE-fail-before-the-pr.md`
- Executor notes: `/tmp/ci_parity_notes.md` (sandbox could not bootstrap the parity venv; coordinator bootstrapped `~/.venvs/alpha_system_ci` via `virtualenv`)

## Verdict: PASS_WITH_WARNINGS

All nine review checks pass on deterministic evidence (live mutations,
byte-identical restores, real gate run). Warnings are follow-ups and
disclosure items, not spec violations. The reviewer made ONE authorized
one-line message fix (W1, disclosed below).

## Check 1 — Scope

PASS.

- Uncommitted diff = exactly the 14 files listed in the executor notes
  (10 modified + 4 untracked-new: `tests/_helpers/__init__.py`,
  `tests/_helpers/local_data.py`, `tests/unit/frontier/test_ci_parity.py`,
  `tools/frontier/ci_parity.py`, `tools/frontier/ci_parity_requirements.txt`)
  plus the one-line `docs/SYSTEM_MAP.md` regeneration (adds `ci-parity` to
  the command-surface line; matches `just system-map` output, drift test
  passes inside the full `ci-parity` run).
- **No `src/alpha_system/**` changes**: `git diff` / `git status` contain
  none. An initial `git diff origin/main` scare (src/governance content)
  was traced to the branch being 2 commits BEHIND origin/main — that diff
  showed upstream #387/#391 content reversed, not phase edits. Verified:
  `git log origin/main..HEAD` is empty (no unpushed commits).

## Check 2 — Tamper guard stays fail-closed

PASS. Mechanism: `tools/hooks/test_tamper_guard.py` pre-substitutes the two
sanctioned tokens (`local_data_skip(`, `skip_unless_local_registry(`) with a
neutral token, THEN applies the unchanged forbidden patterns — so raw
`pytest.skip(` / `@pytest.mark.skip` anywhere else in the same file still
trips the guard.

Live mutations (scratch files under /tmp, removed after):
- raw `pytest.skip("ad hoc")` in a test file → guard rc=1, flagged. ✔
- `@pytest.mark.skip` → guard rc=1, flagged. ✔
- helper-only `skip_unless_local_registry(...)` → guard rc=0, allowed. ✔
- file importing the helper AND calling raw `pytest.skip` → rc=1
  (covered by the new self-test `test_test_tamper_guard_still_blocks_raw_skip_with_helper_import`). ✔

Guard self-tests cover both directions in `tests/test_hooks.py` (2 new tests).
Relock smoke migration:
- With local data: 6 passed (assertions intact, none weakened — the diff only
  replaces the inline `if not exists: pytest.skip` block with
  `skip_unless_local_registry(...)`; `assert label_registry.exists()` and all
  resolver assertions survive).
- `ALPHA_DATA_ROOT=/tmp/empty_data_root_review`: 5 passed, 1 skipped LOUDLY —
  `SKIPPED ... LOCAL DATA SKIP: live local registry absent (CI environment)...`. ✔
- Guard now passes on the migrated file with `FRONTIER_ALLOWED_TEST_PATHS`
  UNSET (rc=0) — env escape no longer needed there, exactly as specced. The
  generic `FRONTIER_ALLOWED_TEST_PATHS` mechanism itself is untouched.

## Check 3 — Driver integration (surgical, existing repair loop)

PASS.

- `ralph_driver.py` diff is +67 lines, zero deletions, zero reformatting:
  three new functions (`ci_parity_required_for_phase`,
  `run_ci_parity_for_phase`, `append_ci_parity_validation`) + two call sites
  immediately after `run_phase_validation` in `execute_provider_phase`
  (~L4710) and `run_provider_repair_loop` (~L4968). No state-order change,
  no STOP-semantics change (STOP check still precedes validation).
- Yellow/red only: `lane in {"yellow", "red"}`. Green lane returns
  `(True, "")` without running anything.
- Runs BEFORE review/handoff: parity is appended to the validation stage,
  which precedes the `VALIDATED → review_prompt → CLAUDE review` block.
- Failure routing: `validation_ok=False` → verdict REWORK →
  **existing** `run_provider_repair_loop` (no new mechanism); repair
  iterations re-run parity.
- Runs in the phase worktree: `run_local_command(["just","ci-parity"],
  root=execution_root)`.
- Escape: `FRONTIER_SKIP_CI_PARITY=1` emits `CI_PARITY_SKIP_ESCAPE_USED`
  event + a visible SKIPPED block in validation.md (test exists, passes).
- Mock-driver tests exist for all four required behaviors: yellow runs
  parity / green does not / failure routes bounded repair (repair_attempts
  P00 == 1, then PASS) / skip escape emits the loud event.

## Check 4 — Workflow drift test

PASS. `tests/unit/frontier/test_ci_parity.py` parses
`.github/workflows/frontier-ci.yml` ("Install Python test dependencies"
step, regex excludes the `pip install --upgrade pip` line) and compares to
`tools/frontier/ci_parity_requirements.txt`. Workflow installs
`pytest pyyaml jinja2`; pin file matches.

Mutation (b): appended `polars` to the pin file →
`test_ci_parity_requirements_match_frontier_ci_workflow` **FAILED** (1 failed
in 0.05s). Restored; sha256 byte-identical
(`f5a90c54238f2799e70f36e25917a843646a24e36737d6a66db3a21d0643748e`).

## Check 5 — Auto-merge first, gates not bypassable

PASS.

- New flow in `github_utils.merge_pr`: after the existing auth/view/draft/
  update-branch preflight, attempt `gh pr merge <n> --auto --<method>`
  first; on auto rc!=0 (auto-merge unavailable / PR already clean) fall
  through to the **unchanged** direct-merge path. The old
  `FRONTIER_ALLOW_AUTOMERGE`-gated post-failure retry block was removed
  (spec-authorized: "attempt --auto first ... fall back to current direct
  path"). Full auto_* diagnostics added to merge metadata.
- **Cannot bypass gates**: (1) `--auto` only arms GitHub's own
  required-checks gate — GitHub merges only when required checks pass;
  (2) the driver's `evaluate_merge_gate` still runs BEFORE `perform_merge`;
  (3) when armed-but-not-merged, `merge_pr` returns status
  `AUTO_MERGE_ARMED` + `auto_merge_armed=True`, and the driver's
  pre-existing `merge_result_auto_armed` branch (ralph_driver ~L3940) routes
  to `mark_auto_merge_pending` and returns False — the phase is NOT marked
  merged, DONE_CHECK does not run, resume re-enters from merge. Verified in
  source; `AUTO_MERGE_ARMED` is a pre-existing state-machine state.
- `FRONTIER_DISABLE_AUTOMERGE=1` kill switch still checked at the very top
  of merge execution (github_utils L1175) AND in `merge_gate.py` — the
  emergency stop covers the new auto-first path.
- Locked `_run_gh` + core.bare restore semantics: **zero diff lines** touch
  `_run_gh` or the bare-restore code. `pr_merge.py` change is a docstring/
  description only (still delegates to `merge_pr`).
- `tests/test_github_utils.py`: 28 passed — including auto-armed,
  auto-unavailable→direct-fallback, direct-failure-but-merged, and
  update-branch-then-auto sequences with exact command-order assertions.
- Note: driver-level `FRONTIER_ALLOW_AUTOMERGE` (ralph_driver L4394) is
  untouched — it still gates merge dry-run as before; only the merge_pr
  internal retry gating was removed.

## Check 6 — ci_parity.py refusal mechanism + bootstrap failure

PASS (with W1 one-line fix by reviewer).

- **Optional-module refusal mechanism**: `assert_no_optional_modules` runs
  `importlib.util.find_spec` INSIDE the parity venv's interpreter for a
  pinned probe list (`databento, duckdb, ib_insync, numpy, pandas, polars,
  pyarrow`) and refuses (exit 2) if any resolve. Verified live both
  directions: research venv → refused listing `duckdb, polars, pyarrow`
  with remediation message; `~/.venvs/alpha_system_ci` → clean, True.
  The venv is created with default `EnvBuilder` (no system site-packages),
  so research/system packages cannot leak in implicitly; the check runs on
  EVERY invocation, so a manually polluted venv is caught next run.
- **No silent fallback**: pointing `FRONTIER_CI_PARITY_VENV` at the research
  venv fails closed at the missing-deps stage (research venv lacks jinja2)
  with: "did not fall back to the research venv or system site-packages,
  because that would not match GitHub CI" (exit 2). Network install is
  opt-in only (`FRONTIER_CI_PARITY_ALLOW_NETWORK=1`); offline wheel dirs
  are searched first.
- **Bootstrap without ensurepip** (this host's system python has NO
  ensurepip — verified): `FRONTIER_CI_PARITY_VENV=/tmp/probe_parity_venv`
  fails closed with the script's clear ERROR message + stdlib venv's
  apt-install hint, nonzero exit (rc=1, propagated SystemExit code). The
  message did NOT mention the `virtualenv` bootstrap route the coordinator
  actually used — per review authorization, the reviewer made the one-line
  fix (see W1).
- Idempotent reuse: existing venv with working pip is reused (real run
  below used the coordinator-bootstrapped venv, no reinstall).

## Check 7 — Mutation tests (all restored byte-identical)

| Mutation | Expected | Result | Restore sha256 |
|---|---|---|---|
| (a) raw `pytest.skip(` scratch test → guard | flag (rc=1) | rc=1 ✔ (helper file rc=0; `@pytest.mark.skip` rc=1) | n/a (scratch /tmp files removed) |
| (b) `polars` appended to `ci_parity_requirements.txt` | drift test FAILS | 1 failed ✔ | `f5a90c54...43748e` (matches before) |
| (c) `ci_parity_required_for_phase` lanes `{"yellow","red"}` → `{"red"}` | a test FAILS | 4 failed: `test_yellow_phase_runs_ci_parity_check_in_mock_driver`, `test_green_phase_does_not_run...`, `test_ci_parity_failure_routes_existing_bounded_repair`, `test_ci_parity_skip_escape_emits_loud_event` ✔ | `20cf613f...bef39542` (matches before) |

## Check 8 — Validation runs (exact counts)

All with `~/.venvs/alpha_system_research/bin/python` unless noted:

- `pytest tests/unit/frontier tests/test_ralph_driver.py tests/test_hooks.py
  tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py -q`
  → **111 passed in 25.07s** (consistent with notes' 105 + 6 relock).
- Same relock file with `ALPHA_DATA_ROOT=/tmp/empty_data_root_review` →
  **5 passed, 1 skipped** (loud `LOCAL DATA SKIP` message).
- `pytest tests/test_github_utils.py -q` → **28 passed**.
- `python tools/hooks/canary_runner.py` → **All Frontier canaries passed**
  (incl. `planted_fake_alpha`, `governance_optimistic_fill`), rc=0.
- `python tools/verify.py --smoke` → rc=0.
- **Real gate run** `just ci-parity` (independent of coordinator's run):
  **3261 passed, 74 skipped in 76.57s**, exit 0 (wall 77.3s — well under
  the ~2-4 min budget claim; coordinator's earlier run had 1 SYSTEM_MAP
  drift failure, fixed by regeneration, now green — i.e. the gate caught a
  real would-be-CI failure during this very phase).
- `tests/unit/frontier/test_ci_parity.py` re-run after reviewer's one-line
  edit → 1 passed; `py_compile tools/frontier/ci_parity.py` OK.

## Check 9 — Git hygiene

PASS. `git diff --cached` empty (0 staged files); `git ls-files runs` empty;
no commit made (diff uncommitted as instructed).

## Warnings

- **W1 (reviewer edit, disclosed)**: The bootstrap-failure message did not
  mention the `virtualenv` route (this host has no system ensurepip; the
  coordinator had to bootstrap `~/.venvs/alpha_system_ci` with
  `virtualenv`). Reviewer made the authorized one-line fix in
  `tools/frontier/ci_parity.py` (`create_venv`, SystemExit branch): message
  now reads "Install python3.12-venv/ensurepip support (or bootstrap with
  `virtualenv <path>` when ensurepip is unavailable), then rerun
  `just ci-parity`." Compile + drift test re-verified. The sibling messages
  (existing-venv-without-pip, OSError branch) still say ensurepip-only —
  acceptable, same remediation applies.
- **W2**: No-ensurepip bootstrap exits rc=1 (propagated stdlib SystemExit
  code) rather than the script's own rc=2; still nonzero and fail-closed
  with a clear message. Cosmetic.
- **W3**: The tamper guard remains regex-based; alias bypasses
  (`from pytest import skip`, `alias = pytest.skip`) predate this change
  and are NOT widened by it — the substitution approach keeps raw
  `pytest.skip(` flagged even in files importing the helper. The helper
  file itself (`tests/_helpers/local_data.py`, which legitimately contains
  the one raw `pytest.skip(`) falls outside `should_check`'s scan scope by
  pre-existing rules (not a test file) — fine today, but a future guard
  hardening pass could scan `tests/_helpers/**` with an explicit allowlist.
- **W4**: Branch is 2 commits behind origin/main (#391 FUTSUB/P036000,
  #387 RIGOR-P05, both merged after branch cut). `just ci-parity` is green
  on THIS tree; re-run after rebase/update-branch before merging — the new
  gate itself (and CI) will catch any interaction with #387's new tests.
- **W5**: `append_ci_parity_validation` runs the ~77s parity gate even when
  `run_phase_validation` already failed — slightly slower repair
  iterations in exchange for complete evidence; acceptable.
- **W6**: Optional-module refusal probes a fixed 7-module list rather than
  asserting "installed == pinned deps exactly"; an exotic extra package
  (e.g. scipy) would not be caught. The list covers every optional dep the
  repo actually uses; extend if the optional surface grows.

## Research-only note

Harness/infra phase; no alpha, profitability, or tradability claims.
