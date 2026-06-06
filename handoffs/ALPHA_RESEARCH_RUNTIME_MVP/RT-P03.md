# RT-P03 Handoff - Runtime Input Resolver

Campaign: `ALPHA_RESEARCH_RUNTIME_MVP`  
Phase: `RT-P03` - Runtime Input Resolver: DatasetVersion and Feature/Label Packs  
Executor: Codex  
Status: implementation complete; review not run by executor

## Scope Completed

- Added `alpha_system.runtime.input_resolver`.
- Added immutable, hashable, value-free `RuntimeInputPack` plus feature, label,
  and canonical input-view handles.
- Added `FeatureLabelPackResolver` for FeatureStore/FeatureRegistry and
  LabelRegistry metadata handle resolution.
- Added fail-closed `resolve_runtime_input_pack` outcome with
  `RuntimeEntryReason` / `RejectionReasonRecord`-shaped reasons.
- Enforced accepted DatasetVersion lifecycle states, sanctioned
  `resolve_dataset_version` lookup, raw/provider metadata rejection, feature
  `available_ts`, label `label_available_ts`, label-as-feature refusal,
  DatasetVersion/partition pack matching, Databento/IBKR non-merge, and
  locked/shadow partition metadata gates.
- Added synthetic unit and no-lookahead tests.
- Added durable input-resolver documentation and updated the README snapshot.

## Explicit Staging List For Ralph

No files were staged by Codex. Per executor instructions, Ralph should stage
only these commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/input_resolver.py`
- `tests/unit/runtime/test_input_resolver.py`
- `tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
- `docs/research_runtime/INPUT_RESOLVER.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P03.md`

No `configs/runtime/**` files were added or edited for RT-P03.

## Git Status

`git status --short` was not run. The executor safety override explicitly
forbade `git status`, `git diff`, staging, committing, and pushing. No
`git add`, `git commit`, `git push`, `git status`, or `git diff` command was
run by Codex.

## Validation Commands

- `find runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP -name STOP -type f -print`
  - Result: exit 1, run directory absent:
    `find: 'runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP': No such file or directory`.
- `python -c "import alpha_system.runtime.input_resolver"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not put `src` on `PYTHONPATH` for raw `python -c`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.input_resolver"`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime/test_input_resolver.py tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py -q`
  - Result: exit 0, `12 passed`.
- `test -f docs/research_runtime/INPUT_RESOLVER.md`
  - Result: exit 0.
- `python -m ruff format src/alpha_system/runtime/input_resolver.py tests/unit/runtime/test_input_resolver.py tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
  - Result: exit 0, `3 files reformatted`.
- `python -m ruff format --check src/alpha_system/runtime/input_resolver.py tests/unit/runtime/test_input_resolver.py tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
  - Result: exit 0, `3 files already formatted`.
- `python -m ruff check src/alpha_system/runtime/input_resolver.py tests/unit/runtime/test_input_resolver.py tests/no_lookahead/research_runtime/test_input_resolver_available_ts.py`
  - Result: exit 0, `All checks passed!`.
- `python -m pytest tests/unit/runtime tests/no_lookahead/research_runtime -q`
  - Result: exit 0, `26 passed`.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `python tools/verify.py --lint`
  - Result: exit 1.
  - Summary: repo-wide baseline lint/format debt outside RT-P03 scope
    (`277 files would be reformatted`, `Found 1341 errors`). The RT-P03 files
    passed targeted `ruff format --check` and `ruff check`.
- `python tools/verify.py --typecheck`
  - Result: exit 0, `python -m compileall -q src tests tools`.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0, all Frontier canaries passed.
- `git ls-files runs`
  - Result: exit 0, empty output.
- `find runs -name STOP -type f -print`
  - Result: exit 1, `runs` directory absent. No active STOP file was present
    in this checkout.

## Artifact Audit

- `git ls-files runs` returned empty output.
- No `runs/**` artifact was created.
- The referenced run artifact directory was absent in this checkout, so no
  run-local `handoff.md`, `review.md`, or `verdict.json` was written.
- No review artifacts were created; Claude review is owned by Ralph/reviewer.
- No files were staged by Codex. Therefore no staged `runs/` path or forbidden
  heavy/data/cache/log/DB artifact was introduced by this executor.
- `git diff --cached --name-only` was not run because the executor safety
  override forbade `git diff` and Codex did no staging.

## Caveats

- Tests use synthetic fixtures and injected seams only. No local data corpus,
  local registry DB, raw provider files, FeatureStore values, LabelStore values,
  Databento calls, or IBKR calls were used.
- Exact raw import smoke without `PYTHONPATH=src` failed due import path setup;
  the equivalent `PYTHONPATH=src` import passed, and pytest/verify commands
  use the repo-configured source path.
- Repo-wide lint remains blocked by pre-existing baseline issues outside the
  RT-P03 allowed paths. RT-P03-targeted format and lint checks pass.
