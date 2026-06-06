I have completed my review. All consumed primitives are verified to exist, the artifact state is clean, and the fail-closed logic matches the spec. Here is my review.

---

# Claude Review — RT-P03 — Runtime Input Resolver: DatasetVersion and Feature/Label Packs

**Campaign:** `ALPHA_RESEARCH_RUNTIME_MVP` · **Phase:** `RT-P03` · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 xhigh

## Summary

RT-P03 adds `alpha_system.runtime.input_resolver`, turning an admitted `RuntimeEntryResult` + governance `StudyInputPack` into a value-free `RuntimeInputPack` (or a visible fail-closed rejection). The implementation is an orchestration layer over existing primitives, enforces availability discipline at resolution time, and does not duplicate or edit any consumed package. Scope matches the spec; artifact policy is clean.

## Boundary & Safety Verification

| Requirement | Finding |
|---|---|
| DatasetVersion only via `resolve_dataset_version` | ✅ Default `dataset_version_resolver=resolve_dataset_version` (`input_resolver.py:598`); admissible only in `{VERSIONED, READY_FOR_RESEARCH}` (`:675`). |
| No raw-provider / no external call | ✅ Raw suffix + provider-reader metadata guards (`_forbidden_reference_reasons`, `FORBIDDEN_PROVIDER_METADATA_KEYS`); no Databento/IBKR client import — verified by grep of imports (all in `data.foundation`/`features`/`labels`/`governance`). |
| `available_ts` / `label_available_ts` enforced, no-lookahead | ✅ `_require_availability_not_before_event` on both handles; missing-ts and precedes-event blocked. No-lookahead test proves ordering. |
| No label exposed as live feature | ✅ Ref-level (`_normalize_feature_pack_ref` rejects `lver_`/`lspec_`) and contract-level (`_reject_label_as_live_feature` on suspicious fields/views). |
| Databento/IBKR never merged | ✅ `_source_family_merge_requested` blocks combined-family scope. |
| Locked/shadow partition gate | ✅ Routes through `feature_consumption.require_partition_access`; missing metadata → `INPUTS_INCONCLUSIVE`; locked-test selection → `INPUTS_BLOCKED`. |
| Value-free output | ✅ `RuntimeInputPack` carries ids/handles/availability metadata only; `to_dict()` emits `"value_free": True`; no raw/heavy payloads. |
| Reuses entry reason shape (no parallel governance type) | ✅ `RejectionReasonRecord = RuntimeEntryReason`. |
| Orchestrate-never-edit forbidden packages | ✅ Only `input_resolver.py` + 2 tests + doc + README + handoff in working tree; no edits under `features/**`, `labels/**`, `data/**`, `governance/**`. |
| No broker/live/paper/order, no alpha/tradability/profitability claim | ✅ Doc and README explicitly disclaim; no such scope reachable. |

All imported symbols independently confirmed present: `resolve_dataset_version`, `require_partition_access`, `FeatureStore.from_alpha_data_root`, `LabelRegistry.from_alpha_data_root`, `FEATURE_VERSION_PATTERN`, `LABEL_VERSION_PATTERN`, canonical record types, `DatasetVersion`/`DatasetPartitionPlan.from_mapping`, governance serialization, and all `entry_contract` exports. The `require_partition_access` call signature matches the definition.

## Artifact Policy

- `git status --short`: only `README.md` (M) and the six allowed untracked paths; nothing staged. ✅
- `git ls-files runs`: empty. ✅
- No `runs/` path, no data/DB/cache/heavy artifact, no secrets in the change set. ✅
- Canaries: all 17 PASS (validation output). ✅ `frontier-doctor`: passed. ✅

## Tests

- New tests only; no existing tests weakened/skipped/special-cased. Synthetic fixtures + injected seams; no market data, no provider calls.
- Executor + harness report `26 passed` (`tests/unit/runtime` + `tests/no_lookahead/research_runtime`), smoke/typecheck/canaries pass.

## Warnings

1. **`tools/verify.py --lint` failed (exit 1)** on pre-existing repo-wide debt (`277 files`, `1341 errors`) outside RT-P03 paths; RT-P03 files pass targeted `ruff format --check` and `ruff check`. Documented in the handoff; consistent with the known repo baseline. Not introduced by this phase.
2. **Reviewer could not independently re-execute tests/lint** — command approvals were denied in this review environment. I verified all imports/symbols statically and confirmed the clean working-tree/artifact state directly; test-pass counts are relied upon from the executor and the validation harness output.
3. **`dataset_version_resolver` injection seam** defaults to the sanctioned path; a caller could inject an alternate resolver. Acceptable as the spec explicitly permits dependency seams, and the production default is `resolve_dataset_version`. Worth keeping in mind for later phases that wire real callers.
4. **`--typecheck` is `compileall`**, not a true type-checker — pre-existing repo convention, not a regression.

No broker/live/paper scope, destructive operations, hidden failed runs, test weakening, artifact violations, unsupported claims, or scope drift were found.

VERDICT: PASS_WITH_WARNINGS
