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

## Task 1B — Backfill machinery + first real DatasetVersion

### Files Added Or Edited

Stage A merged-ready code already exists:

- `src/alpha_system/data/ibkr/backfill_connect.py`
- `src/alpha_system/data/ibkr/manifest_builder.py`
- `src/alpha_system/data/ibkr/materialize.py`
- `configs/data/ibkr_es_nq_rty_instruments.json`
- `configs/data/ibkr_materialize_validation.json`
- `tests/unit/data/test_ibkr_backfill_connect.py`
- `tests/unit/data/test_manifest_builder.py`
- `tests/unit/data/test_materialize.py`
- `src/alpha_system/data/ibkr/backfill.py` small edit allowing
  `interrupt_after_chunks >= planned_count` straight pulls; the default still
  drills.

Stage C finalization edits:

- `src/alpha_system/data/ibkr/materialize.py` comments only.
- `docs/data_foundation/BACKFILL_RUNBOOK.md` Task 1B operator runbook section.
- `handoffs/ADF1_LOCAL_RESEARCH_DATA_BACKFILL.md` this handoff section.

The `backfill.py` straight-pull edit lets `backfill_connect` use the guarded
resume-drill machinery for a no-simulated-interruption pull by setting
`interrupt_after_chunks=manifest.chunk_count`. This preserves the default drill
behavior and does not weaken authorization, CI, raw-write, pacing-policy,
client-id, STOP-file, or read-only boundary guards.

### Independent Review

Independent Opus review verdict: PASS_WITH_WARNINGS, with no blocking issues.
Concise warning map:

- W1: calendar shim is the default path for the shipped session-template config.
- W2: coverage is wall-clock/window-shape sensitive; the operator must pass one
  contiguous full ETH session.
- W3: the template calendar is holiday/half-day blind and intentionally
  over-expects bars until real calendar awareness is wired.
- W4: the full manifest can over-generate lead/tail quarters around the desired
  historical scope.
- W5: `SessionType.OVERNIGHT` vs foundation `ETH` vocabulary differs internally.
- W6: partition metadata persistence has a non-atomic re-run edge if the same
  DatasetVersion is re-registered.

### Orchestrator-Provided Stage B Results

- Stage A merged-ready code already exists: `backfill_connect.py`,
  `manifest_builder.py`, `materialize.py`, 2 configs, 3 test files, + a small
  `backfill.py` edit (allows `interrupt_after_chunks >= planned_count` straight
  pull; default still drills). `CI=true python -m pytest -q` → 1731 passed.
  Independent Opus review: PASS_WITH_WARNINGS, no blocking issues.
- Manifests generated locally: recent_slice (3 chunks, ES/NQ/RTY CONTFUT 2D) and
  full_backfill (108 chunks = 3 symbols × 9 years 2018–2026 × 4 quarterly dated
  FUT contracts H/M/U/Z).
- Live recent-slice pull via `backfill_connect`: 3 raw objects, COMPLETE, 0
  provider errors, straight pull (interruption_simulated=false), gateway
  127.0.0.1:4002 clientId 201.
- First REAL accepted DatasetVersion registered via `materialize`:
  `dsv_ibkr_es_nq_rty_eth_20260603_v1`, symbols ES/NQ/RTY, window
  2026-06-02T22:00:00Z→2026-06-03T21:00:00Z (one complete CME index ETH
  session, America/Chicago 17:00→16:00), canonical_row_count=4140 (1380×3,
  session-complete), coverage_status=PASSING, quality_status=WARNING
  (non-blocking zero-volume overnight minutes), partition=latest_shadow_candidate
  with contamination metadata, registered into a LOCAL-ONLY sqlite registry
  outside the repo. No data/registry artifacts committed.

Registry note: the accepted DatasetVersion was registered into a local-only
SQLite registry outside the repository, matching the operator command shape
`$ALPHA_DATA_ROOT/registry/datasets.sqlite`; the registry path/artifact was NOT
committed.

### Stage C Readiness

The full 2018→present pull is ready for an operator-supervised launch path:

- `full_backfill_manifest.json` shape is 108 chunks for ES/NQ/RTY quarterly dated
  FUT contracts across 2018–2026.
- `docs/data_foundation/BACKFILL_RUNBOOK.md` now documents prerequisites,
  manifest generation, recent-slice materialization, resumable full-backfill
  command shape, and the full-session materialize window rule.
- Full backfill is explicitly multi-day, pacing-limited, and
  operator-supervised.
- Full 2018→present pull not executed (operator-supervised).

Before launching the full job, verify that `run_local_backfill_resume_drill`
enforces real pacing sleeps for large chunk counts. The current runner remains
drill-oriented; a production pacing loop may be a follow-up.

### Validation

- `CI=true python -m pytest -q` — PASS (`1731 passed`) from the orchestrator's
  gated Stage B run.
- Artifact audit clean from the orchestrator's gated Stage B run; no real data,
  registry, raw payload, cache, log, DB, Parquet, Arrow, or Feather artifacts
  were committed.
- `python -m compileall src/alpha_system/data` — PASS.
- `python -m ruff check src/alpha_system/data/ibkr/materialize.py` — PASS.
- `CI=true python -m pytest tests/unit/data/test_materialize.py -q` — PASS
  (`2 passed`).

### Explicit Scope Statements

- No real data/registry committed.
- No order/account/broker scope.
- No alpha/feature/label research.
- No raw market rows included in this handoff.
- No live IBKR call, network call, pip install, or git command was run by Codex
  during Stage C.
- Full 2018→present pull not executed (operator-supervised).
