I have enough to complete the review. All artifacts examined; package imports cleanly (which runs full contract validation at module load), validation canaries are green, and the executor's reported 41-passed/smoke-pass is consistent with the code.

# Claude Review — AGENT-P05: Tool Contract Registry and Structured Outputs

## Summary
This phase adds the contracts-only agent-facing tool surface: `ToolContract` schema (`tools/contracts.py`), a default-deny `ToolRegistry` (`tools/registry.py`) loaded from `configs/agent_factory/tools/registry.toml`, and the single value-free `AgentToolResult` envelope (`tools/results.py`), with tests, `docs/agent_factory/TOOLS.md`, README snapshot, and handoff. It is purely additive scaffolding under `agent_factory/tools/`.

## Scope & boundary compliance — PASS
- **No edits to consumed primitives.** `git status` shows changes confined to `agent_factory/tools/`, its tests, `configs/agent_factory/tools/`, `docs/agent_factory/TOOLS.md`, `README.md`, and the handoff. No `runtime/**`, `governance/**`, `data/**`, `cli/**`, or any forbidden path touched. `forbidden_boundary_import` and `forbidden_scope_drift` canaries pass.
- **Registry import isolation.** `registry.py` imports only `contracts` + `results`; `contracts.py` imports `permissions.matrix` (the P04 dependency — expected and in-scope). The "no runtime/governance/data import" property is asserted by `test_registry_module_does_not_import_consumed_primitive_packages`.
- **Candidate tool surface matches the campaign exactly:** 24 tools across the 5 required groups (`registry`/`feature_label`/`runtime`/`review`/`ledger_memory_promotion`), confirmed against the config, docs table, and `EXPECTED_TOOLS` test set.

## Safety properties — PASS
- **Default-deny / fail-closed.** `resolve()` raises `KeyError` for unknown tools and `PermissionError` for disallowed callers; discovery helpers (`contract_for`, `list_by_group`, etc.) explicitly do not grant call authority (`test_registry_discovery_does_not_grant_call_authority`).
- **Value-free results.** `AgentToolResult` has exactly the 16 required fields (frozen, slots), and `__post_init__` rejects bytes/bytearray/memoryview, dataframe/array objects (by module root), duplicates, control chars, raw/provider/heavy markers, and heavy-suffix references. Strong, fail-closed construction-time validation.
- **No broker/live/paper/promotion scope.** Every contract forbids `broker_paper_live_order_scope` and direct registry writes; `promotion.review` is `status=future` with an extra `factor_promotion_without_human_approval` forbidden effect and `human_operator` as required reviewer. No autonomous agent, alpha search, or runtime execution introduced.
- **P04 cross-reference is enforced, not cosmetic.** `_validate_permission_matrix_cross_refs` runs at module load via `TOOL_REGISTRY = ToolRegistry.from_config()`; clean import proves every `allowed_caller` has a matching P04 tool permission. Allowed callers are all real roster roles.

## Artifact policy — PASS
`git ls-files runs` is empty; no `runs/`, heavy, DB, log, or cache paths in the working set. The handoff lives at the commit-eligible `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P05.md`; no review/verdict artifacts authored by the executor. `verify-canaries` (incl. `forbidden_raw_data_commit`, `forbidden_local_artifacts`, `forbidden_large_binary`) all pass. README snapshot is factual and compact with correct contracts-only / no-claims language and the next phase (`AGENT-P06`).

## No test weakening / honest handoff — PASS
New tests only; no skips or weakened assertions. The handoff truthfully records that the spec's bare `python -c "import ..."` fails without `PYTHONPATH=src` in the executor environment and passes with it — a real environment caveat, not a hidden failure (the repo's pytest config resolves the path; smoke and the 41-test suite pass). No falsified completion.

## Warnings (non-blocking)
1. **P05↔P04 name-space is not 1:1 (R-025 watch item).** Several agent-facing tool names map to a broader P04 permission id (e.g. `registry.list_datasets` → `permission_matrix_refs=["registry.resolve_dataset_version"]`). This is documented in `TOOLS.md` and validated programmatically, so it is defensible — but the divergence is exactly the "tool contract drift from runtime/permission" risk the campaign flags. Future phases (esp. the AGENT-P21 bridge) should keep this mapping audited and consider narrowing P04 permission ids as implementations land.
2. **Value-freeness is substring-heuristic + type-based.** Markers like `"numpy"`, `"pandas"`, `"metadata/"`, `"array("` will both (a) miss adversarially-encoded payloads and (b) occasionally false-positive on legitimate summary prose. Acceptable defense-in-depth for a contracts-only phase; the real guarantee depends on the deferred AGENT-P21 bridge honoring the contract, which this phase correctly scopes out.

Neither warning blocks merge; both are forward-looking maintainability/audit notes.

## Verdict rationale
Complete against the spec's done criteria, correctly bounded, fail-closed, no artifact or scope violations, no broker/live scope, no test weakening, honest handoff. The only findings are documented, intentional design choices worth tracking — not defects.

VERDICT: PASS_WITH_WARNINGS
