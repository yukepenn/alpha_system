Every claim in the docs is grounded in real, on-`main` artifacts. My review is complete.

## Review — AGENT-P20: Agent Factory Docs and Operator Guide

### Scope & lane
Documentation-only YELLOW phase. The executor created exactly the three docs under `docs/agent_factory/` plus the localized `README.md` snapshot and the campaign-foldered handoff. Working tree confirms a clean, minimal footprint:
- `M README.md` (19 insertions / 5 deletions — localized changelog + status block only)
- `?? docs/agent_factory/GUIDE.md`, `OPERATOR.md`, `NEXT_CORE_ALPHA_PILOT_READINESS.md`
- `?? handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P20.md`

No `.py` under `src/**` or `tests/**`, no consumed-primitive edits, no sibling Wave-3 paths (`templates/agent_factory/prompts/**`, `docs/agent_factory/RUNTIME_BRIDGE.md`), and no `ACTIVE_CAMPAIGN.md` change. DAG disjointness with AGENT-P19/P21 is respected.

### Artifact policy
`git ls-files runs` returns empty; nothing under `runs/**` is staged. No data/DB/parquet/arrow/cache/log path appears. Canaries all PASS (incl. `forbidden_raw_data_commit`, `forbidden_local_artifacts`, `forbidden_scope_drift`); `just frontier-doctor` and `tools/verify.py --smoke` pass.

### Factual accuracy (guarded against fabricated claims)
- `AgentToolResult` field list in OPERATOR.md matches `docs/agent_factory/TOOLS.md` (`request_id`, `alpha_spec_id`, `diagnostics_summary`, `cost_summary`, `blocking_findings`, `next_required_gate`, …).
- Lifecycle states match `campaigns/.../GOAL.md` and source (`queue/models.py`, `memory/models.py`): `RESEARCH_TASK_QUEUED … REFERENCE_HANDOFF_RECORDED → LIBRARIAN_MEMORY_RECORDED`, and ACCEPTANCE.md §10 confirms `REFERENCE_HANDOFF_RECORDED` is the most-advanced survivor state.
- The prohibited-state list (`ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `LIVE_READY`, `PAPER_READY`, etc.) is correctly framed as unreachable.
- All cross-links resolve to existing files (8 companion docs + CLI.md + interpretation policy + ADR-0006 + STRUCTURAL_BACKLOG.md).
- The "exist today" CLI commands are real: `cli/runtime.py` registers `runtime` with `plan`, `validate-inputs`, `summarize` subcommands. The not-yet-built `alpha agent …` dry-run commands are explicitly marked `TARGET, not yet built`.

### Boundaries & no-claims language
The docs reinforce rather than weaken the campaign posture: contracts-only, no autonomous agent, no continuous runner, no alpha search, no factor promotion, accepted-DatasetVersion-only, value-free results, separation of duties, and explicit "seed/synthetic dry-run is not alpha evidence / EvidenceDraft is not a candidate / ReferenceCandidateHandoff is not Reference validation / diagnostic PASS is not promotion." The forward blockers (`FEATURE_LABEL_PARQUET_SINK_V1`, `SESSION_LABEL_GUARD_FIX_V1`, dataset-registry rehydration gap) are named as carried-forward, not as this phase's work. No broker/live/paper/order/account scope. README restates unchanged safety boundaries with no profitability/tradability claim. The grep hits for boundary terms are all prohibition language, as the handoff documents.

### Notes (non-blocking)
- The handoff records `git status` checks as "Skipped" per the executor prompt forbidding git; this is by-design (the driver owns the authoritative staged-set audit) and is documented truthfully — not a hidden failure.
- README is a per-phase changelog and does not add an AGENT-P19 entry; correct, since P19 owns its own README edit and the serial merge queue reconciles parallel Wave-3 snapshots.

The implementer did not self-approve; Codex created no `review.md`/`verdict.json` and asserted no PASS.

VERDICT: PASS
