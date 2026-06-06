I have everything needed for a verdict. Let me record my review findings.

# Claude Opus Review — RT-P13: Bounded Grid / Variant Budget Guard

**Lane:** YELLOW · **Campaign:** ALPHA_RESEARCH_RUNTIME_MVP · **Reviewer:** Claude Opus 4.8 xhigh

## Scope & boundary conformance

- **Spec ↔ campaign alignment:** PHASE_PLAN.md:88, campaign.yaml:1646, and RUNBOOK.md:478 all define RT-P13 exactly as specced (YELLOW, dep RT-P12, `must_run_alone`, merge group `integration`, gate `runtime_integration`). No scope drift.
- **Allowed paths:** Working tree changes are confined to `src/alpha_system/runtime/grid/**`, `tests/unit/runtime/grid/**`, `docs/research_runtime/BOUNDED_GRID.md`, `configs/runtime/grid/**`, `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P13.md`, and `README.md`. Nothing outside §5.
- **`runs/**` handling:** campaign.yaml:1678 lists `runs/**` in `allowed_paths`, but the spec correctly resolved it as local-only and excluded it. `git ls-files runs` is empty. ✅
- **Forbidden paths:** `git status` is clean for `src/alpha_system/governance` and `src/alpha_system/experiments` — no forbidden package edited.

## Invariant verification (read the actual code + primitives)

1. **Orchestrates, does not duplicate** — Verified at the source level. `contracts.py:15-19` imports and calls `experiments.limits.product_count`, `CombinationLimit.enforce(count, grid_id=…)`, and `overfit_controls.assess_management_overfit_controls(...)`. I cross-checked every signature against `limits.py` (`product_count`, `CombinationLimit`, `GridLimitError.count/.max_combinations`) and `overfit_controls.py` (kwargs `combination_count`, `max_combinations`, `parameter_paths`, `survivor_warning_count`, `rejected_count`; `.controls`/`.warnings`) — **all match exactly**. No grid/limit/overfit math is reimplemented. `governance.serialization` is consumed by ~10 existing runtime modules — established consume pattern, not a boundary breach.
2. **Variant budget mandatory & hard** — `_coerce_variant_budget` emits `unbounded_grid` when absent (`contracts.py:859`); `VariantBudget.__post_init__` rejects non-positive caps; construction fails closed (`BoundedGridContractError`). Test-covered.
3. **No unbounded grid** — empty/zero-dimension axes route through `product_count` → `GridLimitError` → `unbounded_grid` reason (test `test_empty_axis_is_unbounded_grid_rejection`).
4. **No locked-test selection** — `_locked_partition_reasons` (`contracts.py:1105`) emits `locked_test_selection` when purpose contains "selection" on a locked/shadow partition, and additionally requires contamination metadata for any locked use. Refusal of the contamination *gate itself* is correctly left to governance (the guard only fails closed). Test-covered.
5. **Failures visible** — every rejection produces a `RuntimeEntryReason` + a `BoundedGridRunRecord`; `BoundedGridRunRecord` raises if rejected without reasons (`contracts.py:468`); repeated-run lineage retained (`previous_run_record_ids`). No retry-to-pass, nothing hidden.
6. **Bounded grid ≠ promotion** — `promotion_basis_allowed: False` baked into both payloads; prohibited-MVP-state token scan over all new files is clean.
7. **Value-free records** — the durable `BoundedGridRunRecord` embeds only the spec *ref* (id + hash), counts, ids, statuses, reason codes — no raw/heavy data. (Parameter-axis candidate values live only in the spec, which is the grid definition, not market data.)
8. **Local/deterministic** — content-hash–based ids, no network/provider/filesystem assumptions.

## Validation

- Independently confirmed green in this review: **canary suite** (incl. `forbidden_scope_drift`, `forbidden_boundary_import`, `forbidden_raw_data_commit`) and **frontier-doctor** both PASS (provided validation output).
- Executor-reported: `pytest tests/unit/runtime/grid -q` = 7 passed, `ruff` clean, `verify.py --smoke` pass, artifact audits empty.
- No PR / merge / broker / live / paper / provider / order-routing / deployment actions. No `review.md`/`verdict.json` created by executor. No `git add` performed.

## Warnings

1. **Focused unit suite not independently re-run in this review.** Environment permissions blocked me from executing `pytest tests/unit/runtime/grid` and `verify.py --smoke` directly, so I rely on the executor's "7 passed" plus the separately-run canary/doctor green signals. Static verification of the code and all consumed-primitive signatures is consistent with those results; confidence is high but the focused test execution was not reproduced here.
2. **Broadening checks deferred** (`pytest tests/unit/runtime`, `verify.py --all`, `canary_runner` from the executor shell). This is policy-compliant for an additive, import-isolated package under narrow-first test rules, and the canary suite was independently run and passed during validation. Noted, not blocking.

## Conclusion

The implementation is a faithful, fail-closed orchestration layer: budgets are mandatory and hard, unbounded grids and locked-test selection are unreachable, failures stay visible, primitives are consumed (not duplicated, not edited), records are value-free and non-promotional, and artifact/git discipline holds. The only reservations are the un-reproduced focused test run (environment-limited on my side) and the deferred broadening checks (covered by separately-passing canaries) — neither is a defect in the work.

VERDICT: PASS_WITH_WARNINGS
