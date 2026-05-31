# ALPHA_SYSTEM_V1 Runbook

## 1. Runbook Purpose

This runbook explains how to operate the `ALPHA_SYSTEM_V1` campaign for the `alpha_system` repository under Frontier Harness Generic v3.0 Workflow 2.

The campaign builds a clean-slate, local-first Alpha Research Platform for 1-minute-session-first intraday research, future multi-asset support, and future Level-2 readiness.

This campaign is not a loose prompt workflow. It must be executed as a strict Ralph-driven autonomous loop with Codex execution, Claude review, Git memory, handoffs, repair loops, artifact discipline, and semantic done-checks.

This campaign is also not a live trading campaign.

The following are explicitly out of scope:

* broker integration,
* paper trading adapter,
* live trading,
* real-time order routing,
* production execution adapter,
* live account sync,
* real-time market data dependency,
* alpha/tradability/profitability claims without later evidence and review.

A truthful `BLOCKED` state is acceptable. A false `COMPLETE` state is not acceptable.

---

## 2. Preflight Checklist

Before starting or resuming any Workflow 2 run, Ralph must verify the repository, campaign files, working tree, path policy, and artifact policy.

### 2.1 Required Repo Path

The active repo must live under the WSL2 Linux filesystem:

```bash
pwd
```

Expected path pattern:

```text
/home/<user>/projects/alpha_system
```

Canonical repo path:

```text
~/projects/alpha_system
```

Forbidden active repo or worktree paths:

```text
/mnt/c
/mnt/d
/mnt/e
OneDrive
Dropbox
Google Drive
Windows-synced folders
network drives
temporary directories
```

If the repo or worktree is under a forbidden path, stop immediately before executing any phase.

### 2.2 Required Campaign Files

Run:

```bash
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_SYSTEM_V1/GOAL.md
test -f campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_SYSTEM_V1/campaign.yaml
test -f campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md
```

If any file is missing, stop and repair the campaign contract before running implementation phases.

### 2.3 Git Preflight

Run:

```bash
git status --short
git status -sb
```

The working tree should be clean unless the current run state explicitly explains existing changes.

Before any phase starts, Ralph must know:

* current branch,
* current commit,
* whether working tree is clean,
* whether untracked files exist,
* whether generated artifacts exist,
* whether a previous phase left partial changes.

### 2.4 Artifact Preflight

Run:

```bash
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print 2>/dev/null || true
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
```

Any unexpected output must be investigated before phase execution.

Files under these paths must not be staged or committed unless the phase explicitly allows tiny fixture exceptions:

```text
data/raw/**
data/canonical/**
data/factors/**
data/labels/**
data/cache/**
metadata/*.sqlite
metadata/*.db
artifacts/**
```

### 2.5 STOP File Preflight

If a run already exists, inspect:

```bash
find runs -path "*/STOP" -type f -print
```

For the active run:

```bash
cat runs/<run_id>/STOP
```

If STOP is active, do not start a new phase, do not create a PR, and do not merge.

### 2.6 Non-Negotiable Preflight Questions

Before executing a phase, Ralph must confirm:

* Is the active worktree under WSL2 Linux filesystem?
* Is `campaign.yaml` available?
* Is `PHASE_PLAN.md` available?
* Are dependencies for the selected phase complete?
* Is there an active STOP file?
* Are raw data files staged?
* Are generated heavy artifacts staged?
* Are SQLite DB files staged?
* Is the phase allowed to modify the files it plans to modify?
* Does the phase require Claude review?
* Is this phase attempting broker/live/paper trading scope?
* Is the phase making alpha/tradability/profitability claims?
* Are tests being weakened or removed?

Any negative answer that violates campaign policy must stop phase execution.

---

## 3. WSL2 Repo Setup Expectations

The repo must be created and operated from WSL2 Ubuntu.

Expected setup pattern:

```bash
mkdir -p ~/projects
cd ~/projects
git clone <repo-url> alpha_system
cd ~/projects/alpha_system
```

Forbidden setup pattern:

```bash
cd /mnt/c/Users/<user>/OneDrive/...
cd /mnt/c/...
cd "/mnt/c/Users/<user>/Documents/..."
```

The reason is operational, not cosmetic:

* Windows-synced paths can cause file-locking problems.
* OneDrive/Dropbox/Google Drive can mutate files asynchronously.
* Agent loops perform many file operations and need Linux filesystem performance.
* Local artifacts and DBs should never be mixed with synced folders.

If the repo is accidentally created under `/mnt/c` or OneDrive, do not run the campaign there. Move or reclone under `~/projects/alpha_system`.

---

## 4. How to Start Ralph / Workflow 2

Ralph must start from the campaign contract, not from a vague prompt.

Required inputs:

* `ACTIVE_CAMPAIGN.md`
* `campaigns/ALPHA_SYSTEM_V1/GOAL.md`
* `campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md`
* `campaigns/ALPHA_SYSTEM_V1/campaign.yaml`
* `campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md`
* `campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md`
* `campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md`

Start with:

```bash
cd ~/projects/alpha_system
pwd
git status --short
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_SYSTEM_V1/campaign.yaml
```

Then Ralph must initialize a Workflow 2 run and create a unique run id.

Recommended run id format:

```text
YYYYMMDD_HHMMSS_ALPHA_SYSTEM_V1
```

Example:

```text
20260601_213000_ALPHA_SYSTEM_V1
```

Ralph must never skip directly to implementation without loading the campaign files.

---

## 5. Run Directory Creation

Every Workflow 2 run must create:

```text
runs/<run_id>/
```

Required run-level outputs:

```text
runs/<run_id>/RUN_GOAL.md
runs/<run_id>/PHASE_PLAN.md
runs/<run_id>/prd.json
runs/<run_id>/progress.txt
runs/<run_id>/state.json
runs/<run_id>/events.jsonl
runs/<run_id>/costs.jsonl
runs/<run_id>/STOP
runs/<run_id>/RUN_SUMMARY.md
```

Recommended initialization commands:

```bash
mkdir -p runs/<run_id>/phases
touch runs/<run_id>/progress.txt
touch runs/<run_id>/events.jsonl
touch runs/<run_id>/costs.jsonl
touch runs/<run_id>/STOP
```

Initial STOP file should exist but indicate not stopped, for example:

```text
STOP_REQUESTED=false
reason=
requested_by=
timestamp=
```

`RUN_GOAL.md` must summarize:

* campaign id,
* repo name,
* repo path,
* workflow mode,
* current run objective,
* non-negotiable constraints.

`PHASE_PLAN.md` in the run directory must be a copy or snapshot of the active campaign phase plan.

`prd.json` must capture machine-readable campaign/run metadata.

`state.json` must track:

* current state,
* current phase,
* current branch/worktree,
* last successful state,
* current verdict,
* repair attempt count,
* STOP status.

`RUN_SUMMARY.md` must be updated throughout the run.

---

## 6. Campaign Load

During `CAMPAIGN_LOAD`, Ralph must read and validate:

```bash
test -f campaigns/ALPHA_SYSTEM_V1/GOAL.md
test -f campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_SYSTEM_V1/campaign.yaml
test -f campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md
```

Ralph must parse `campaign.yaml` after all generated parts have been concatenated and cleaned.

Important cleanup requirement:

* Generated file delimiter lines must not remain in the actual YAML file.
* Generated chunk-end comments are syntactically valid YAML comments but should be removed from the production file after concatenation.
* If comments remain, they must not break parsing.

Cleanup validation:

```bash
! grep -R "^=====[ ]FILE:" ACTIVE_CAMPAIGN.md campaigns/ALPHA_SYSTEM_V1
! grep -R "PART [0-9][0-9]* OF [0-9][0-9]*" campaigns/ALPHA_SYSTEM_V1
```

Ralph must validate that `campaign.yaml` contains:

* `campaign_id`
* `repo_name`
* `repo_path`
* `project_profile`
* `workflow`
* `runtime`
* `models`
* `lane_policy`
* `state_machine`
* `artifact_policy`
* `git_policy`
* `review_policy`
* `merge_policy`
* `phase_defaults`
* `run_outputs`
* `phases`
* `acceptance_gates`
* `risk_controls`
* `stop_conditions`

If `campaign.yaml` cannot be parsed, stop before phase selection.

---

## 7. Phase Selection

During `PHASE_SELECT`, Ralph selects the next phase whose dependencies are complete and not blocked.

Rules:

1. Start at the phase pointer in `ACTIVE_CAMPAIGN.md`.
2. Confirm that all dependencies are complete.
3. Confirm that the previous phase has:

   * handoff,
   * checks,
   * review if required,
   * verdict,
   * merge/done status.
4. Confirm no STOP file is active.
5. Confirm no blocking risk remains unresolved.
6. Confirm the selected phase is listed in `campaign.yaml`.
7. Confirm the selected phase’s lane and review requirements.

If dependencies are missing, do not continue. Create or update run summary and stop with a blocked state.

Example phase dependency check:

```bash
grep -n "ASV1-P10" campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md
grep -n "ASV1-P10" campaigns/ALPHA_SYSTEM_V1/campaign.yaml
```

Phase selection must be recorded in:

```text
runs/<run_id>/state.json
runs/<run_id>/events.jsonl
runs/<run_id>/progress.txt
```

---

## 8. Spec Generation

During `SPEC_GENERATE`, Ralph or Claude Opus creates the phase spec:

```text
runs/<run_id>/phases/<phase_id>/spec.md
```

The phase spec must be generated from:

* `GOAL.md`
* `PHASE_PLAN.md`
* `campaign.yaml`
* `ACCEPTANCE.md`
* `RISK_REGISTER.md`
* current repo state
* previous handoffs and reviews

A valid phase spec must include:

* phase id,
* phase name,
* lane,
* dependencies,
* purpose,
* scope,
* non-goals,
* allowed paths,
* forbidden paths,
* expected files/directories,
* exact validation commands,
* test categories,
* artifact policy,
* explicit staging instructions,
* handoff requirements,
* review requirements,
* done criteria,
* auto-merge eligibility,
* relevant risks from `RISK_REGISTER.md`,
* explicit no broker/live trading statement,
* explicit no raw data/heavy artifact statement,
* explicit no alpha/tradability claim statement where relevant.

The generated executor prompt must be written to:

```text
runs/<run_id>/phases/<phase_id>/executor_prompt.md
```

The executor prompt is what Codex must follow.

Do not allow vague instructions such as:

* “add tests”
* “improve docs”
* “handle errors”
* “ensure correctness”
* “implement infrastructure”

The spec must name concrete files, tests, commands, and blocked behavior.

---

## 9. Spec Validation

During `SPEC_VALIDATE`, Ralph must verify that the generated phase spec matches the campaign contract.

Spec validation checklist:

* Phase id matches `campaign.yaml`.
* Phase name matches `PHASE_PLAN.md`.
* Lane matches `campaign.yaml`.
* Dependencies match `campaign.yaml`.
* Allowed paths are narrow and phase-specific.
* Forbidden paths include raw data, local DBs, heavy artifacts, and out-of-scope files.
* Validation commands are concrete.
* Handoff is required.
* Review is required for Yellow.
* Artifact policy is explicit.
* Broker/live trading remains out of scope.
* No alpha/tradability claims are authorized.
* No test weakening is authorized.
* No generated runtime artifacts are allowed in committed paths.

If the spec is incomplete or too broad, Ralph must repair the spec before Codex execution.

Do not execute Codex against an invalid or vague spec.

---

## 10. Worktree Creation

During `WORKTREE_CREATE`, Ralph creates or selects a clean branch/worktree for the phase.

Rules:

* Worktree must be under WSL2 Linux filesystem.
* Worktree must not be under `/mnt/c`, OneDrive, Dropbox, Google Drive, or Windows-synced folders.
* Branch name should include campaign id and phase id.
* Initial git status must be recorded.

Recommended branch naming pattern:

```text
campaign/ALPHA_SYSTEM_V1/ASV1-PXX-short-name
```

Before execution:

```bash
pwd
git status --short
git branch --show-current
```

If a worktree path violates policy, stop immediately.

---

## 11. Codex Execution

During `CODEX_EXECUTE`, Codex GPT-5.5 high executes the phase spec.

Codex must:

* read `executor_prompt.md`,
* modify only allowed files,
* avoid forbidden paths,
* create required tests,
* update required docs/configs,
* run required checks where feasible,
* write executor notes,
* prepare handoff,
* preserve artifact policy,
* avoid broad scope expansion,
* avoid broker/live scope,
* avoid alpha/tradability claims,
* avoid test weakening.

Codex must not:

* use `git add .`,
* use `git add -A`,
* force push,
* commit raw data,
* commit heavy artifacts,
* commit SQLite DB files,
* hide failed commands,
* remove or weaken tests to pass,
* create broker/live/paper trading code,
* create unbounded grid runs,
* create full L2 replay or queue model,
* claim production readiness.

Executor notes must be written to:

```text
runs/<run_id>/phases/<phase_id>/executor_notes.md
```

Executor notes must include:

* implementation summary,
* files changed,
* tests run,
* failed commands and fixes,
* generated artifacts and whether local-only,
* deviations from spec,
* remaining risks.

---

## 12. Checks Run

During `CHECKS_RUN`, Ralph runs the phase checks defined in `campaign.yaml` and the phase spec.

Common checks include:

```bash
git status --short
python -m pytest
python -m compileall src
python -m ruff check src tests || true
```

Artifact checks include:

```bash
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Phase-specific checks may include CLI help commands:

```bash
python -m alpha_system.cli registry status --help
python -m alpha_system.cli data validate --help
python -m alpha_system.cli data build-bars --help
python -m alpha_system.cli factor validate --help
python -m alpha_system.cli factor materialize --help
python -m alpha_system.cli study run --help
python -m alpha_system.cli grid run --help
python -m alpha_system.cli management grid --help
python -m alpha_system.cli ml run --help
python -m alpha_system.cli backtest run --help
python -m alpha_system.cli report build --help
```

Ralph must record checks in:

```text
runs/<run_id>/phases/<phase_id>/checks.json
```

`checks.json` must include:

* command,
* exit code,
* result,
* blocking/non-blocking status,
* stdout/stderr path or excerpt,
* timestamp,
* repair recommendation if failed.

If a command is unavailable because the phase introducing it has not run yet, this may be non-blocking only if the phase spec explicitly allows it. If the current phase introduces that command, missing CLI help is blocking.

---

## 13. Handoff Validation

Every phase must create:

```text
runs/<run_id>/phases/<phase_id>/handoff.md
```

The repo may also mirror handoffs under:

```text
handoffs/<phase_id>.md
```

A valid handoff must include:

* phase id,
* phase name,
* branch/worktree,
* files changed,
* scope summary,
* tests/checks run,
* check results,
* failed commands,
* repair attempts if any,
* artifact policy confirmation,
* raw data confirmation,
* heavy artifact confirmation,
* SQLite DB confirmation,
* broker/live scope confirmation,
* alpha/tradability claim confirmation,
* known limitations,
* relevant risks,
* review focus,
* recommended next state.

Handoff validation must fail if:

* files changed are not listed,
* checks are missing,
* failures are hidden,
* artifact policy is not addressed,
* generated artifacts are not explained,
* broker/live scope is ambiguous,
* unsupported claims appear,
* limitations are omitted.

If handoff validation fails, route to repair before Claude review.

---

## 14. Claude Review

Yellow phases require fresh Claude Opus 4.8 xhigh review.

Review input must include:

* phase spec,
* executor notes,
* diff summary,
* changed files,
* checks result,
* handoff,
* relevant risk register entries,
* source maps if available,
* artifact audit result.

Claude review must evaluate:

* scope compliance,
* phase objective completeness,
* tests adequacy,
* no-lookahead compliance where relevant,
* domain boundary compliance,
* artifact policy,
* raw data absence,
* heavy artifact absence,
* SQLite DB absence,
* broker/live absence,
* no unsupported alpha/tradability claims,
* no hidden failed runs,
* no test weakening/gaming,
* handoff quality,
* semantic done criteria.

Review output must be written to:

```text
runs/<run_id>/phases/<phase_id>/review.md
```

Claude must return one of:

* `PASS`
* `PASS_WITH_WARNINGS`
* `REWORK`
* `BLOCKED`

Green phases may skip Claude review only if the phase permits it. If skipped, Ralph must record why.

---

## 15. Verdict Parsing

During `VERDICT_PARSE`, Ralph converts the review into:

```text
runs/<run_id>/phases/<phase_id>/verdict.json
```

`verdict.json` must include:

* phase id,
* reviewer,
* review timestamp,
* verdict,
* blocking issues,
* warnings,
* required repairs,
* merge allowed true/false,
* rationale.

Allowed verdicts:

```text
PASS
PASS_WITH_WARNINGS
REWORK
BLOCKED
```

Merge is allowed only for:

```text
PASS
PASS_WITH_WARNINGS
```

Merge is blocked for:

```text
REWORK
BLOCKED
FAIL
missing verdict
unparseable verdict
ambiguous verdict
```

If verdict parsing fails, do not merge. Route to repair or review clarification.

---

## 16. Repair Loop

Repair loop is required when checks fail, handoff validation fails, or review returns `REWORK`.

Default maximum repair attempts:

```text
3
```

Repair attempts must be stored under:

```text
runs/<run_id>/phases/<phase_id>/repair_attempts/
```

Each repair attempt must record:

* repair attempt number,
* repair prompt,
* issue being repaired,
* files changed,
* checks rerun,
* result,
* updated handoff if needed,
* updated review if required.

Repair rules:

* Repair must stay within phase scope.
* Repair must not broaden allowed paths.
* Repair must not weaken tests.
* Repair must not hide failed runs.
* Repair must not remove evidence.
* Repair must not introduce broker/live scope.
* Repair must not stage artifacts.
* Repair must not fake completion.

If repair attempts are exhausted:

1. Mark phase `BLOCKED`.
2. Create blocked handoff.
3. Update `state.json`.
4. Update `progress.txt`.
5. Update `RUN_SUMMARY.md`.
6. Stop dependent phase progression.

A blocked phase is a valid outcome. False completion is not.

---

## 17. PR Creation

During `PR_CREATE`, Ralph creates a PR only after checks, handoff validation, and review requirements have passed.

Before PR creation:

```bash
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

PR description must include:

* campaign id,
* phase id,
* phase name,
* lane,
* summary,
* files changed,
* checks run,
* review verdict,
* artifact policy confirmation,
* known limitations,
* risk notes.

Do not create a PR if:

* STOP file is active,
* review required but missing,
* verdict blocks merge,
* raw data is staged,
* heavy artifacts are staged,
* local DB is staged,
* tests were weakened,
* handoff is invalid,
* phase is out of scope.

---

## 18. CI Wait

During `CI_WAIT`, Ralph waits for configured CI.

If CI exists, merge requires CI pass unless the phase spec explicitly allows a non-blocking CI exception.

If CI does not exist yet, Ralph must record:

* CI not configured,
* local checks used as current gate,
* future CI setup recommendation if relevant.

If CI fails:

* route to repair loop,
* do not merge,
* record failure in `checks.json`,
* update handoff.

---

## 19. Merge Gate

The merge gate is the final pre-merge safety check.

Ralph must verify:

* phase checks passed,
* CI passed if configured,
* handoff validates,
* review passed if required,
* verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy passed,
* no STOP file active,
* no raw data staged,
* no heavy artifacts staged,
* no SQLite DB staged,
* no generated Parquet staged outside allowed fixtures,
* no broker/live/paper scope introduced,
* no unsupported alpha/tradability claim introduced,
* no test weakening/gaming detected,
* no hidden failed run,
* semantic done-check passed.

Recommended merge gate commands:

```bash
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
```

If any blocker is found, do not merge.

---

## 20. Merge

Green and Yellow phases may auto merge when lane policy passes.

Green merge requires:

* checks pass,
* handoff valid,
* artifact policy pass,
* no forbidden paths,
* no STOP file,
* semantic done-check pass.

Yellow merge requires:

* checks pass,
* handoff valid,
* fresh Claude review,
* `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy pass,
* no forbidden paths,
* no STOP file,
* CI pass if configured,
* semantic done-check pass.

Red merge is disabled by default in this campaign.

After merge, Ralph must update:

```text
runs/<run_id>/progress.txt
runs/<run_id>/state.json
runs/<run_id>/events.jsonl
runs/<run_id>/RUN_SUMMARY.md
ACTIVE_CAMPAIGN.md if phase pointer moves
```

---

## 21. Done Check

Done check is semantic, not merely test-based.

For each phase, Ralph must verify:

* phase purpose is satisfied,
* scope is complete,
* non-goals were respected,
* expected files exist,
* tests are meaningful,
* artifacts are clean,
* handoff exists,
* review requirements are satisfied,
* no forbidden changes occurred,
* no unresolved blocking risks remain.

Examples:

* ASV1-P05 is not done unless SQLite migrations work in temp DB and no DB file is committed.
* ASV1-P10 is not done unless labels cannot leak into factor or strategy inputs.
* ASV1-P15 is not done unless reference engine remains canonical truth.
* ASV1-P19 is not done unless fast path parity is tested.
* ASV1-P20 is not done unless grid explosion controls exist.
* ASV1-P29 is not done unless final semantic closeout is complete.

Passing tests is necessary but not sufficient.

---

## 22. Next Phase

During `NEXT_PHASE`, Ralph updates campaign state and selects the next eligible phase.

Ralph must:

1. Confirm current phase is done or blocked.
2. Update run progress.
3. Update `ACTIVE_CAMPAIGN.md` phase pointer if appropriate.
4. Check STOP file.
5. Check dependencies.
6. Select next phase from `campaign.yaml`.
7. Record event in `events.jsonl`.

Do not start the next phase if:

* current phase is not done,
* current phase is blocked,
* STOP is active,
* dependencies are missing,
* artifact audit is dirty,
* handoff is invalid,
* review is missing.

---

## 23. Campaign Done Check

During `CAMPAIGN_DONE_CHECK`, Ralph verifies campaign-level acceptance gates.

The campaign cannot be marked complete unless:

* all required phases ASV1-P00 through ASV1-P29 are done,
* all Yellow phases have Claude review,
* all required checks passed,
* final v0.1 validation completed,
* artifact audit passed,
* no raw data committed,
* no heavy artifacts committed,
* no SQLite DB committed,
* no broker/live/paper scope introduced,
* no unsupported alpha/tradability claims,
* no hidden failed runs,
* no test weakening/gaming,
* final semantic done-check completed,
* closeout docs exist.

Required final closeout files:

```bash
test -f docs/V0_1_VALIDATION.md
test -f docs/V0_1_RELEASE_NOTES.md
test -f docs/KNOWN_LIMITATIONS.md
test -f docs/NEXT_CAMPAIGN_CANDIDATES.md
test -f campaigns/ALPHA_SYSTEM_V1/CLOSEOUT.md
```

Allowed final verdicts:

```text
COMPLETE
COMPLETE_WITH_WARNINGS
BLOCKED
```

If any critical acceptance gate fails, final verdict must be `BLOCKED`.

---

## 24. Run Summary

`RUN_SUMMARY.md` must be updated throughout the run and finalized at campaign closeout.

Required contents:

* campaign id,
* repo path,
* run id,
* workflow mode,
* current/final state,
* phases completed,
* phases blocked,
* checks run,
* review verdicts,
* repair attempts,
* artifact audit result,
* no-lookahead status,
* fast parity status,
* registry status,
* final acceptance gate status,
* known limitations,
* next campaign candidates,
* explicit no broker/live/paper statement,
* explicit no alpha/tradability claim statement,
* final verdict.

Run summary path:

```text
runs/<run_id>/RUN_SUMMARY.md
```

The run summary must not hide failed runs or repair attempts.

---

## 25. How to Stop via STOP File

To request a stop, update:

```text
runs/<run_id>/STOP
```

Recommended content:

```text
STOP_REQUESTED=true
reason=<reason>
requested_by=<human|ralph|reviewer>
timestamp=<timestamp>
```

When STOP is active, Ralph must:

* finish only safe state recording,
* not start a new phase,
* not run Codex,
* not create a PR,
* not merge,
* update `state.json`,
* update `progress.txt`,
* update `RUN_SUMMARY.md`.

Ralph must check STOP before:

* phase selection,
* worktree creation,
* Codex execution,
* PR creation,
* merge gate,
* merge,
* next phase.

Ignoring STOP is a critical Workflow 2 violation.

---

## 26. How to Resume

To resume a stopped or interrupted run:

1. Confirm repo path:

```bash
pwd
```

2. Inspect run state:

```bash
cat runs/<run_id>/state.json
cat runs/<run_id>/progress.txt
cat runs/<run_id>/RUN_SUMMARY.md
```

3. Inspect STOP file:

```bash
cat runs/<run_id>/STOP
```

4. Inspect latest phase artifacts:

```bash
ls runs/<run_id>/phases/<phase_id>/
cat runs/<run_id>/phases/<phase_id>/handoff.md
cat runs/<run_id>/phases/<phase_id>/verdict.json
cat runs/<run_id>/phases/<phase_id>/checks.json
```

5. Confirm artifact policy:

```bash
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

6. Resume from the recorded state, not from memory.

Valid resume states include:

* repair loop,
* checks rerun,
* handoff validation,
* Claude review,
* verdict parsing,
* PR creation,
* CI wait,
* merge gate,
* next phase.

Do not restart blindly unless intentionally abandoning the old run and creating a new run.

---

## 27. How to Inspect Artifacts

Workflow artifacts are under:

```text
runs/<run_id>/
```

Phase artifacts are under:

```text
runs/<run_id>/phases/<phase_id>/
```

Repo-level handoffs and reviews may be mirrored under:

```text
handoffs/
reviews/
```

Local-only generated research artifacts may appear under:

```text
artifacts/
```

Local-only data may appear under:

```text
data/
```

Local-only registry DBs may appear under:

```text
metadata/
```

Before staging any file, inspect:

```bash
git status --short
```

Before merge, inspect:

```bash
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Full local-only artifacts should not be committed.

Commit-eligible examples:

* source files,
* configs,
* docs,
* tests,
* small synthetic fixtures,
* handoffs,
* reviews,
* source maps,
* curated summaries,
* validation summaries.

Commit-forbidden examples:

* raw data,
* canonical data,
* factor values,
* label values,
* generated signal stores,
* full grid outputs,
* full trade logs,
* generated review bundles,
* runtime SQLite DBs,
* model binaries,
* large Parquet files,
* logs,
* caches.

---

## 28. Handling Blocked Phases

A phase must be marked `BLOCKED` when:

* repair attempts are exhausted,
* Claude verdict is `BLOCKED`,
* campaign scope is violated,
* required dependency is missing,
* artifact policy cannot be repaired,
* no-lookahead defect remains,
* execution truth ambiguity remains,
* tests were weakened or cannot be trusted,
* broker/live scope was introduced,
* raw/heavy artifacts were committed and cannot be safely repaired.

Blocked phase handling:

1. Stop dependent phase progression.
2. Preserve evidence.
3. Create blocked handoff.
4. Update `state.json`.
5. Update `progress.txt`.
6. Update `RUN_SUMMARY.md`.
7. Record blocker in `events.jsonl`.
8. Do not mark phase complete.
9. Do not merge unsafe partial work.
10. Escalate to human/ChatGPT strategy review if needed.

A blocked handoff must include:

* blocker summary,
* failed checks,
* review findings,
* files changed,
* artifact status,
* repair attempts,
* why repair stopped,
* recommended options:

  * repair in same phase,
  * revert,
  * split scope,
  * amend campaign,
  * accept blocked state.

---

## 29. Preventing Raw Data and Heavy Artifact Commits

The campaign requires explicit staging only.

Forbidden:

```bash
git add .
git add -A
```

Safe pattern:

```bash
git add path/to/specific_file_1.py
git add path/to/specific_file_2.md
git add path/to/specific_test.py
```

Before staging, run:

```bash
git status --short
```

Before commit or merge, run:

```bash
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
```

If any forbidden file appears:

* do not stage,
* do not commit,
* repair `.gitignore` if needed,
* remove generated file from repo tree if safe,
* document in handoff.

Tiny fixture exception:

* Synthetic tiny fixtures under `tests/fixtures/**` may be committed only if documented and below repository size threshold.
* Fixture results must never be presented as market evidence.

---

## 30. Handling Green/Yellow Auto PR and Auto Merge

### Green

Green phases are low-risk docs, scaffolding, or mechanical phases.

Green phases may auto execute, auto repair, auto PR, and auto merge when:

* checks pass,
* handoff exists,
* artifact policy passes,
* no forbidden paths are staged,
* no STOP file is active,
* semantic done-check passes,
* review passes if requested.

ASV1-P28 is Green.

### Yellow

Yellow phases are material engineering or research infrastructure phases.

Yellow phases may auto execute and auto repair, but merge requires:

* checks pass,
* handoff validates,
* fresh Claude Opus review exists,
* verdict is `PASS` or `PASS_WITH_WARNINGS`,
* artifact policy passes,
* no forbidden paths are staged,
* no STOP file is active,
* CI passes if configured,
* semantic done-check passes.

Most phases are Yellow.

### Red

Red phases are production, destructive, live, external, or costly operations.

This campaign should not require Red phases.

If Red scope appears unexpectedly, stop unless explicitly authorized and in scope.

---

## 31. Red Authorization

Red operations are pre-authorized automatic when scoped, not banned. However, this campaign should not require Red.

A Red operation requires all environment variables:

```bash
echo "$PROJECT_OP_AUTHORIZED"
echo "$PROJECT_OP_SCOPE"
echo "$PROJECT_OP_EXPIRES"
```

Required variables:

```text
PROJECT_OP_AUTHORIZED
PROJECT_OP_SCOPE
PROJECT_OP_EXPIRES
```

Examples of Red operations:

* broker integration,
* paper trading against broker API,
* live trading,
* live order routing,
* destructive production operation,
* costly external cloud operation,
* real-time external data pull with cost.

For `ALPHA_SYSTEM_V1`, these are out of scope:

* broker integration,
* paper trading,
* live trading,
* live order routing,
* costly external infrastructure,
* destructive production operations.

If Red appears in this campaign, Ralph should normally mark the phase blocked unless the campaign contract is explicitly amended.

---

## 32. Final Campaign Closeout

ASV1-P29 performs final validation and closeout.

Required closeout files:

```bash
test -f docs/V0_1_VALIDATION.md
test -f docs/V0_1_RELEASE_NOTES.md
test -f docs/KNOWN_LIMITATIONS.md
test -f docs/NEXT_CAMPAIGN_CANDIDATES.md
test -f campaigns/ALPHA_SYSTEM_V1/CLOSEOUT.md
```

Required final validation checks:

```bash
python -m pytest
python -m compileall src
python -m ruff check src tests || true
git status --short
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Required CLI smoke checks:

```bash
python -m alpha_system.cli registry status --help
python -m alpha_system.cli data validate --help
python -m alpha_system.cli data build-bars --help
python -m alpha_system.cli factor validate --help
python -m alpha_system.cli factor materialize --help
python -m alpha_system.cli study run --help
python -m alpha_system.cli backtest run --help
python -m alpha_system.cli grid run --help
python -m alpha_system.cli management grid --help
python -m alpha_system.cli ml run --help
python -m alpha_system.cli report build --help
```

Final closeout must state:

* final verdict,
* completed phases,
* blocked phases if any,
* acceptance gates,
* artifact audit,
* no-lookahead status,
* fast/reference parity status,
* registry/reproducibility status,
* known limitations,
* next campaign candidates,
* no broker/live/paper trading,
* no alpha/tradability/profitability claims.

Allowed final verdicts:

```text
COMPLETE
COMPLETE_WITH_WARNINGS
BLOCKED
```

If any critical risk remains unresolved, final verdict must be `BLOCKED`.

---

## 33. Operator Quick Commands

### Repo and Campaign Checks

```bash
pwd
git status --short
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_SYSTEM_V1/GOAL.md
test -f campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md
test -f campaigns/ALPHA_SYSTEM_V1/campaign.yaml
test -f campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md
test -f campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md
test -f campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md
```

### Artifact Audit

```bash
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
```

### Test and Static Checks

```bash
python -m pytest
python -m compileall src
python -m ruff check src tests || true
```

### CLI Smoke Checks

```bash
python -m alpha_system.cli registry status --help
python -m alpha_system.cli data validate --help
python -m alpha_system.cli data build-bars --help
python -m alpha_system.cli factor validate --help
python -m alpha_system.cli factor materialize --help
python -m alpha_system.cli study run --help
python -m alpha_system.cli backtest run --help
python -m alpha_system.cli grid run --help
python -m alpha_system.cli management grid --help
python -m alpha_system.cli ml run --help
python -m alpha_system.cli report build --help
```

### Handoff / Review Inspection

```bash
ls runs/<run_id>/phases/<phase_id>/
cat runs/<run_id>/phases/<phase_id>/handoff.md
cat runs/<run_id>/phases/<phase_id>/review.md
cat runs/<run_id>/phases/<phase_id>/verdict.json
cat runs/<run_id>/phases/<phase_id>/checks.json
```

### STOP File

```bash
cat runs/<run_id>/STOP
```

### Git Safety

```bash
git status --short
git diff --stat
git diff --name-only
```

Do not use:

```bash
git add .
git add -A
```

Use explicit staging only:

```bash
git add <specific-file>
```

---

## 34. Final Reminder of Out-of-Scope Boundaries

`ALPHA_SYSTEM_V1` builds a local-first Alpha Research Platform foundation.

It does not build:

* broker integration,
* paper trading,
* live trading,
* order routing,
* live account sync,
* production execution,
* real-time market data infrastructure,
* cloud data platform,
* paid database platform,
* server-first architecture,
* full L2 replay engine,
* queue-position simulator,
* production ML system,
* web UI.

It must not claim:

* alpha,
* tradability,
* profitability,
* market-beating performance,
* production readiness,
* live readiness,
* candidate approval without review.

The correct final output of this campaign is a reproducible, local-first, test-heavy, reviewable research-platform foundation with clear limitations and next-campaign candidates.

A truthful blocked state is acceptable.

A false complete state is not.
