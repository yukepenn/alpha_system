I have enough to render a verdict. All checks confirm a clean, faithful, assets-only phase.

# Claude Review — AGENT-P19: Agent Prompt and Skill Assets

**Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 (fresh, independent) · **Campaign:** `ALPHA_AGENT_FACTORY_MVP`

## What was verified

**Scope & roster completeness — PASS**
- All ten MVP roster roles have a prompt template under `templates/agent_factory/prompts/`: `research_director`, `hypothesis_scout`, `alpha_spec_critic`, `data_contract_auditor`, `feature_engineer`, `label_engineer`, `no_lookahead_auditor`, `diagnostics_runner`, `statistical_reviewer`, `librarian`.
- Each of the ten prompts contains all 9 required contract sections (Purpose, Readable Inputs, Callable Tools, Producible Outputs, Allowed Decisions, Forbidden Decisions, Required Handoff Format, Reviewer-Independence Rules, Expected Failure) — verified 9/9 per file via grep.
- Each prompt carries an `AgentRole source:` pointer to the merged role contract and is marked "prompt / skill asset only; not a registered agent." Only `README.md` lacks the source ref, correctly (it is the index).

**Contract fidelity — PASS**
- Spot-checked `diagnostics_runner.md`: its Callable Tools list exactly matches the merged `DIAGNOSTICS_RUNNER_ROLE.CALLABLE_TOOL_IDS` (`runtime.plan`, `runtime.validate_inputs`, `runtime.run_diagnostics`, `runtime.run_label_diagnostics`, `runtime.run_signal_probe`, `runtime.run_cost_stress`, `runtime.build_evidence_draft`, `runtime.build_reference_handoff`). Tool names are real, not fabricated.
- Boundaries are consistently restated across prompts and the index: drive-not-edit primitives, `resolve_dataset_version`-only input resolution, no raw/provider access, structured value-free `AgentToolResult` outputs only, separation-of-duties (no self-review, runner-cannot-promote, librarian-needs-verdict), human owns risk/capital/live.

**Single source-of-truth index — PASS**
- `templates/agent_factory/prompts/README.md` indexes all ten role prompts with paths and one-line purposes, plus naming/index policy and shared boundaries.
- Scatter check confirms no prompt assets outside the indexed directory.

**Artifact & DAG policy — PASS**
- `git status --short` shows only `README.md` (M), `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P19.md`, and `templates/agent_factory/prompts/` — all within Allowed Paths.
- `git ls-files runs` is empty; no `runs/**` staged or tracked. No `src/**`, no `docs/agent_factory/**` (P20/P21 sibling surfaces untouched), no `ACTIVE_CAMPAIGN.md` write, no `.claude/agents/` registration.
- Disjointness with W3 siblings holds; only the serial-merge-safe shared root `README.md` is touched, additively.

**README snapshot — PASS**
- Factual and compact: states `assets_and_bridge` gate in progress, names AGENT-P19 and next Wave 3 work, lists the new `templates/agent_factory/prompts/**` surface, reaffirms unchanged safety boundaries. No alpha/profitability/tradability/broker/live/paper/deployment claims, no run-local paths, no duplicated handoff content.

**Validation — PASS**
- `python tools/verify.py --smoke` exit 0; `just frontier-doctor` exit 0; `just verify-canaries` all 16 canaries PASS (including `forbidden_scope_drift`, `forbidden_git_add_dot`, `forbidden_local_artifacts`, governance canaries).
- Handoff is complete: explicit staged file list, commands with results, skipped-check reasons (git status/diff forbidden to executor by design), artifact-audit confirmation.

## Observations (non-blocking)
- `diagnostics_runner.md` and others reference the runtime bridge as supplied by AGENT-P21 (same wave, not yet merged) and correctly mark it `BLOCKED until AGENT-P21 supplies the bridge` — an honest forward reference, not a claim of working integration.
- The prompts index references `docs/agent_factory/NAMING.md` (owned by a sibling phase) by read-only mention; the file was read, not edited. Fine.

## Conclusion
Assets-only phase: no autonomous agent, no continuous runner, no code/docs/src outside the prompt surface, no broker/live/paper/order scope, no data/provider access, no value commits, no unsupported claims, no test weakening, no artifact-policy violation, no scope drift. Prompts faithfully mirror merged `AgentRole` contracts and restate all required boundaries. Handoff is truthful and the executor did not self-approve.

VERDICT: PASS
