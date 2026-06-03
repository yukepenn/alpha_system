# ALPHA_RESEARCH_GOVERNANCE_MVP Runbook

## 1. Runbook Purpose

This runbook is the operator manual for executing the `ALPHA_RESEARCH_GOVERNANCE_MVP`
campaign under Frontier Harness Generic v3.0 Workflow 2. It covers preflight, start,
each Workflow 2 state, STOP/resume, artifact inspection, blocked-phase handling,
raw/heavy commit prevention, lane behavior, closeout, and quick commands.

The campaign is the admissibility and evidence-governance layer for AI alpha research.
It implements governance machinery only. It does not search for alpha, ingest real data,
or touch broker/live/paper trading. Keep that boundary in mind at every state.

## 2. Preflight Checklist

### 2.1 Required Repo Path
The active repo and all worktrees must be under `~/projects/alpha_system` on the WSL2
Linux filesystem. Forbidden active locations: `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive,
Dropbox, Google Drive, Windows-synced folders, network drives, temp directories.

```bash
cd ~/projects/alpha_system
pwd                 # must be /home/<user>/projects/alpha_system
git status -sb
```

### 2.2 Required Campaign Files
```bash
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/GOAL.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/PHASE_PLAN.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACCEPTANCE.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RISK_REGISTER.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RUNBOOK.md
test ! -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACTIVE_CAMPAIGN.md
```

### 2.3 YAML Parse and Consistency
```bash
python - <<'PY'
from pathlib import Path
import yaml
p = Path("campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml")
data = yaml.safe_load(p.read_text())
assert data["campaign_id"] == "ALPHA_RESEARCH_GOVERNANCE_MVP"
assert "phases" in data and data["phases"]
assert "acceptance_gates" in data and data["acceptance_gates"]
phase_ids = [ph["id"] for ph in data["phases"]]
covered = []
for g in data["acceptance_gates"].values():
    covered.extend(g.get("phases", []))
assert set(phase_ids) == set(covered), "acceptance gate coverage mismatch"
print("campaign.yaml parses and gate coverage is complete")
PY
```

### 2.4 Git and Artifact Preflight
```bash
git status --short
git ls-files runs                       # must be empty
find data -type f ! -name README.md ! -name ".gitkeep" -print   # must be empty
find metadata -type f ! -name README.md ! -name ".gitkeep" -print # must be empty
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
python tools/verify.py --smoke
```

### 2.5 STOP File Preflight
```bash
ls runs/*/STOP 2>/dev/null || echo "no active STOP file"
```

### 2.6 Non-Negotiable Preflight Questions
* Is the worktree under the WSL2 path? If not, STOP at RUN_INIT.
* Does `campaign.yaml` parse and cover every phase in exactly one gate? If not, block.
* Is any forbidden artifact already staged? If so, unstage before starting.
* Is any broker/live/real-data scope present? If so, STOP and escalate.

## 3. WSL2 Repo Setup Expectations
Run from WSL2 Ubuntu against the Linux-filesystem clone at `~/projects/alpha_system`.
Use the project Python environment. Never operate the active repo from a Windows-synced
path. Worktrees created by Workflow 2 must also be under the WSL2 filesystem.

## 4. How to Start Ralph / Workflow 2
Start a Workflow 2 run with the campaign loaded as the active campaign. Ralph initializes
run state under `runs/<run_id>/`, loads the campaign contract, and selects the first
incomplete phase (initially `ARGOV-P00`). Ralph owns all state transitions and gates;
Codex executes specs; Claude Opus reviews YELLOW phases.

## 5. Run Directory Creation (RUN_INIT)
Ralph creates `runs/<run_id>/` with `RUN_GOAL.md`, `PHASE_PLAN.md`, `prd.json`,
`progress.txt`, `state.json`, `events.jsonl`, `costs.jsonl`, and (when needed) `STOP` and
`RUN_SUMMARY.md`. All of `runs/**` is local-only and must never be staged or committed.
Confirm the worktree path is under WSL2 before proceeding.

## 6. Campaign Load (CAMPAIGN_LOAD)
Ralph loads `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml`, the GOAL, PHASE_PLAN,
ACCEPTANCE, RISK_REGISTER, and this RUNBOOK. If the YAML fails to parse or gate coverage is
incomplete, STOP (`campaign YAML invalid` / `acceptance gates missing phases`).

## 7. Phase Selection (PHASE_SELECT)
Ralph selects the lowest-numbered incomplete phase whose dependencies are complete.
Check STOP before selection. If dependencies are missing or blocked, STOP phase selection.

## 8. Spec Generation (SPEC_GENERATE)
Ralph requests a phase spec (Claude Opus) derived from the PHASE_PLAN detailed section for
the selected phase. The spec is written to `runs/<run_id>/phases/<phase_id>/spec.md`
(local-only).

## 9. Spec Validation (SPEC_VALIDATE)
Validate the spec against the phase contract: allowed/forbidden paths, validation
commands, artifact policy, and done criteria match `campaign.yaml`. If the spec contradicts
the contract, reject and regenerate; do not proceed on an inconsistent spec.

## 10. Worktree Creation (WORKTREE_CREATE)
Ralph creates an isolated worktree under the WSL2 filesystem. Confirm the path is not under
any forbidden Windows-synced location. Check STOP before creation.

## 11. Codex Execution (CODEX_EXECUTE)
Codex implements only the phase scope using explicit staging. Codex must honor an active
STOP file, never use `git add .`/`git add -A`, never force push, and never introduce
broker/live/real-data scope or unsupported claims. Codex writes truthful executor notes.

## 12. Checks Run (CHECKS_RUN)
Run the phase `checks` from `campaign.yaml`. Typical governance checks:
```bash
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q   # P15, P16, P18, P19
python -m pytest tests/no_lookahead -q             # P06, P14
python tools/hooks/canary_runner.py                # P14, P18, P19
git ls-files runs
```
Record every check and result in `runs/<run_id>/phases/<phase_id>/checks.json` (local-only).

## 13. Handoff Validation (HANDOFF_VALIDATE)
Codex writes the commit-eligible handoff to
`handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/<PHASE_ID>.md` and a local-only
`runs/<run_id>/phases/<phase_id>/handoff.md`. Ralph validates that the handoff lists exact
staged files, validation results, artifact-policy confirmation, and explicit no-scope/no-claim
statements. Missing handoff blocks merge (R-015).

## 14. Claude Review (CLAUDE_REVIEW)
Every phase is YELLOW and requires fresh Claude Opus review. The reviewer must be
independent of the implementer. Review verifies governance completeness, fail-closed
validation, reviewer-independence enforcement, ledger/evidence/promotion gating, canary
fail-closed behavior, artifact policy, and absence of prohibited scope/claims. Commit-eligible
review artifacts go under `reviews/ALPHA_RESEARCH_GOVERNANCE_MVP/**`; the local-only copy is
`runs/<run_id>/phases/<phase_id>/review.md`.

## 15. Verdict Parsing (VERDICT_PARSE)
Ralph parses `verdict.json`. Allowed: `PASS`, `PASS_WITH_WARNINGS`, `REWORK`, `BLOCKED`.
Merge-eligible: `PASS`, `PASS_WITH_WARNINGS`. `REWORK` → repair loop. `BLOCKED`/`FAIL` →
blocked handoff and stop.

## 16. Repair Loop (REWORK)
Bounded repair, `max_repair_attempts = 3`, tracked under
`runs/<run_id>/phases/<phase_id>/repair_attempts/`. Codex repairs only valid in-scope
findings. Exceeding the limit routes to a truthful `BLOCKED` handoff. Fake completion is
forbidden.

## 17. PR Creation (PR_CREATE)
On a merge-eligible verdict, Ralph creates the PR with the curated staged set. Confirm no
`runs/` path and no forbidden artifact is staged before creating the PR.

## 18. CI Wait (CI_WAIT)
If CI is configured, wait for it to pass. CI failure routes to repair or blocked handoff.

## 19. Merge Gate (MERGE_GATE)
Merge requires: checks pass, handoff valid, `PASS`/`PASS_WITH_WARNINGS`, artifact policy
pass, no forbidden paths, no STOP file, CI pass if configured, and semantic done-check pass.
Global blockers include any staged forbidden artifact, hidden failed run, test weakening,
broker/live/real-data scope, unsupported claim, candidate-without-evidence, or
promotion-without-trial-ledger.

## 20. Merge (MERGE)
Ralph merges the reviewed phase. `main` is protected from direct risky changes; merges flow
through the gated PR. No force push, no auto-merge bypass.

## 21. Done Check (DONE_CHECK)
Ralph confirms the phase done criteria (spec scope complete, checks passed or exceptions
documented, handoff present, review artifacts present, artifact policy satisfied, curated
files committed). Update `ACTIVE_CAMPAIGN.md` last-completed pointer.

## 22. Next Phase (NEXT_PHASE)
Check STOP, then select the next dependency-satisfied phase and repeat.

## 23. Campaign Done Check (CAMPAIGN_DONE_CHECK)
After `ARGOV-P19`, Ralph runs the acceptance audit (`ACCEPTANCE.md`) across all gates and a
final semantic done-check. The campaign is done only when all gates pass and no prohibited
shortcut applies.

## 24. Run Summary (RUN_SUMMARY)
Ralph writes `runs/<run_id>/RUN_SUMMARY.md` (local-only) and the campaign records
`campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/CLOSEOUT.md` with the final verdict.

## 25. How to Stop via STOP File
Create `runs/<run_id>/STOP` with a short reason. Ralph checks STOP before provider calls,
phase selection, Codex execution, validation, review, PR, CI, merge, done-check, and
next-phase selection, and halts at the next checkpoint.
```bash
echo "operator stop: <reason>" > runs/<run_id>/STOP
```

## 26. How to Resume
Remove or resolve the STOP condition, then resume the run. Ralph resumes from recorded run
state and does not regenerate completed, merged phases.
```bash
rm runs/<run_id>/STOP
```

## 27. How to Inspect Artifacts
```bash
ls runs/<run_id>/phases/<phase_id>/
cat handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/<PHASE_ID>.md
ls reviews/ALPHA_RESEARCH_GOVERNANCE_MVP/
git ls-files runs                      # must remain empty
```

## 28. Handling Blocked Phases
A `BLOCKED` verdict or exceeded repair limit produces a truthful blocked handoff. Dependent
phases are blocked. Do not fake completion. Escalate to the human for direction. Resolve the
blocker (scope, authorization, or impossible validation) before resuming.

## 29. Preventing Raw Data and Heavy Artifact Commits
```bash
git status --short
git diff --name-only
git ls-files runs
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```
If any forbidden path is staged, unstage it and repair the handoff before merge. Stage
explicit paths only; never `git add .` / `git add -A`.

## 30. Green / Yellow / Red Lane Behavior

### Green
Not used in this campaign by default; if a pure-docs phase is ever marked GREEN, it still
requires checks, handoff, and artifact policy.

### Yellow
All 20 phases are YELLOW: automatic execute/repair/PR/merge after fresh Claude Opus review
with a `PASS`/`PASS_WITH_WARNINGS` verdict and all gates passing.

### Red
Not expected. This campaign excludes live/broker/external/destructive/costly scope. If RED
scope appears unexpectedly, STOP unless `PROJECT_OP_AUTHORIZED`, `PROJECT_OP_SCOPE`, and
`PROJECT_OP_EXPIRES` are armed and the contract explicitly allows it (it does not here).

## 31. Red Authorization
Red-lane operations require all three scope variables present, scope-matched, and unexpired.
This campaign does not authorize any Red operation; treat any Red-triggering action as a
blocking scope-creep event (R-018).

## 32. Final Campaign Closeout
At `ARGOV-P19`: confirm acceptance audit passes, run the final semantic done-check, write
`CLOSEOUT.md` with the final verdict (`COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`),
update `ACTIVE_CAMPAIGN.md`, and add durable lessons to `project-skill` when applicable.
Confirm the artifact audit is clean and no prohibited scope or claim exists.

## 33. Operator Quick Commands

### Repo and Campaign Checks
```bash
cd ~/projects/alpha_system
git status --short
git status -sb
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml
```

### Artifact Audit
```bash
git ls-files runs
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

### Tests and Static Checks
```bash
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
python -m pytest tests/no_lookahead -q
python tools/hooks/canary_runner.py
```

### Handoff / Review Inspection
```bash
cat handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/<PHASE_ID>.md
ls reviews/ALPHA_RESEARCH_GOVERNANCE_MVP/
```

### STOP File
```bash
echo "operator stop: <reason>" > runs/<run_id>/STOP
rm runs/<run_id>/STOP
```

### Git Safety
```bash
# Stage explicit paths only — never:
#   git add .
#   git add -A
# Never force push.
git add <explicit/path/one> <explicit/path/two>
```

## 34. Final Reminder of Out-of-Scope Boundaries
This campaign installs governance machinery only. It must end with: no real data ingestion,
no IBKR/broker connectivity, no paper/live trading, no order routing, no L2 replay, no
ML/DL expansion, no strategy optimization, no portfolio allocation, no production execution,
and no alpha/profitability/tradability/production-readiness claims. Be aggressive about
evidence governance; be conservative about market claims and trading scope.
