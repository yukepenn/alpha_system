I have everything I need. The contract module, tests, docs, template, README snapshot, and handoff are all present; shared role/registry/permission-matrix/tool files are confirmed unmodified; `git ls-files runs` is empty; and all referenced dependencies (`tools.results` exports, the P04 `hypothesis_scout` matrix entry, `queue.models`) exist and match the contract.

---

# Claude Review — AGENT-P08: Hypothesis Scout Role Contract

**Campaign:** `ALPHA_AGENT_FACTORY_MVP` · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 xhigh

## Scope & posture
The phase delivers a single additive, value-free **role contract** with no agent instantiation, no loop, no runtime/dataset/registry calls. Deliverables match the spec's §4.1 Allowed Paths exactly:
- `src/alpha_system/agent_factory/roles/hypothesis_scout.py`
- `tests/unit/agent_factory/roles/test_hypothesis_scout.py`
- `docs/agent_factory/roles/hypothesis_scout.md`
- `templates/agent_factory/roles/hypothesis_scout.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P08.md`
- `README.md` (minimal, append-style snapshot in the campaign-progress region)

`git status --short` shows only these paths; no out-of-scope or forbidden file touched.

## Boundary & invariant verification
- **Discovery registration, no shared-file edits:** `git diff HEAD` on `roles/__init__.py`, `roles/registry.py`, and `permissions/matrix.py` is empty. The role self-registers via `register(_ROLE_CONTRACT)` at import (`hypothesis_scout.py:209`), preserving wave-1 disjointness. ✔
- **Permission-matrix linkage is default-deny:** the P04 `hypothesis_scout` entry (`matrix.py:88`) grants exactly the three callable tool ids and write scope `("alphaspec.draft",)`, with no review/promotion/raw-data scopes. The contract's `CALLABLE_TOOL_IDS` match. ✔
- **Separation of duties:** `generator ≠ approver` encoded in `reviewer_independence`; `forbidden_decisions` explicitly denies self-approval, self-critique, implementation, diagnostics, dataset resolution, registry writes, promotion, and continuous runners. ✔
- **Bounded drafting:** `validate_draft_batch` enforces 3–5 drafts and the task `VariantBudget`; no loop/continuous shape. ✔
- **Value-free outputs:** `AlphaSpecDraftRef`/`RejectionReasonRecordRef`/`AgentHandoff` validators reject bytes, dataframe/array objects (`RAW_OBJECT_MODULE_PREFIXES`), forbidden payload markers, and heavy suffixes. Outputs carry only ids/refs/summaries. ✔
- **Duplicate surfacing:** `surface_prior_rejections` flags matched prior `RejectionReasonRecordRef` rather than silently re-proposing; downstream gate routes to duplicate review. ✔
- **No prohibited states / no claims:** transitions are confined to `HYPOTHESIS_DRAFTED → {ALPHASPEC_DRAFTED, INPUTS_BLOCKED, BLOCKED}`; `_validate_task_status_name` rejects `PROHIBITED_MVP_TASK_STATUSES`. Strong no-claims language in doc/template/limitations. No broker/live/paper/order/account surface anywhere. ✔

## Artifact & safety policy
- `git ls-files runs` is empty; no `runs/` path staged or created; no run-local `handoff.md` committed. ✔
- No data/heavy/DB/provider artifacts; commit-eligible handoff is under `handoffs/<campaign>/<phase>.md`. ✔
- `ACTIVE_CAMPAIGN.md` untouched (coordinator-owned). ✔
- `just verify-canaries` (16 PASS, incl. `forbidden_scope_drift`, `forbidden_boundary_import`, `forbidden_raw_data_commit`) and `just frontier-doctor` pass. ✔
- No test weakening: tests assert positive denials (self-approval/promotion/raw payloads), budget bounds, and failure-mode shapes on synthetic fixtures only.

## Tests
Executor reported `8 passed`. I could not re-execute pytest in this review session (interactive approval unavailable), but I independently confirmed every symbol the tests and module depend on exists and matches: `tools.results` exports (`AgentToolResult`, `AgentToolStatus`, `FORBIDDEN_*`, `RAW_OBJECT_MODULE_PREFIXES`), the P04 matrix entry, and `queue.models` types. The import succeeded under `PYTHONPATH=src`.

## Warnings (non-blocking)
1. **P05 tool-registry gap (disclosed):** the P04 matrix and this contract reference tool ids `memory.lookup_rejected_ideas`, `library.summarize_prior_work`, `alphaspec.draft`, but the P05 tool registry does not yet declare concrete contracts for them. The spec §2 presumed these were "already declared in the AGENT-P05 tool registry." P08 is correctly forbidden from editing the shared registry, references by id only, and fails closed (`INPUTS_BLOCKED`) when summaries are unavailable. This is a cross-phase wiring gap for P05/integration (P16), not a P08 defect — but the coordinator should track it so the ids get backed by real tool contracts before any executor wiring phase.
2. **Local `AgentHandoff` shape:** defined in-module pending the shared AGENT-P17 handoff record. It is value-free, validated, and flagged for replacement when P17 lands — consistent with the spec's "AGENT-P17-era contracts" language.
3. **README is a shared file on a parallel-safe phase:** the snapshot is minimal and merge is serial, matching §4.3. The coordinator must re-validate the merge gate against fresh `main` and resolve any README overlap deterministically during serial merge.

## Conclusion
The phase is contracts-only, fail-closed, boundary-clean, artifact-compliant, and free of broker/live/paper, destructive, hidden-failure, test-weakening, claim, or scope-drift issues. The handoff is complete and truthful, including honest disclosure of the two deferred-integration caveats. The caveats are forward-looking and outside this phase's permitted edit surface, so they warrant warnings rather than rework.

VERDICT: PASS_WITH_WARNINGS
