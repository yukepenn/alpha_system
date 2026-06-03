# ASV1-P27 Handoff - Review Bundles, Source Maps, and Audit Reports

## Scope Completed

Implemented the review artifact layer in the allowed paths:

- Review bundle model, validation, deterministic rendering, and local-only writer.
- Source map builder with source/config/test discovery, file hashes, manifest reference, registry reference, and artifact references.
- Audit report and release-validation report variants that reuse bundle/validation primitives and perform document-only reporting.
- Prohibited-claim checker for review artifacts.
- `alpha report build` review-bundle CLI wiring while preserving factor-card and study-report modes.
- Durable docs for review bundles, source maps, and audit reports.
- Default report config at `configs/reports/review_bundle.yaml`.
- README snapshot updated through ASV1-P27 with ASV1-P28 as the next planned phase.

## Coverage Summary

Review bundles include run manifest metadata, source map, config/code hashes, data/factor/label versions, engine version, registry records, diagnostics summary, optional backtest/cost/monthly sections, rejected configs, warnings, failed steps, failed runs, promotion decision status, no-lookahead validation status, artifact manifest, missing artifacts, known limitations, review status, and structured validation.

Source maps include relevant report source files, report config files, discoverable review-bundle tests, run manifest path, registry reference, and artifact references with existence/hash/policy metadata.

Audit reports summarize provenance completeness, missing sections, missing versions/hashes, missing artifacts, failed runs/steps, rejected configs, policy warnings, promotion decision status, no-lookahead status, review status, and known limitations.

Missing artifacts, failed runs, failed steps, and rejected configs are surfaced as structured sections and warnings. The bundle builder does not filter them out.

## Prohibited-Claim Behavior

`src/alpha_system/reports/claim_checks.py` blocks the phase’s prohibited report-claim vocabulary and contextual approval-without-review wording. Review bundle, audit report, release-validation report, Markdown, CSV, and summary paths invoke the checker.

No alpha, tradability, broker, live, paper, deployment, release-action, or promotion-state mutation claim was introduced.

## Registry Integration

Registry reads are injected through an explicit `registry_path` and opened read-only. Tests initialize and read a temp SQLite DB only. The builder does not initialize, migrate, or write registry state.

## Validation Results

Passed:

- `python -m pytest tests/unit tests/integration` - 589 passed.
- `python -m pytest tests/unit/test_source_map_contents.py tests/unit/test_review_bundle_required_files.py tests/unit/test_review_bundle_artifact_policy.py` - 5 passed.
- `PYTHONPATH=src python -m alpha_system.cli report build --help` - passed and displayed review-bundle arguments.
- `python -m compileall src` - passed.
- `python tools/hooks/canary_runner.py` - passed; all Frontier canaries passed.
- `find artifacts/review_bundles -type f ! -name README.md ! -name .gitkeep -print 2>/dev/null || true` - no output.
- `find artifacts -type f -size +1M -print 2>/dev/null || true` - no output.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print` - no output.
- `find . -path './tests/fixtures/*' -prune -o -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' \) -print` - no output.
- `find . -type f \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.db-journal' -o -name '*.wal' \) -print` - no output.
- `git ls-files runs` - no output.

Environment/tool availability notes:

- `python -m alpha_system.cli report build --help` failed in this shell with `ModuleNotFoundError: No module named 'alpha_system'` because the package is not installed and `src` is not on `PYTHONPATH` for raw module execution.
- `alpha report build --help` failed with `alpha: command not found`; the console script is not installed in this shell.
- `python -m ruff check src tests` failed with `No module named ruff`; optional tool unavailable.
- `python -m mypy src` failed with `No module named mypy`; optional tool unavailable.

## Artifact Policy Confirmation

No full review bundle, generated bundle directory, heavy artifact, raw/canonical data, factor/label/signal store, local DB, log, or cache was committed. The fixture CLI integration writes only to pytest temp directories.

`runs/**` remains local-only. `git ls-files runs` returned empty. No run-local handoff, review, verdict, checks, or repair artifact was staged.

## Files Changed And Explicit Staging Set

The explicit staging set is:

- `README.md`
- `src/alpha_system/reports/review_bundle.py`
- `src/alpha_system/reports/source_map.py`
- `src/alpha_system/reports/audit_report.py`
- `src/alpha_system/reports/release_report.py`
- `src/alpha_system/reports/bundle_validation.py`
- `src/alpha_system/reports/claim_checks.py`
- `src/alpha_system/cli/report.py`
- `docs/REVIEW_BUNDLES.md`
- `docs/SOURCE_MAPS.md`
- `docs/AUDIT_REPORTS.md`
- `configs/reports/review_bundle.yaml`
- `tests/unit/reports/__init__.py`
- `tests/unit/reports/review_bundle_fixtures.py`
- `tests/unit/test_source_map_contents.py`
- `tests/unit/test_source_map_includes_configs.py`
- `tests/unit/test_review_bundle_required_files.py`
- `tests/unit/test_review_bundle_required_versions.py`
- `tests/unit/test_review_bundle_missing_artifact_warning.py`
- `tests/unit/test_review_bundle_failed_run_visibility.py`
- `tests/unit/test_review_bundle_rejected_configs_visibility.py`
- `tests/unit/test_review_bundle_promotion_status.py`
- `tests/unit/test_review_bundle_prohibited_claims.py`
- `tests/unit/test_review_bundle_summary_schema.py`
- `tests/unit/test_review_bundle_artifact_policy.py`
- `tests/integration/test_report_build_cli_help.py`
- `tests/integration/test_review_bundle_fixture.py`
- `tests/integration/test_review_bundle_registry_tempdb.py`
- `handoffs/ASV1-P27.md`

## Known Limitations

- Exact raw `python -m alpha_system.cli ...` execution requires either an installed package or `PYTHONPATH=src` in this environment.
- The review bundle writer is a local static file writer, not a dashboard.
- The source map uses configured globs and explicit artifact references; it does not infer every possible transitive import.
- Release-validation reports are summaries over bundle/audit evidence only and do not take release actions.

## Relevant Risks

Addressed controls for R-014, R-015, R-016, R-025, R-034, R-037, and R-040:

- Claim checker blocks prohibited report language.
- Bundle reports promotion decision status without mutating lifecycle state.
- Failed runs/steps and rejected configs remain visible.
- Generated bundle output stays local-only and out of git.
- CLI integration writes to temp dirs in tests.
- Release and L2/event-driven scope remain document-only where referenced.

## Review Focus

Please review bundle completeness, source-map usefulness, failed/missing/rejected evidence surfacing, claim-check behavior, registry temp-DB handling, local-only artifact policy, and absence of broker/live/paper/deployment scope or second PnL truth.
