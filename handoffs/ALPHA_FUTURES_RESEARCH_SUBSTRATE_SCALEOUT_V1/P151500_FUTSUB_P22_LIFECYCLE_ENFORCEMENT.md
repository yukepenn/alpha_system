# P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT Handoff

Phase: `P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT`
Branch: `repair/p22-lifecycle-enforcement`
Date: 2026-06-11

## Scope Completed

- Added explicit REGISTERED-only label resolution APIs while preserving raw by-id
  audit/deprecation reads:
  `src/alpha_system/labels/registry.py:571`.
- Added matching feature registry/store active resolution and deprecation lookup
  surfaces:
  `src/alpha_system/features/registry.py:544`,
  `src/alpha_system/features/store.py:208`.
- Enforced runtime pack lifecycle state for both feature and label locks before
  handles are accepted:
  `src/alpha_system/runtime/input_resolver.py:470`,
  `src/alpha_system/runtime/input_resolver.py:544`,
  `src/alpha_system/runtime/input_resolver.py:1334`.
- Deprecated label locks now fail closed with `label_pack_deprecated`; when a
  `replacement_label_version_id` exists in registry deprecation metadata, it is
  surfaced in the reason `actual` string.
- Missing ids still use the existing `label_pack_not_found` /
  `feature_pack_not_found` paths.
- Raw deprecated access remains available through `resolve_label` /
  `resolve_label_by_version` and `resolve_feature` /
  `resolve_feature_by_version` defaults.

## Bounded Repair Attempt 1

- Flipped the two remaining resolver-backed runtime-positive label fixtures from
  `READY_FOR_STUDY` to `REGISTERED`:
  `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
  and `tests/integration/runtime/test_smoke.py`. The original availability-gate
  and smoke PASS assertions are exercised again; no assertions were weakened.
- Executed the coordinator admissibility decision recorded in the spec on
  2026-06-11T15:45Z: runtime pack resolution remains `REGISTERED`-only.
  Updated the `docs/feature_label_foundation/` descriptions to say
  `READY_FOR_STUDY` is reserved, has no production writer, and is not
  runtime-admissible until a reviewed promotion API explicitly extends
  admissibility.
- Grep sweep found no additional `READY_FOR_STUDY` test fixtures that route
  through the `FeatureLabelPackResolver` lifecycle gate after the two fixture
  flips above. Remaining test-tree occurrences are direct `RuntimeInputPack` /
  `LabelPackHandle` fixtures or legacy lifecycle-flow assertions, not resolver
  gate inputs.

## Feature-Side Symmetry Verdict

The same lifecycle gap existed on the feature side. Before this phase,
`FeatureLabelPackResolver.resolve_feature_packs` only blocked `None` lookups;
`FeatureRegistry.resolve_feature` fetched by id without lifecycle filtering.
This phase closed it identically: feature runtime resolution tries the active
REGISTERED-only resolver first, falls back to raw by-id only to produce a
reasoned closed failure, and rejects non-REGISTERED rows with
`feature_pack_deprecated` or `feature_pack_not_registered`. Replacement feature
ids are surfaced from `replacement_feature_version_id` when available.

## Tests Added Or Updated

- Added `tests/unit/labels/test_registry_lifecycle_resolution.py`, using a real
  temp SQLite `LabelRegistry` and the production runtime resolver path. It
  asserts deprecated label lock failure with replacement pointer, REGISTERED
  label resolution, and raw audit access to deprecated rows.
- Updated `tests/unit/runtime/test_input_resolver.py` with feature-side
  deprecated-pack closure coverage.
- Updated existing runtime-positive fixtures from `READY_FOR_STUDY` to
  `REGISTERED` where they flow through `FeatureLabelPackResolver`, per this
  phase's new runtime admissibility rule.
- Updated the two full-suite collateral fixtures identified by review:
  `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
  and `tests/integration/runtime/test_smoke.py`.
- Updated `tests/unit/features/test_feature_store.py` to assert feature raw
  audit access and active REGISTERED-only filtering remain distinct.

## Files Changed

- `src/alpha_system/labels/registry.py`
- `src/alpha_system/features/registry.py`
- `src/alpha_system/features/store.py`
- `src/alpha_system/runtime/input_resolver.py`
- `src/alpha_system/runtime/dry_run.py`
- `tests/unit/labels/test_registry_lifecycle_resolution.py`
- `tests/unit/runtime/test_input_resolver.py`
- `tests/unit/runtime/fail_closed/test_runtime_fail_closed.py`
- `tests/unit/features/test_feature_store.py`
- `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
- `tests/integration/runtime/test_smoke.py`
- `docs/feature_label_foundation/LABEL_STORE.md`
- `docs/feature_label_foundation/README.md`
- `docs/feature_label_foundation/guide/README.md`
- `docs/feature_label_foundation/guide/safety_semantics.md`
- `docs/feature_label_foundation/guide/request_to_study.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P151500_FUTSUB_P22_LIFECYCLE_ENFORCEMENT.md`

Forbidden files were not edited:
`labels/engine.py`, `labels/families/**`, `labels/fast/**`,
`labels/roll_guard.py`, `labels/version.py`.

## Validation

- `python tools/frontier/status_doctor.py` - WARN: no run dir with `state.json`
  found for this campaign; no live run to reconcile. Hook floor and runtime
  contract OK.
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/labels/test_registry_lifecycle_resolution.py -q` - PASS:
  `3 passed in 0.41s`.
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/runtime/test_input_resolver.py -q` - PASS:
  `8 passed in 0.16s`.
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features/test_feature_store.py -q` - PASS:
  `6 passed in 0.69s`.
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/labels -q` - PASS:
  `37 passed in 0.66s`.
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k 'registry or resolver' -q` - PASS:
  `74 passed, 2520 deselected in 2.44s`.
- `python tools/verify.py --smoke` - PASS: exit 0, no output.
- `python tools/hooks/canary_runner.py` - PASS: all Frontier canaries passed.
- `git diff --check` - PASS: no output.
- `git ls-files runs` - PASS: no output.

Bounded repair attempt 1 validation:

- `~/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py tests/integration/runtime/test_smoke.py -q` - PASS:
  `8 passed in 0.22s`.
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q` - expected local env failures only:
  `3 failed, 2830 passed, 1 skipped in 50.72s`.
  Failures:
  `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`,
  `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`,
  `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`.
- Base triage used an archive of `origin/main`
  `6f405bc84875a0c817d0d20fe10ad7c750444574` extracted under `/tmp` because
  `git worktree add` could not write metadata to the read-only canonical
  `.git`. Command:
  `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture -q`
  from the base archive - REPRODUCED:
  `3 failed in 0.70s` with the same three failure classes
  (empty Databento canonicalized OHLCV rows; DuckDB and Polars returning tuple
  rows while the tests expect list rows).
- `python tools/verify.py --smoke` - PASS: exit 0, no output.
- `python tools/hooks/canary_runner.py` - PASS: all Frontier canaries passed.

Non-required note:

- `~/.venvs/alpha_system_research/bin/python -m ruff format --check ...` could
  not run because `ruff` is not installed in the research venv.

## Review Notes

- The run-local P22 review mentioned in the spec was not present because this
  worktree has no `runs/` directory. Implementation followed the committed
  phase spec and the reviewer facts supplied in the executor prompt.
- No commits, PRs, reviews, or verdict artifacts were created.
- All changes are intentionally left unstaged.
