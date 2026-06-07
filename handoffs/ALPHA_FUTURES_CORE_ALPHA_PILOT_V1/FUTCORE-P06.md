# FUTCORE-P06 Handoff

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P06`  
Executor: Codex  
Date: 2026-06-07

## Summary

Produced the bounded research queue and role-assignment / separation-of-duties
contracts for the downstream pilot phases.

- `research_queue.md` records a finite `25` task queue for `FUTCORE-P07` through
  `FUTCORE-P30`, including per-family drafting, critique, data-contract audit,
  StudySpec authoring, split FeatureRequest/LabelSpec additions, per-family
  diagnostics, consolidations, audits, reviewer verdicts, ledgers, evidence
  drafting, allowed research-state decision recording, failure-mode handoffs,
  and closeout.
- `role_assignment_map.md` binds every task to exactly one Agent Factory role id
  and records forbidden-role bindings.
- `separation_of_duties.md` records drafter != critic != reviewer != promoter,
  implementer != self-reviewer, Diagnostics Runner != promoter, Librarian
  verdict gating, and human-owned capital/live boundaries.
- `docs/futures_core_alpha_pilot/RESEARCH_QUEUE.md` indexes the queue artifacts
  for human readers.
- `README.md` was updated with the compact post-P06 snapshot and unchanged
  safety boundaries.

No AlphaSpecs, StudySpecs, diagnostics, ledgers, reviewer verdicts, promotion
decisions, market data, feature values, label values, provider responses, or
heavy artifacts were produced.

## Explicit Staging List For Ralph

Codex staged no files, per executor safety instructions. The files for Ralph to
stage explicitly are:

- `docs/futures_core_alpha_pilot/RESEARCH_QUEUE.md`
- `research/futures_core_alpha_pilot_v1/queue/research_queue.md`
- `research/futures_core_alpha_pilot_v1/queue/role_assignment_map.md`
- `research/futures_core_alpha_pilot_v1/queue/separation_of_duties.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P06.md`

No `runs/**` path is commit-eligible for this phase.

## Validation

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/STOP` | Passed; no STOP file present. |
| `git status --short` | Not run. The executor prompt explicitly forbade Codex from running `git status`; Ralph owns authoritative working-tree validation. |
| `source /home/yuke_zhang/.venvs/alpha_system_research/bin/activate && python -c "import alpha_system.agent_factory.queue.models"` | Passed; no output. |
| `python tools/verify.py --smoke` | Passed; no output. |
| `test -f research/futures_core_alpha_pilot_v1/queue/research_queue.md` | Passed; file exists. |
| `test -f docs/futures_core_alpha_pilot/RESEARCH_QUEUE.md` | Passed; file exists. |
| `git ls-files runs` | Passed; empty output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.dbn' '**/*.zst'` | Passed; empty output. |

Additional local consistency checks:

| Command | Result |
| --- | --- |
| `if [ -x /home/yuke_zhang/.venvs/alpha_system_research/bin/python ]; then /home/yuke_zhang/.venvs/alpha_system_research/bin/python -c "from alpha_system.agent_factory.separation.wiring import assemble_validated_bundle; bundle = assemble_validated_bundle(); print(bundle.status.value); print(','.join(bundle.role_ids))"; else python -c "from alpha_system.agent_factory.separation.wiring import assemble_validated_bundle; bundle = assemble_validated_bundle(); print(bundle.status.value); print(','.join(bundle.role_ids))"; fi` | Passed; printed `PASS` and the ten expected role ids. |
| `LC_ALL=C grep -RIn '[^ -~]' README.md docs/futures_core_alpha_pilot/RESEARCH_QUEUE.md research/futures_core_alpha_pilot_v1/queue || true` | Passed; empty output. |

## Safety Confirmations

- No agent was instantiated.
- No autonomous or continuous runner was started.
- No Claude or reviewer was called by Codex.
- No `review.md` or `verdict.json` was created by Codex.
- No PR was created and no merge was attempted.
- No `git add`, `git commit`, `git push`, `git status`, or `git diff` command
  was run by Codex.
- No consumed primitive under `src/alpha_system/**` was edited.
- `ACTIVE_CAMPAIGN.md` was not touched.
- No broker, live, paper, order-routing, deployment, provider-call, or
  destructive operation was performed.
- The run-local `handoff.md`, `review.md`, and `verdict.json` under
  `runs/2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/phases/FUTCORE-P06/`
  remain local-only and were not staged by Codex.

## Open Items For Ralph

- Run authoritative `git status --short` validation, because Codex was
  explicitly prohibited from running it.
- Stage only the explicit paths listed above.
- Run Yellow-lane review and verdict handling through the Ralph-owned workflow.
