# DATA-P16 Handoff - Data Quality Checks and Coverage Reports

## Scope Executed

Implemented DATA-P16 in `src/alpha_system/data/foundation/datasets.py`.

`DataQualityReport` is now a frozen, fail-closed aggregate quality audit with
exactly the campaign-required fields:

- `quality_report_id`
- `dataset_version_id`
- `gap_summary`
- `duplicate_summary`
- `non_monotonic_summary`
- `ohlc_errors`
- `zero_negative_price_errors`
- `zero_volume_anomalies`
- `dst_anomalies`
- `session_coverage`
- `roll_discontinuities`
- `provider_error_summary`
- `status`

`CoverageReport` is now a frozen, fail-closed aggregate coverage report with
exactly the campaign-required fields:

- `coverage_report_id`
- `dataset_version_id`
- `symbol_coverage`
- `contract_coverage`
- `session_coverage`
- `partition_coverage`
- `missing_intervals`
- `incomplete_chunks`

Both remain importable through `alpha_system.data.foundation`.

## Quality Behavior

`DataQualityReport.from_canonical_bars(...)` consumes DATA-P15
`CanonicalBarRecord` instances or strict canonical-shaped mappings read-only.
It computes aggregate findings for gaps, duplicates, non-monotonic timestamps,
OHLC validity, zero/negative prices, zero-volume anomalies, DST/timestamp
anomalies, session coverage, roll discontinuities, and provider errors.

Construction and `from_mapping(...)` are fail-closed: missing fields, extra
fields, malformed summaries, hidden raw/full canonical bar rows, and a
top-level `status` that does not reconcile with finding summaries raise
`DataFoundationValidationError`.

Status semantics:

- `PASSING`: no warning or blocking finding in the scoped input.
- `WARNING`: non-blocking anomaly present; currently zero-volume anomalies.
- `BLOCKING`: versioning must be blocked.

Blocking findings include silent gaps, duplicate timestamps, non-monotonic
timestamps, OHLC errors, zero/negative prices, DST/timestamp anomalies, missing
expected sessions, undocumented roll transitions, and provider errors.

## Coverage Behavior

`CoverageReport.from_canonical_bars(...)` computes aggregate coverage by symbol,
contract, session, and partition from explicit expected intervals. Missing
intervals and incomplete chunks are aggregate summaries, not raw bar dumps.

Coverage status is derived via `coverage_status` and `blocks_versioning`; it is
not an extra stored report field. Missing coverage and incomplete chunks produce
`BLOCKING`. Undocumented missing coverage fails closed: partition counts must
match `missing_intervals` and `incomplete_chunks`, and summaries with missing
counts cannot pass with an empty missing-interval list.

Coverage alone is not quality. `CoverageReport.require_linked_quality_report`
rejects `None`, mismatched `dataset_version_id`, blocking coverage, and blocking
quality reports. Only an explicit non-blocking `DataQualityReport` for the same
dataset version can satisfy the linkage contract for later DATA-P17 use.

## Aggregate Summary Bound

Reports store counts, statuses, grouped counts, and capped sample intervals or
identifiers. They reject embedded raw/full canonical bar rows and cap sample
detail at 25 entries. No full report containing raw market data was committed.

## Synthetic Fixtures

Added `tests/fixtures/data/synthetic_quality_coverage_inputs.json`, a tiny
hand-authored fixture with three synthetic canonical-shaped bar mappings and one
coverage expectation. It is not real market data and is not a committed full
quality or coverage report. Tests mutate those synthetic mappings in memory to
exercise each defect class.

No curated synthetic report summary artifact was emitted.

## Tests And Docs

Added:

- `tests/unit/data/test_data_quality_report.py`
- `tests/unit/data/test_coverage_report.py`
- `tests/fixtures/data/synthetic_quality_coverage_inputs.json`
- `docs/data_foundation/DATA_QUALITY.md`
- `docs/data_foundation/COVERAGE_REPORT.md`

Updated:

- `README.md`
- `tests/fixtures/data/README.md`

The README snapshot now states that the
`canonicalization_quality_versioning` gate has progressed through DATA-P16,
names the active phase as DATA-P16 and next phase as DATA-P17, lists the new
quality/coverage contracts and docs, and preserves the existing local-only,
read-only historical, no broker/order/account/paper/live, real-data-local-only,
and no alpha/profitability/tradability-claim boundaries.

## Validation Results

No requested validation command was skipped. One requested command failed in
this shell due to package path setup, and the diagnostic import with
`PYTHONPATH=src` passed.

| Command | Result |
| --- | --- |
| `git status --short` | Passed; final output showed only DATA-P16 allowed-path changes: `README.md`, `src/alpha_system/data/foundation/datasets.py`, `tests/fixtures/data/README.md`, new DATA-P16 docs, `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P16.md`, new DATA-P16 fixture, and new DATA-P16 tests. |
| `python -c "from alpha_system.data.foundation import DataQualityReport, CoverageReport"` | Failed in this shell with `ModuleNotFoundError: No module named 'alpha_system'`; this bare command does not include `src` on `sys.path` and the package is not installed editable in the execution environment. |
| `PYTHONPATH=src python -c "from alpha_system.data.foundation import DataQualityReport, CoverageReport"` | Additional diagnostic passed with no output. |
| `python -m pytest tests/unit/data/test_data_quality_report.py tests/unit/data/test_coverage_report.py -q` | Passed: `16 passed in 0.04s`. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `python -m pytest tests/unit/data -q` | Passed: `296 passed in 0.21s`. |
| `test -f docs/data_foundation/DATA_QUALITY.md` | Passed with no output. |
| `test -f docs/data_foundation/COVERAGE_REPORT.md` | Passed with no output. |
| `test -f README.md` | Passed with no output. |
| `git ls-files runs` | Passed with empty output. |
| `find data -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `python -m py_compile src/alpha_system/data/foundation/datasets.py` | Additional syntax check passed with no output. |
| `git diff --check` | Additional whitespace check passed with no output. |
| `test -w .git && echo GIT_DIR_WRITABLE || echo GIT_DIR_NOT_WRITABLE` | Audit output: `GIT_DIR_NOT_WRITABLE`. |
| `test -w .git/index && echo INDEX_WRITABLE || echo INDEX_NOT_WRITABLE` | Audit output: `INDEX_NOT_WRITABLE`. |
| `git diff --cached --name-only` | Passed with empty output. |

## Exact Staged File Set

`git diff --cached --name-only` returns the exact staged file set below:

```text
```

The staged set is empty because this execution sandbox exposes `.git` and
`.git/index` as non-writable. No `runs/**` path is staged.

The intended explicit commit-eligible file set for Ralph or a writable-git
executor is:

```text
README.md
docs/data_foundation/COVERAGE_REPORT.md
docs/data_foundation/DATA_QUALITY.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P16.md
src/alpha_system/data/foundation/datasets.py
tests/fixtures/data/README.md
tests/fixtures/data/synthetic_quality_coverage_inputs.json
tests/unit/data/test_coverage_report.py
tests/unit/data/test_data_quality_report.py
```

`git add .`, `git add -A`, force push, commit, push, PR creation, merge,
reviewer execution, `review.md`, and `verdict.json` were not used or created.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is staged or intended for staging.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.
- No raw data, provider response, canonical data, factor data, label data,
  cache data, local DB, SQLite/WAL/journal file, log, Parquet/Arrow/Feather
  file, pickle, NumPy artifact, model artifact, secret, credential, account
  artifact, or heavy artifact was produced or staged.
- The repository `data/` and `metadata/` audits returned empty output except
  for allowed placeholder files.
- The committed fixture candidate is tiny, deterministic, and synthetic.

## Scope Boundary Confirmation

Codex did not call Claude, run a reviewer, create review artifacts, create a
verdict, create a PR, merge, mark the phase PASS, perform any external IBKR
call, pull real data, write raw/canonical provider data, operate broker/order/
account/paper/live/real-time surfaces, deploy production code, or make alpha,
profitability, tradability, or production-readiness claims.

Review artifacts are required later for the YELLOW lane, but the executor was
explicitly instructed not to call Claude, run reviewer, create `review.md`, or
create `verdict.json`. Ralph remains responsible for validation orchestration,
review, verdict parsing, semantic done-check, PR/CI, merge gate, and final
phase outcome.
