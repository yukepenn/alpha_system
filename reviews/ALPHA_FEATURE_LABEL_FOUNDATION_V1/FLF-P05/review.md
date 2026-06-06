Review complete. The implementation is clean, in-scope, and fail-closed. Summary of findings below.

# FLF-P05 Review — FeatureRequest Gate and Duplicate Exposure Guard

## Scope & boundary compliance
- **Exactly the allowed paths changed.** `git status` shows only `README.md` (M) plus the four new files: `src/alpha_system/features/request_gate.py`, `tests/unit/features/test_request_gate.py`, `docs/feature_label_foundation/FEATURE_REQUEST_GATE.md`, `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P05.md`. No stray files, no scope drift.
- **Governance consumed, not duplicated (R-022/R-003/R-005).** `git diff --stat HEAD -- src/alpha_system/governance/` is empty — no governance module touched. The gate imports and delegates to `validate_feature_request`, `FeatureRequestApprovalStatus`, `check_duplicate_exposure`, and `apply_duplicate_exposure_notes`; I confirmed each symbol exists with the consumed signature. It adds no alternate request schema, approval rule, or exposure detector — only thin frozen views (`DuplicateExposureReport`, `EquivalentFeatureGroup` via `MappingProxyType`).
- **No forbidden scope.** No broker/live/paper/order/account paths, no provider calls, no raw-data access, no value materialization, no `ACTIVE_CAMPAIGN.md` write, no MVP lifecycle states. README is factual and within snapshot policy (no alpha/tradability claims).

## Fail-closed correctness
The gate rejects every non-approved path with a typed reason: missing request, invalid request (governance validation failure), unapproved (`PENDING`/`NEEDS_REVIEW`), `BLOCKED_DUPLICATE`, unavailable registry, blocking finding, and inapplicable notes. Notably it **re-runs** the duplicate check and re-applies notes even on an already-`APPROVED` request, so a request can only be admitted if its *checked* status remains `APPROVED` — a genuine fail-closed re-validation, not a rubber stamp.

## Tests & validation
- Tests are genuine and not weakened: no `skip`/`xfail`; `parametrize` used legitimately. They cover all five negative paths plus the positive path, and assert the registry is **never mutated** (`write_calls == []`) using a spy that raises on any write attempt.
- Executor reported 9 passed (gate) / 30 passed (features) / smoke pass / `git ls-files runs` empty. Independent validation corroborates: all 16 canaries PASS (including `forbidden_test_tamper`, `forbidden_scope_drift`, `governance_future_shift`, `governance_permuted_labels`) and `frontier-doctor` passed. (Direct `pytest` re-run was blocked by local approval gating, so I relied on executor output + canary/doctor signal.)

## Artifact & git discipline
Nothing staged (executor left work unstaged per prompt), no `runs/` path tracked, run-local handoff not committed, commit-eligible handoff correctly under `handoffs/<CAMPAIGN>/FLF-P05.md`. No data/DB/cache/heavy artifacts introduced.

## Warnings (non-blocking)
1. **Spec validation command discrepancy (honestly disclosed).** The spec lists `python -c "import alpha_system.features.request_gate"` as expected to succeed; it fails in a bare shell (`ModuleNotFoundError`) and only passes with `PYTHONPATH=src`. This is the repo's existing src-layout characteristic shared by all feature modules, not a defect in this phase — the test runner and smoke check resolve the path correctly. The executor was transparent about the workaround. Ralph's authoritative checks should run with the project's configured path resolution.

VERDICT: PASS_WITH_WARNINGS
