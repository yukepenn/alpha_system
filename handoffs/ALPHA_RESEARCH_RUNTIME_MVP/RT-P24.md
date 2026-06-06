# RT-P24 Handoff - Workflow 2 DAG Integration and Parallel Plan

## Scope Completed

- Added `docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md` documenting the campaign's `dag_wave` scheduler settings, conceptual w0-w4 wave shape, computed `plan-dag` batches, parallel-safety rule, disjoint allowed-path guarantees, serial merge queue, coordinator-only `ACTIVE_CAMPAIGN.md` ownership, and preflight protocol.
- Updated `README.md` with the RT-P24 snapshot, the active/next phase (`RT-P25` End-to-End Runtime Dry Run), the new DAG integration doc, and unchanged safety boundaries.
- Ran the read-only `plan-dag` preview and confirmed the computed scheduler output matches the intended campaign shape when grouped into the documented w0-w4 bands.
- Did not edit scheduler code, runtime code, `campaign.yaml`, `PHASE_PLAN.md`, or `ACTIVE_CAMPAIGN.md`.

## Files For Ralph To Stage Explicitly

Codex staged no files. For the authoritative commit, Ralph should stage only:

- `docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24.md`

`reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24/**` is reviewer-owned and was not created because the executor prompt explicitly forbids Codex from calling Claude, running reviewer, creating `review.md`, or creating `verdict.json`.

## Git Status

`git status --short`: skipped. The executor prompt explicitly forbids Codex from running `git status`.

`git diff --cached --name-only`: skipped. The executor prompt forbids `git diff`; Codex also performed no staging.

## Validation And Execution

- `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md` -> pass; loaded the Frontier executor skill.
- `sed -n '1,220p' AGENTS.md` -> pass; loaded repo operating rules.
- `sed -n '1,220p' frontier.yaml` -> pass; loaded harness and command settings.
- `sed -n '1,120p' ACTIVE_CAMPAIGN.md` -> pass; confirmed the active campaign pointer and coordinator-only scheduler note.
- `rg --files | rg '(^campaigns/|campaign\.yaml$|PHASE_PLAN\.md$|README\.md$|handoffs/|reviews/|docs/research_runtime)'` -> pass; located campaign, docs, handoff, and review surfaces.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && printf 'STOP present\n' || printf 'STOP absent\n'` -> pass, output `STOP absent`.
- `sed -n '1,260p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml` -> pass; confirmed scheduler settings.
- `sed -n '1,260p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md` -> pass; confirmed the documented wave shape and RT-P24 contract.
- `find runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P24 -maxdepth 2 -type f -print | sort` -> failed before edits because the run-local phase directory did not exist. No `runs/**` path was created.
- `rg -n "workflow2:|scheduler:|phase_id: RT-P0[7-9]|phase_id: RT-P1[0-1]|phase_id: RT-P2[0-4]|parallel_safe:|must_run_alone:|allowed_paths:|forbidden_paths:|merge_group:" campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml` -> pass; located DAG metadata.
- `sed -n '1,260p' README.md` -> pass; read snapshot context.
- `sed -n '1,220p' docs/research_runtime/README.md` -> pass; read docs-root context.
- `sed -n '1,200p' handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P21.md` -> pass; checked recent handoff style and executor constraints.
- `python tools/frontier/ralph_driver.py plan-dag --campaign-id ALPHA_RESEARCH_RUNTIME_MVP` -> pass. Output confirmed `dag_wave`, `max_parallel_phases: 3`, 22 scheduler waves, max width 3, and parallel batches:
  - Wave 7: `RT-P07`, `RT-P08`, `RT-P09`
  - Wave 8: `RT-P10`, `RT-P11`
  - Wave 17: `RT-P20`, `RT-P22`, `RT-P23`
  The command emitted no `Conflicts` or `Blocked` sections. Run-alone phases were reported as `declared must_run_alone`, including `RT-P24`.
- `sed -n '1200,1540p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml` -> pass; confirmed diagnostics-wave allowed paths and shared/global forbidden paths.
- `sed -n '2160,2490p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml` -> pass; confirmed tests/tools/docs-wave allowed paths and RT-P24 metadata.
- `sed -n '3040,3085p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml` -> pass; confirmed DAG and serial-merge risk controls.
- `sed -n '2470,2570p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml` -> pass; read RT-P24 and RT-P25 contract excerpts.
- `rg -n "def .*plan|plan-dag|allowed_paths|parallel_safe|disjoint|max_parallel" tools/frontier campaigns/ALPHA_RESEARCH_RUNTIME_MVP -g '*.py' -g '*.yaml' -g '*.md'` -> pass; located the scheduler validation code and campaign references.
- `sed -n '1,260p' tools/frontier/dag_scheduler.py` -> pass; confirmed `plan-dag` uses allowed-path overlap and global-file checks.
- `sed -n '1,220p' tools/frontier/ralph_driver.py` -> pass; confirmed `plan-dag` is read-only.
- `sed -n '320,590p' tools/frontier/dag_scheduler.py` -> pass; confirmed conservative parallel-safety and conflict logic.
- `sed -n '5890,5945p' tools/frontier/ralph_driver.py` -> pass; confirmed text output behavior for waves, unsafe phases, conflicts, and blocked phases.
- `sed -n '2225,2295p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md` -> pass; read RT-P24 contract excerpt.
- `sed -n '145,240p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RUNBOOK.md` -> pass; read preflight protocol.
- `sed -n '288,305p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACCEPTANCE.md` -> pass; read DAG-scheduler acceptance excerpt.
- `find handoffs/ALPHA_RESEARCH_RUNTIME_MVP -maxdepth 1 -type f -name 'RT-P24.md' -print && find reviews/ALPHA_RESEARCH_RUNTIME_MVP -maxdepth 2 -type f -path '*/RT-P24/*' -print 2>/dev/null` -> returned nonzero with no output before edits; no pre-existing RT-P24 handoff or review artifact was present.
- `test -f docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md` -> pass after edit.
- `sed -n '1,120p' README.md` and `sed -n '120,180p' README.md` -> pass; checked README patch context.
- `sed -n '84,116p' README.md` -> pass; checked updated durable docs and safety block.
- `sed -n '116,136p' README.md` -> pass; checked remaining README snapshot context.
- `python tools/verify.py --smoke` -> pass, no output.
- `python tools/frontier/ralph_driver.py plan-dag --campaign-id ALPHA_RESEARCH_RUNTIME_MVP` -> pass on final validation, same confirmed output as above.
- `test -f docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md` -> pass.
- `test -f README.md` -> pass.
- `git ls-files runs` -> pass, no output.
- `find runs -maxdepth 3 -type d -print | sort | sed -n '1,80p'` -> failed because `runs/` does not exist in this worktree. This confirms no local run directory was present or created by this phase.
- `test -f handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24.md` -> pass after handoff creation.
- `test -f docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md` -> pass on final presence check.
- `test -f README.md` -> pass on final presence check.
- `git ls-files runs` -> pass on final audit, no output.
- `find reviews/ALPHA_RESEARCH_RUNTIME_MVP -maxdepth 2 -type f -path '*/RT-P24/*' -print 2>/dev/null` -> returned nonzero with no output because no RT-P24 review artifact path exists.
- `find runs -maxdepth 3 -type f -print 2>/dev/null` -> returned nonzero with no output because `runs/` does not exist.
- `test -f docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md` -> pass on final sanity check.
- `test -f handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24.md` -> pass on final sanity check.

Skipped checks:

- `git status --short` was skipped because the executor prompt forbids `git status`.
- `git diff --cached --name-only` / staged-set inspection was skipped because the executor prompt forbids `git diff`; Codex performed no staging.
- Reviewer artifacts under `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P24/**` were skipped because the executor prompt forbids calling Claude, running reviewer, creating `review.md`, or creating `verdict.json`.

## Plan-Dag Confirmation

The read-only plan output maps to the documented campaign bands:

- `w0`: scheduler waves 0-6 (`RT-P00` through `RT-P06`), all single-phase run-alone waves.
- `w1`: scheduler waves 7-8 (`RT-P07` through `RT-P11`), split by `max_parallel_phases: 3`.
- `w2`: scheduler waves 9-16 (`RT-P12` through `RT-P19`), all single-phase run-alone waves.
- `w3`: scheduler wave 17 (`RT-P20`, `RT-P22`, `RT-P23`), parallel.
- `w4`: scheduler waves 18-21 (`RT-P21`, `RT-P24`, `RT-P25`, `RT-P26`), all single-phase run-alone closeout waves.

The only co-running phases are the declared parallel-safe diagnostics and tests/tools/docs phases. The preview emitted no `Conflicts` or `Blocked` section, and the scheduler code validates missing `allowed_paths`, global/coordinator paths, overlapping path prefixes, declared conflicts, and shared resources before co-running phases.
The declared parallel-safe phases (`RT-P07` through `RT-P11`, `RT-P20`, `RT-P22`, and `RT-P23`) were absent from the run-alone list, confirming they had declared `allowed_paths` and no global/coordinator path under the current contract.

## Artifact Audit

- `git ls-files runs` -> pass, no output.
- Codex staged no files and did not run any staging command.
- No `runs/**` file, raw/canonical/feature/label/runtime value, provider response, DB, cache, log, or heavy artifact was intentionally created as a commit-eligible output.
- Authoritative staged-set validation remains with Ralph because this executor prompt forbids Codex from running `git status` and `git diff --cached`.

## README Snapshot

`README.md` was updated per policy: it records RT-P24 documentation/verification work, names RT-P25 as next, mentions `docs/research_runtime/WORKFLOW2_DAG_INTEGRATION.md` and the read-only `plan-dag` preview workflow, and restates unchanged safety boundaries without run details or alpha/trading claims.

## Caveats

- The generated RT-P24 spec mentions reviewer artifacts, but the executor prompt explicitly forbids Codex from creating `review.md` or `verdict.json`; those remain reviewer/Ralph-owned.
- The generated validation list includes `git status --short`, but the executor prompt explicitly forbids it; this handoff records the skip rather than faking output.
- The supplied run-local directory was absent in this worktree (`runs/` does not exist). No run-local handoff was written and no `runs/**` path was created.
- Codex did not call Claude, run reviewer, create review artifacts, create a verdict, create a PR, merge, stage, commit, push, or mark the phase PASS.
