# ADF1 Local Research Data Backfill Handoff

## Task 1A - Connector + Smoke

### Scope Completed

Implemented a minimal optional IBKR historical-data connector for the existing
read-only data boundary. The connector:

- exposes only `reqHistoricalData` through `IBKRReadOnlyApiBoundary`;
- imports `ib_insync` lazily only when a real client or contract class is
  needed;
- maps `HistoricalRequestSpec` to `ContFuture` for `CONTFUT` and `Future` for
  dated `FUT`;
- converts returned bars to CSV bytes with header
  `symbol,contract_ref,provider_ts,open,high,low,close,volume,wap,barCount`;
- adds no order/account/broker/position/paper/live/trading scope.

Added a thin operator entry point:

```bash
python -m alpha_system.data.ibkr.smoke_connect --batch mini_main --max-chunks 1
```

The entry point reads `IBKRConnectionProfile.from_env(os.environ)`, validates
the existing clientId policy, opens the connector boundary, calls
`run_ibkr_smoke_pull(... execute=True, use_default_manifest=True,
use_default_pacing_policy=True)`, and prints a redacted summary as JSON.

### Files Changed

- `src/alpha_system/data/ibkr/connector.py`
- `src/alpha_system/data/ibkr/smoke_connect.py`
- `tests/unit/data/test_ibkr_connector.py`
- `pyproject.toml`
- `docs/data_foundation/SMOKE_PULL.md`
- `docs/data_foundation/BACKFILL_RUNBOOK.md`
- `handoffs/ADF1_LOCAL_RESEARCH_DATA_BACKFILL.md`

### Live Smoke Command

Install optional dependency:

```bash
pip install -e ".[ibkr]"
```

Required env var names:

```text
ALPHA_DATA_PULL_AUTHORIZED
ALPHA_ALLOW_EXTERNAL_IBKR
ALPHA_IBKR_READ_ONLY_MODE
ALPHA_ALLOW_RAW_LOCAL_WRITE
ALPHA_IBKR_HOST
ALPHA_IBKR_PORT
ALPHA_IBKR_CLIENT_ID
ALPHA_DATA_ROOT
```

Command:

```bash
python -m alpha_system.data.ibkr.smoke_connect --batch mini_main --max-chunks 1
```

LIVE SMOKE RESULT (orchestrator-run, 2026-06-04, gated authorized read-only pull):

- Reachability: REACHABLE at 127.0.0.1:4002 (paper IB Gateway; WSL2 mirrored networking, no host/port switch).
- clientId used: 201 (default data client; 101/102 remain hard-blocked).
- Symbol / window: ES continuous future (CONTFUT), 1 min, TRADES, most recent ~30-minute window.
- Row count: 31 real 1-minute bars (provider_ts span 2026-06-04 10:17:00Z → 10:47:00Z), contiguous, 10 columns matching the canonical parser header.
- Manifest ID: `hrm_ibkr_smoke_mini_main_v1`.
- Pull ledger ID: `hpl_ibkr_smoke_mini_main_20260604T104729Z` (status COMPLETE; provider_errors_logged 0).
- Raw object: written content-addressed under `ALPHA_DATA_ROOT` only (local-only; not committed).
- Environment: `ib_insync` 0.9.86 installed into an isolated target dir (`~/.alpha_ibkr_libs`), system site-packages untouched, no venv; run with `PYTHONPATH=src:<libs>` and the eight authorization/connection env vars (=1 gates).
- Live-path bug found and fixed during this run: IBKR `Error 10339` (endDateTime not allowed for continuous futures); connector now sends `endDateTime=""` for CONTFUT and keeps the explicit end only for dated FUT. A first (pre-fix) run wrote a header-only 0-row raw object that remains under the local data root as harmless audit history.

### Validation Run (final, post-repair)

- `python tools/verify.py --all` - PASS (`1721 passed`; includes full pytest + compileall).
- `python -m ruff check src/alpha_system/data/ibkr/connector.py src/alpha_system/data/ibkr/smoke_connect.py tests/unit/data/test_ibkr_connector.py` - PASS.
- Artifact audit - PASS (`git ls-files runs` empty; no parquet/sqlite/db/log/arrow/feather/raw committed; only code/docs/handoff staged).

### Review And Repair History

Independent Opus review verdict: PASS_WITH_WARNINGS. Findings addressed via scoped Codex repairs:

- W1 (auth ordering): `smoke_connect.main` and `open_ibkr_historical_boundary` now validate the four authorization gates BEFORE any reachability probe or IBKR socket connect, so the connector fails closed before touching the broker.
- W2 (CI detection): replaced hardcoded `ci=False` with `ci=None`, so an accidental CI invocation still blocks via `_runtime_ci_enabled`.
- Nits: removed a dead `Decimal` branch; strengthened the source-guard test against `from ib_insync import`/aliased imports.
- Live-path fix: CONTFUT `endDateTime=""` (see live smoke result above).

### Non-Runs And Deferred Work

- No live IBKR pull was run by Codex.
- No network call was made by Codex.
- No `pip install` was run by Codex.
- No git command was run by Codex.
- DatasetVersion registration is intentionally DEFERRED to Task 1B. The Task 1A
  tiny slice remains quality BLOCKING by design; no quality guard was weakened.
- No raw/canonical/registry/data artifact is intentionally committed.

### Explicit Scope Statements

- No order/account/broker scope added.
- No alpha/feature/label research.
- No live pull run by Codex.
- Raw, canonical, registry, run-local, cache, log, DB, Parquet, Arrow, and
  Feather artifacts are intentionally not committed.

### Risks And Caveats

- The live connector requires local operator authorization, `ib_insync`, and a
  reachable configured IBKR endpoint; this executor did not test those external
  conditions.
- The request pacing policy remains the existing to-be-verified policy and must
  be re-checked during any gated live operation.
- Unit tests use dependency-injected fakes and do not prove provider coverage,
  data completeness, or research readiness.
- The connector smoke-pull unit test injects a tmp-root artifact store so unit
  files stay under pytest `tmp_path`; the existing operator `ALPHA_DATA_ROOT`
  guard remains unchanged and still rejects temporary locations for default
  live manifests.

### Review Request Focus

- Verify the connector never calls forbidden IBKR methods and never imports
  `ib_insync` at module import time.
- Verify CSV output matches the existing raw bar parser aliases.
- Verify the smoke connector uses the existing clientId, access-mode, manifest,
  pacing, reachability, raw-write, and summary guards.

### Branch And Commit Metadata

Not inspected by Codex because the task explicitly forbids all git commands.
The orchestrator owns staging, commits, pushes, and branch metadata.

### Next Recommended Step

Task 1A is complete (connector implemented + gated live smoke proved a real
31-bar ES slice end-to-end). Next is Task 1B: the full, separately
operator-supervised ES/NQ/RTY 2018-01-01 -> present 1-minute TRADES resumable
local backfill, which canonicalizes session-complete data and registers the
first real accepted DatasetVersion (with DataQualityReport + CoverageReport).
Task 1B is intentionally not started in this merge.
