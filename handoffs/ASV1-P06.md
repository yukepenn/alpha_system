# ASV1-P06 Handoff

## Phase

- Phase ID: `ASV1-P06`
- Phase name: Canonical 1-Minute Data Layer
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p06-canonical-1-minute-data-layer`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P06` (local-only)

## Scope Completed

Implemented the canonical 1-minute bar data-layer foundation with:

- contract-aligned canonical bar schema fields and normalized type checks,
- local-only path helpers for `data/raw`, `data/canonical`, `data/factors`,
  `data/labels`, and `data/cache`,
- fixture CSV loading and local Parquet helper functions,
- DuckDB SQL helper functions for local CSV/Parquet fixtures,
- Polars lazy fixture helper functions,
- fixture-level bar normalization logic,
- validation primitives for required fields, point-in-time timestamps, OHLC,
  volume, trade count, bid/ask/spread, versions, keys, and duplicates,
- deterministic `source_version` / `data_version` helpers with optional
  temp/local registry recording through the P05 `dataset_versions` table,
- data-layer documentation, example config, tiny synthetic fixture, and tests.

No vendor ingestion, cloud/object storage, large dataset, data CLI completion,
factor computation, label generation, signal logic, strategy logic, backtest
engine behavior, broker/paper/live scope, order routing, production execution,
or unsupported alpha/tradability claim was introduced.

## Data Schema Summary

`src/alpha_system/data/bar_schema.py` defines these required fields in the
same order as `alpha_system.data.contracts.OneMinuteBar`:

```text
instrument_id
session_id
bar_index
bar_start_ts
bar_end_ts
event_ts
available_ts
open
high
low
close
volume
vwap
trade_count
bid
ask
spread
source_version
data_version
quality_flags
```

Normalized records use `datetime` for timestamp fields, `Decimal` for
price/size fields, `int` for `bar_index` and `trade_count`, strings for
identity/version fields, and `tuple[str, ...]` for `quality_flags`.

## Validation Checks Implemented

`src/alpha_system/data/validation.py` checks:

- required field presence,
- instrument/session/bar key presence,
- `data_version` and `source_version` presence,
- normalized field types,
- `bar_start_ts < bar_end_ts`,
- `event_ts` inside the bar interval by default,
- `available_ts >= event_ts`,
- `available_ts >= bar_end_ts + configured latency`,
- `high >= low`,
- `low <= open <= high`,
- `low <= close <= high`,
- nonnegative volume,
- nonnegative `trade_count`,
- nonnegative bid/ask/spread when present,
- `bid <= ask` when both are present,
- spread equals `ask - bid` within configured tolerance,
- duplicate `instrument_id/session_id/bar_index` keys,
- duplicate `instrument_id/session_id/bar_start_ts` keys.

## DuckDB / Polars Fixture Summary

Added `tests/fixtures/data/synthetic_1min_bars.csv`, a three-row local CSV
fixture. `query_csv_with_duckdb` uses an in-memory DuckDB connection and
`read_csv_auto` when DuckDB is installed. `polars_fixture_close_summary` uses
Polars `scan_csv` and lazy aggregation when Polars is installed.

Local environment note: this interpreter does not have `duckdb`, `polars`, or
`pyarrow` installed, and `pyproject.toml` is not an allowed ASV1-P06 path. The
integration tests therefore verify fail-closed dependency errors in this host.
The same tests execute the real DuckDB/Polars fixture paths when those packages
are present.

## Fixtures

Commit-eligible fixture files:

```text
tests/fixtures/data/README.md
tests/fixtures/data/synthetic_1min_bars.csv
```

R-024 declaration: these fixtures are tiny, synthetic, deterministic,
hand-authored correctness fixtures only. They are not real raw market data and
are not evidence for any instrument, venue, market behavior, tradability, or
research result.

Fixture size:

- `synthetic_1min_bars.csv`: 3 rows, one fabricated instrument/session.
- `README.md`: fixture policy note.

## Validation Results

Commands run by Codex:

```text
find runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1 -maxdepth 2 -name STOP -print
PASS - returned empty before validation.

python -m pytest tests/unit/test_bar_schema.py tests/unit/test_data_paths.py tests/unit/test_data_versions.py tests/unit/test_bar_validation_required_fields.py tests/unit/test_bar_validation_ohlc.py tests/unit/test_bar_validation_spread.py tests/unit/test_bar_validation_duplicates.py tests/no_lookahead/test_bar_available_ts.py tests/integration/test_duckdb_query_fixture.py tests/integration/test_polars_lazy_fixture.py tests/integration/test_no_generated_data_committed.py
PASS - 27 passed.

python -m compileall -q src/alpha_system/data tests/unit tests/integration tests/no_lookahead
PASS - exit 0.

python -m pytest tests/unit tests/integration tests/no_lookahead
PASS - 78 passed.

git status --short
PASS - before staging, showed only ASV1-P06 untracked files under allowed paths.

find data -type f ! -name README.md ! -name ".gitkeep" -print
PASS - returned empty.

find . -path "./tests/fixtures/*" -prune -o -type f \( -name "*.parquet" -o -name "*.csv" -o -name "*.jsonl" \) -print
NON-BLOCKING OUTPUT - returned existing local-only Workflow 2 `runs/**` JSONL
files. No data, metadata, artifact, or source path was returned. `runs/**` is
local-only and was not staged.

find . -path "./tests/fixtures/*" -prune -o -path "./runs/*" -prune -o -type f \( -name "*.parquet" -o -name "*.csv" -o -name "*.jsonl" \) -print
PASS - supplemental audit returned empty.

find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
PASS - returned empty.

git ls-files runs
PASS - returned empty.

git diff --check
PASS - returned empty.

python -m ruff check .
UNAVAILABLE - exit 1; /usr/bin/python: No module named ruff.

python -m mypy src
UNAVAILABLE - exit 1; /usr/bin/python: No module named mypy.
```

## Files Changed And Staged

Files for this phase are staged explicitly by path:

```text
configs/data/example_1min.yaml
docs/DATA_LAYER.md
handoffs/ASV1-P06.md
src/alpha_system/data/bar_schema.py
src/alpha_system/data/build_bars.py
src/alpha_system/data/paths.py
src/alpha_system/data/query.py
src/alpha_system/data/storage.py
src/alpha_system/data/validation.py
src/alpha_system/data/versions.py
tests/fixtures/data/README.md
tests/fixtures/data/synthetic_1min_bars.csv
tests/integration/test_duckdb_query_fixture.py
tests/integration/test_no_generated_data_committed.py
tests/integration/test_polars_lazy_fixture.py
tests/no_lookahead/test_bar_available_ts.py
tests/unit/test_bar_schema.py
tests/unit/test_bar_validation_duplicates.py
tests/unit/test_bar_validation_ohlc.py
tests/unit/test_bar_validation_required_fields.py
tests/unit/test_bar_validation_spread.py
tests/unit/test_data_paths.py
tests/unit/test_data_versions.py
```

## Allowed Paths Vs Local-Only Artifacts

Allowed commit-eligible paths are limited to ASV1-P06 source, docs, config,
tests, tiny synthetic fixtures under `tests/fixtures/data/`, and this handoff.
No `runs/**` path is commit-eligible.

`runs/**` remains local-only runtime state. Codex did not create `review.md`,
did not create `verdict.json`, did not call Claude, did not run a reviewer, did
not create a PR, did not merge, and did not mark the phase PASS.

## Artifact Policy Confirmation

- No raw data was committed or staged.
- No generated canonical data under `data/canonical/` was committed or staged.
- No generated factor or label data was committed or staged.
- No local SQLite/DB/journal/WAL file was created under the repo.
- No Parquet, Arrow, or Feather file was created under the repo.
- No generated report, log, cache, model artifact, or heavy artifact was
  staged.
- The only CSV added is the tiny documented synthetic fixture under
  `tests/fixtures/data/`.
- `git ls-files runs` returned empty.
- No broker, paper trading, live trading, order routing, or production
  execution scope was introduced.
- No alpha, profitability, robustness, tradability, or production-readiness
  claim was introduced.

## Explicit Staging Confirmation

Files were staged explicitly by path. `git add .`, `git add -A`, force push,
PR creation, merge, reviewer execution, `review.md`, and `verdict.json` were
not used.

Staged-set audit after explicit staging:

```text
git diff --cached --name-only
PASS - returned exactly the staged files listed above.

git diff --cached --name-only | rg '^runs/'
PASS - returned empty.

git diff --cached --name-only | rg '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.db-journal$|\.wal$|\.log$|__pycache__|\.pyc$|\.pkl$|\.pickle$|\.joblib$|\.onnx$|\.npy$|\.npz$)'
PASS - returned empty.

git diff --cached --check
PASS - returned empty.
```

## Known Limitations

- The local host lacks DuckDB, Polars, and a Parquet engine. Because dependency
  metadata is outside the ASV1-P06 allowed paths, this phase did not add those
  dependencies. The adapters are implemented and fail closed when the packages
  are unavailable.
- No real or generated Parquet fixture was committed. Parquet read/write
  helpers require Polars at runtime and should be exercised in an environment
  with the data dependencies installed.
- The data CLI remains intentionally incomplete and is deferred to ASV1-P08.
- The data layer does not define execution semantics, factor/label logic, or
  backtest behavior.

## Relevant Risks

- R-001/R-002 lookahead and timestamp ambiguity: mitigated with explicit
  `event_ts`, `bar_start_ts`, `bar_end_ts`, `available_ts`, latency validation,
  and no-lookahead tests.
- R-003 session reset bugs: mitigated by preserving `session_id` and
  `bar_index` in schema and duplicate checks.
- R-011 data quality issues: mitigated with required field, OHLC, volume,
  trade count, spread, version, key, and duplicate validation tests.
- R-012/R-013/R-038/R-039 artifact leakage: mitigated with local-only path
  helpers, fixture-only CSV, artifact audits, staged-set audits, and
  `git ls-files runs`.
- R-024 real fixture confusion: mitigated by fixture README, docs, handoff
  declaration, and synthetic naming.
- R-036 trivial fixtures: mitigated with negative validation tests for OHLC,
  duplicates, spread mismatch, availability latency, negative volume, and
  negative trade count.
- R-037 local path contamination: mitigated by temp registry tests and no writes
  to repo data/metadata/artifact payload paths.

## Review Focus

- Verify schema completeness and exact alignment with `OneMinuteBar`.
- Verify no-lookahead semantics, especially `available_ts >= bar_end_ts` plus
  configured latency and distinct timestamp meanings.
- Verify the DuckDB/Polars adapters are acceptable given local dependency
  unavailability and no dependency metadata scope in this phase.
- Verify local-first storage discipline and fixture-only data scope.
- Verify validation negative cases are meaningful and not weakened.
- Verify no factor, label, signal, strategy, backtest, broker, paper, or live
  trading scope was introduced.
- Verify artifact policy and `runs/**` local-only handling.
