## Review — RT-P10: Cross-Market Diagnostics Runtime

### Scope & boundary compliance ✓
Working tree contains **only** allowed paths: `src/.../cross_market/{__init__.py,runtime.py}`, `tests/unit/.../cross_market/`, `tests/fixtures/.../cross_market/`, `docs/research_runtime/diagnostics/cross_market.md`, `configs/runtime/diagnostics/cross_market/`, `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P10.md`, and a `README.md` doc edit. No forbidden global files touched — the parallel-mode forbidden set (`diagnostics/__init__.py`, `contracts.py`, `report.py`, `cli/main.py`, `ACTIVE_CAMPAIGN.md`) is untouched. The edited `__init__.py` is the phase-local `cross_market/__init__.py`, which is in-scope.

### Orchestration, not duplication ✓
`_correlation` (runtime.py:1474) delegates verbatim to `research_correlation.correlations_to_existing_factors`; the primitive exists. No Pearson/rank/correlation math is re-implemented. Spread/residual are plain arithmetic descriptors of synchronized differences, explicitly framed as "arithmetic descriptors only; no hedge model, strategy, or portfolio object" in both config limitations and the doc. A dedicated test (`test_..._delegates_correlation_to_research_primitive`) monkeypatches the primitive and asserts the call.

### No-lookahead discipline ✓
Exact `event_ts` grouping; a snapshot forms only when all required symbols are present and every symbol's `available_ts ≤ decision_ts` (decision_ts = explicit value or max available_ts). Late symbols are dropped and surfaced, not forward-filled; lead/lag uses strictly prior snapshots (`index - lag_steps`). `test_alignment_uses_exact_timestamps_and_does_not_forward_fill` confirms no forward-fill.

### Inputs/governance/leakage ✓
DatasetVersion resolved via `resolve_dataset_version`; accepted lifecycle states only; mixed Databento+IBKR families rejected; feature/label pack DatasetVersion mismatch rejected; `available_ts`/`label_available_ts` windows required; label-only fields rejected as `leakage_risk`; locked-partition use requires governance metadata. No raw-provider reads or external calls.

### Failure visibility ✓
Failing conditions emit `RunRejectionReason` with terminal `REJECTED` / `DIAGNOSTICS_FAILED` / `INCONCLUSIVE` states, mirrored on the `DiagnosticsRunRecord`. Tests cover rejection paths. Nothing hidden.

### Claims & artifact policy ✓
Doc and report are descriptive/non-promotional with explicit limitations and an interpretation guardrail ("not alpha validation… not broker/paper/live/deployment/portfolio readiness"); tests assert prohibited terms are absent. Nothing staged; `git ls-files runs` empty; fixture is 2.7KB synthetic; stray `__pycache__/*.pyc` are gitignored (`__pycache__/`, `*.pyc`) and excluded from explicit staging. No broker/live/paper/destructive scope. Canaries all PASS; `frontier-doctor` PASS.

### Warnings
1. **Lane full-suite checks fail on pre-existing backlog.** `verify.py --lint` fails repo-wide (1355 errors / 281 files) and `verify.py --test` reports `13 failed, 2258 passed` on unrelated Workflow/Ralph/GitHub tests. RT-P10 touches only new isolated files + a README doc edit, so it cannot have introduced these; scoped Ruff (`format --check` + `check`) and the 6 RT-P10 tests pass. This matches the established baseline merged in RT-P07/P08/P09. Honestly disclosed in the handoff, but the YELLOW lane's `lint`/`test` gates only pass *scoped*, not full-suite.
2. **Independent re-execution not possible in this review sandbox** (import/pytest were permission-blocked). The verdict on test results relies on the executor's reported `6 passed` plus direct code inspection; the implementation and tests are internally coherent and well-formed.

Neither warning reflects a defect introduced by this phase. The handoff is complete and truthful (staged list, commands with results, skipped `git status`/`git diff` per executor constraints, artifact audit, README snapshot confirmation).

VERDICT: PASS_WITH_WARNINGS
