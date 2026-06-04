# DATA-P21 Handoff - Synthetic IBKR Fixture Tests

## Scope Executed

Implemented DATA-P21 with additive synthetic fixtures, tests, docs, README
snapshot, and handoffs only. No source-code seam was required.

Added `tests/fixtures/data/synthetic_ibkr_e2e_provider_fixture.json`, a tiny
hand-authored IBKR-shaped fixture labeled `synthetic: true` and
`real_provider_response: false`. It includes a fake read-only connection
profile, fake contract-details fields, a fake historical-bar CSV payload,
manifest expectations, raw-object metadata, and canonical timestamp
expectations. It is deterministic and is not derived from an IBKR pull.

Updated `tests/fixtures/data/README.md` to document the new fixture as
synthetic, not a provider response, not raw market data, and not canonical
market data.

## Pipeline Coverage

Added `tests/unit/data/test_synthetic_ibkr_fixture_composition.py`.

The unit tests verify:

- `DataAccessMode.synthetic()` is CI-allowed and forbids external API calls.
- `IBKRReadOnlyApiBoundary` refuses `reqHistoricalData` before a registered
  test handler can run.
- `HistoricalRequestSpec` / `HistoricalRequestManifest` compose through
  `REQUEST_PLANNED` and `REQUEST_AUTHORIZED`.
- `RequestPacingPolicy` accounts for `TRADES` and `BID_ASK` weights.
- `HistoricalChunkRecord` and `HistoricalPullLedger` reconcile completed and
  pending chunks, duplicate request keys, missing expected chunks, and resume
  tokens.
- clientId `101` and `102` remain hard-blocked.
- Missing manifest and missing pacing policy block the simulated pull before
  fixture payload access.
- Missing `available_ts` blocks canonicalization.
- Provider-continuous series cannot be used as dated-contract truth.

Added `tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py`.

The integration test drives this synthetic path:

```text
synthetic fixture
-> ContractDiscoveryRequest / FuturesContractRecord / ContractDetailsSnapshot
-> HistoricalRequestSpec / HistoricalRequestManifest / RequestPacingPolicy
-> RawDataObject with fake payload loader
-> ParsedBarRecord
-> CanonicalBarRecord
-> DataQualityReport / CoverageReport
-> DatasetVersion
-> temp local registry persist / resolve
```

The registry DB is created only under pytest `tmp_path` and is not committed.

## Fail-Closed Negative Cases

The tests assert the composed guards required by DATA-P21:

- clientId `101` and `102` fail closed.
- No manifest blocks a simulated pull before fixture access.
- No pacing policy blocks a simulated pull before fixture access.
- Missing `available_ts` blocks `CanonicalBarRecord`.
- Silent gaps block quality and versioning.
- Missing coverage blocks versioning.
- Duplicate timestamps, non-monotonic timestamps, and OHLC defects become
  blocking quality findings.
- Zero-volume bars become explicit DATA-P16 warning anomalies rather than
  silent acceptance.
- Provider-continuous `CONTFUT`-style provenance is rejected as dated-contract
  truth.

## No External Call Mechanism

No IBKR client library is imported, no socket is opened, and no provider call is
performed.

The unit test registers a handler that raises if reached. In synthetic mode,
`IBKRReadOnlyApiBoundary` rejects `reqHistoricalData` before invoking the
handler; the handler's external-call counter remains zero.

The integration test uses a test-local `SyntheticIBKRFixtureTransport` that
returns bytes from the fixture after manifest and pacing validation. It keeps a
separate external-attempt counter and asserts it remains zero.

## Documentation And README Snapshot

Added `docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md`, documenting the
fixture set, pipeline coverage, no-external-call proof, fail-closed assertions,
and artifact posture.

Updated `docs/data_foundation/README.md` to include the new doc.

Updated `README.md` to record the DATA-P21 executor snapshot and set the next
phase to `DATA-P22` - Small Authorized IBKR Smoke Pull. The README preserves
the unchanged boundaries: IBKR read-only historical only, clientId `101`/`102`
fail-closed, namespace `201-209`, no broker/order/account/paper/live scope,
real data local-only, and no external pull in DATA-P21 or CI.

## Validation Results

No validation command was skipped. One required broad command failed in
pre-existing harness-level tests unrelated to the DATA-P21 data tests.

| Command | Result |
| --- | --- |
| `python -m pytest tests/unit/data/test_synthetic_ibkr_fixture_composition.py -q` | Passed before formatting: `3 passed in 0.04s`. |
| `python -m pytest tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py -q` | Passed before formatting: `2 passed in 0.21s`. |
| `python -m ruff format tests/unit/data/test_synthetic_ibkr_fixture_composition.py tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py` | Passed: `2 files reformatted`. |
| `python -m ruff check tests/unit/data/test_synthetic_ibkr_fixture_composition.py tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py` | Passed after formatting: `All checks passed!`. |
| `python -m ruff format --check tests/unit/data/test_synthetic_ibkr_fixture_composition.py tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py` | Passed after formatting: `2 files already formatted`. |
| `python -m pytest tests/unit/data/test_synthetic_ibkr_fixture_composition.py tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py -q` | Passed after formatting: `5 passed in 0.25s`. |
| `python tools/verify.py --smoke` | Passed with no output, rerun after formatting. |
| `python tools/verify.py --all` | Failed with exit 1 after formatting: `7 failed, 1682 passed in 23.85s`. The failures were `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` where `GitHubResult.dry_run` was `False`, and six `tests/test_ralph_driver.py` mock/provider-wired expectations where state/status was `PUSH_BLOCKED` instead of `STOPPED`, `PASS`, or `COMPLETED`. DATA-P21 data tests passed inside this run. |
| `python -m pytest tests/unit/data -q` | Passed after formatting: `324 passed in 0.26s`. |
| `python -m pytest tests/integration/data -q` | Passed after formatting: `7 passed in 0.90s`. |
| `test -f docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md` | Passed with no output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `git ls-files runs` | Passed with empty output. |
| `find data -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find artifacts -type f -size +1M -print` | Passed with empty output. |
| `git ls-files \| grep -E '\.(sqlite\|sqlite3\|db\|db-journal\|wal\|parquet\|arrow\|feather\|log)$' \| grep -v '^tests/fixtures/' \|\| echo "no committed heavy/db/log artifacts"` | Passed: `no committed heavy/db/log artifacts`. |
| `git grep -nE 'placeOrder\|reqAccount\|reqPositions\|account_summary' -- src/alpha_system/data \|\| echo "no order/account API surface in data module"` | Passed: `no order/account API surface in data module`. |
| `python tools/hooks/canary_runner.py` | Passed; output ended with `All Frontier canaries passed.` |
| `git add README.md docs/data_foundation/README.md docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P21.md handoffs/DATA-P21.md tests/fixtures/data/README.md tests/fixtures/data/synthetic_ibkr_e2e_provider_fixture.json tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py tests/unit/data/test_synthetic_ibkr_fixture_composition.py` | Passed with explicit paths only. |
| `git diff --cached --name-only` | Passed; staged set contains only the DATA-P21 commit-eligible paths listed below and no `runs/**` path. |
| `git diff --check` | Passed with no output. |
| `git status --short` | Passed; output shows only the staged DATA-P21 files listed below. |

## Exact Staged File Set

`git diff --cached --name-only` returns the exact staged file set below:

```text
README.md
docs/data_foundation/README.md
docs/data_foundation/SYNTHETIC_FIXTURE_TESTS.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P21.md
handoffs/DATA-P21.md
tests/fixtures/data/README.md
tests/fixtures/data/synthetic_ibkr_e2e_provider_fixture.json
tests/integration/data/test_synthetic_ibkr_fixture_pipeline.py
tests/unit/data/test_synthetic_ibkr_fixture_composition.py
```

No `runs/**` path is staged.

`git add .`, `git add -A`, force push, PR creation, merge, reviewer execution,
`review.md`, and `verdict.json` were not used or created.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` returned only DATA-P21 commit-eligible paths.
- No `runs/**` path is staged.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.
- The new fixture is tiny, deterministic, synthetic, and explicitly marked not
  a real provider response.
- No raw data, canonical data, factor data, label data, cache data, real
  provider response, local DB, SQLite/WAL/journal file, log, Parquet/Arrow/
  Feather file, pickle, NumPy artifact, model artifact, secret, credential,
  account artifact, or heavy artifact was produced or staged.
- The repository `data/`, `metadata/`, and `artifacts/` audits returned clean.
- Quality and coverage report bodies are generated in tests only and remain
  aggregate; no raw bar dump or canonical data artifact is committed.

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
