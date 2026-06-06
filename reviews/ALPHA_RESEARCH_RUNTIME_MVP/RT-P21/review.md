I have enough to complete the review. Test execution requires interactive approval in this context, but I've independently verified file contents, the README diff, absence of provider/raw references, no committed heavy artifacts, untracked `runs/`, and admissible-state doc accuracy — and the provided validation output shows the full canary suite and frontier-doctor passing.

---

# Claude Opus Review — ALPHA_RESEARCH_RUNTIME_MVP / RT-P21

**Phase:** Small Real FLF DatasetVersion Runtime Smoke · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 xhigh

## Summary

RT-P21 adds a local-only smoke driver (`src/alpha_system/runtime/smoke.py`), a CI-safe integration test, `docs/research_runtime/REAL_SMOKE.md`, a README snapshot, and a commit-eligible handoff. The smoke resolves one accepted local `DatasetVersion` plus registered Feature/Label handles, drives Tier 0 factor/label diagnostics → `double_cost` cost stress → no-lookahead audit → `EvidenceDraft` → value-free `RuntimeToolResult`/`RuntimeRunSummary`, and returns a truthful `PASS_WITH_WARNINGS` when local data is absent. The work is in-scope, fails closed, and is honestly framed.

## Verified against contract

**Scope & paths** — Exactly the five Allowed Paths were produced; `reviews/**` correctly left for the reviewer. README diff (`README.md`) is the only modification to an existing file and is factual/compact (no claims, no run details). No Forbidden Path touched; `ACTIVE_CAMPAIGN.md` untouched. Codex left everything unstaged for Ralph. ✓

**Orchestration, not duplication** — `smoke.py` imports and composes existing primitives (`entry_contract`, `input_resolver`, `diagnostics.factor/label`, `cost.runtime`, `evidence.draft`, `decisions`, `tool_results`, governance `alpha_spec`/`study_spec`/`study_input_pack`). No diagnostic/cost/grid/governance math is re-implemented; no consumed package is edited. ✓

**Safety boundaries** — `external_provider_call_requested=False`; no provider imports; `grep` for `databento|ibkr|.dbn|.zst|.parquet|.arrow|.feather` returns clean. Only reads are read-only SQLite **registry index** metadata + `resolve_dataset_version` — no raw market-data files. `AlphaSpec`+`StudySpec` built and validated; `StudyInputPack` references validated. `available_ts`/`label_available_ts` honored and a real no-lookahead audit is exercised (`POINT_IN_TIME_SAFE` asserted). `double_cost` present. No alpha/tradability/profitability/strategy/paper/live/broker scope; no prohibited MVP state; rejection paths stay visible via `RejectionReasonRecord` and `BLOCKED`/`PASS_WITH_WARNINGS`. ✓

**Fail-closed** — Absent root/registry/version/handles → `PASS_WITH_WARNINGS`, exit 0, exact operator command documented. CLI on this runner returned `PASS_WITH_WARNINGS` (no `ALPHA_DATA_ROOT`). ✓

**No test weakening** — Tests assert real behavior on both branches; the handoff-noted repair added a required `StudySpec.locked_test_policy` field to the test's own fixture setup, not an assertion relaxation. ✓

**Artifact policy** — `git ls-files runs` empty; no committed heavy/db/log artifacts; `data/`, `artifacts/`, parquet scans clean (per validation output and my checks). Canary suite (incl. `forbidden_scope_drift`, `forbidden_boundary_import`, `forbidden_raw_data_commit`, `forbidden_test_tamper`) and `frontier-doctor` all PASS. ✓

## Warnings

1. **"Real" smoke uses synthetic observation values.** The DatasetVersion and Feature/Label *handles* are resolved from real local metadata, but the actual diagnostic inputs (`_smoke_factor_observations`, `_smoke_label_observations`, `_smoke_fills`) are hardcoded deterministic tuples — an inherent consequence of the value-free / no-raw-access constraint. This is honestly disclosed in `REAL_SMOKE.md` ("tiny deterministic smoke inputs used to verify wiring; they are not alpha evidence") and in the `EvidenceDraft` limitations. Acceptable, but the human should understand the smoke validates *wiring*, not real feature/label values.

2. **Lifecycle admissibility can fail-open.** `_lifecycle_state` defaults to `"VERSIONED"` (admissible) when a resolved record lacks `lifecycle_state`. Bounded — `resolve_dataset_version` returns accepted versions and an operator can override via `ALPHA_DATASET_LIFECYCLE_STATE` — but a stricter default (or requiring an explicit state) would be safer.

3. **Spec validation command quirk.** The generated spec's bare `python -c "import alpha_system.runtime.smoke"` fails without `PYTHONPATH=src` in this `src`-layout repo; handled and disclosed in the handoff (`PYTHONPATH=src` passes, pytest passes). Spec/env nit, not a code defect.

4. **`smoke.py` is 1108 lines** — larger than the "thin driver" framing implies, though it is glue/helpers with no duplicated math. Minor.

None of these rise to REWORK: scope is honored, the runtime fails closed, no broker/live/paper/destructive scope, no hidden failures, no test weakening, no artifact-policy violation, and no unsupported claims.

VERDICT: PASS_WITH_WARNINGS
