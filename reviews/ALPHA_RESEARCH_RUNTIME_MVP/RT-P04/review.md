No primitive files modified. I have a complete picture.

---

# Claude Opus Review — RT-P04: StudyRunSpec and RuntimePlan Contracts

**Campaign:** `ALPHA_RESEARCH_RUNTIME_MVP` · **Phase:** `RT-P04` · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 (fresh)

## Summary

RT-P04 adds the pre-execution contract layer (`RuntimeRequest`, `RuntimePlan`, `StudyRunSpec`) under `alpha_system.runtime.contracts`. The implementation is faithful to the spec: it is contract-and-validation-only, fails closed on every required invariant, consumes governance/experiments/RT-P03 primitives rather than duplicating them, executes nothing, and makes no alpha/tradability claim. Validation (canaries, frontier-doctor, smoke) is green and the executor reports 18/39 tests passing.

## Verification Against Spec & Policy

**Scope & boundaries — clean.** `git status` shows only commit-eligible paths: `runtime/contracts/{__init__,run_spec,plan}.py`, `tests/unit/runtime/contracts/`, `docs/research_runtime/RUN_SPEC_AND_PLAN.md`, `README.md`, and the foldered handoff. `git diff --stat` against `governance/experiments/backtest/features/labels/data` is **empty** — no consumed primitive was edited. `ACTIVE_CAMPAIGN.md` untouched. No CLI surface added.

**Consumption, not duplication — confirmed.** Imports resolve to real surfaces: `experiments.limits.CombinationLimit/GridLimitError`, `governance.{alpha_spec,study_spec,study_input_pack,serialization}`, `runtime.entry_contract` (`ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES`, reuses `RuntimeEntryReason/Status` rather than a parallel rejection model), `runtime.input_resolver` (`RuntimeInputPack`, `LOCKED_PARTITION_IDS`). No budget/overfit/limit math is re-implemented — the plan only records a finite `CombinationLimit` reference, deferring enforcement to RT-P13 as specified.

**Fail-closed gating — test-proven.** `RuntimeRequest` requires approved `AlphaSpec` (`IMPLEMENTATION_ALLOWED`) + `StudySpec` (`DIAGNOSTICS_ALLOWED`), `StudyInputPack`, target `dsv_` DatasetVersion, and a matching `RuntimeInputPack` (cross-checks alpha/study/dataset/lifecycle/scope). `RuntimePlan` rejects unbounded plans, off-contract partition windows, probe-without-grid/budget/`double_cost`, and locked-partition use without contamination metadata; locked-test *selection* is refused outright. Partition windows match the campaign contract exactly (`development 2018–2022`, `validation 2023–2024`, `locked/shadow 2025-01-01..as_of_run`). Lifecycle is capped at `PLAN_VALIDATED`; `to_dict()` always emits `execution_outcome: null`. Tests exercise each rejection path with real governance objects — no weakening, no test-only branches.

**Artifact policy — clean.** `git ls-files runs` empty; no `runs/` path staged; no review/verdict written by the executor (correctly left to the reviewer). All 16 canaries pass, including `forbidden_boundary_import`, `forbidden_scope_drift`, and `forbidden_test_tamper`. README snapshot is factual and compact (RT-P04 complete / 5 of 27, next RT-P05, unchanged safety boundaries).

## Warnings (non-blocking)

1. **Cross-module private imports.** `plan.py` imports underscore-prefixed helpers (`_actual`, `_is_missing`, `_json_dict`, `_prefixed_hash`, `_reason`) from `run_spec.py`. It works and stays inside the package, but it is fragile coupling; a small shared `_internal`/helpers module would be cleaner if these grow.
2. **Locked-partition-missing-metadata returns `INPUTS_INCONCLUSIVE`, not `INPUTS_BLOCKED`.** The spec phrased this as "rejected." It *is* fail-closed (no plan object is produced; `RuntimeContractError` raised), so the safety intent holds — the status is a deliberate "under-specified" nuance vs. a hard violation. Flagging only to confirm the distinction is intended and that downstream phases treat both statuses as non-passing.
3. **`RuntimeLifecycleState.INPUTS_RESOLVED` is declared but never assigned** to any contract object (the success reason uses the separate `RuntimeEntryStatus.INPUTS_RESOLVED`). Cosmetic; documents the intended progression.

None of these affect correctness, safety, or scope. No broker/live/paper scope, no execution, no promotion semantics, no hidden failures, no test weakening, no artifact leakage.

VERDICT: PASS_WITH_WARNINGS
