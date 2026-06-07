All verifications pass. I've independently confirmed the source, the matrix-to-roster alignment, docs, config mirror, README snapshot, handoff, and artifact discipline. Here is my review.

---

# Claude Opus Review — AGENT-P04: Agent Permission Matrix and Tool Access Policy

**Campaign:** ALPHA_AGENT_FACTORY_MVP · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 xhigh

## Summary

This is a clean, contracts-only phase that delivers exactly what the spec scopes: a default-deny / fail-closed permission model (`permissions/model.py`) and a static, importable role→permission matrix (`permissions/matrix.py`) covering all ten MVP roster roles, plus tests, docs, a value-free YAML mirror, README snapshot, and a truthful handoff. No autonomous agent, no tool execution, no data/provider access, no consumed-primitive edits.

## Verification performed (independent, not just trusting the summary)

| Check | Result |
| --- | --- |
| Working tree / `git ls-files runs` | ✅ empty — no `runs/` path staged or tracked |
| `roles/**` untouched | ✅ `git status` clean for `roles/` (import-only dependency on `FORBIDDEN_*` markers) |
| Matrix roster vs `campaign.yaml agent_policy.roster` | ✅ all 10 roles match exactly |
| Review roles confined to independent reviewers | ✅ only `alpha_spec_critic` + `statistical_reviewer` hold `ReviewPermission` (matches roster: only Critic and Statistical Reviewer review; both forbidden from reviewing own work, enforced by `independence_required=True`) |
| No promotion for any role | ✅ `PromotionPermission` rejects `can_promote=True` on construction; matrix invariant re-asserts |
| No raw/provider data grant | ✅ `DataPermission` rejects `raw_provider_access` and `raw`/`provider`/`*_file` scope markers; data roles (`data_contract_auditor`, `feature_engineer`, `label_engineer`, `diagnostics_runner`) get accepted-DatasetVersion-only refs |
| No direct registry write | ✅ `WritePermission` rejects `direct_registry_write` and direct-registry scope markers; Librarian writes are `*_after_verdict` only (matches "no registry write without reviewer verdict") |
| Fail-closed lookup | ✅ `permission_for` raises `KeyError` on unknown, `ValueError` on empty/blank; matrix validated at import via `_validate_matrix(_MATRIX)` |
| Human-approval / Red-lane reservation | ✅ every role marks risk/capital/promotion/paper/live/broker/order for human approval and external-provider/deployment/paper/live/broker/order for Red lane — declarative reservation only, grants nothing |
| YAML config mirrors Python matrix | ✅ exact, value-free, marked non-authoritative |
| Docs / README snapshot | ✅ accurate, no-claims language, no alpha/tradability/broker/live framing, next phase = AGENT-P05 |
| Tests not weakened | ✅ only the two allowed new test files added under `tests/unit/agent_factory/permissions/`; `__init__.py` pre-existing/unchanged; assertions are substantive |
| Provided validation | ✅ `verify.py --smoke` pass, 39 + 78 pytest pass, all 16 canaries pass, `frontier-doctor` pass |

## Risk-register coverage

R-004 (self-review), R-005 (self-promotion), R-006 (raw-data access), R-016/R-023/R-024 (direct registry write / overfit-machine enablers) are each addressed by an enforced, construction-time denial plus a matrix-level invariant and a corresponding test. The model fails *closed* — an unspecified role or grant is denied, not implicitly allowed.

## Notes (non-blocking)

- `is_default_deny` intentionally ignores the `human_approval`/`red_lane` marker fields. This is correct: those are *restriction* markers (actions requiring approval), not grants, so a populated marker set does not make a role "non-deny." Worth keeping in mind for AGENT-P16 wiring, but not a defect.
- Enforcement is declarative only by design; the actual separation-of-duties assertion and tool gating land in AGENT-P16 / AGENT-P05, as the spec scopes. The stable lookup API (`permission_for` / `role_ids` / `all_permissions` / `PERMISSIONS_BY_ROLE_ID`) is exported and ready for those consumers.

## Boundary / artifact / scope

No broker/live/paper/order scope, no destructive ops, no hidden failed runs, no test weakening, no artifact-policy violation, no unsupported alpha/tradability claims, no scope drift. Additive package only; rollback is contained. Handoff is truthful and records the one environment-specific skip (bare `python -c` import needs `PYTHONPATH=src`) with the passing variant.

VERDICT: PASS
