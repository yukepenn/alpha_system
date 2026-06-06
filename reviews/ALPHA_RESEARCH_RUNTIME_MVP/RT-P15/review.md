The change set exactly matches the allowed paths — no upstream module edits, no `runs/` paths, nothing staged. I have everything needed for the review.

---

# Claude Review — RT-P15: RejectionReasonRecord and Runtime Decision States

**Campaign:** `ALPHA_RESEARCH_RUNTIME_MVP` · **Phase:** RT-P15 · **Lane:** YELLOW · **Merge group:** integration

## Summary

RT-P15 adds `src/alpha_system/runtime/decisions/` (a `states.py` / `records.py` / `models.py` / `__init__.py` package), a focused test module, `docs/research_runtime/DECISION_STATES.md`, a README snapshot, and a commit-eligible handoff. The phase implements the runtime anti-hidden-failure surface: terminal `REJECTED` / `INCONCLUSIVE` / `BLOCKED` decisions, the canonical `RejectionReasonRecord`, the closed nine-code category set, upstream adapters, and `RuntimeStopCondition`. It closes R-015 and supports R-027.

## Verification against spec & campaign

**Scope / boundaries (consume, don't duplicate) — PASS.** Working-tree change set is exactly: `decisions/**`, `tests/unit/runtime/decisions/**`, `DECISION_STATES.md`, `RT-P15.md` handoff, `README.md`. No upstream reason-emitting module (`runtime/contracts/**`, `entry_contract.py`, `audit/**`, `grid/**`) was modified — the modules are imported and normalized only. I confirmed the consumed contract shapes (`BoundedGridRunRecord.guard_outcome`/`rejection_reasons`, `NoLookaheadAuditReason`, `RunRejectionReason`, `RuntimeEntryReason`, `StudyRunResultState.DIAGNOSTICS_FAILED`, `RuntimeLifecycleState`) all exist as used. No forbidden-path domain (broker/live/paper/order/strategies/portfolio/governance/experiments/backtest/research/features/labels/data) was touched.

**Fail-closed visibility — PASS.**
- `RuntimeDecision` rejects a terminal state with zero reasons (`require visible reasons`), rejects a forward state carrying reasons, and rejects reasons whose `decision_state` mismatches the decision (`models.py:51-67`).
- `RejectionReasonRecord` enforces decision_state ∈ {REJECTED, INCONCLUSIVE, BLOCKED} and a required non-empty message (`records.py:86-93`).
- `DIAGNOSTICS_FAILED` is folded into terminal `REJECTED` rather than left as a separate hidden end state (`states.py:113`).

**Prohibited MVP states unreachable — PASS.** The enum omits all nine prohibited states; `coerce_runtime_decision_state` raises on them; message validation rejects promotional tokens (`states.py:50-62,144-145`; `records.py:409-434`). Test `test_prohibited_mvp_states_are_not_constructible_or_reachable` proves it.

**Reason record shape — PASS.** Immutable, slotted, hashable frozen dataclass; `to_dict()` carries only code/message/decision_state/stage/source_code/(source_id) — no expected/actual/rows/raw/heavy payload. Round-trips via `from_dict`. Adapters preserve upstream `source_code` and originating `stage`.

**RuntimeStopCondition — PASS.** Maps to `BLOCKED`, carries a visible reason, and is explicitly documented and tested as distinct from the operator `runs/<run_id>/STOP` file (payload asserts no `runs/` or `/STOP` substrings).

**DAG / coordinator discipline — PASS.** `parallel_safe: false`, `must_run_alone: true`, `merge_group: integration` match campaign.yaml; no `ACTIVE_CAMPAIGN.md` write.

**Artifact policy — PASS.** `git ls-files runs` empty; nothing staged by executor (override-correct); no heavy/data/DB/cache/log paths; `frontier-doctor` and all 17 canaries (incl. `forbidden_scope_drift`, `forbidden_boundary_import`, `forbidden_test_tamper`, `forbidden_raw_data_commit`) pass.

**Tests / validation — PASS.** No test weakening or visible test-only branches. Executor + Ralph validation: decisions tests `5 passed`, broader `tests/unit/runtime` `160 passed`, `--smoke` clean, docs present, canaries pass.

**No unsupported claims — PASS.** Docs, README, and handoff are factual and carry the non-promotional disclaimer; no alpha/tradability/profitability/strategy language.

## Warnings (non-blocking)

1. **README.md is outside the per-phase contract's allowed_paths.** `campaign.yaml` RT-P15 `allowed_paths` and `PHASE_PLAN.md` "Expected Files" list the decisions package, tests, `DECISION_STATES.md`, handoff, and reviews — **not** root `README.md`. The generated spec added `README.md` under a bounded "README Snapshot Policy." It is acceptable here because README is not in `forbidden_paths`, prior phases established the per-phase README-snapshot convention (the file already reflects RT-P14/audit), the change is factual/compact and within the stated policy, and the scope-drift canary passes. Flagging so the staging contract divergence is on record; Ralph should stage README explicitly per the handoff.

2. **Keyword-heuristic categorizer (`records.py:354-386`) is fragile.** `_canonical_code_from_source` maps unknown upstream codes to the closed set via substring matching, which can mis-bucket the canonical `code` for novel upstream codes. Risk is bounded: the verbatim upstream `source_code` is always preserved, so no information is lost and visibility is never compromised — but downstream consumers relying on `code` should be aware. Worth a follow-up if more upstream reason codes are added.

3. **Minor robustness nit.** `decision_state_from_study_run_result_state`/`_runtime_lifecycle_state` coerce via `RuntimeDecisionState(value.value)`, which raises a bare `ValueError` (not `RuntimeDecisionStateError`) if a future forward result/lifecycle value is absent from the decision enum. This fails closed (raises rather than hides), so it is safe, but the error type is inconsistent with the module's fail-closed `RuntimeDecisionStateError` convention.

## Conclusion

The phase is correctly scoped, consume-only, fail-closed, free of broker/live/paper/destructive/hidden-failure/test-weakening/artifact concerns, and satisfies the Definition of Phase Done. The only material note is the README allowed-path divergence from the machine-readable contract, which is conventional and within the spec's snapshot policy. Merge-eligible.

VERDICT: PASS_WITH_WARNINGS
