# FLF-P28 Handoff - CLI / Tooling Surface

## Summary

Added the local-only Feature/Label CLI surface for FLF-P28.

The phase adds:

- `alpha feature list`, `plan`, `materialize --dry-run`, `report`, and
  `duplicate-audit`.
- `alpha label list`, `plan`, `materialize --dry-run`, `report`,
  `leakage-audit`, and `input-pack`.
- Shared parser registration in `alpha_system.cli.main` using the established
  `register_subparser(subparsers)` pattern.
- Focused CLI unit tests for parser wiring, dry-run defaults, fail-closed
  missing input behavior, and provider-client import cleanliness.
- A Feature/Label section in `docs/CLI_REFERENCE.md`.
- A compact README snapshot update for FLF-P28.

The CLI is a thin read/plan/dry-run surface. Feature planning consumes
registered local FeatureSetSpec membership from the FeatureRegistry and resolves
accepted DatasetVersions through the existing feature materialization adapter.
Label planning consumes governed LabelSpec JSON through the existing label
family builders and resolves accepted DatasetVersions through the existing
label materialization adapter. Registry listing/reporting/audits use read-only
SQLite connections and do not write values.

## Staging / Curated File List

Staged by Codex: none. The executor prompt explicitly prohibited `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes are left
unstaged for Ralph.

Curated files for Ralph to stage explicitly by path:

- `src/alpha_system/cli/feature.py`
- `src/alpha_system/cli/label.py`
- `src/alpha_system/cli/main.py`
- `tests/unit/cli/test_feature_cli.py`
- `tests/unit/cli/test_label_cli.py`
- `docs/CLI_REFERENCE.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P28.md`

No review artifacts were created by Codex because the executor prompt forbade
calling Claude, running reviewer, and creating `review.md` or `verdict.json`.
YELLOW review remains Ralph-owned.

## Validation

- `git status --short` - skipped; explicitly forbidden by the executor prompt.
- `python -c "import alpha_system.cli.main"` - failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because bare `python`
  does not put `src/` on `sys.path` in this checkout.
- `PYTHONPATH=src python -c "import alpha_system.cli.main"` - passed.
- `python tools/verify.py --smoke` - passed.
- `python -m pytest tests/unit/cli/test_feature_cli.py tests/unit/cli/test_label_cli.py -q` -
  passed, `8 passed`.
- `git ls-files runs` - passed; empty output.
- `python -m alpha_system.cli.main --help` - failed with
  `ModuleNotFoundError: No module named 'alpha_system'` for the same bare
  `python` environment reason.
- `PYTHONPATH=src python -m alpha_system.cli.main --help` - passed and showed
  both `feature` and `label` command groups. It emitted the pre-existing
  runpy warning caused by `alpha_system.cli.__init__` importing the main
  submodule before module execution.
- Provider/file-reader heuristic:
  `grep -REn "\.dbn|\.zst|read_parquet|pyarrow|databento|ib_insync|\.feather" src/alpha_system/cli/feature.py src/alpha_system/cli/label.py 2>/dev/null | grep -v "from_mapping\|resolve_dataset_version" || echo "no direct provider/file readers in feature/label CLI"` -
  passed with `no direct provider/file readers in feature/label CLI`.
- `python tools/hooks/canary_runner.py` - passed; all Frontier canaries passed.
- `python -m ruff check src/alpha_system/cli/feature.py src/alpha_system/cli/label.py src/alpha_system/cli/main.py tests/unit/cli/test_feature_cli.py tests/unit/cli/test_label_cli.py` -
  passed.
- `python -m ruff format --check src/alpha_system/cli/feature.py src/alpha_system/cli/label.py src/alpha_system/cli/main.py tests/unit/cli/test_feature_cli.py tests/unit/cli/test_label_cli.py` -
  passed.

## Artifact Policy

- No `runs/**` file was created for commit eligibility or staged by Codex.
- `git ls-files runs` returned empty output.
- The run-local phase directory remains local-only; Codex did not create
  run-local `handoff.md`, `review.md`, `verdict.json`, checks, or repair
  artifacts.
- No raw, canonical, factor, feature-value, label-value, provider-response,
  parquet, arrow, feather, DBN, Zstd, SQLite, local registry, log, cache, model,
  report bundle, or heavy artifact was added for commit eligibility.
- Codex did not run `git add`, `git commit`, `git push`, create a PR, merge, or
  force push.
- `git diff --cached --name-only` was not run because the executor prompt
  forbade `git diff`; Codex performed no staging, so there is no Codex-staged
  set to inspect.

## DAG / Scope

- FLF-P28 DAG metadata was treated as run-alone:
  `parallel_safe=false`, `must_run_alone=true`, merge group
  `diagnostics_and_packaging`.
- `ACTIVE_CAMPAIGN.md` was not edited.
- The only shared CLI integration file edited was `src/alpha_system/cli/main.py`.
- README snapshot was updated compactly for FLF-P28, the new
  `alpha feature` / `alpha label` command groups, the updated
  `docs/CLI_REFERENCE.md`, the next FLF-P29 phase, and unchanged safety
  boundaries.
- Governance modules were consumed, not edited:
  feature requests, label specs, duplicate exposure, label leakage guard,
  StudySpec, and StudySpec input-pack helpers remain unchanged.
- The CLI consumes accepted DatasetVersion evidence through existing feature and
  label materialization dataset resolvers. It does not read raw provider files
  or call external providers.
- No live trading, paper trading, broker operation, account operation, order
  routing, production deployment, alpha search, strategy command, backtest
  command, portfolio command, PR creation, merge, or destructive cleanup was
  performed or added.
- No alpha, profitability, tradability, promotion, broker-readiness,
  paper-readiness, live-readiness, or production-readiness claim was introduced.

## Review Status

Fresh Claude Opus review is required for this YELLOW phase, but Codex did not
call Claude or create review artifacts because the executor prompt forbade
those actions. Ralph owns staging, commit, review, verdict parsing, PR, CI,
merge gate, and semantic done-check.
