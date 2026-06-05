# FLF-P23 Handoff - Label Leakage and Availability Audits

## Summary

Added the label leakage and availability audit layer in
`src/alpha_system/labels/leakage_audit.py`.

The audit produces `LabelLeakageAuditReport` objects for registered
`LabelRegistryRecord`s, invokes the existing governance
`alpha_system.governance.label_leakage_guard.check_label_leakage(...)` for
`label_as_feature` and `availability_time`, checks direct label identity reuse
as live feature references, and audits supplied local label value records for
`label_available_ts` presence and ordering. Missing value records, missing
timestamps, forbidden feature overlap, label identity reuse, live feature
availability at or after label availability, or `label_available_ts` before
`horizon_end_ts` / governed `availability_time` are blocking.

The module is additive and descriptive only. It does not modify governance
modules, label materialization, label registry/store code, feature code, or
provider/data access code.

## Repair Summary

The review found that the spec-required test basenames under
`tests/no_lookahead/feature_label/` collided with pre-existing test basenames
under `tests/no_lookahead/`, causing whole-suite pytest collection to fail under
pytest's default import mode.

This bounded repair adds package markers at:

- `tests/no_lookahead/__init__.py`
- `tests/no_lookahead/feature_label/__init__.py`

With those markers, pytest gives the colliding modules distinct import names
and collection no longer fails with import-file mismatch. This keeps the
spec-required test filenames unchanged and avoids a global pytest import-mode
change.

The two package-marker files were not in the original FLF-P23 commit-eligible
path list. The review explicitly identified this finding as requiring a small
allowed-path amendment; Ralph should treat these two files as the
review-driven repair amendment if this repair is accepted.

This bounded repair also substantiates the full-suite base-parity finding from
the done-check. A local `/tmp` clone of the pre-FLF-P23 base commit
`e30edfa` was validated with the same commands. The active-shell base run fails
with the same GitHub/Ralph environment-gated group plus the same four
`tests/unit/features/test_feature_store.py` failures. With the active Frontier
PR/parallel env vars unset, the base run clears the GitHub/Ralph group and
still fails only the same four `feature_store` cases. This confirms those four
failures are pre-existing relative to FLF-P23 rather than introduced by the
label leakage audit or the package-marker repair.

## Files Changed

- `src/alpha_system/labels/leakage_audit.py`
- `tests/no_lookahead/feature_label/test_label_leakage_guard.py`
- `tests/no_lookahead/feature_label/test_label_available_ts.py`
- `tests/no_lookahead/__init__.py`
- `tests/no_lookahead/feature_label/__init__.py`
- `docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P23.md`

## Executor Staging

Codex staged no files. `git diff --cached --name-only` returned empty output.

If Ralph accepts this repair, stage only curated paths explicitly by path. The
original FLF-P23 commit-eligible files are:

- `src/alpha_system/labels/leakage_audit.py`
- `tests/no_lookahead/feature_label/test_label_leakage_guard.py`
- `tests/no_lookahead/feature_label/test_label_available_ts.py`
- `docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P23.md`

The review-driven repair amendments are:

- `tests/no_lookahead/__init__.py`
- `tests/no_lookahead/feature_label/__init__.py`

No `runs/**` path was created for commit eligibility or staged by Codex.

## Validation

- `git status --short` - succeeded. Output showed:
  - ` M README.md`
  - `?? docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md`
  - `?? handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P23.md`
  - `?? src/alpha_system/labels/leakage_audit.py`
  - `?? tests/no_lookahead/__init__.py`
  - `?? tests/no_lookahead/feature_label/__init__.py`
  - `?? tests/no_lookahead/feature_label/test_label_available_ts.py`
  - `?? tests/no_lookahead/feature_label/test_label_leakage_guard.py`
- `python -c "import alpha_system.labels.leakage_audit"` - failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because this shell does
  not add `src` to `sys.path` outside pytest or an installed package.
- `PYTHONPATH=src python -c "import alpha_system.labels.leakage_audit"` -
  succeeded.
- `python tools/verify.py --smoke` - succeeded.
- `python -m pytest tests/no_lookahead/feature_label -q` - succeeded,
  `13 passed`.
- `python -m pytest tests/no_lookahead/test_label_available_ts.py tests/no_lookahead/feature_label/test_label_available_ts.py tests/no_lookahead/test_label_leakage_guard.py tests/no_lookahead/feature_label/test_label_leakage_guard.py -q` -
  succeeded, `16 passed`; this directly verifies the colliding basenames now
  collect together.
- `python -m pytest tests/unit/features/test_feature_store.py -q` - succeeded,
  `4 passed`.
- `test -f docs/feature_label_foundation/LABEL_LEAKAGE_AUDIT.md` - succeeded.
- `python -m ruff check src/alpha_system/labels/leakage_audit.py tests/no_lookahead/feature_label/test_label_leakage_guard.py tests/no_lookahead/feature_label/test_label_available_ts.py` -
  succeeded, `All checks passed!`.
- `python tools/hooks/canary_runner.py` - succeeded, all Frontier canaries
  passed.
- `python tools/verify.py --test` - collection regression repaired. Pytest
  collected `2077` items, including both new `feature_label` files, and no
  longer reports import-file mismatch. The command still failed with
  `17 failed, 2060 passed` in the active shell. Failures were outside FLF-P23
  audit scope: `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network`,
  twelve `tests/test_ralph_driver.py` provider/merge-gate status tests, and
  four `tests/unit/features/test_feature_store.py` request-gate tests.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES python tools/verify.py --test` -
  collection regression repaired. With the active Frontier PR/parallel env vars
  removed, the GitHub/Ralph driver failures cleared, but the full run still
  failed with `4 failed, 2073 passed` in
  `tests/unit/features/test_feature_store.py`. Those four pass when run alone
  and appear order-sensitive to the existing `tests/unit/test_no_local_data_required.py`
  module-clearing behavior. This repair did not edit those out-of-scope tests
  or feature/governance code.
- `python tools/verify.py --all` - collection regression repaired. The command
  still failed with the same active-shell `17 failed, 2060 passed` pytest result
  above after `compileall` and pytest. No import-file mismatch remained.
- Base parity check:
  `python tools/verify.py --all` in `/tmp/flf-p23-base-clone.bh4OcQ`
  at base commit `e30edfa` failed with `17 failed, 2052 passed`. The failing
  groups matched the repaired working tree under the active Frontier
  environment: one `tests/test_github_utils.py` dry-run PR test, twelve
  `tests/test_ralph_driver.py` provider/merge-gate tests, and the same four
  `tests/unit/features/test_feature_store.py` request-gate tests.
- Base parity check with active Frontier PR/parallel env vars unset:
  `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES python tools/verify.py --all`
  in `/tmp/flf-p23-base-clone.bh4OcQ` at base commit `e30edfa` failed with
  `4 failed, 2065 passed`. The only failures were the same four
  `tests/unit/features/test_feature_store.py` cases:
  `test_registration_fails_closed_without_valid_spec_request_or_lineage`,
  `test_successful_registration_resolves_by_version_and_feature_set`,
  `test_duplicate_or_equivalent_exposure_is_not_silently_admitted`, and
  `test_deprecation_preserves_lineage_and_excludes_prohibited_states`.
- `git ls-files runs` - succeeded, empty output.
- `git diff --cached --name-only` - succeeded, empty output.
- `find data -type f ! -name README.md ! -name .gitkeep -print` - succeeded,
  empty output.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print` -
  succeeded, empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` -
  succeeded, empty output.
- `git ls-files | grep -E '\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|dbn|zst|log)$' | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"` -
  succeeded, `no committed heavy/db/log artifacts`.

## Artifact Policy

- No raw, canonical, factor, label value, provider-response, parquet, arrow,
  feather, DBN, Zstd, SQLite, local registry, log, cache, or heavy artifact was
  added for commit eligibility.
- Tests use synthetic in-memory contracts and pytest temp paths only.
- `git ls-files runs` returned empty output.
- No run-local `handoff.md`, `review.md`, or `verdict.json` was created.
- The `runs/` directory is absent in this checkout; no STOP file was present for
  Codex to act on.
- Codex did not run `git add`, `git commit`, `git push`, create a PR, or merge.
- Explicit staging remains Ralph-owned after executor completion.

## DAG And Scope

- DAG metadata remains correct for this phase: run-alone, not parallel-safe,
  serial `label_integration` merge group, disjoint implementation paths, and no
  `ACTIVE_CAMPAIGN.md` write.
- Governance modules were consumed read-only and not edited:
  `label_leakage_guard.py`, `label_spec.py`, `study_spec.py`,
  `feature_request.py`, and `duplicate_exposure.py` were not modified.
- Other label modules and feature-core files were not edited.
- No Claude call, reviewer execution, `review.md`, `verdict.json`, PR, merge,
  deployment, broker, live, paper, order-routing, account, or destructive
  cleanup operation was performed.
- No label-as-feature path, external provider call, raw provider access,
  committed feature/label values, prohibited lifecycle state, or alpha,
  profitability, tradability, strategy, backtest, portfolio, broker, paper,
  live, or production-readiness claim was added.

## Review Request Focus

Please review the audit report semantics, governance-guard consumption,
fail-closed handling of missing label value records, direct label identity
checks, `label_available_ts` ordering checks, and the review-driven package
markers that repair whole-suite collection for the spec-required
same-basename tests.
