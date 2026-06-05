# ASV1-P01 Handoff

## Phase

- Phase ID: `ASV1-P01`
- Phase name: Frontier Harness Baseline Files
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p01-frontier-harness-baseline-files`
- Worktree: `/home/yuke_zhang/projects/alpha_system`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P01` (local-only)

## Files Created Or Updated

- `AGENTS.md`
- `CLAUDE.md`
- `frontier.yaml`
- `ACTIVE_CAMPAIGN.md`
- `.github/workflows/frontier-automerge.yml`
- `tools/frontier/merge_gate.py`
- `scripts/ralph/README.md`
- `docs/HARNESS_WORKFLOW_2.md`
- `docs/GIT_AND_ARTIFACT_DISCIPLINE.md`
- `docs/STOP_AND_RESUME.md`
- `handoffs/ASV1-P01.md`

No `src/**`, `tests/**`, data, metadata, artifacts, `pyproject.toml`, review verdict, PR, merge, deployment, broker, paper-trading, live-trading, or order-routing scope was introduced.

## Lane Policy Summary

Green is low-risk automatic work gated by checks, artifact policy, handoff validation, no STOP, and semantic done-check.

Yellow is material engineering or research work. It requires fresh Claude Opus review and a parsed `PASS` or `PASS_WITH_WARNINGS` before merge eligibility.

Red covers external, destructive, live, production, costly, or broker-adjacent operations and requires scoped authorization through `PROJECT_OP_AUTHORIZED`, `PROJECT_OP_SCOPE`, and `PROJECT_OP_EXPIRES`. This phase introduced no Red operation.

## Workflow 2 Summary

The control surface now documents the required state order:

```text
RUN_INIT -> CAMPAIGN_LOAD -> PHASE_SELECT -> SPEC_GENERATE -> SPEC_VALIDATE -> WORKTREE_CREATE -> CODEX_EXECUTE -> CHECKS_RUN -> HANDOFF_VALIDATE -> CLAUDE_REVIEW -> VERDICT_PARSE -> PR_CREATE -> CI_WAIT -> MERGE_GATE -> MERGE -> DONE_CHECK -> NEXT_PHASE -> CAMPAIGN_DONE_CHECK -> RUN_SUMMARY
```

Ralph owns driver state, STOP/resume, validation orchestration, handoff validation, review routing, verdict parsing, bounded repair, PR/CI/merge gates, done-checks, next-phase selection, and run summaries. Codex owns generated-spec execution, scoped repair, authorized local checks, and truthful handoffs. Claude Opus owns Yellow/Red semantic review. Claude Sonnet owns verifier/source-map/audit support. ChatGPT owns strategic reasoning.

## Hook And Artifact Enforcement

Existing hook wrappers under `.githooks/` delegate to Python guards under `tools/hooks/`. The documented guard set includes artifact, bulk-add, secret, test-tamper, forbidden-pattern, and boundary checks.

`tools/hooks/artifact_guard.py` already treats `runs/**`, local data directories, metadata DBs, artifacts, logs, caches, and heavy/generated files as forbidden. `tools/hooks/bulk_add_guard.py` supports explicit staging discipline by blocking suspiciously large staged additions.

Known enforcement gap: executable shell wrappers under `.githooks/` do not expose a formal `--check` or dry-run option. They were not armed or run as mutating hooks in this phase. The Python guard modules remain directly invokable, and formal dry-run hook entrypoints should be considered follow-up work.

## Run-Artifact Convention

`runs/**` is local-only runtime state and was not staged. Run-local specs, prompts, executor notes, checks, handoffs, reviews, verdicts, done-checks, ledgers, STOP files, PR bodies, CI status, merge-gate results, summaries, and repair attempts must remain out of git.

Commit-eligible handoffs belong under `handoffs/<PHASE_ID>.md`; for this phase, that is `handoffs/ASV1-P01.md`. Commit-eligible review artifacts belong under `reviews/**` and are reviewer-owned. No review artifact was created by Codex.

## Commit-Eligible Vs Local-Only

Commit-eligible for this phase: the allowed harness control files, policy docs, hook/control-plane scaffolding updates, lightweight workflow text, `ACTIVE_CAMPAIGN.md`, and `handoffs/ASV1-P01.md`.

Local-only and never staged: `runs/**`, raw/canonical/factor/label/cache data, metadata DBs and journals, logs, caches, generated heavy artifacts, Parquet/Arrow/Feather files, local SQLite/DB files, and generated report bundles.

## Validation Results

All requested ASV1-P01 validation commands were run locally. No command created a PR, merge, deployment, live/paper/broker operation, review artifact, or verdict artifact.

```text
git status --short
PASS - expected ASV1-P01 modified/untracked files only.

git status -sb
PASS - branch is auto/alpha_system_v1/asv1-p01-frontier-harness-baseline-files...origin/main with expected ASV1-P01 changes.

pwd
PASS - /home/yuke_zhang/projects/alpha_system

test -f AGENTS.md
test -f CLAUDE.md
test -f frontier.yaml
test -f docs/HARNESS_WORKFLOW_2.md
test -f docs/GIT_AND_ARTIFACT_DISCIPLINE.md
test -f docs/STOP_AND_RESUME.md
test -f handoffs/ASV1-P01.md
PASS

test -d .codex
test -d .claude
test -d .githooks
test -d tools/frontier
test -d tools/hooks
test -d scripts/ralph
PASS

grep -R "RUN_INIT" AGENTS.md CLAUDE.md frontier.yaml docs/HARNESS_WORKFLOW_2.md
PASS - all four files contain RUN_INIT.

grep -R "PROJECT_OP_AUTHORIZED" AGENTS.md CLAUDE.md frontier.yaml docs/HARNESS_WORKFLOW_2.md
PASS - all four files contain PROJECT_OP_AUTHORIZED.

grep -R "git add ." AGENTS.md CLAUDE.md docs/GIT_AND_ARTIFACT_DISCIPLINE.md || true
PASS - occurrences are forbidden examples only.

grep -R "git add -A" AGENTS.md CLAUDE.md docs/GIT_AND_ARTIFACT_DISCIPLINE.md || true
PASS - occurrences are forbidden examples only.

git ls-files runs
PASS - returned empty.

find data -type f ! -name README.md ! -name ".gitkeep" -print
PASS - returned empty.

find metadata -type f ! -name README.md ! -name ".gitkeep" -print
PASS - returned empty.

find artifacts -type f -size +1M -print 2>/dev/null || true
PASS - returned empty.

find . -path ./tests/fixtures -prune -o -type f -name "*.parquet" -print
PASS - returned empty.

find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
PASS - returned empty.
```

Hook handling: executable `.githooks/` shell wrappers do not expose a dry-run or `--check` mode, so they were not run as hooks in this phase. This limitation is documented in `docs/GIT_AND_ARTIFACT_DISCIPLINE.md`.

Final staged-set audit before commit:

```text
git diff --cached --name-only
PASS - staged files:
.github/workflows/frontier-automerge.yml
ACTIVE_CAMPAIGN.md
AGENTS.md
CLAUDE.md
docs/GIT_AND_ARTIFACT_DISCIPLINE.md
docs/HARNESS_WORKFLOW_2.md
docs/STOP_AND_RESUME.md
frontier.yaml
handoffs/ASV1-P01.md
scripts/ralph/README.md
tools/frontier/merge_gate.py

git diff --cached --name-only | grep '^runs/' || true
PASS - returned empty.

python tools/hooks/pre_commit.py
PASS - hook check implementation passed against the staged set.

git diff --cached --check
PASS
```

## Artifact Policy Confirmation

- `runs/**` local-only: confirmed by `git ls-files runs` and staged-set grep returning empty.
- Raw data staged: no.
- Heavy artifacts staged: no.
- SQLite/DB files staged: no.
- Parquet/Arrow/Feather staged: no.
- Logs/caches staged: no.

## Explicit Staging Confirmation

`git add .`, `git add -A`, and force push were not used during implementation, validation, or staging. Files were staged by explicit path only. `git diff --cached --name-only` contained no `runs/` path.

## Scope Confirmations

- Broker/live/paper trading scope introduced: no.
- Order routing introduced: no.
- Production deployment introduced: no.
- Cloud/server/paid database dependency introduced: no.
- Unsupported alpha/profitability/robustness/tradability claim introduced: no.
- Tests weakened or modified: no.

## Risk Dispositions

- R-012 Raw data committed accidentally: mitigated by docs, artifact policy, clean data audit, and staged-set audit.
- R-013 Heavy artifact committed accidentally: mitigated by docs, artifact policy, clean heavy artifact audit, and staged-set audit.
- R-019 Local path/WSL2 misuse: mitigated by docs and current worktree path.
- R-020 Windows/OneDrive path contamination: mitigated by docs.
- R-022 Accidental broker/live scope creep: mitigated; no such scope added.
- R-023 Cloud/server dependency creep: mitigated; no such dependency added.
- R-026 Handoff missing/incomplete: mitigated by this commit-eligible handoff.
- R-027 Verdict not parsed: requires follow-up by Ralph/reviewer; verdict parsing conventions are documented, and Codex did not create `verdict.json`.
- R-028 STOP file ignored: mitigated in docs/control surface.
- R-029 Repair loop unbounded: mitigated in docs/control surface.
- R-038 Generated SQLite DB committed: mitigated by clean DB audit and staged-set audit.
- R-039 Generated Parquet committed: mitigated by clean Parquet audit and staged-set audit.

## Known Limitations

- `.githooks/` shell wrappers do not expose a dedicated dry-run mode.
- Older general docs outside the ASV1-P01 allowed doc paths still mention legacy `FRONTIER_RED_*` names. The ASV1-P01-required control surface and in-scope helper paths use `PROJECT_OP_*`.
- Claude review, verdict parsing, done-check, PR, CI, merge gate, and merge are Ralph-owned and were not run by Codex.

## Review Focus

- Verify the Workflow 2 state machine appears completely and consistently in `AGENTS.md`, `CLAUDE.md`, `frontier.yaml`, and `docs/HARNESS_WORKFLOW_2.md`.
- Verify `runs/**` is local-only and absent from staged/committed paths.
- Verify Red authorization uses `PROJECT_OP_AUTHORIZED`, `PROJECT_OP_SCOPE`, and `PROJECT_OP_EXPIRES` in the ASV1-P01 control surface.
- Verify STOP/resume semantics and bounded repair are sufficiently documented.
- Verify no broker/live/paper/order-routing, production deployment, raw/heavy artifact, SQLite/DB, or unsupported alpha/tradability scope was introduced.
