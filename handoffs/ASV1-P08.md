# ASV1-P08 Handoff

## Phase

- Phase ID: `ASV1-P08`
- Phase name: Data Validation CLI and Local Fixture Policy
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p08-data-validation-cli-and-local-fixture-policy`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P08` (local-only)

## Executor Result

Implemented the scoped data CLI and fixture policy:

- `alpha data validate` is registered under the existing argparse CLI shell.
- `alpha data build-bars` is registered under the same `alpha data` group.
- Validation delegates to ASV1-P06 canonical bar normalization and validation.
- Calendar/session/quality behavior delegates to ASV1-P07 calendar,
  sessionization, and quality helpers.
- Local fixture and generated-output policy is implemented and documented.
- Tests cover CLI help, validation, build-bars, no-lookahead latency,
  temp-registry writes, fixture policy, and artifact policy.

No broker, paper trading, live trading, order routing, production deployment,
reviewer call, Claude call, PR creation, merge, or PASS marking was performed.

## Command Summary

### `alpha data validate`

Inputs:

- `--config`
- `--input`
- `--schema-id`
- optional `--calendar-id`
- optional `--registry-path`
- optional `--summary-out`
- optional `--json`

Behavior:

- Loads tiny CSV fixture-scale canonical bars.
- Applies P06 validation for required fields, types, timestamp ordering,
  OHLC/numeric sanity, nonnegative volume/trade count, spread consistency,
  duplicate keys, version fields, and configured
  `available_ts >= bar_end_ts + latency`.
- Applies P07 sessionization and quality reporting when the config supplies a
  `calendar_config`.
- Writes an explicit summary only when `--summary-out` is supplied.
- Writes a registry entry only when `--registry-path` targets a temp/local
  SQLite path outside the repo.
- Returns `0` for valid, `1` for validation/quality issues, and `2` for
  argument/config/policy/dependency errors.

### `alpha data build-bars`

Inputs:

- `--input`
- `--instrument-config`
- `--calendar-config`
- `--output`
- `--data-version`
- optional `--registry-path`
- optional `--validation-config`
- optional `--json`

Behavior:

- Accepts fixture inputs under `tests/fixtures/data/` by default.
- Refuses non-fixture inputs unless an explicit config sets
  `allow_non_fixture_input: true`.
- Uses P06 CSV normalization and validation.
- Uses P07 sessionization to derive session ids and per-session `bar_index`
  values.
- Validates the built rows and quality report before writing output.
- Writes local-only bars plus a small manifest and validation summary.
- Supports `.parquet` output through the existing P06 Polars-backed writer
  when that optional dependency is installed.
- Supports `.csv` output for deterministic dependency-free fixture tests; this
  is local-only and not commit-eligible.

## Fixture Policy Summary

Implemented in `src/alpha_system/data/fixture_policy.py`:

- data fixtures must be under `tests/fixtures/data/`;
- fixture size threshold is `64 KiB`;
- fixture text must document synthetic and deterministic correctness-only use;
- generated outputs are rejected under committed source/test/docs/config/
  handoff/review/metadata/artifact/run paths;
- build-bars outputs must resolve under a local-only `data` directory;
- data CLI registry writes must target temp/local SQLite paths outside the repo.

Existing P06 fixtures were reused. No new fixture data files were added.

## Files Changed

Commit-eligible files changed:

```text
configs/data/build_bars_example.yaml
configs/data/validation_example.yaml
docs/DATA_VALIDATION_CLI.md
docs/FIXTURE_POLICY.md
handoffs/ASV1-P08.md
src/alpha_system/cli/data.py
src/alpha_system/cli/main.py
src/alpha_system/data/cli_validation.py
src/alpha_system/data/fixture_policy.py
tests/integration/test_build_bars_fixture_command.py
tests/integration/test_data_artifact_policy.py
tests/integration/test_data_cli_registry_tempdb.py
tests/integration/test_data_validate_command.py
tests/no_lookahead/test_data_cli_available_ts.py
tests/unit/test_data_cli_help.py
tests/unit/test_fixture_policy.py
```

Files explicitly staged:

```text
configs/data/build_bars_example.yaml
configs/data/validation_example.yaml
docs/DATA_VALIDATION_CLI.md
docs/FIXTURE_POLICY.md
handoffs/ASV1-P08.md
src/alpha_system/cli/data.py
src/alpha_system/cli/main.py
src/alpha_system/data/cli_validation.py
src/alpha_system/data/fixture_policy.py
tests/integration/test_build_bars_fixture_command.py
tests/integration/test_data_artifact_policy.py
tests/integration/test_data_cli_registry_tempdb.py
tests/integration/test_data_validate_command.py
tests/no_lookahead/test_data_cli_available_ts.py
tests/unit/test_data_cli_help.py
tests/unit/test_fixture_policy.py
```

No `runs/**` path is commit-eligible or staged.

## Validation Results

Commands run by Codex:

```text
test -f runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/STOP
PASS - exit 1; no STOP file was active.

python -m pytest tests/unit/test_data_cli_help.py tests/unit/test_fixture_policy.py tests/integration/test_data_validate_command.py tests/integration/test_build_bars_fixture_command.py tests/integration/test_data_cli_registry_tempdb.py tests/integration/test_data_artifact_policy.py tests/no_lookahead/test_data_cli_available_ts.py
PASS - 15 passed.

python -m pytest tests/unit tests/integration tests/no_lookahead
PASS - 107 passed.

python -m alpha_system.cli data validate --help
FAIL - exit 1; this checkout is not installed and the command was run without
PYTHONPATH, so Python could not import `alpha_system`.

python -m alpha_system.cli data build-bars --help
FAIL - exit 1; this checkout is not installed and the command was run without
PYTHONPATH, so Python could not import `alpha_system`.

PYTHONPATH=src python -m alpha_system.cli data validate --help
PASS - exit 0.

PYTHONPATH=src python -m alpha_system.cli data build-bars --help
PASS - exit 0.

alpha data validate --help
UNAVAILABLE - exit 127; console script is not installed in this shell.

alpha data build-bars --help
UNAVAILABLE - exit 127; console script is not installed in this shell.

git status --short
PASS - showed only ASV1-P08 allowed-path source/docs/config/tests/handoff changes.

find data -type f ! -name README.md ! -name .gitkeep -print
PASS - returned empty.

find metadata -type f ! -name README.md ! -name .gitkeep -print
PASS - returned empty.

find artifacts -type f -size +1M -print 2>/dev/null || true
PASS - returned empty.

find . -path ./tests/fixtures/* -prune -o -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' \) -print
PASS - returned empty.

find . -type f \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.db-journal' -o -name '*.wal' \) -print
PASS - returned empty.

git ls-files runs
PASS - returned empty.

python -m ruff check src tests || true
UNAVAILABLE - `/usr/bin/python: No module named ruff`.

python -m mypy src || true
UNAVAILABLE - `/usr/bin/python: No module named mypy`.

python -m compileall src
PASS - exit 0.

git diff --check
PASS - returned empty.

git diff --cached --name-only
PASS - returned empty before staging.

git add configs/data/build_bars_example.yaml configs/data/validation_example.yaml docs/DATA_VALIDATION_CLI.md docs/FIXTURE_POLICY.md handoffs/ASV1-P08.md src/alpha_system/cli/data.py src/alpha_system/cli/main.py src/alpha_system/data/cli_validation.py src/alpha_system/data/fixture_policy.py tests/integration/test_build_bars_fixture_command.py tests/integration/test_data_artifact_policy.py tests/integration/test_data_cli_registry_tempdb.py tests/integration/test_data_validate_command.py tests/no_lookahead/test_data_cli_available_ts.py tests/unit/test_data_cli_help.py tests/unit/test_fixture_policy.py
PASS - explicit allowed-path staging succeeded.

git diff --cached --name-only
PASS - returned exactly the staged files listed above.

git diff --cached --name-only | rg '^runs/'
PASS - returned empty.

git diff --cached --name-only | rg '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.db-journal$|\.wal$|\.log$|__pycache__|\.pyc$|\.pkl$|\.pickle$|\.joblib$|\.onnx$|\.npy$|\.npz$)'
PASS - returned empty.

git diff --cached --check
PASS - returned empty.
```

Local `__pycache__` directories generated by test/compile runs were removed.

## Artifact Policy Confirmation

- No generated data was committed under `data/`.
- No generated data was left under repo `data/`, `metadata/`, or `artifacts/`.
- No local SQLite/DB/journal/WAL artifact was committed or staged.
- No generated Parquet, Arrow, or Feather artifact was committed or staged.
- No heavy artifacts, logs, caches, model artifacts, raw data, canonical data,
  factors, or labels were committed or staged.
- `git ls-files runs` returned empty.
- No `runs/**` artifact was staged or committed.
- No broker, paper trading, live trading, order-routing, or production
  execution scope was introduced.
- No alpha, profitability, robustness, tradability, or production-readiness
  claim was introduced.

## Relevant Risk Status

- R-001 Lookahead leakage: mitigated for this phase by CLI no-lookahead latency
  enforcement and `tests/no_lookahead/test_data_cli_available_ts.py`.
- R-002 `event_ts` / `available_ts` ambiguity: mitigated by delegating to P06
  timestamp validation and exposing latency config in the CLI.
- R-011 Data quality issues: mitigated by P06 validation delegation, P07
  session/quality delegation, CLI summaries, and integration tests.
- R-024 Real market fixture mistaken as synthetic: mitigated by fixture policy
  size/marker/path enforcement and docs.
- R-037 CLI writes to local-only paths during tests: mitigated by temp-dir CLI
  tests and clean repo artifact audits.
- R-039 Generated Parquet committed: mitigated by local-only output policy and
  clean Parquet/Arrow/Feather audits.
- R-012/R-013/R-038: mitigated by clean raw/heavy/SQLite artifact audits and no
  generated artifact staging.

## Known Limitations

- The local shell has not installed the package, so exact
  `python -m alpha_system.cli ...` commands without `PYTHONPATH=src` fail with
  `ModuleNotFoundError`, and the `alpha` console script is unavailable. The
  registered command surface passes with `PYTHONPATH=src` and in pytest, which
  configures `pythonpath = ["src"]`.
- The host lacks optional `polars`/Parquet dependencies. `.parquet` output is
  wired through the existing P06 writer and will fail closed when that
  dependency is absent. The deterministic fixture integration test uses a
  local-only `.csv` output path.
- The CLI supports tiny CSV fixture-scale inputs in this phase. It does not add
  vendor connectors, cloud ingestion, or large dataset processing.

## Review Focus

Reviewer should focus on:

- `alpha data` argument/help stability and exit-code semantics;
- no-lookahead enforcement through the CLI path;
- whether the `.csv` dependency-free output path for fixture tests is acceptable
  alongside Polars-backed `.parquet` output;
- fixture policy enforcement and documentation;
- artifact-policy behavior for generated outputs and temp registry paths;
- reuse of ASV1-P06/P07 primitives without validation/session reimplementation;
- absence of broker/live/paper/order-routing scope and unsupported
  alpha/tradability claims.

## Next Recommended State

Ralph should run/record validation, validate this handoff, route the required
fresh Claude Opus review, parse the verdict, run semantic done-check, and
continue Workflow 2 gating.
