The review sandbox blocks writes/exec; per the task I'll return the review markdown directly (Ralph owns artifact persistence). My findings are based on direct artifact inspection plus the provided independent validation output.

---

# Claude Opus Review — RT-P09: Session / Regime / RTH / ETH Split Diagnostics

## Summary

RT-P09 builds out the reserved `alpha_system.runtime.diagnostics.splits` namespace into a descriptive session/regime split-diagnostics runtime. It produces `SessionSplitReport` and `RegimeSplitReport` that wrap the RT-P06 `DiagnosticsReport` contract, orchestrate the existing `alpha_system.research.regimes` primitive, honor `available_ts`/`label_available_ts`, and fail closed with visible rejection reasons. The implementation is in-scope, policy-compliant, and structurally correct against the consumed contracts.

## Verification performed

**Orchestration, not duplication (confirmed).** `core.py:403-406` calls `regimes.regime_filter_coverage / regime_filter_uplift / false_rejection_rate / conditional_strategy_improvement` and only summarizes their scalar outputs. No regime/IC/bucket math is reimplemented — the runtime merely builds a boolean `regime_filter` view per bucket. All four functions exist with matching signatures (`research/regimes.py:9,31,44,57`). The dedicated test `test_regime_report_orchestrates_research_regimes` asserts all four are invoked.

**RT-P06 contract conformance (confirmed).** Reports embed a real `DiagnosticsReport` (`core.py:331`) with `DiagnosticsFamily.SPLITS` (`contracts.py:63`), a `DiagnosticsQualityGate`, lineage refs, coverage/quality summaries, limitations, and rejection reasons. Constructor kwargs match `report.py:186-200`; gate kwargs match `report.py:116-125`. Failure states (`INCONCLUSIVE`/`REJECTED`) always carry a `RunRejectionReason`, satisfying the contract's `DIAGNOSTICS_FAILURE_STATES` non-empty-reason invariant (`report.py:229`).

**Availability discipline / no label-as-feature (confirmed).** `_eligible_rows` excludes rows lacking `available_ts` (`data_unavailable`) and rows with `label_available_ts < available_ts` (`leakage_risk`) — both recorded visibly (`core.py:448-493`). `_conditioning_field_allowed` rejects label/`*_label` (except `session_label`)/future/outcome fields as conditioning inputs (`core.py:585-593`), producing a `REJECTED` status. `label_value` is fed to the primitive only as an *outcome*, never as a bucket-conditioning input — the correct distinction. Tests cover both the assignment path and the unsafe-field rejection.

**Fail-closed + descriptive/non-promotional posture (confirmed).** Low-sample/zero-eligible splits set `status="inconclusive"` with `low_sample`/`data_unavailable` codes while remaining visible; `limitations()` explicitly states a gate result is not alpha validation. `test_split_reports_do_not_emit_promotional_claim_phrases` guards against promotional language. README/docs carry no alpha/tradability/profitability/strategy claims.

**Artifact & scope policy (confirmed).** Working tree touches only Allowed Paths (splits source, scoped tests, tiny synthetic fixtures, splits doc, synthetic configs, the commit-eligible handoff, README). `git ls-files runs` is empty. No forbidden primitive package (`research/**`, `governance/**`, etc.), shared diagnostics core (`__init__.py`/`contracts.py`/`report.py`), CLI, or `ACTIVE_CAMPAIGN.md` was edited — the prior `splits/__init__.py` was a reserved placeholder, now legitimately built out. Fixture is 2 KB synthetic JSON. No broker/live/paper/order/portfolio/strategy scope. Independent validation provided shows **all 16 Frontier canaries PASS** (including `forbidden_test_tamper`, `forbidden_scope_drift`, `forbidden_boundary_import`, `forbidden_raw_data_commit`) and **frontier-doctor PASS** — corroborating no test weakening and no boundary/scope drift.

## Warnings

1. **Unit-test pass is executor-reported, not reproduced in this review.** The review sandbox denied `pytest`/`verify.py --smoke` execution, so I could not independently re-run `tests/unit/runtime/diagnostics/splits` (executor reports `5 passed`). I traced each test's assertions against the code by hand and they hold, and the independently-run canary + doctor suite passed, but Ralph should confirm the pytest + smoke result is recorded green in the validation ledger before the merge gate.
2. **Session assignment treats naive UTC clock-time as session-local.** `_session_label`/`_session_segment` compare `available_ts.timetz()` (tz stripped) against naive `HH:MM` windows (`core.py:529,544`). Acceptable for synthetic descriptive diagnostics and documented as such, but a real session-calendar/timezone resolution is implicitly deferred to a later phase — worth noting so it is not mistaken for production session math.
3. **README edited on the build branch** though RT-P09 is parallel-safe. The spec explicitly authorizes `README.md` under Allowed Paths and routes it through the serial merge queue, so this is compliant; flagging only so the merge step re-validates README against fresh `main` to preserve the disjoint-build invariant.

None of these rise to a blocker: no broker/live/paper scope, no destructive ops, no hidden failed runs (the one import "failure" is a transparently-recorded `PYTHONPATH` env caveat with the `PYTHONPATH=src` form passing), no test weakening, no artifact-policy violation, no unsupported claims, no scope drift.

VERDICT: PASS_WITH_WARNINGS
