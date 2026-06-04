# DATA-P15 Handoff - Canonical 1m Bar Contract

## Scope Executed

Implemented the DATA-P15 canonical silver-layer bar contract in
`src/alpha_system/data/foundation/bars.py`.

`CanonicalBarRecord` is now a frozen, fail-closed value object with exactly the
required fields:

- identity/provenance: `instrument_id`, `contract_id`, `series_id`, `source`,
  `source_request_id`, `data_version`
- timestamps: `bar_start_ts`, `bar_end_ts`, `event_ts`, `available_ts`,
  `ingested_at`
- values: `open`, `high`, `low`, `close`, `volume`
- metadata: `quality_flags`, `session_label`

Validation enforces timezone-aware timestamp presence, a mandatory
`available_ts`, `bar_end_ts > bar_start_ts`, `available_ts >= bar_end_ts`,
positive finite OHLC prices, `low <= open <= high`, `low <= close <= high`,
non-negative finite volume, `source` linkage to a `dsrc_...` profile,
`source_request_id`, explicit `quality_flags`, and a `session_label` drawn from
the DATA-P12 session model. Unsupported extra fields, including `provider_ts`,
are rejected at this canonical layer.

## Timestamp Semantics

Implemented `TimestampSemanticsPolicy` with these required fields:

- `policy_id`
- `event_ts_definition`
- `bar_start_ts_definition`
- `bar_end_ts_definition`
- `available_ts_definition`
- `ingested_at_definition`
- `lookahead_rules`

`TimestampSemanticsPolicy.v1_no_lookahead()` encodes the DATA-P15 policy:
`available_ts` is when the completed bar would have been usable in
research/backtest logic, not the historical API return time; `ingested_at` is
stored separately from `available_ts`; provider timestamps are not
research-ready without canonical timestamp validation; and canonicalization
fails if `available_ts` is missing.

## Tests And Docs

Added `tests/unit/data/test_canonical_bars.py` covering required field shape,
five separate timestamp fields, missing `available_ts`, timestamp ordering,
OHLC and volume validation, `session_label`, explicit `quality_flags`,
unsupported `provider_ts`, and timestamp-policy rules.

Added `tests/no_lookahead/test_canonical_bar_timestamp_contract.py` asserting
the canonical timestamp field set, `available_ts >= bar_end_ts`, and rejection
of bars missing `available_ts`.

Added `docs/data_foundation/CANONICAL_BARS.md` documenting the canonical bar
contract, timestamp semantics, fail-closed rules, and provider-timestamp
boundary.

Updated `README.md` per the snapshot policy: DATA-P15 advances the
`canonicalization_quality_versioning` gate, DATA-P16 is next, the new
`CanonicalBarRecord`, `TimestampSemanticsPolicy`, canonical-bars doc, and
no-lookahead tests are listed, and the existing read-only/local-only/no-claims
safety boundaries remain unchanged.

No new fixture file was needed; tests use tiny synthetic mappings inline.

## Validation Results

No validation command was skipped.

| Command | Result |
| --- | --- |
| `git status --short` | Passed; final output showed `README.md`, `src/alpha_system/data/foundation/__init__.py`, `src/alpha_system/data/foundation/bars.py`, `docs/data_foundation/CANONICAL_BARS.md`, `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P15.md`, `tests/no_lookahead/test_canonical_bar_timestamp_contract.py`, and `tests/unit/data/test_canonical_bars.py`. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `python -m pytest tests/unit/data -q` | Passed: `280 passed in 0.21s`. |
| `python -m pytest tests/no_lookahead -q` | Passed: `61 passed in 0.34s`. |
| `test -f docs/data_foundation/CANONICAL_BARS.md` | Passed with no output. |
| `git ls-files runs` | Passed with empty output. |
| `find data -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `python -m pytest tests/unit/data/test_canonical_bars.py -q` | Additional narrow check passed: `19 passed in 0.04s`. |
| `python -m pytest tests/no_lookahead/test_canonical_bar_timestamp_contract.py -q` | Additional narrow check passed: `3 passed in 0.03s`. |
| `awk 'length($0) > 100 {print FILENAME ":" FNR ":" length($0) ":" $0}' src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_canonical_bars.py tests/no_lookahead/test_canonical_bar_timestamp_contract.py` | Passed with empty output after wrapping two overlong lines. |
| `rg -n "profit|profitable|tradable|tradability|production-ready|production readiness|paper|live|order|broker|account|real-time|realtime|L1|L2|MBO|tick feed" README.md docs/data_foundation/CANONICAL_BARS.md src/alpha_system/data/foundation/bars.py tests/unit/data/test_canonical_bars.py tests/no_lookahead/test_canonical_bar_timestamp_contract.py` | Reviewed output; matches were safety-boundary disclaimers or ordinary words such as `ordering`, with no new forbidden scope. |
| `find . -name "*.sqlite" -o -name "*.db" -o -name "*.wal" -o -name "*.db-journal" -o -name "*.arrow" -o -name "*.feather" -o -name "*.pkl" -o -name "*.npy" -o -name "*.log" \| sed -n '1,200p'` | Passed with empty output. |
| `git diff --check` | Passed with no output. |
| `test -w .git && echo GIT_DIR_WRITABLE || echo GIT_DIR_NOT_WRITABLE; test -w .git/index && echo INDEX_WRITABLE || echo INDEX_NOT_WRITABLE` | Audit output: `GIT_DIR_NOT_WRITABLE` and `INDEX_NOT_WRITABLE`; staging/commit/push are blocked by this sandbox. |
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
docs/data_foundation/CANONICAL_BARS.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P15.md
src/alpha_system/data/foundation/__init__.py
src/alpha_system/data/foundation/bars.py
tests/no_lookahead/test_canonical_bar_timestamp_contract.py
tests/unit/data/test_canonical_bars.py
```

`git add .`, `git add -A`, force push, commit, PR creation, merge, reviewer
execution, `review.md`, and `verdict.json` were not used or created.

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
- No generated fixture was added.

## Scope Boundary Confirmation

Codex did not call Claude, run a reviewer, create review artifacts, create a
verdict, create a PR, merge, mark the phase PASS, perform any external IBKR
call, pull real data, write raw/canonical provider data, operate broker/order/
account/paper/live/real-time surfaces, deploy production code, or make alpha,
profitability, tradability, or production-readiness claims.

Ralph remains responsible for validation orchestration, review, verdict
parsing, semantic done-check, PR/CI, merge gate, and final phase outcome.
