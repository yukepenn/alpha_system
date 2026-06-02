@AGENTS.md

# Claude-specific Frontier Notes

Use this repository as Frontier Harness Generic v3.0.

Claude default responsibilities:

- campaign decomposition
- phase specs
- architecture and ADRs
- Claude Opus 4.8 xhigh cross-provider review for Yellow and Red phases
- boundary audit
- semantic done-check
- Ralph loop planning
- project-skill lessons
- Claude Sonnet 4.6 verifier, source-map, and mechanical audit support

Claude default non-responsibilities:

- bulk implementation
- routine mechanical edits
- primary execution after spec approval
- Codex execution, Codex repair, or Codex handoff authorship
- Ralph state transitions, PR creation, CI waiting, merge gates, or merge execution

Use project skills:

- frontier-campaign
- frontier-spec
- frontier-review
- frontier-audit
- frontier-ralph
- project-skill

Do not create custom commands named `/plan`, `/review`, or `/verify`. Prefer frontier-prefixed skills and commands.

## Workflow 2 Review Contract

Workflow 2 state order:

```text
RUN_INIT -> CAMPAIGN_LOAD -> PHASE_SELECT -> SPEC_GENERATE -> SPEC_VALIDATE -> WORKTREE_CREATE -> CODEX_EXECUTE -> CHECKS_RUN -> HANDOFF_VALIDATE -> CLAUDE_REVIEW -> VERDICT_PARSE -> PR_CREATE -> CI_WAIT -> MERGE_GATE -> MERGE -> DONE_CHECK -> NEXT_PHASE -> CAMPAIGN_DONE_CHECK -> RUN_SUMMARY
```

Ralph owns the strict driver loop, STOP checks, validation orchestration, review routing, verdict parsing, bounded repair routing, PR/CI/merge gates, and run summaries. Codex owns scoped execution of the generated spec and truthful handoffs. ChatGPT owns strategic campaign reasoning and post-run reasoning.

Claude review must verify Workflow 2 completeness, model-routing clarity, lane policy, Red authorization, artifact policy, STOP/resume semantics, and handoff truthfulness. Review artifacts are written by the reviewer under `reviews/**` when commit-eligible and under `runs/<run_id>/phases/<phase_id>/review.md` plus `verdict.json` for local audit.

## Lane And Artifact Rules

Green is low-risk automatic work. Yellow is material engineering or research work and requires fresh Claude Opus review. Red covers external, destructive, live, production, costly, or broker-adjacent work and requires scoped authorization:

```text
PROJECT_OP_AUTHORIZED
PROJECT_OP_SCOPE
PROJECT_OP_EXPIRES
```

`runs/**` is local-only runtime state. Run-local handoffs, checks, review files, verdict files, repair attempts, ledgers, STOP files, and summaries must not be staged or committed. Commit-eligible phase handoffs belong under `handoffs/<PHASE_ID>.md`.

Explicit staging is required. `git add .` and `git add -A` are forbidden examples only. Force push is forbidden.

The active repo must stay under the WSL2 Linux filesystem at `~/projects/alpha_system`; `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temporary directories are forbidden active worktree locations.
