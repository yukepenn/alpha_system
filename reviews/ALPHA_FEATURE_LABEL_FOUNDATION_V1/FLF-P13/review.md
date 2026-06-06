The sandbox blocks the scoped ruff re-run, but I've independently verified the substrate gating functions exist and are genuinely consumed (not re-implemented), the implementation enforces every claimed invariant, the artifacts are clean, and validation (canaries, smoke, typecheck) passed. The full-repo `--lint` failure is a pre-existing repo-wide backlog (254 files / 1314 errors) unrelated to this phase's four touched files, which pass scoped ruff per the handoff. I have enough to render a conservative verdict.

---

# Claude Review — FLF-P13: Feature Materialization Engine

**Campaign:** `ALPHA_FEATURE_LABEL_FOUNDATION_V1` · **Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 xhigh

## Scope Compliance — PASS
The change is exactly engine + plan + dry-run. `src/alpha_system/features/engine/materialization.py` adds `FeatureMaterializationPlan`, `FeatureMaterializationInputs`, `FeatureMaterializationResult`, `build_feature_materialization_plan`, `materialize_features`, and `resolve_feature_materialization_dataset`. No FeatureStore/FeatureRegistry persistence (FLF-P14), no quality/coverage reports (FLF-P15), no alpha/factor/strategy/backtest scope. `engine/__init__.py` is the only edit to existing tracked code and is a pure additive re-export. No shared family, governance, or `labels/` files were touched (confirmed via `git status`).

## Gating & Safety Invariants — PASS (verified against substrate)
I confirmed each gate is real code consuming the sanctioned substrate, not re-implemented governance:
- **Accepted-DatasetVersion-only:** `resolve_feature_materialization_dataset` delegates to `consumption.resolve_accepted_dataset_version`; the unit test monkeypatches `consumption.resolve_dataset_version` and asserts the adapter is the resolution path. No raw provider readers — confirmed `consumption.py` is the sole data entry and the engine imports only contracts/families/input_views/semantics/consumption.
- **Fail-closed on unvalidated specs:** `_validate_materializable_feature_spec` rejects non-`implementation_eligible` specs, non-causal/non-live-compatible windows, and `available_ts` rules not derived from `available_ts`. `_definitions_by_feature_id` additionally requires each definition's request-gate decision to allow implementation and the FeatureVersion to match. Verified `implementation_eligible`, `live`, `window.is_live_compatible`, and `derive_feature_version` exist on `FeatureSpec`.
- **Locked-partition governance:** routed through `accepted_version.require_partition_access(...)` → `require_governance_metadata_for_locked_partition_use`; the unit test confirms a `locked_test_candidate` partition raises without contamination metadata and succeeds with it.
- **available_ts on every value:** `_validate_materialized_records` requires tz-aware `event_ts`/`available_ts` on every record and `available_ts >= event_ts`; the integration test asserts every emitted value line carries `available_ts`.
- **BBO / no-trade semantics:** dense-grid rows pass through `is_synthetic_no_trade_bar`; synthetic rows lacking the canonical no-trade signature are rejected; no forward-fill introduced.
- **Output containment:** `_alpha_data_root` rejects a root equal to or under the repo tree; `_require_under_root` enforces every write stays under `$ALPHA_DATA_ROOT`. The unit test confirms `Path.cwd()/data` is refused.
- **Idempotency/determinism:** content-hashed `plan_id`/`idempotency_key`, atomic temp-file replace, no-op rewrite when content is unchanged (integration test asserts `wrote_output` flips to `False` on second run).

## Artifact & Git Policy — PASS
`git ls-files runs` is empty. Working tree changes are confined to Allowed Paths; nothing staged (executor correctly left all unstaged for Ralph). No `runs/`, data, value, parquet/arrow/sqlite, or heavy artifacts present. No `ACTIVE_CAMPAIGN.md` write. Materialized values in tests go only to pytest `tmp_path`. Canary suite passed including `forbidden_test_tamper`, `forbidden_scope_drift`, `forbidden_raw_data_commit`, and the three governance leakage canaries.

## Claims & Boundaries — PASS
No broker/live/paper/order/account scope. No external provider calls. README snapshot is compact and factual (FLF-P13 complete, `feature_materialization` gate, FLF-P14 next, new module/doc named, unchanged safety boundaries) and incidentally cleans up stray duplicated fragments left by prior phases. Doc and README "alpha/tradability" matches are all explicit negations. No prohibited MVP state reachable.

## Warnings
1. **Lane-required `python tools/verify.py --lint` failed** on a pre-existing repo-wide Ruff backlog (254 files / 1314 errors). The four touched files pass scoped `ruff check`/`ruff format --check` per the handoff. This is a documented campaign-baseline condition, not introduced here, but the lane's broad lint check is not green. Recommend the campaign track the backlog separately.
2. **Bare `python -c "import alpha_system.features.engine"` fails** without `PYTHONPATH=src` (src-layout, no editable install). Environmental/checkout-wide, affects all modules; the import succeeds with `PYTHONPATH=src`. Worth normalizing at the campaign level but not a phase defect.
3. **Commit-eligible review artifacts** under `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P13/**` are not yet present — correctly deferred to this review / Ralph, not an executor miss.

None of the warnings indicate hidden failures, test weakening, scope drift, or policy violations. They are pre-existing/environmental and explicitly recorded in the handoff.

VERDICT: PASS_WITH_WARNINGS
