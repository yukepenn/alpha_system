# FLF-P27 Handoff - Governance Integration: StudySpec Input Packs

## Summary

Added the additive `alpha_system.governance.study_input_pack` helper for
StudySpec input packs. The helper bundles governed `freq_` FeatureRequest
handles, `lspec_` LabelSpec handles, one `aspec_` AlphaSpec handle, and a
substantive `dataset_scope` mapping into an immutable, hashable, canonically
serializable input bundle.

The helper validates handles through `alpha_system.governance.ids` and exposes
optional resolved-record validation that consumes the public `FeatureRequest`,
`LabelSpec`, `AlphaSpec`, and `StudySpec` validators. It does not construct or
persist a `StudySpec` from a pack, does not modify `StudySpec`, and adds no
parallel study or experiment schema.

Added focused unit tests, a synthetic config template, the governance
integration doc, and the compact README snapshot update required by the phase.

## Files Changed

- `src/alpha_system/governance/study_input_pack.py`
- `tests/unit/governance/test_study_input_pack.py`
- `configs/governance/feature_label_pack/README.md`
- `configs/governance/feature_label_pack/study_input_pack.synthetic.json`
- `docs/feature_label_foundation/governance_integration.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P27.md`

## Executor Staging

Codex staged no files.

Explicitly staged files by Codex: none.

Ralph should stage only the curated commit-eligible paths above, by explicit
path. No `git add`, `git commit`, `git push`, PR creation, merge, or force push
was run by Codex.

`git status --short` was not run because the executor prompt explicitly
forbade `git status`. No output is available for that command from Codex.

`git diff --cached --name-only` was not run because the executor prompt
explicitly forbade `git diff`. Codex did not stage any files.

## Validation

- `git status --short` - skipped by executor safety override; the prompt
  explicitly forbade `git status`.
- `git ls-files runs` - passed; empty output.
- `python -c "import alpha_system.governance.study_input_pack"` - failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because this shell does
  not add `src` to `sys.path`.
- `PYTHONPATH=src python -c "import alpha_system.governance.study_input_pack"` -
  passed.
- `python -m pytest tests/unit/governance/test_study_input_pack.py -q` -
  passed, `17 passed in 0.03s`.
- `test -f docs/feature_label_foundation/governance_integration.md` - passed.
- `python tools/verify.py --smoke` - passed.
- Governance consume-only audit command using
  `git diff --name-only HEAD | grep ...` - skipped by executor safety override;
  the prompt explicitly forbade `git diff`. Codex did not edit existing
  governance modules.
- `find data -type f ! -name README.md ! -name .gitkeep -print` - passed;
  empty output.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print` - passed;
  empty output.
- `find . -name '*.parquet' -not -path './tests/fixtures/*' -print` - passed;
  empty output.
- `python tools/hooks/canary_runner.py` - passed; all Frontier canaries passed.
- `python -m ruff check src/alpha_system/governance/study_input_pack.py tests/unit/governance/test_study_input_pack.py` -
  passed.
- `python -m ruff format --check src/alpha_system/governance/study_input_pack.py tests/unit/governance/test_study_input_pack.py` -
  passed, `2 files already formatted`.
- `python tools/verify.py --typecheck` - passed; ran
  `compileall -q src tests tools`.
- `PYTHONPATH=src python -c "import json; from pathlib import Path; from alpha_system.governance.study_input_pack import validate_study_input_pack; validate_study_input_pack(json.loads(Path('configs/governance/feature_label_pack/study_input_pack.synthetic.json').read_text(encoding='utf-8')))"` -
  passed.
- `python tools/verify.py --lint` - failed on the existing full-repo ruff
  backlog outside this phase: `270 files would be reformatted`, `517 files
  already formatted`, and `1311 errors`. The new FLF-P27 Python files pass the
  targeted ruff checks above.
- `python tools/verify.py --test` - failed with pre-existing/out-of-scope
  full-suite failures: `17 failed, 2077 passed in 32.05s`. Failure groups were
  `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network`, twelve
  `tests/test_ralph_driver.py` Workflow 2 provider/merge-gate tests, and four
  `tests/unit/features/test_feature_store.py` tests.
- `python -m pytest tests/unit/features/test_feature_store.py -q` - passed,
  `4 passed in 0.31s`, confirming the `feature_store` failures remain
  order/environment-sensitive in the full suite.

## Artifact Policy

- No `runs/**` path was created for commit eligibility or staged by Codex.
- `git ls-files runs` returned empty output.
- The run-local phase directory
  `runs/2026-06-05T131433Z_ALPHA_FEATURE_LABEL_FOUNDATION_V1/phases/FLF-P27`
  was absent in this checkout; no run-local `handoff.md`, `review.md`, or
  `verdict.json` was created by Codex.
- No raw, canonical, factor, label-value, provider-response, parquet, arrow,
  feather, DBN, Zstd, SQLite, local registry, log, cache, model, or heavy
  artifact was added for commit eligibility.
- The config file under `configs/governance/feature_label_pack/` is a tiny
  synthetic template only. It contains placeholder governance handles and no
  real ids, real data, alpha evidence, provider response, or materialized
  feature/label values.

## DAG And README Snapshot

- FLF-P27 remains parallel-safe with disjoint allowed paths in the
  `diagnostics_and_packaging` merge group and `workflow_and_closeout` gate.
- No shared feature/label core path was edited.
- `ACTIVE_CAMPAIGN.md` was not edited.
- README snapshot was applied compactly for FLF-P27, the new helper/doc, the
  FLF-P28 dependency pointer, and unchanged safety boundaries. It does not add
  generated run details or duplicated handoff content.
- Serial merge, PR creation, CI waiting, merge-gate evaluation, review, verdict
  parsing, and done-check remain Ralph-owned.

## Governance Consume Confirmation

- Existing governance modules were consumed through public APIs and not edited:
  `study_spec.py`, `feature_request.py`, `label_spec.py`,
  `duplicate_exposure.py`, `label_leakage_guard.py`, `alpha_spec.py`,
  `promotion*.py`, `registry.py`, and `ids.py`.
- `StudySpec` schema is unchanged.
- No parallel `StudySpec`, study schema, experiment schema, registry, or
  persistence layer was introduced.
- The pack is an input bundle only; it does not state that a study was run, that
  diagnostics passed, or that evidence was produced.

## Forbidden Scope Confirmation

- No live trading, paper trading, broker operation, account operation, order
  routing, production deployment, PR creation, merge, or destructive cleanup was
  performed.
- No Databento, IBKR, external provider, raw-provider, or broker client was
  imported or called.
- No strategy, backtest, portfolio, execution, order, account, broker, paper,
  live, or deployment scope was added.
- No alpha, profitability, tradability, robustness, approval, promotion,
  production-readiness, paper-readiness, live-readiness, broker-readiness, or
  order-routing-safety claim was added.
