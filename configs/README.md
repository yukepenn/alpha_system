# Configs

Per-domain configuration for `alpha_system`, grouped by subsystem. These are
declarative inputs (YAML/JSON) — not code, and not data.

## Layout

One subdirectory per domain:

- `data/` — provider instrument masters + validation configs (IBKR + Databento).
- `execution/` — **backtest cost / slippage models, NOT order execution** (loaded by `backtest/`).
- `factors/` · `labels/` · `grids/` · `studies/` · `ml/` · `management/` · `portfolio/`
  · `strategies/` · `universes/` · `reports/` · `governance/` · `registry/`.

## Conventions

- `examples/` subdirectories (and a few `*_example.*` files) hold human-facing
  reference configs — intentional examples, not stale cruft.
- `configs/data/request_pacing_policy_to_be_verified.json` is **intentional**: its
  `verification_status: "to_be_verified"` is a governance-honesty marker for a
  conservative IBKR pacing default that must be verified before any authorized pull.
  Do not silently "fix" the name.

No credentials, account details, provider secrets, real market data, committed
local paths, or production settings belong here. Real data stays local-only under
`ALPHA_DATA_ROOT`.
