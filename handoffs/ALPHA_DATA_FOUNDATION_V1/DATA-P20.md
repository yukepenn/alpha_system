# DATA-P20 Handoff - Optional BID_ASK / Spread Proxy Pilot Plan

## Scope Executed

Implemented the DATA-P20 planning-and-scaffold contract under
`src/alpha_system/data/foundation/bid_ask_pilot.py`.

Added:

- `BidAskPilotPlan`
- `SpreadProxyMetric`
- `compute_spread_proxy_metrics()`
- `configs/data/bid_ask_pilot_plan.json`
- `docs/data_foundation/BID_ASK_PILOT.md`
- `tests/fixtures/data/synthetic_bid_ask_spread_proxy_inputs.json`
- `tests/unit/data/test_bid_ask_pilot.py`

Updated the package namespace exports, README snapshot, data-foundation docs
index, and fixture README.

## Pilot Plan

The pilot is explicitly optional, bounded, and secondary:

- `optional = true`
- `pilot_only = true`
- `research_diagnostics_only = true`
- `secondary_to_primary_trades_panel = true`
- `what_to_show = BID_ASK`
- `merge_into_primary_trades_panel = false`
- `implies_pull_authorization = false`
- `external_provider_call = false`
- `real_data_pull = false`

Default caps:

- symbols: `ES` only
- contracts: 1 synthetic contract reference
- date window: `2025-01-02` through `2025-01-03`
- maximum date-window days: 3
- planned chunks: 2
- maximum chunks: 4
- maximum local storage footprint: 5 MiB
- estimated local storage footprint: 128 KiB

The plan enforces the configured caps and hard pilot ceilings fail-closed. It
does not make BID_ASK part of the DATA-P10 primary `TRADES` panel.

## Pacing, Manifest, Resume, And Quality Linkage

The pilot references the existing DATA-P08 pacing policy id
`rpp_ibkr_historical_conservative_tobeverified_v1`. `BidAskPilotPlan` validates
that the supplied `RequestPacingPolicy` has `bid_ask_counts_double = true` and
that `accounting_weight("BID_ASK") == 2` while `accounting_weight("TRADES") ==
1`.

The pilot reuses the DATA-P08 request and resume contracts:

- `HistoricalRequestSpec`
- `HistoricalRequestManifest`
- `HistoricalPullLedger`
- `ProviderErrorRecord`

`validate_provider_pull_contracts()` validates a BID_ASK manifest, matching
pacing policy, and matching resume ledger, then returns a record with
`provider_pull_authorized = false` and `external_provider_call = false`. It
does not introduce a connector or pull path.

The pilot reuses DATA-P16 quality/coverage contracts through
`require_quality_coverage_contract()`, which requires linked `DataQualityReport`
and `CoverageReport` records and fails closed on missing reports, blocking
reports, or dataset-version mismatches.

## Spread-Proxy Scaffold

`compute_spread_proxy_metrics()` computes deterministic pilot-only diagnostics
from synthetic/declarative BID_ASK observations:

- midpoint: `(bid + ask) / 2`
- spread: `ask - bid`
- spread basis points relative to midpoint

Inputs fail closed when required fields are missing, extra fields are present,
`bid`/`ask` are non-positive or non-finite, `ask < bid`, the timestamp is
outside the pilot window, or the contract/plan id does not match. Output metrics
are marked `pilot_only = true`, `research_diagnostics_only = true`,
`tradable_cost_claim = false`, `liquidity_truth_claim = false`, and
`feeds_canonical_trades_panel = false`.

The scaffold does not assert tradable spread, transaction-cost, slippage,
liquidity, execution, alpha, profitability, or production-readiness truth.

## Validation Results

No requested validation command was skipped.

| Command | Result |
| --- | --- |
| `git status --short` | Passed; final output showed only DATA-P20 commit-eligible changes: `README.md`, `configs/data/bid_ask_pilot_plan.json`, `docs/data_foundation/BID_ASK_PILOT.md`, `docs/data_foundation/README.md`, `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P20.md`, `src/alpha_system/data/foundation/__init__.py`, `src/alpha_system/data/foundation/bid_ask_pilot.py`, `tests/fixtures/data/README.md`, `tests/fixtures/data/synthetic_bid_ask_spread_proxy_inputs.json`, and `tests/unit/data/test_bid_ask_pilot.py`. |
| `python -m pytest tests/unit/data/test_bid_ask_pilot.py -q` | Passed: `6 passed in 0.05s`. |
| `python -m ruff format src/alpha_system/data/foundation/bid_ask_pilot.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_bid_ask_pilot.py` | Passed; output: `1 file reformatted, 2 files left unchanged`. |
| `python -m ruff format --check src/alpha_system/data/foundation/bid_ask_pilot.py tests/unit/data/test_bid_ask_pilot.py src/alpha_system/data/foundation/__init__.py` | Passed: `3 files already formatted`. |
| `python -m ruff check src/alpha_system/data/foundation/bid_ask_pilot.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_bid_ask_pilot.py` | Passed: `All checks passed!`. |
| `PYTHONPATH=src python -c "from alpha_system.data.foundation import BID_ASK_PILOT_PLAN, BidAskPilotPlan, SpreadProxyMetric, compute_spread_proxy_metrics; assert BID_ASK_PILOT_PLAN.what_to_show == 'BID_ASK'"` | Passed with no output. |
| `python -m pytest tests/unit/data -q` | Passed: `321 passed in 0.25s`. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `test -f docs/data_foundation/BID_ASK_PILOT.md` | Passed with no output. |
| `git ls-files runs` | Passed with empty output. |
| `find data -type f ! -name README.md ! -name .gitkeep -print` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name .gitkeep -print` | Passed with empty output. |
| `find . -name '*.parquet' -not -path './tests/fixtures/*' -print` | Passed with empty output. |
| `git diff --check` | Passed with no output. |
| `test ! -f runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/STOP` | Passed with no output; no active STOP file. |
| `test -w .git && echo GIT_DIR_WRITABLE || echo GIT_DIR_NOT_WRITABLE` | Audit output: `GIT_DIR_NOT_WRITABLE`. |
| `test -w .git/index && echo INDEX_WRITABLE || echo INDEX_NOT_WRITABLE` | Audit output: `INDEX_NOT_WRITABLE`. |
| `git diff --cached --name-only` | Passed with empty output. |

## Git Status And Staging

`git diff --cached --name-only` returns the exact staged file set below:

```text
```

The staged set is empty because this execution sandbox exposes `.git` and
`.git/index` as non-writable. No `runs/**` path is staged.

The intended explicit commit-eligible file set for Ralph or a writable-git
executor is:

```text
README.md
configs/data/bid_ask_pilot_plan.json
docs/data_foundation/BID_ASK_PILOT.md
docs/data_foundation/README.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P20.md
src/alpha_system/data/foundation/__init__.py
src/alpha_system/data/foundation/bid_ask_pilot.py
tests/fixtures/data/README.md
tests/fixtures/data/synthetic_bid_ask_spread_proxy_inputs.json
tests/unit/data/test_bid_ask_pilot.py
```

`git add .`, `git add -A`, force push, commit, push, PR creation, merge,
reviewer execution, `review.md`, and `verdict.json` were not used or created.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is staged or intended for staging.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.
- No raw data, canonical data, factor data, label data, cache data, provider
  response, account artifact, local DB, SQLite/WAL/journal file, log,
  Parquet/Arrow/Feather file, pickle, NumPy artifact, model artifact, secret,
  credential, or heavy artifact was produced or staged.
- The new fixture under `tests/fixtures/data/` is tiny, deterministic,
  synthetic, and contains no provider response or real market data.
- The repository `data/` and `metadata/` artifact audits returned empty output
  except for allowed placeholder files.

## Scope Boundary Confirmation

Codex did not call Claude, run a reviewer, create review artifacts, create a
verdict, create a PR, merge, mark the phase PASS, perform any external IBKR
call, pull real data, write raw/canonical/provider data, operate broker/order/
account/paper/live/real-time surfaces, deploy production code, or make alpha,
profitability, tradability, liquidity-truth, cost-truth, execution-truth, or
production-readiness claims.

Ralph remains responsible for validation orchestration, handoff validation,
independent review, verdict parsing, semantic done-check, PR/CI, merge gate,
and final phase outcome.
