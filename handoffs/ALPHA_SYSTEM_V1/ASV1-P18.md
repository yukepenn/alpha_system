# ASV1-P18 Handoff — Portfolio Target and Sizing Layer

## Summary

Implemented the scoped portfolio target and sizing layer for
`ALPHA_SYSTEM_V1`. The new layer converts strategy-intent signals into
deterministic portfolio targets, supports fixed notional sizing,
risk-per-trade sizing, capital allocation state, max position percent, max
gross exposure, max net exposure, insufficient-capital handling, multi-symbol
constraints, and contract-only future sector/asset and correlation-aware
allocation fields.

No live trading, paper trading, broker account sync, order routing,
production execution adapter, alpha generation, management exit logic, or PnL
truth was introduced.

## PortfolioSpec Field Coverage

`src/alpha_system/portfolio/spec.py` defines the concrete ASV1-P18
`PortfolioSpec` support fields:

- `portfolio_target`
- `position_sizing`
- `capital_allocation`
- `risk_limits`
- `multi_symbol_constraints`
- `max_gross_exposure`
- `max_net_exposure`
- `future_sector_asset_constraints`
- `future_correlation_aware_allocation`
- `signal_to_target_conversion`

The P04 schema-only `src/alpha_system/portfolio/contracts.py` primitive was
left unchanged because it is outside this phase's allowed paths.

## Sizing And Risk Behavior

- Fixed notional sizing returns deterministic target notional, quantity, and
  signed weight.
- Risk-per-trade sizing uses equity, risk fraction, price, and stop distance.
- Max position percent caps individual targets.
- Max gross exposure scales active targets deterministically.
- Max net exposure scales same-direction or imbalanced targets
  deterministically.
- Capital allocation state tracks total equity, available cash, and reserved
  target notional.
- Insufficient capital supports explicit `reject` and `cap` policies.
- Multi-symbol constraints require `instrument_id` identity and support active
  instrument count limits.

## Multi-Symbol Readiness

Portfolio targets and constraints use `instrument_id` as the required identity.
No single-symbol-only core contract was introduced. Tests cover multiple
instrument ids and max active instrument rejection.

## Boundary Separation

- Strategy remains signal intent only.
- Management remains post-entry exit/adjustment logic only.
- Portfolio owns target sizing and exposure constraints only.
- The reference 1-minute backtest engine remains the accounting and PnL truth.

Source-level boundary greps over `src/alpha_system/portfolio` returned no
matches for broker/live/account-sync/paper terms and no matches for execution
accounting terms.

## Reference Integration

`src/alpha_system/portfolio/integration.py` converts ASV1-P14 `SignalRecord`
inputs into `PortfolioTarget` records. The integration test derives a target
quantity from a tiny deterministic portfolio target and passes that quantity to
the existing reference backtest configuration. The reference engine performs
the resulting accounting; portfolio code does not.

## Files Changed And Staged

Source:

- `src/alpha_system/portfolio/spec.py`
- `src/alpha_system/portfolio/sizing.py`
- `src/alpha_system/portfolio/risk.py`
- `src/alpha_system/portfolio/targets.py`
- `src/alpha_system/portfolio/allocation.py`
- `src/alpha_system/portfolio/validation.py`
- `src/alpha_system/portfolio/integration.py`

Docs/config:

- `docs/PORTFOLIO_LAYER.md`
- `docs/PORTFOLIO_BOUNDARIES.md`
- `configs/portfolio/examples/fixed_notional_portfolio.json`

Tests:

- `tests/unit/test_portfolio_spec_fields.py`
- `tests/unit/test_fixed_risk_sizing.py`
- `tests/unit/test_max_position_percent.py`
- `tests/unit/test_max_gross_exposure.py`
- `tests/unit/test_max_net_exposure.py`
- `tests/unit/test_multi_symbol_limits.py`
- `tests/unit/test_signal_to_target_conversion.py`
- `tests/unit/test_insufficient_capital.py`
- `tests/unit/test_portfolio_target_schema.py`
- `tests/unit/test_future_sector_asset_constraints.py`
- `tests/unit/test_future_correlation_aware_allocation_contract.py`
- `tests/unit/test_portfolio_boundary_no_fills.py`
- `tests/integration/test_portfolio_reference_integration.py`
- `tests/unit/test_portfolio_artifact_policy.py`

Handoff:

- `handoffs/ASV1-P18.md`

## Validation Results

Passed:

- `python -m pytest tests/unit tests/integration` — PASS, 387 passed.
- `python -m pytest tests/unit/test_portfolio_spec_fields.py tests/unit/test_fixed_risk_sizing.py tests/unit/test_max_position_percent.py` — PASS, 5 passed.
- `python -m pytest tests/unit/test_max_gross_exposure.py tests/unit/test_max_net_exposure.py tests/unit/test_signal_to_target_conversion.py` — PASS, 3 passed.
- `python -m compileall src` — PASS.
- `git status --short` — PASS for audit; before staging it showed only ASV1-P18 allowed-path files.
- `find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` — PASS, no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — PASS, no output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` — PASS, no output.
- `find . -path "./tests/fixtures/*" -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print` — PASS, no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print` — PASS, no output.
- `git ls-files runs` — PASS, no output.
- `grep -RnE "broker|live_order|account_sync|paper_trad" src/alpha_system/portfolio || true` — PASS, no output.
- `grep -RnE "fill|slippage|commission" src/alpha_system/portfolio || true` — PASS, no output.
- `git diff --check` — PASS, no output.
- `git diff --cached --name-only` — PASS before commit; returned only the
  ASV1-P18 allowed paths listed in this handoff.
- `git diff --cached --name-only | grep '^runs/'` — PASS before commit; exit
  1 with no output, so no `runs/` path was staged.
- `git diff --cached --name-only | grep -E '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.db-journal$|\.wal$|\.log$|__pycache__|\.pyc$|\.pkl$|\.pickle$|\.joblib$|\.onnx$|\.npy$|\.npz$)'` — PASS before commit; exit 1 with no output.
- `git push origin auto/alpha_system_v1/asv1-p18-portfolio-target-and-sizing-layer` — PASS. The repository pre-push Frontier canaries also passed.

Unavailable non-blocking tools:

- `python -m ruff check src tests || true` — ruff unavailable:
  `/usr/bin/python: No module named ruff`; command exited 0 due `|| true`.
- `python -m mypy src || true` — mypy unavailable:
  `/usr/bin/python: No module named mypy`; command exited 0 due `|| true`.

Development failure fixed and recorded:

- Initial portfolio-specific pytest run failed because
  `tests/unit/test_signal_to_target_conversion.py` used string
  `desired_exposure`, while the existing ASV1-P14 `SignalRecord` schema
  requires numeric optional exposure values. The test fixture was corrected to
  use `Decimal("0.5")`; final validation passed.

## Artifact Policy Confirmation

- `runs/**` remains local-only. `git ls-files runs` returned empty.
- No run-local `handoff.md`, `review.md`, `verdict.json`, or `checks.json` was
  staged or committed.
- No portfolio outputs, generated report bundles, raw data, canonical data,
  factor stores, label stores, signal stores, SQLite/DB/journal/WAL files,
  Parquet/Arrow/Feather files, logs, caches, model binaries, or heavy artifacts
  were staged or committed.
- Tests write no repository-local portfolio outputs.
- The example config is tiny, deterministic, and documented as validation-only,
  not market evidence.

## Staging Confirmation

Explicit staging only is used for the files listed above. `git add .`,
`git add -A`, force push, PR creation, merge, reviewer execution, Claude calls,
`review.md`, and `verdict.json` were not used.

Implementation commit:

- `f3b0a5a ASV1-P18 portfolio target sizing layer`

Before commit, the staged set contained no `runs/` path and no forbidden data,
DB, cache, log, or heavy-artifact path.

## Risk Dispositions

- R-013 — Heavy artifact committed accidentally: mitigated by artifact audits
  and explicit staging discipline.
- R-022 — Accidental broker/live scope creep: mitigated; no broker/live/paper
  source terms or account sync were introduced.
- R-006 / R-008 — Strategy / management overfit: mitigated; portfolio contains
  no alpha logic and no management exit logic.
- R-014 — Alpha/tradability overclaiming: mitigated; docs/config state
  validation-only scope and make no profitability, tradability, or production
  claims.
- R-031 / R-032 — Cross-sectional universe leakage / symbol identity misuse:
  mitigated by `instrument_id` target identity and multi-symbol tests.
- R-033 — Cost model silently disabled: did not materialize; portfolio does
  not own cost semantics and reference engine ownership is preserved.
- R-017 — Test weakening/gaming: mitigated; new tests assert behavior and the
  one development failure is recorded.
- R-016 — Hidden failed runs: mitigated by recording the fixed development
  failure above.
- R-037 — CLI/tests writing to local-only paths: mitigated; portfolio tests use
  in-memory fixtures or reject repo-local summary paths.

## Known Limitations

- Sector/asset constraints are contract-only.
- Correlation-aware allocation is contract-only.
- No optimizer or production multi-asset allocation solver is implemented.
- Reference integration passes target quantity into the existing reference
  engine configuration; there is not yet a native reference-engine portfolio
  target ingestion API.
- No persistence or registry integration was added for portfolio specs or
  targets.

## Review Focus

Review should focus on domain separation, risk-limit semantics,
insufficient-capital behavior, signal-to-target conversion, `instrument_id`
multi-symbol readiness, deterministic target schema, artifact-policy
compliance, and ensuring no execution/accounting ownership moved into the
portfolio layer.
