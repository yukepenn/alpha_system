# ASV1-P04 Handoff

## Phase

- Phase ID: `ASV1-P04`
- Phase name: Core Contracts and Schema Primitives
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p04-core-contracts-and-schema-primitives`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P04` (local-only)

## Scope Completed

Implemented schema-only contract primitives for instruments, sessions, 1-minute
bars, quote/trade readiness, factor specs and values, labels, signals,
strategies, management, portfolio, backtest reproducibility, experiment
reproducibility, and future L2 design. Added contract documentation and tests
for required fields, exact enum value sets, timestamp/no-lookahead primitives,
strategy boundaries, management/portfolio ownership, and design-only L2 scope.

No persistence, registry, data ingestion, factor computation, label generation,
signal generation, strategy execution, backtest engine, L2 replay, queue model,
passive-fill model, broker adapter, paper trading, live trading, order routing,
or production execution scope was introduced.

## Contract Coverage

| Contract | Required fields covered | Test reference |
| --- | --- | --- |
| `InstrumentMaster` | `instrument_id`, `symbol`, `asset_class`, `exchange`, `currency`, `timezone`, `tick_size`, `lot_size`, `multiplier`, `start_date`, `end_date`, `corporate_action_policy`, `metadata` | `tests/unit/test_contract_fields.py::test_instrument_master_required_fields_present` |
| `TradingSession` | `calendar_id`, `trading_date`, `session_id`, `open_ts`, `close_ts`, `is_holiday`, `is_half_day`, `session_type`, `timezone`, `quality_flags` | `tests/unit/test_contract_fields.py::test_trading_session_required_fields_present` |
| `OneMinuteBar` | `instrument_id`, `session_id`, `bar_index`, `bar_start_ts`, `bar_end_ts`, `event_ts`, `available_ts`, OHLCV, `vwap`, `trade_count`, `bid`, `ask`, `spread`, `source_version`, `data_version`, `quality_flags` | `tests/unit/test_contract_fields.py::test_one_minute_bar_required_fields_present`; `tests/no_lookahead/test_contract_timestamps.py::test_bar_available_ts_is_distinct_and_latency_bounded` |
| `QuoteTradeReadiness` | quote data, trade prints, bid/ask spread, executable-label readiness, cost-modeling readiness, event/availability timestamps, versions, quality flags | `tests/unit/test_contract_fields.py::test_quote_trade_readiness_fields_present` |
| `FactorSpec` | `factor_id`, `name`, `version`, `owner`, `description`, `input_fields`, `parameters`, `frequency`, `warmup_bars`, `session_reset`, `availability_lag`, `factor_type`, `evaluation_type`, `code_hash`, `config_hash`, `status`, `created_at`, `validation_artifact_path` | `tests/unit/test_contract_fields.py::test_factor_spec_required_fields_present` |
| `FactorValue` | factor/version identity, instrument/session/bar identity, `event_ts`, `available_ts`, values, quality flags, data/compute versions | `tests/unit/test_contract_fields.py::test_factor_value_required_fields_present`; `tests/no_lookahead/test_contract_timestamps.py::test_factor_value_uses_available_ts_distinct_from_event_ts` |
| `LabelSchema` | `label_id`, `instrument_id`, `event_ts`, `horizon`, `label_type`, `value`, `path_metadata`, `data_version`, `label_available_ts` | `tests/unit/test_contract_fields.py::test_label_schema_required_fields_present`; `tests/no_lookahead/test_contract_timestamps.py::test_label_available_ts_is_distinct_after_horizon_completion` |
| `SignalRecord` | signal identity, strategy/instrument identity, `event_ts`, `available_ts`, session/bar identity, entry/exit signal, direction, optional confidence/exposure, factor versions, data version, quality flags | `tests/no_lookahead/test_contract_timestamps.py::test_signal_record_keeps_event_and_availability_separate` |
| `StrategySpec` | entry signal, exit signal, direction, optional confidence score, optional desired exposure, required factor dependencies | `tests/unit/test_strategy_boundary_contracts.py` |
| `ManagementSpec` | fixed stop, ATR stop, volatility stop, target R multiple, laddered partial take profit, breakeven stop, trailing stop, time exit, EOD exit, max trades per day, cooldown, scale-in, scale-out, max holding bars, risk per trade, max position percent | `tests/unit/test_management_portfolio_contracts.py::test_management_spec_support_fields_present` |
| `PortfolioSpec` | portfolio target, position sizing, capital allocation, risk limits, multi-symbol constraints, max gross exposure, max net exposure, future sector/asset constraints, future correlation-aware allocation, signal-to-target conversion | `tests/unit/test_management_portfolio_contracts.py::test_portfolio_spec_support_fields_present` |
| `BacktestSpec` | run id, code hash, config hash, data version, factor versions, label versions, engine version, parameters, artifact paths, decision status | `tests/unit/test_contract_fields.py::test_backtest_experiment_reproducibility_fields_present` |
| `ExperimentSpec` | run id, code hash, config hash, data version, factor versions, label versions, engine version, parameters, artifact paths, decision status | `tests/unit/test_contract_fields.py::test_backtest_experiment_reproducibility_fields_present` |
| `BookLevel`, `L2Snapshot`, `L2EventDelta` | book levels, side, price, size, order count, `event_ts`, `receive_ts`, `available_ts`, data version, quality flags | `tests/unit/test_l2_design_contracts.py` |

## Enum Coverage

- `FactorStatus` exact values: `draft`, `candidate`, `validated`, `approved`,
  `deprecated`.
- `LabelType` complete values: `forward_return_1m`, `forward_return_3m`,
  `forward_return_5m`, `forward_return_10m`, `forward_return_30m`,
  `mfe_by_horizon`, `mae_by_horizon`, `target_before_stop`,
  `stop_before_target`, `future_realized_volatility`,
  `future_spread_liquidity`.
- `FactorInputDomain` intentionally excludes labels.
- `DRAFT_FACTOR_LONG_TERM_MATERIALIZATION_DEFAULT` is `False`.

Covered by `tests/unit/test_contract_enums.py`.

## File Mapping

- Shared primitives: `src/alpha_system/core/contracts.py`,
  `src/alpha_system/core/schema.py`, `src/alpha_system/core/time.py`,
  `src/alpha_system/core/enums.py`.
- Data contracts: `src/alpha_system/data/contracts.py`.
- Factor contracts: `src/alpha_system/factors/contracts.py`.
- Label contracts: `src/alpha_system/labels/contracts.py`.
- Signal contracts: `src/alpha_system/signals/contracts.py`.
- Strategy contracts: `src/alpha_system/strategies/contracts.py`.
- Management contracts: `src/alpha_system/management/contracts.py`.
- Portfolio contracts: `src/alpha_system/portfolio/contracts.py`.
- Backtest contract primitives: `src/alpha_system/backtest/contracts.py`.
- Experiment contract primitives: `src/alpha_system/experiments/contracts.py`.
- L2 design-only contracts: `src/alpha_system/l2/contracts.py`.
- Documentation: `docs/CONTRACTS.md`.
- Tests: `tests/unit/test_contract_fields.py`,
  `tests/unit/test_contract_enums.py`,
  `tests/no_lookahead/test_contract_timestamps.py`,
  `tests/unit/test_strategy_boundary_contracts.py`,
  `tests/unit/test_management_portfolio_contracts.py`,
  `tests/unit/test_l2_design_contracts.py`.

## Validation Results

Codex ran the following local checks. Ralph still owns formal checks recording,
handoff validation, review routing, verdict parsing, PR, CI, merge gate, and
done-check.

```text
test -e runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/STOP
PASS - exit 1 from test command, meaning no STOP file was present.

python -m pytest tests/unit tests/no_lookahead
PASS - exit 0; 32 passed.

python -m alpha_system --help
FAIL - exit 1; /usr/bin/python: No module named alpha_system.
Reason: the src-layout package is not installed into the host interpreter,
matching the ASV1-P03 environment limitation. This phase did not alter package
installation or dependencies because they are out of scope.

PYTHONPATH=src python -m alpha_system --help
PASS - exit 0; CLI help printed.

git status --short
PASS - exit 0; showed only ASV1-P04 files under allowed paths before staging.

python -m ruff check .
UNAVAILABLE - exit 1; /usr/bin/python: No module named ruff.
Reason: Ruff is not installed in the host interpreter and this phase did not
add dev dependencies.

python -m mypy src
UNAVAILABLE - exit 1; /usr/bin/python: No module named mypy.
Reason: Mypy is not installed in the host interpreter and this phase did not
add dev dependencies.

find data -type f ! -name README.md ! -name .gitkeep -print
PASS - exit 0; returned empty.

find metadata -type f ! -name README.md ! -name .gitkeep -print
PASS - exit 0; returned empty.

find . -path ./tests/fixtures/* -prune -o -type f -name '*.parquet' -print
PASS - exit 0; returned empty.

find . -type f \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.db-journal' -o -name '*.wal' \) -print
PASS - exit 0; returned empty.

git ls-files runs
PASS - exit 0; returned empty.

git diff --check
PASS - exit 0; returned empty.
```

## Unresolved Schema Decisions

No blocking schema decisions remain for ASV1-P04. Later phases still need to
define persistence formats, registry enforcement, factor input validation,
label alignment implementation, signal generation, backtest execution
semantics, and concrete L2 data handling. Those are intentionally deferred and
were not implemented here.

## Artifact Policy Confirmation

- Commit-eligible artifacts are limited to the ASV1-P04 Allowed Paths.
- `runs/**` remains local-only. Codex did not create `review.md` or
  `verdict.json`, did not call Claude, did not run reviewer, did not create a
  PR, and did not merge.
- `git ls-files runs` returned empty.
- No raw data, generated canonical data, factor values, label values, Parquet,
  Arrow, Feather, SQLite/DB/journal/WAL files, logs, caches, local environment
  files, model binaries, or generated report bundles were staged or committed.
- No broker, paper trading, live trading, order routing, production execution,
  or unsupported alpha/tradability claims were introduced.
- Allowed Paths and local-only `runs/**` artifacts remain separated.

## Staging Confirmation

Files for this phase were staged explicitly by path. `git add .`, `git add -A`,
force push, PR creation, merge, reviewer execution, `review.md`, and
`verdict.json` were not used.

Staged files are limited to:

```text
docs/CONTRACTS.md
handoffs/ASV1-P04.md
src/alpha_system/backtest/contracts.py
src/alpha_system/core/contracts.py
src/alpha_system/core/enums.py
src/alpha_system/core/schema.py
src/alpha_system/core/time.py
src/alpha_system/data/contracts.py
src/alpha_system/experiments/contracts.py
src/alpha_system/factors/contracts.py
src/alpha_system/l2/contracts.py
src/alpha_system/labels/contracts.py
src/alpha_system/management/contracts.py
src/alpha_system/portfolio/contracts.py
src/alpha_system/signals/contracts.py
src/alpha_system/strategies/contracts.py
tests/no_lookahead/test_contract_timestamps.py
tests/unit/test_contract_enums.py
tests/unit/test_contract_fields.py
tests/unit/test_l2_design_contracts.py
tests/unit/test_management_portfolio_contracts.py
tests/unit/test_strategy_boundary_contracts.py
```

Staged-set audit:

```text
git diff --cached --name-only
PASS - exit 0; returned only the staged files listed above.

git diff --cached --name-only | grep '^runs/'
PASS - exit 1; returned empty, so no runs path is staged.

git diff --cached --name-only | grep -E '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.db-journal$|\.wal$|\.log$|__pycache__|\.pyc$|\.pkl$|\.pickle$|\.joblib$|\.onnx$|\.npy$|\.npz$)'
PASS - exit 1; returned empty, so no forbidden artifact path is staged.

git diff --cached --check
PASS - exit 0; returned empty after whitespace cleanup.
```

## Known Limitations And Review Focus

- Review should focus on field completeness, timestamp semantics, strategy
  boundary separation, L2 design-only scope, and whether the added contract
  primitives remain schema-only.
- The exact `python -m alpha_system --help` command is still blocked by the
  host installation state from ASV1-P03. The supplemental `PYTHONPATH=src`
  invocation passes.
- Ruff and mypy are unavailable in the host interpreter.
- Future enforcement logic for label exclusion from factor inputs is deferred;
  this phase expresses the boundary with contract enums and tests.
