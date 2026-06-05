# ASV1-P16 Handoff — Cost, Slippage, and Conservative Execution Semantics

## Summary

Implemented scoped cost, slippage, liquidity, conservative fill-model, execution
configuration, and semantics support for the Tier 1 reference backtest layer.
The implementation remains local research simulation only. It adds no broker,
live, paper, order-routing, L2 replay, fast-path, production execution, alpha,
profitability, or tradability scope.

## Cost Model Summary

Added deterministic fill-level cost models in
`src/alpha_system/backtest/costs.py`:

- fixed commission;
- per-unit commission;
- bps cost with optional minimum;
- half-spread and full-spread cost;
- composite cost model;
- explicit fixture-only zero-cost model.

Non-test execution configs reject silent zero cost. The reference runner can
consume `ExecutionConfig.cost_model.cost_for_notional()` through the existing
P15 cost hook without replacing the reference engine PnL truth.

## Slippage Model Summary

Added deterministic slippage models in
`src/alpha_system/backtest/slippage.py`:

- bps slippage;
- spread-sensitive slippage;
- adverse-selection proxy hook;
- composite slippage model;
- explicit fixture-only no-slippage model.

Slippage assumptions are included in `ExecutionConfig.to_dict()`, config hashes,
and reference run manifests for reproducibility.

## Conservative Execution Semantics Summary

Added `src/alpha_system/backtest/conservative_semantics.py` and
`src/alpha_system/backtest/fill_models.py` covering:

- next-bar conservative default;
- no same-bar signal fill by default;
- adverse-first same-bar stop/target resolution;
- spread-aware bid/ask fill side selection;
- explicit missing bid/ask fallback with warning/provenance;
- volume participation cap, rejection, and penalty behavior;
- conservative fill-model resolution over tiny deterministic fixtures.

## Defaults And Zero-Cost Policy

`default_execution_config()` is conservative and non-zero-cost:

- `execution_timing = next_bar_conservative`;
- `same_bar_policy = adverse_first`;
- non-zero bps cost;
- non-zero bps slippage;
- explicit missing bid/ask policy.

Zero cost and no slippage are reachable only through
`fixture_zero_cost_execution_config()` or
`configs/execution/cost_models/fixture_zero_cost.json`, both explicitly marked
fixture-only.

## Reference Integration

The ASV1-P15 reference engine remains the single PnL truth. No replacement
engine, second accounting path, fast path, broker path, paper path, live path,
or order lifecycle was added.

Reference integration is via the existing P15 runtime config interface:

- `ExecutionConfig` exposes the same timing/accounting attributes consumed by
  `run_reference_backtest`;
- `ExecutionConfig.cost_model.cost_for_notional()` is consumed by the existing
  fill cost hook;
- `ExecutionConfig.to_dict()` surfaces cost, slippage, liquidity, missing
  quote policy, and research-only metadata;
- the reference manifest records the execution config and config hash.

Known limitation for review: the generated allowed-path list excluded the P15
`reference.py`, `fills.py`, and `engine_config.py` files. Therefore this phase
does not edit the existing P15 fill-price path directly; the full slippage
price semantics live in `ConservativeFillModel`, while the current reference
runner consumes the configured cost hook and records slippage assumptions in
metadata.

## Files Changed And Explicit Staging Set

Source:

- `src/alpha_system/backtest/costs.py`
- `src/alpha_system/backtest/slippage.py`
- `src/alpha_system/backtest/liquidity.py`
- `src/alpha_system/backtest/fill_models.py`
- `src/alpha_system/backtest/execution_config.py`
- `src/alpha_system/backtest/conservative_semantics.py`

Docs/configs:

- `docs/COST_AND_SLIPPAGE.md`
- `docs/CONSERVATIVE_EXECUTION_SEMANTICS.md`
- `configs/execution/cost_models/default_conservative.json`
- `configs/execution/cost_models/spread_sensitive_conservative.json`
- `configs/execution/cost_models/fixture_zero_cost.json`

Tests:

- `tests/unit/test_fixed_commission.py`
- `tests/unit/test_per_unit_commission.py`
- `tests/unit/test_bps_cost.py`
- `tests/unit/test_half_full_spread_cost.py`
- `tests/unit/test_slippage_bps.py`
- `tests/unit/test_spread_sensitive_slippage.py`
- `tests/unit/test_volume_participation_cap.py`
- `tests/unit/test_liquidity_rejection.py`
- `tests/unit/test_adverse_selection_proxy_hook.py`
- `tests/unit/test_conservative_fill_price.py`
- `tests/unit/test_missing_bid_ask_behavior.py`
- `tests/unit/test_zero_cost_only_explicit_fixture.py`
- `tests/integration/test_reference_backtest_cost_model.py`
- `tests/integration/test_reference_backtest_slippage_model.py`
- `tests/no_lookahead/test_cost_model_no_same_bar_optimism.py`
- `tests/unit/test_execution_artifact_policy.py`

Handoff:

- `handoffs/ASV1-P16.md`

## Validation

Passed:

- `python -m pytest tests/unit tests/integration tests/no_lookahead` — PASS,
  378 passed.
- `python -m pytest tests/unit/test_fixed_commission.py tests/unit/test_per_unit_commission.py tests/unit/test_bps_cost.py tests/unit/test_half_full_spread_cost.py`
  — PASS, 6 passed.
- `python -m pytest tests/unit/test_slippage_bps.py tests/unit/test_spread_sensitive_slippage.py tests/unit/test_volume_participation_cap.py tests/unit/test_conservative_fill_price.py`
  — PASS, 7 passed.
- `python -m compileall src` — PASS.
- `git status --short` — PASS for audit; output showed only new allowed-path
  files before staging.
- `find artifacts/execution_validations -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true`
  — PASS, no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print`
  — PASS, no output.
- `find . -path "./tests/fixtures/*" -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print`
  — PASS, no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print`
  — PASS, no output.
- `git ls-files runs` — PASS, no output.

Non-blocking unavailable tools:

- `python -m ruff check src tests || true` — ruff unavailable:
  `No module named ruff`; command exited 0 due `|| true`.
- `python -m mypy src || true` — mypy unavailable:
  `No module named mypy`; command exited 0 due `|| true`.

Development failure fixed:

- Initial ASV1-P16 narrow pytest run failed because
  `test_reference_backtest_cost_model.py` attempted to use fixture no-slippage
  in a non-fixture config. The test was corrected to keep non-test configs
  non-zero and conservative. Final validation passed.

## Fixture Limitations And Known Limitations

All new tests use tiny synthetic deterministic correctness fixtures only. They
are not market evidence and support no alpha, tradability, profitability, or
production execution claim.

Known limitations:

- no broker-specific commission schedules;
- no live/paper/broker adapter;
- no market-impact model beyond simple local approximations;
- no L2 replay, queue, or passive-fill model;
- no fast-path or parity implementation;
- no new CLI command.

## Risk Notes

- R-033: mitigated by non-zero default config and fixture-only zero-cost tests.
- R-004: mitigated by adverse-first same-bar stop/target tests.
- R-009: mitigated by preserving the P15 reference engine as the only PnL truth.
- R-001/R-002: mitigated by next-bar no-same-bar tests and existing reference
  timing checks.
- R-022: no broker/live/paper/order-routing scope introduced.
- R-014: docs state research simulation only and make no alpha/tradability
  claims.
- R-013/R-038/R-039: artifact, metadata, SQLite/DB/WAL, and columnar-file audits
  produced no output.
- R-037: tests use tempdirs or in-memory fixtures; no repo-local execution
  outputs were generated.

## Artifact Policy Confirmation

No generated execution artifacts, trade logs, equity curves, DBs, SQLite/WAL
files, raw/heavy artifacts, Parquet/Arrow/Feather files, caches, logs, or
`runs/**` paths were staged or committed. `runs/**` remains local-only. No
run-local `handoff.md`, `review.md`, or `verdict.json` was created or staged.

Explicit staging only was used. `git add .`, `git add -A`, force push, PR
creation, merge, reviewer execution, Claude calls, and verdict creation were
not performed.

## Review Focus And Recommended Next State

Recommended next state: Ralph should run its validation recording step and route
fresh Claude Opus review. Review should focus on the allowed-path-constrained
reference integration boundary, conservative default enforcement, zero-cost
fixture policy, spread/slippage metadata reproducibility, no-same-bar optimism,
and artifact policy compliance.
