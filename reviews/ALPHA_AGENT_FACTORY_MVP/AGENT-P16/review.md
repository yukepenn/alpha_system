## Review: AGENT-P16 — Separation-of-Duties and No-Self-Review Enforcement

### Scope & boundary conformance
- **Scope matches the spec exactly.** Only the Allowed-Path files were created/modified: `separation/{enforcement,wiring}.py`, `separation/__init__.py` (additive re-export), the two test modules, `docs/agent_factory/SEPARATION_OF_DUTIES.md`, `README.md`, and the commit-eligible handoff. `git status --short` shows nothing outside the allowed set.
- **Consume-never-edit upheld.** No edits to `roles/*.py`, `roles/__init__.py`, `roles/registry.py`, the permission matrix, or any runtime/governance/research/feature/label/data/CLI primitive. Verified `roles/registry.py` already exposes the `get()` API the wiring consumes, and `ROSTER_ROLE_IDS` contains exactly the ten MVP roles wired in `CONCRETE_ROLE_MODULES`.
- **No autonomous agent / continuous runner / tool execution / data access.** The layer is pure, deterministic predicates over role + matrix data.

### Enforcement correctness (fail-closed)
- All **five** required rules are present plus two assembly guards (`permission_matrix_coverage`, `human_reserved_flags_preserved`). Every validator defaults to `BLOCKED` on missing/unknown/ambiguous input (`_coerce_ref`, `_coerce_known_role_ids`, `_known_roles_block` all return blocking results), with no implicit pass path.
- **No promotion reachable**: `check_no_promotion_permission` rejects any `can_promote==True`, treats malformed/missing entries as BLOCKED, and names `diagnostics_runner` specifically.
- **Human-reserved flags preserved**: guard rejects any entry that drops a required `HumanApprovalRequired`/`RedLaneRequired` action; it verifies (does not grant) markers.
- **Value-free outputs**: `SeparationRuleResult.__post_init__` + `_validate_reason`/`_coerce_ref` reject payload markers and heavy-artifact suffixes, bounding length and rejecting control chars. Outputs carry only ids/status/role refs/reason.
- **Wiring fails closed**: `assemble_validated_bundle` raises `SeparationWiringError` on any BLOCKED result by default; `_roles_by_id` flags malformed/duplicate roles; missing roles/entries surface as `permission_matrix_coverage` BLOCKED.

### Tests
- `test_enforcement.py` and `test_wiring.py` give each rule a **passing case, a self-violation negative case, and a fail-closed-on-missing-input case**; wiring tests assert exactly ten roles, single-place import, all rule families run, and BLOCKED on missing role / missing entry / promotion grant / weakened human-reserved flag / verdict-less librarian write. No skips, no weakened assertions, no test-only branches.

### Artifact & git policy
- `git ls-files runs` is **empty**; no `runs/**`, data, DB, cache, log, or heavy-artifact path staged or created in git. No `ACTIVE_CAMPAIGN.md` write. Executor left everything unstaged (Ralph owns staging) — correct WF2 behavior. No PR/merge/review/verdict created by the executor.
- README snapshot is compact, factual, and free of alpha/tradability/broker/live claims. No broker/live/paper/order/account scope anywhere.

### Validation
- `just frontier-doctor` PASS; `just verify-canaries` all PASS (incl. scope-drift, boundary-import, raw-data, governance canaries). Executor recorded `24 passed`, ruff clean, smoke PASS.

### Warnings (non-blocking)
1. **Test re-execution not independently confirmed in this review environment.** Test invocation required interactive approval unavailable to the reviewer, so I verified the suite statically (genuine fail-closed coverage confirmed) and relied on the executor's recorded `24 passed` + ruff-clean + the clean doctor/canary run. CI must confirm the suite is green before merge.
2. **The spec's literal bare `python -c "import ..."` validation command fails** without `src/` on `sys.path` (`ModuleNotFoundError`), as it does for prior phases in this campaign. Properly disclosed in the handoff; the supplemental `PYTHONPATH=src` import passes. Cosmetic source-layout quirk, not a defect.

These are disclosure/verification caveats, not correctness or policy problems. The work is complete, fail-closed, value-free, and policy-compliant.

VERDICT: PASS_WITH_WARNINGS
