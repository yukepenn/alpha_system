I've completed a thorough review. Let me note that I could not re-run pytest myself (sandbox approval), but the executor reported `40 passed`, validation canaries all pass, frontier-doctor passes, and I have independently verified the code, imports, role IDs, lifecycle lists, and artifact state statically.

# Claude Review — AGENT-P06: Research Queue and Work Item Contracts

## Scope & Deliverables
All expected files are present and confined to allowed paths (`queue/` subpackage, `docs/agent_factory/`, `templates/agent_factory/`, `tests/unit/agent_factory/queue/`, `README.md`, `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P06.md`). No consumed primitive was edited — `models.py` only *imports* (read-only) from the AGENT-P04 `permissions.matrix` and AGENT-P05 `tools.results` modules.

## Verified Against Campaign Contracts

- **R-001 / single-task-bounded (primary risk):** `ResearchQueue` is a finite tuple with `max_tasks` cap (≤100); `ordered_tasks()` only sorts already-declared tasks. `test_contract_surface_is_single_task_bounded` asserts the public surface contains no `scheduler/schedule/cycle/auto_enqueue/auto_generate/run_forever/cron` member. No data read, no I/O, frozen dataclasses. ✓
- **Mandatory finite budgets:** `VariantBudget`/`ComputeBudget` reject 0/negative/None/non-int and enforce hard ceilings (25 variants, 720 min); `ResearchBudget` requires both; `FamilyBudgetPolicy.validate_tasks` caps per-family count/variants/runtime across the queue. "Unlimited" is unrepresentable. ✓
- **Prohibited MVP states:** The allowed `ResearchTaskStatus` enum matches the campaign's allowed list exactly (top forward state = `REFERENCE_HANDOFF_RECORDED`, no promotion states). `PROHIBITED_MVP_TASK_STATUSES` matches the campaign's 11-state list verbatim including `AUTONOMOUS_RESEARCH_RUNNING`, and `_coerce_task_status` rejects them explicitly. ✓
- **Value-free:** `_reject_raw_object` blocks bytes/bytearray/memoryview and numpy/pandas/polars/pyarrow objects; `_validate_text` rejects forbidden raw/heavy payload markers, heavy suffixes, and continuous-runner markers. Tests cover bytes, fake DataFrame, and a `.parquet` ref. ✓
- **Partition/blocker semantics:** development/validation/locked_test_candidate refs match `campaign.yaml`; allowed∩blocked rejected; locked-test in `allowed_partitions` requires governance metadata refs; `BlockerKind` covers parquet-sink and session-label-guard future blockers as value-free records. ✓
- **Admissible inputs:** `DatasetVersionState` limited to `{VERSIONED, READY_FOR_RESEARCH}`; pack inputs are id/ref tuples only. ✓
- **Assignment carries no authority:** `AgentAssignment` fields are exactly `{assignment_id, task_id, role_id, assignment_scope_ref}`; `permission_for(role_id)` validates the role exists but grants nothing. All role IDs used (`research_director`, `data_contract_auditor`, `alpha_spec_critic`, `statistical_reviewer`, `hypothesis_scout`, `feature_engineer`, `diagnostics_runner`) exist in `ROSTER_ROLE_IDS`; reviewer roles are in `REVIEW_ROLE_IDS`. ✓
- **DAG metadata:** `parallel_safe: false`, `must_run_alone: true`, merge_group `foundation`; no `ACTIVE_CAMPAIGN.md` write; no `runs/` in Allowed Paths. ✓

## Artifact & Safety Discipline
- `git ls-files runs` returns empty; nothing staged (all changes unstaged in working tree, per executor rules). No forbidden-path/heavy-suffix file created. No `review.md`/`verdict.json`/PR/merge by executor.
- All 16 Frontier canaries PASS (incl. `forbidden_scope_drift`, `forbidden_boundary_import`, `forbidden_raw_data_commit`); `frontier-doctor` PASS.
- Docs and template carry explicit no-alpha / no-runner / no-broker disclaimers; README snapshot is factual, compact, and correctly advances progress to P06 with next=P07.
- Handoff is complete and truthful (explicit file list, per-command results, documented skips).

## Warnings (non-blocking)
- The spec's literal `python -c "import alpha_system.agent_factory.queue.models"` returned exit 1 in the executor's sandbox solely because `src/` was not on `PYTHONPATH`; it passes with `PYTHONPATH=src`, and `verify.py --smoke` + the 40-test pytest suite passed. This is the same import-check pattern used by AGENT-P01…P05; the authoritative Ralph/CI environment resolves the package. Transparently recorded in the handoff — not a hidden failure. Ralph should confirm the bare import passes in its authoritative run before merge.

No broker/live/paper scope, no destructive ops, no test weakening, no scope drift, no unsupported alpha/tradability claims, no artifact-policy violation detected.

VERDICT: PASS
