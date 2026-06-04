# DATA-P08 Handoff - Pacing, Chunking, Retry, And Resume Ledger

## Scope Executed

Implemented DATA-P08 local-only data-foundation records under
`src/alpha_system/data/foundation/requests.py`:

- `RequestPacingPolicy`
- `HistoricalChunkRecord`
- `HistoricalPullLedger`
- `ProviderErrorRecord`

All four are frozen records with fail-closed validation and mapping
round-trips. The package namespace in
`src/alpha_system/data/foundation/__init__.py` now exports the records,
statuses, and guard helpers.

## Pacing, Chunk, Retry, And Resume Design

`RequestPacingPolicy` carries the required pacing fields:
`pacing_policy_id`, `min_seconds_between_identical_requests`,
`max_requests_per_window`, `window_seconds`, `bid_ask_counts_double`,
`backoff_policy`, and `source`. Missing policy blocks provider-pull preflight
through `require_pacing_policy_for_provider_pull()` and
`forbid_naive_request_loop()`. `bid_ask_counts_double` must be true, so
`BID_ASK` has accounting weight `2` while `TRADES` has weight `1`.

The conservative default config lives at
`configs/data/request_pacing_policy_to_be_verified.json`. Its source is marked
`to_be_verified`, with the verification method recorded as checking current
IBKR historical-data pacing documentation before any authorized DATA-P22/DATA-P23
pull or recording an authorized local smoke-run result. These values are not
presented as current provider truth.

`HistoricalChunkRecord` carries the required chunk lifecycle fields:
`chunk_id`, `request_spec_id`, `symbol_root`, `contract_ref`, `start_ts`,
`end_ts`, `status`, `attempt_count`, `provider_request_id`, `raw_object_ref`,
`row_count`, `error_ref`, and `retrieved_at`. Statuses are
`NOT_STARTED`, `IN_PROGRESS`, `COMPLETE`, `INCOMPLETE`, `FAILED`, and
`QUARANTINED`; there is no assumed-complete state. Attempted chunks must carry
`provider_request_id`. Complete chunks require immutable content-addressed
`raw_object_ref`, `row_count`, and `retrieved_at`. Incomplete, failed, and
quarantined chunks require `error_ref`.

No raw overwrite is enforced by requiring `raw_object_ref` to use
`sha256:<digest>` or `raw://sha256/<digest>` and by rejecting attempts to
replace an existing raw ref with a different ref during resume.

`HistoricalPullLedger` carries the required pull-audit fields: `pull_id`,
`manifest_id`, `chunk_records`, `started_at`, `finished_at`, `status`,
`resume_token`, `coverage_summary`, and `error_summary`. It detects duplicate
`chunk_id`, duplicate chunk request keys, and duplicate `provider_request_id`
values. It reconciles `coverage_summary.expected_chunk_ids` against
`chunk_records`; missing expected chunks and unexpected chunks fail closed.

`resume_token` is a deterministic `sha256:<digest>` over the pull id, manifest
id, and chunk-record state. `pending_chunk_ids_for_resume()` validates the token
and returns only non-complete chunks; `completed_chunk_ids()` exposes chunks that
resume must not regenerate.

Coverage and error summaries reconcile with chunk state. They record explicit
not-started, in-progress, complete, incomplete, failed, and quarantined counts
and use `quality_status = not_quality_checked`; they do not imply dataset
version readiness or quality acceptance.

## Provider Error Ledger

`ProviderErrorRecord` carries the required provider-error fields: `error_id`,
`provider`, `request_id`, `chunk_id`, `error_code`, `error_message`,
`retryable`, `attempt`, `timestamp`, and `resolution`.

Retryable errors can use `RETRY_BACKOFF_SCHEDULED`, `RETRY_EXHAUSTED`, or
`INCOMPLETE_RESPONSE_RECORDED` and compute retry delay through the linked
`RequestPacingPolicy`. Attempts cannot silently exceed
`backoff_policy.max_attempts`. Non-retryable errors must use
`QUARANTINED_NON_RETRYABLE`, which quarantines the chunk instead of retrying.
The record classifies retryability and does not make an unclassified fatality
claim.

## Documentation And README Snapshot

Added `docs/data_foundation/PACING_AND_RESUME.md` documenting the pacing policy,
chunk lifecycle, retry/backoff behavior, provider-error ledger, duplicate
detection, `resume_token`, no-silent-gaps reconciliation, and no-raw-overwrite
guarantee.

Updated `README.md` with the compact DATA-P08 snapshot: `ALPHA_DATA_FOUNDATION_V1`
is in the `request_and_storage` gate, DATA-P08 is complete, DATA-P09 is next,
the new objects/config/doc are listed, and the unchanged safety boundaries are
recorded without run-local paths, provider-pull claims, quality-pass claims, or
alpha/profitability/tradability claims.

## Validation Results

No required checks were skipped.

| Command | Result |
| --- | --- |
| `test -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP; printf 'STOP_STATUS=%s\n' "$?"` | Passed with output `STOP_STATUS=1`; no active STOP file. |
| `python -m pytest tests/unit/data/test_pacing_resume_ledger.py -q` | Passed: `6 passed in 0.03s`. |
| `python -m pytest tests/unit/data -q` | Passed: `180 passed in 0.14s`. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `python tools/hooks/canary_runner.py` | Passed; output ended with `All Frontier canaries passed.` |
| `test -f docs/data_foundation/PACING_AND_RESUME.md` | Passed with no output. |
| `test -f README.md` | Passed with no output. |
| `git status --short` | Passed; showed only DATA-P08 commit-eligible README/source/config/doc/fixture/test changes before handoff. |
| `git ls-files runs` | Passed with empty output. |
| `find data -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `git diff --check` | Passed with no output. |

Additional local checks:

- `python -m ruff format --check src/alpha_system/data/foundation/requests.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_pacing_resume_ledger.py`
  passed: `3 files already formatted`.
- `python -m ruff check src/alpha_system/data/foundation/requests.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_pacing_resume_ledger.py`
  passed: `All checks passed!`.
- `PYTHONPATH=src python - <<'PY' ... import HistoricalChunkRecord ... PY`
  passed and printed the four DATA-P08 record names.

One optional ad hoc import command was first run without `PYTHONPATH=src` and
failed with `ModuleNotFoundError: No module named 'alpha_system'`. This was not
a required spec check; pytest uses project `pythonpath = ["src"]`. The command
was rerun with `PYTHONPATH=src` and passed as recorded above.

## Explicit Staged File Set

Files staged with explicit paths only and verified by
`git diff --cached --name-only`:

```text
README.md
configs/data/request_pacing_policy_to_be_verified.json
docs/data_foundation/PACING_AND_RESUME.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P08.md
src/alpha_system/data/foundation/__init__.py
src/alpha_system/data/foundation/requests.py
tests/fixtures/data/synthetic_pacing_resume_chunks.json
tests/unit/data/test_pacing_resume_ledger.py
```

No `runs/**` path is included. `git add .` and `git add -A` were not used.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is in the staged set.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.
- No raw data, canonical data, factor data, label data, cache data, provider
  response, account artifact, DB file, SQLite/WAL/journal file, log,
  Parquet/Arrow/Feather file, pickle, NumPy artifact, model artifact, secret,
  credential, or heavy artifact was produced or staged.
- The fixture under `tests/fixtures/data/` is tiny, synthetic, and contains no
  provider response or real market data.
- Explicit staging only was used for the listed commit-eligible paths.

## Scope Boundaries

No external IBKR call, provider pull, real-data pull, raw data lake write path,
broker, order, account, position, paper, live, real-time, production deployment,
alpha search, factor/label research, profitability claim, tradability claim, or
production-readiness claim was introduced.

Codex did not call Claude, run a reviewer, create `review.md`, create
`verdict.json`, create a PR, merge, or mark the phase PASS. Ralph owns review,
verdict parsing, done-checks, PR, CI, merge gate, and final phase outcome.
