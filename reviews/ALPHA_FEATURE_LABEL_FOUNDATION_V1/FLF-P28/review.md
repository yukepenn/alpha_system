I have enough to render a verdict. All artifacts verified: imports resolve, signatures match, tests are not weakened, artifact policy is clean, and canaries/doctor pass.

# Claude Review — FLF-P28: CLI / Tooling Surface

**Lane:** YELLOW · **Reviewer:** Claude Opus 4.8 · **Phase:** `ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P28`

## Scope compliance

All spec scope delivered and confined to Allowed Paths:

- `src/alpha_system/cli/feature.py` — `list` / `plan` / `materialize --dry-run` / `report` / `duplicate-audit`. ✅
- `src/alpha_system/cli/label.py` — `list` / `plan` / `materialize --dry-run` / `report` / `leakage-audit` / `input-pack`. ✅
- `src/alpha_system/cli/main.py` — adds `register_feature_subparser` / `register_label_subparser` imports and calls in the established alphabetical pattern; no existing subcommand altered. ✅
- Both CLI test files + `docs/CLI_REFERENCE.md` + compact `README.md` snapshot + commit-eligible handoff. ✅

`git status --short` shows **only** the 8 allowed paths (3 modified, 5 untracked). No stray files.

## Safety verification (independently checked)

- **Imports/signatures resolve.** I confirmed every symbol the CLI imports exists and that call sites match real APIs: `build_feature_materialization_plan` / `resolve_feature_materialization_dataset` (re-exported from `features.engine`), `build_label_materialization_plan` (accepts `instrument_ids`/`alpha_data_root`/`governance_metadata`/`partition_plan`/`dry_run`), all four `labels.families.*` builders, `validate_study_input_pack`, `audit_registered_label`, and the FLF-P15 `FeatureQualityReport`/`FeatureCoverageReport.from_registry_record`. The two tests' main failure risk (unresolved imports) is therefore ruled out.
- **No provider/network surface.** No `databento`/`ib_insync`/parquet/arrow/dbn/zst readers in either module; provider-reader heuristic returns clean; both tests assert provider client modules stay out of `sys.modules`. Dataset access is only via the sanctioned `resolve_*_materialization_dataset` adapters. ✅
- **Dry-run defaults.** `materialize` sets `default=True` + `set_defaults(dry_run=True)` in both groups; payloads hardcode `writes_values: False`. Plan builders write nothing. ✅
- **Fail-closed.** Missing registry/spec/DatasetVersion raises typed errors → exit 2 with no fabricated output; registries opened read-only (`mode=ro`). ✅
- **No forbidden scope.** No order/account/broker/paper/live, no alpha-search/strategy/backtest/portfolio, no promotion. No prohibited MVP-state strings reachable. Output is row-free metadata (ids/counts/lifecycle), no value leakage. ✅
- **Governance consumed not edited (R-022).** No edits to `governance/study_spec.py`, `feature_request.py`, `label_spec.py`, `duplicate_exposure.py`, `label_leakage_guard.py`, or `study_input_pack.py`. `ACTIVE_CAMPAIGN.md` untouched. ✅
- **Artifact policy.** `git ls-files runs` empty; no `runs/` path staged; no DB/parquet/heavy/data artifact in the change set; explicit staging only. ✅
- **Tests not weakened.** No `skip`/`xfail`/marker/mock-stub; `monkeypatch` used legitimately to simulate missing-dataset fail-closed paths. ✅

## Validation

`just verify-canaries` (16 + governance canaries) and `just frontier-doctor` both pass (re-run by me). Executor reports `verify.py --smoke` and `pytest … 8 passed` green. I could not re-run pytest/verify myself (environment blocked compound/dynamic commands for approval), so those two dynamic results are taken from the executor log — mitigated by my static confirmation that all imports and call signatures resolve and the canary/doctor gates pass locally.

## Warnings (non-blocking)

1. **Private-API coupling.** Both modules import the underscore-prefixed `_record_from_json` from `features.registry` / `labels.registry` (and `features.registry._record_from_json`). This reaches into private helpers and is fragile across refactors. Prefer a public accessor in a follow-up. (Not a forbidden path; consume-only.)
2. **`label report` substitution.** Spec §3 named `LabelQualityReport`/`LabelCoverageReport` for `label report`; those classes do not exist in the codebase, so the implementer reasonably rendered LabelRegistry record summaries (incl. `exposure_report`) instead. Defensible given the spec's "e.g." framing — flagging the deviation for the record.
3. **`main.py` `__main__` guard.** A small additive `if __name__ == "__main__": raise SystemExit(main())` block was added beyond pure registration wiring. Harmless and consistent with module-runnable CLIs; does not change existing subcommand behavior.

## Conclusion

Phase scope is complete, local-only, CI-safe, and fully within artifact/lane policy. No broker/live/paper/destructive scope, no hidden failed runs, no test weakening, no unsupported claims, no scope drift. The warnings are maintainability/transparency notes, not correctness or safety defects.

VERDICT: PASS_WITH_WARNINGS
