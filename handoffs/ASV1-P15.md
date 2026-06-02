# ASV1-P15 Handoff — Reference 1-Minute Backtest Truth

## Summary

Implemented the Tier 1 reference 1-minute bar backtest engine as the canonical
PnL truth for this campaign. The engine consumes canonical bars and ASV1-P14
`SignalRecord` streams, enforces data and signal availability, applies
next-eligible-bar conservative execution, performs deterministic accounting,
emits structured trades/equity, writes local-only artifacts when requested, and
records `backtest_runs` rows in the existing SQLite registry schema.

No fast path, parity module, broker adapter, paper/live adapter, order router,
production execution lifecycle, strategy promotion, or alpha/tradability claim
was introduced.

## Backtest Truth Policy

`docs/BACKTEST_TRUTH_POLICY.md` documents the single-PnL-truth rule: the
reference engine is authoritative for 1-minute strategy PnL semantics. Future
fast paths are acceleration only and must defer to the reference engine after
parity; they may not define a second accounting or fill truth.

## No-Lookahead Semantics

Implemented and tested:

- bars are usable only when `available_ts >= bar_end_ts + data_latency_seconds`;
- signals must reference an origin bar and must have
  `signal.available_ts >= origin_bar.available_ts`;
- signal execution never occurs inside the signal's own bar by default;
- if data latency makes the next bar open too early, the engine skips to the
  first later bar whose `bar_start_ts` is not before signal availability.

## Conservative Fill Semantics

Default execution is `next_bar_conservative`. Long entries use ask/open, long
exits use bid/open or bid/close for EOD, short entries use bid/open, and short
exits use ask/open or ask/close for EOD. Same-bar stop/target ambiguity resolves
adverse-first; if both stop and target are reachable from OHLC in the same bar,
the stop is selected. Optional EOD flat exits close remaining session positions.

## Schemas

Trade journal rows include run, strategy, instrument/session, entry/exit signal
and order ids, bar indexes, timestamps, prices, gross PnL, costs, net PnL,
exit reason, data version, factor versions, and quality flags.

Equity rows include run id, timestamps, instrument/session, bar index, cash,
realized PnL, unrealized PnL, total equity, and open position count. Equity is
deterministic for fixed inputs and run id.

## Registry Integration

Backtest runs use the existing `backtest_runs` table and
`alpha_system.experiments.registry.RunRecord`. No migration was added. Tests
write only to pytest temp SQLite paths and verify reproducibility fields:
run id, engine version, data version, factor versions, parameters, artifact
paths, and decision status.

## Files Changed

Source:

- `src/alpha_system/backtest/reference.py`
- `src/alpha_system/backtest/orders.py`
- `src/alpha_system/backtest/fills.py`
- `src/alpha_system/backtest/accounting.py`
- `src/alpha_system/backtest/trades.py`
- `src/alpha_system/backtest/equity.py`
- `src/alpha_system/backtest/results.py`
- `src/alpha_system/backtest/engine_config.py`
- `src/alpha_system/cli/backtest.py`
- `src/alpha_system/cli/main.py` — additional curated path; minimal
  registration only for `alpha backtest`.

Docs/config/tests:

- `docs/REFERENCE_BACKTEST.md`
- `docs/BACKTEST_TRUTH_POLICY.md`
- `configs/execution/reference_1min.yaml`
- `tests/fixtures/backtest_reference.py`
- `tests/unit/test_reference_next_bar_entry.py`
- `tests/unit/test_reference_next_bar_exit.py`
- `tests/no_lookahead/test_no_same_bar_signal_execution.py`
- `tests/unit/test_same_bar_stop_target_conservative.py`
- `tests/unit/test_reference_accounting.py`
- `tests/unit/test_trade_journal_schema.py`
- `tests/unit/test_equity_curve_schema.py`
- `tests/unit/test_eod_flat_behavior.py`
- `tests/no_lookahead/test_backtest_data_latency.py`
- `tests/no_lookahead/test_backtest_signal_availability.py`
- `tests/integration/test_reference_backtest_fixture.py`
- `tests/integration/test_backtest_registry_tempdb.py`
- `tests/integration/test_backtest_cli_help.py`
- `tests/unit/test_backtest_artifact_policy.py`
- `handoffs/ASV1-P15.md`

## Validation

Passed:

- `python -m pytest tests/unit tests/integration tests/no_lookahead` — PASS,
  351 passed.
- `python -m pytest tests/unit/test_reference_next_bar_entry.py tests/unit/test_reference_next_bar_exit.py tests/no_lookahead/test_no_same_bar_signal_execution.py`
  — PASS, 3 passed.
- `python -m pytest tests/unit/test_same_bar_stop_target_conservative.py tests/unit/test_reference_accounting.py tests/unit/test_trade_journal_schema.py tests/unit/test_equity_curve_schema.py`
  — PASS, 5 passed.
- `PYTHONPATH=src python -m alpha_system.cli backtest run --help` — PASS.
- `python -m compileall src` — PASS.
- `find artifacts/execution_validations -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true`
  — PASS, no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print`
  — PASS, no output.
- `find . -path "./tests/fixtures/*" -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print`
  — PASS, no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print`
  — PASS, no output.
- `git ls-files runs` — PASS, no output.

Failed or unavailable, recorded:

- `python -m alpha_system.cli backtest run --help` — FAIL in this shell:
  `ModuleNotFoundError: No module named 'alpha_system'`. The package is not
  installed and the shell has no `PYTHONPATH`; the same command with
  `PYTHONPATH=src` passed.
- `alpha backtest run --help` — unavailable: `alpha: command not found`.
- `python -m ruff check src tests || true` — ruff unavailable:
  `No module named ruff`; command exited 0 due `|| true`.
- `python -m mypy src || true` — mypy unavailable:
  `No module named mypy`; command exited 0 due `|| true`.

## Artifact Policy Confirmation

Full backtest trade/equity/summary/manifest outputs default to
`/tmp/alpha_system/backtests` and tests write to `tmp_path`. Repository output
paths for full trade/equity artifacts are rejected. The only fixture helper
added under `tests/fixtures/**` is tiny, synthetic, deterministic correctness
support and is not market evidence.

No generated backtest outputs, SQLite/DB/WAL files, Parquet/Arrow/Feather files,
raw/canonical/factor/label data, logs, caches, heavy artifacts, or `runs/**`
paths were staged or committed. `git ls-files runs` returned empty.

## Staging Confirmation

No `git add .`, no `git add -A`, and no force push were used. Curated files were
staged explicitly by path only. The staged set must contain no `runs/**` paths
and no forbidden generated artifacts.

## Known Limitations

- Full cost model hardening is deferred to ASV1-P16; this phase provides a
  required non-zero fixed-bps cost hook in the non-test config.
- Fast-path parity is deferred to ASV1-P19.
- Management and portfolio are represented only as baseline run-context
  placeholders; full modules remain out of scope for ASV1-P17/ASV1-P18.
- The exact module CLI command needs either an installed package or
  `PYTHONPATH=src` in this environment.

## Risk Notes

- R-001/R-002: no-lookahead and availability checks are enforced and tested.
- R-004: same-bar stop/target ambiguity resolves adverse-first and is tested.
- R-009: docs and implementation identify the reference engine as the sole PnL
  truth.
- R-033: non-test config has a non-zero fixed-bps cost hook.
- R-022: no broker/live/paper/order-router scope was added.
- R-013/R-038/R-039: artifact audits found no heavy artifacts, DBs, or
  Parquet/Arrow/Feather files.
- R-040: docs scope this as Tier 1 1-minute bar truth only, not event-driven or
  L2 replay.

## Review Focus

Review should focus on timestamp semantics, next-eligible-bar selection under
data latency, conservative stop/target ordering, single-PnL-truth policy,
registry field use, artifact policy, the additional CLI registration path, and
ensuring no broker/paper/live or fast-path truth creep was introduced.
