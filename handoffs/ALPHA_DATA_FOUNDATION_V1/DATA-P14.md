# DATA-P14 Handoff - Parser and Parsed Bar Records

## Scope Executed

Implemented the DATA-P14 parsed bronze bar layer in
`src/alpha_system/data/foundation/bars.py`.

`ParsedBarRecord` is now a frozen, fail-closed provider-shaped record with
exactly these fields:

- Required: `source`, `symbol`, `contract_ref`, `provider_ts`, `open`, `high`,
  `low`, `close`, `volume`, `request_id`, `raw_object_id`
- Optional: `wap_if_available`, `bar_count_if_available`

Required fields are validated. Optional WAP and bar-count fields may be absent
or `None`. Numeric OHLC/WAP/volume values are parsed as exact finite
`Decimal`s, with volume/WAP non-negative and bar count a non-negative integer
when present.

## Parser Design

Added `ParsedBarParser` and `parse_raw_bar_records()` for deterministic parsing
from one or more `RawDataObject` refs to `ParsedBarRecord` tuples.

The default parser reads the `RawDataObject.path` validated by the DATA-P09 raw
lake policy, verifies loaded bytes against `RawDataObject.content_hash`, parses
provider-shaped CSV rows, and enforces that the produced parsed-row count equals
`RawDataObject.row_count`. Malformed rows, unreadable payloads, hash mismatches,
extra CSV columns, missing required provider columns, invalid numerics, and row
count mismatches raise `DataFoundationValidationError`; rows are not silently
dropped.

The parser carries `source`, `request_id`, and `raw_object_id` from the raw
object into every parsed bar. The synthetic unit tests use an injectable raw
payload loader to feed tiny repo-tracked fixture bytes without writing fake raw
files into the local data root; the production default remains path-based raw
object reading.

## Provider-Shaped Boundary

Parsed bars remain provider-shaped. `provider_ts` is preserved as provider
timestamp text only. The record rejects canonical timestamp/session fields such
as `event_ts`, `bar_start_ts`, `bar_end_ts`, `available_ts`, `ingested_at`, and
`session_label`.

No canonical timestamp semantics, session labels, contract normalization,
lookahead/availability semantics, quality scoring, deduplication, monotonicity
enforcement, dataset versioning, broker/order/account/paper/live/real-time
surface, or alpha/profitability/tradability claim was introduced.

## Docs, Fixture, And README Snapshot

Added `docs/data_foundation/PARSED_BARS.md` documenting the bronze parsed layer,
the `ParsedBarRecord` field contract, raw-to-parsed provenance, and the explicit
parsed-not-canonical boundary.

Added `tests/fixtures/data/synthetic_ibkr_raw_bars.csv`, a two-row synthetic
provider-shaped CSV fixture, and documented it in `tests/fixtures/data/README.md`.
This fixture is not a provider response and is not canonical market data.

Updated `README.md` to reflect DATA-P14 executor scope complete within
`ALPHA_DATA_FOUNDATION_V1`, next phase `DATA-P15` - Canonical 1m Bar Contract,
the new parser/record/doc, and unchanged safety boundaries.

## Validation Results

No validation command was skipped. Two repo-wide lane gates failed on existing
out-of-scope Frontier/Ruff issues; the DATA-P14 data tests and targeted touched
file checks passed.

| Command | Result |
| --- | --- |
| `python -m pytest tests/unit/data/test_parsed_bars.py -q` | Passed: `4 passed in 0.04s`. |
| `python -m ruff check --fix src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_parsed_bars.py && python -m ruff format src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_parsed_bars.py && python -m pytest tests/unit/data/test_parsed_bars.py -q` | Passed after fixing touched-file import/order and bytes-literal style: `4 passed in 0.04s`. |
| `python -m pytest tests/unit/data -q` | Passed: `261 passed in 0.21s`. |
| `git status --short` | Passed; showed only DATA-P14 allowed-path changes. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python tools/verify.py --smoke` | Passed with no output. |
| `test -f docs/data_foundation/PARSED_BARS.md` | Passed with no output. |
| `git ls-files runs` | Passed with empty output. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python tools/verify.py --lint` | Failed on pre-existing full-repo Ruff backlog outside DATA-P14 scope: `209 files would be reformatted`; `ruff check .` reported `1289 errors` across unrelated existing files. Touched DATA-P14 Python files pass targeted Ruff checks. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python tools/verify.py --typecheck` | Passed: `compileall -q src tests tools`. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python tools/verify.py --test` | Failed in out-of-scope Frontier/GitHub/Ralph tests: `7 failed, 1609 passed in 23.13s`. Failing tests were `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` and six provider-wired `tests/test_ralph_driver.py` cases expecting `PASS`/`STOPPED`/`COMPLETED` but receiving `PUSH_BLOCKED`. DATA-P14 data tests passed within this run. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP && python tools/hooks/canary_runner.py` | Passed; output ended with `All Frontier canaries passed.` |
| `find data -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `python -m ruff format --check src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_parsed_bars.py && python -m ruff check src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_parsed_bars.py && git diff --check` | Passed: touched Python files were formatted, targeted Ruff passed, and `git diff --check` had no output. |
| `test -w .git && echo GIT_DIR_WRITABLE || echo GIT_DIR_NOT_WRITABLE; test -w .git/index && echo INDEX_WRITABLE || echo INDEX_NOT_WRITABLE` | Passed audit command; output was `GIT_DIR_NOT_WRITABLE` and `INDEX_NOT_WRITABLE`, so staging/commit/push is blocked by sandbox permissions. |
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
docs/data_foundation/PARSED_BARS.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P14.md
src/alpha_system/data/foundation/__init__.py
src/alpha_system/data/foundation/bars.py
tests/fixtures/data/README.md
tests/fixtures/data/synthetic_ibkr_raw_bars.csv
tests/unit/data/test_parsed_bars.py
```

`git add .`, `git add -A`, force push, commit, PR creation, merge, reviewer
execution, `review.md`, and `verdict.json` were not used or created.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is staged or intended for staging.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.
- No raw data, provider response, canonical data, factor data, label data, cache
  data, local DB, SQLite/WAL/journal file, log, Parquet/Arrow/Feather file,
  pickle, NumPy artifact, model artifact, secret, credential, account artifact,
  or heavy artifact was produced or staged.
- The repository `data/` and `metadata/` audits returned empty output except for
  allowed placeholder files.
- The synthetic CSV fixture is tiny, deterministic, documented under
  `tests/fixtures/data/`, and is not real market data.

## Scope Boundary Confirmation

Codex did not call Claude, run a reviewer, create review artifacts, create a
verdict, create a PR, merge, mark the phase PASS, perform any external IBKR
call, pull real data, write raw/canonical provider data, operate broker/order/
account/paper/live/real-time surfaces, deploy production code, or make alpha,
profitability, tradability, or production-readiness claims.

Ralph remains responsible for validation orchestration, review, verdict parsing,
semantic done-check, PR/CI, merge gate, and final phase outcome.
