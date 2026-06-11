# P200000_FUTSUB_EXPOSURE_GUARD_LIFECYCLE Handoff

## Branch / Commit

- Branch: `repair/futsub-ohlcv-rth-repoint`
- Base commit observed: `f0986bd`
- Commits made: none. Per instruction, changes are left unstaged.

## Scope Completed

- `FeatureRegistry.read_factor_versions()` now exposes only
  `REGISTERED` feature rows to the governance duplicate-exposure guard.
- Raw feature audit reads are unchanged: `resolve_feature(...,
  include_deprecated=True)` still returns deprecated rows.
- Symmetric label-side exposure view existed:
  `src/alpha_system/labels/registry.py:783` `read_label_versions()`.
  It now uses a `REGISTERED`-only helper; label duplicate exposure accounting
  in `build_exposure_report()` also uses that active-only row set.
- Raw label audit reads are unchanged:
  `src/alpha_system/labels/registry.py:791` `read_label_records()` still
  returns deprecated rows.
- Did not modify `src/alpha_system/governance/duplicate_exposure.py`.

## Files Changed

- `src/alpha_system/features/registry.py`
- `src/alpha_system/labels/registry.py`
- `tests/unit/features/test_feature_store.py`
- `tests/unit/labels/test_label_store.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P200000_FUTSUB_EXPOSURE_GUARD_LIFECYCLE.md`

Pre-existing unstaged P194500 files were present before this phase and were not
intentionally modified by P200000.

## Validation

- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features -q`
  - PASS: `131 passed in 1.08s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k 'exposure or request_gate or registry' -q`
  - PASS: `94 passed, 2527 deselected in 2.78s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q`
  - Expected non-green modulo known pre-existing env failures:
    `3 failed, 2857 passed, 1 skipped in 51.17s`
  - Failures observed:
    - `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`
    - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`
    - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`
- `python tools/verify.py --smoke`
  - PASS: exit code 0
- `python tools/hooks/canary_runner.py .`
  - PASS: all Frontier canaries passed
- Additional focused rerun after formatting:
  - `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features/test_feature_store.py tests/unit/labels/test_label_store.py -q`
  - PASS: `13 passed in 1.14s`
- `git diff --check`
  - PASS
- Artifact checks:
  - `git ls-files runs` returned empty
  - `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'` returned empty

## Test Coverage Added

- Deprecated feature row no longer produces a blocking exposure for a new
  equivalent/superseding `FeatureRequest`.
- Identical `REGISTERED` feature row still produces a blocking duplicate
  exposure finding.
- Raw feature reads still see deprecated rows.
- Label-side symmetric exposure view/accounting ignores deprecated rows while
  raw label reads retain them; `REGISTERED` label duplicates still record a
  duplicate exposure.

## Non-Runs / Constraints

- No commits, staging, PR creation, or review artifact creation, per user
  instruction.
- No `git worktree` command was run.
- No `.git/config` changes were made.
- No forbidden paths or external data/provider access were needed.

## Risks / Caveats

- `read_factor_versions()` is also consumed by feature reports; those consumers
  now receive the same active-only view as the duplicate-exposure guard. Raw
  audit/deprecation reads remain available through explicit registry resolvers.
- The full pytest sweep remains red only for the three pre-existing failures
  listed above.

## Review Request Focus

- Confirm `FeatureRegistry.read_factor_versions()` is the intended active-only
  governance view and that no raw audit consumer depended on it for deprecated
  rows.
- Confirm the label-side closure is acceptable: `read_label_versions()` and
  `build_exposure_report()` now count only `REGISTERED` labels as active
  exposures.

## Next Recommended Step

- Fresh reviewer should inspect the lifecycle filter boundaries and verify the
  three full-suite failures are the known pre-existing environment failures, not
  regressions from this phase.
