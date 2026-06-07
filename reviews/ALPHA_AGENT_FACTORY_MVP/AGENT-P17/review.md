## Review — AGENT-P17: Agent Handoff and Tool Invocation Records

### Scope & lane
YELLOW contract-engineering phase. Deliverable is **contracts-only**: eight value-free record dataclasses, exports, tests, doc, template, README snapshot. No autonomous agent, no runner, no registry writes, no tool execution. Confirmed against spec, AGENTS.md, and CLAUDE.md.

### What I verified

**Contracts-only / value-free (core requirement) — PASS**
- `records/models.py` defines all eight required contracts (`AgentRunRecord`, `AgentDecisionRecord`, `AgentHandoff`, `ToolInvocationRecord`, `AgentAuditLog`, `AgentPromptVersion`, `AgentRoleVersion`, `AgentPermissionVersion`), all `@dataclass(frozen=True, slots=True)`.
- Fail-closed value rejection is real and layered: `_reject_raw_object` blocks `bytes`/`bytearray`/`memoryview`, mutable collections, and any object whose module root is in `RAW_OBJECT_MODULE_PREFIXES` (dataframe/array). `_validate_text` rejects forbidden payload markers, heavy suffixes (parquet/arrow/feather/dbn/zst/sqlite/db…), control chars, and over-length strings. Not cosmetic.

**Consumes but does not duplicate/edit primitives — PASS**
- Imports `permissions.matrix.ROSTER_ROLE_IDS`, `queue.models.ResearchTaskStatus`, `separation.enforcement.SeparationRuleResult`, `tools.results.*`, and lazily `tools.registry.resolve`. `git diff` shows only `README.md` and `records/__init__.py` modified; everything else is net-new under `records/`, `tests/.../records/`, `docs/`, `templates/`, `handoffs/`. No consumed primitive, role, separation, permissions, tools, or queue module touched.

**Decision → tool → spec linkage is genuine — PASS**
- `AgentHandoff._validate_linkage` cross-checks that decision role/request match the handoff, that every linked invocation's caller/request match, and that each spec/runtime/pack ref is **actually carried by a linked `AgentToolResult`** (`_validate_optional_ref_in_tool_results` / `_validate_ref_subset_in_tool_results`). A handoff cannot claim a spec ref no tool produced. The negative test (`dataset_version:different`) exercises this.
- `ToolInvocationRecord` validation calls `registry.resolve(tool_name, caller_role)`, which raises `PermissionError` for an unauthorized role (registry.py:73). The `hypothesis_scout` → `runtime.run_diagnostics` `PermissionError` assertion is therefore a real permission check, not vacuous.

**Tests not weakened — PASS**
- Test file asserts round-trip equality, immutability (`FrozenInstanceError`), linkage, registry enforcement, version/audit semantics, and a parametrized raw/heavy/value-array rejection sweep. No skips, no xfail, no test-only branches in source.

**Artifact policy — PASS**
- `git ls-files runs` empty. Working tree contains only commit-eligible Allowed Paths; no `runs/`, heavy, DB, or value paths. Run-local handoff stayed under `runs/.../AGENT-P17/handoff.md` (untracked). No `git add`/commit/push by executor. `ACTIVE_CAMPAIGN.md` untouched. No `review.md`/`verdict.json` created by Codex (correct — that's this review).

**README snapshot — PASS**
- Factual and compact: advances progress to "through AGENT-P17", names AGENT-P18 next, lists the new module/doc/template, restates safety boundaries, "No new command is added." No alpha/profitability/broker/live claims, no run-local paths.

**Safety boundaries — PASS**
- No broker/live/paper/order/deployment scope. No alpha/tradability/promotion claim anywhere in source, doc, or template. Doc and template explicitly disclaim alpha/factor-promotion/strategy-validation.

**Handoff truthfulness — PASS**
- Transparent that bare `python -c import` failed (source layout; `pyproject` sets `pythonpath=["src"]` for pytest, so this is expected, not a defect) and that `git status`/`git diff` were skipped per the executor override. Reports `16 passed`, smoke PASS, canaries PASS.

### Validation I re-ran this session
- `just verify-canaries` / `canary_runner.py`: all 16 canaries PASS (including `forbidden_scope_drift`, `forbidden_raw_data_commit`, `forbidden_local_artifacts`, `forbidden_boundary_import`).
- `just frontier-doctor`: PASS.
- Consumed-import existence, `registry.resolve` PermissionError path, and full source/test reading: confirmed by inspection.

### Warnings (non-blocking)
- I could not independently re-execute the `pytest` unit run in this review shell (sandbox approval), so the `16 passed` result rests on the executor report plus my line-by-line reading of the test and source. The tests are genuine and the validators they assert against are real; canaries and doctor passed in my own session.

No broker/live/paper scope, no destructive ops, no hidden failed runs, no test weakening, no artifact-policy violation, no unsupported claims, no scope drift.

VERDICT: PASS
