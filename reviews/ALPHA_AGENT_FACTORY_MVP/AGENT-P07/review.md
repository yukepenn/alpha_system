Verification complete. The targeted pytest re-run requires interactive approval in this sandbox, but the executor recorded `6 passed`, the validation block shows `frontier-doctor` and all 16 canaries passing, and I independently confirmed the source, matrix, contract model, registry, and git state below.

# Review — AGENT-P07: Research Director Role Contract

## Verification performed
I inspected the actual repository artifacts rather than trusting the executor summary:

- **`roles/research_director.py`** — constructs one `AgentRole(role_id="research_director")` and registers it at import via the P03 discovery registry. No agent instantiation, no loop, no runner, no alpha search, no diagnostics, no I/O.
- **Permission matrix (`permissions/matrix.py:83-87`)** — `research_director` is granted exactly `("queue.scope_task", "queue.assign_roles", "queue.set_budget")`. The role module derives `callable_tools` directly from `permission_for(ROLE_ID).tool.allowed_tool_ids`, so the matrix remains the single source of truth and drift is impossible.
- **Contract model (`roles/contracts.py`)** — fails closed on empty fields, payload markers, and heavy suffixes; the contract populates every field with value-free declarative strings.
- **Registry (`roles/registry.py`)** — rejects duplicate ids; the module's `_register_once` guards against re-registration on reload.
- **Git state** — nothing staged; only the 6 allowed paths are modified/untracked (`README.md`, role module, test, doc, template, commit-eligible handoff). `git ls-files runs` is **empty**. No edits to `roles/__init__.py`, `roles/registry.py`, `permissions/**`, `queue/**`, `tools/**`, or `ACTIVE_CAMPAIGN.md` (confirmed via targeted `git status`).
- **Run-local handoff** lives under `runs/.../phases/AGENT-P07/handoff.md` and is correctly excluded from the staging list.

## Boundary / safety checks
- **Contracts-only:** confirmed. No autonomous agent, no continuous runner, no promotion, no review verdict, no diagnostics.
- **Separation of duties:** `forbidden_decisions` and `reviewer_independence` explicitly bar self-approval, promotion, review verdicts, implementation, AlphaSpec drafting/critique, looping/batching, queue/budget bypass, raw-provider reads, external-provider calls, and capital/risk/live decisions. Tests assert these fragments are present.
- **No broker/live/paper/order scope; no raw/heavy/db artifacts; no alpha/tradability claims** — doc uses explicit no-claims language; canary `forbidden_scope_drift`, `forbidden_raw_data_commit`, and `forbidden_boundary_import` all PASS.
- **DAG parallel-safety:** disjoint phase-owned files; role self-registers via discovery (no shared-file edit).

## Warnings (non-blocking)
1. **README edited inside the parallel role-contract wave (P07–P15).** `README.md` is a shared file each wave phase touches the same snapshot section of. The spec sanctions this and relies on the serial merge queue re-validating against fresh `main` — acceptable, but the merge queue must expect and resolve sequential README conflicts across P08–P15. Flagging for merge-gate awareness, not a defect in this phase.
2. **Tautological import-time guard.** `research_director.py:79` compares `RESEARCH_DIRECTOR_ROLE.callable_tools` against `_matrix_callable_tools()` — but `callable_tools` was *constructed from* that same call, so the check can never fail. It is harmless defensive code; the real matrix-alignment verification is in the unit test (`test_callable_tools_match_permission_matrix...`), which does assert against the literal expected set. No action required.
3. **Bare `python -c "import ..."` validation command fails** without `src/` on `PYTHONPATH` (recorded honestly in the handoff). The `PYTHONPATH=src` variant and the pytest run both passed; this is an environment artifact, not a code defect.

## Artifact / handoff completeness
Handoff lists the exact staged file set, records every validation command with results (including the honestly-recorded bare-import failure and the skipped `git status` per executor instructions), and confirms the artifact audit (`git ls-files runs` empty, no heavy/db/raw paths, no reviewer artifacts created by Codex). No hidden failed runs. No test weakening (tests are additive and assertive).

VERDICT: PASS_WITH_WARNINGS
