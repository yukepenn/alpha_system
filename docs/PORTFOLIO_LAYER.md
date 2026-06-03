# Portfolio Layer

The portfolio layer converts reviewed strategy-intent signals into deterministic
portfolio targets. It owns target sizing, capital allocation state, and exposure
constraints. It does not generate factors, create signals, decide management
exits, or produce PnL.

## Supported Scope

- `PortfolioSpec` with target schema, sizing, allocation, risk limits,
  multi-symbol constraints, future sector/asset constraint contracts, future
  correlation-aware allocation contracts, and signal-to-target conversion.
- Fixed notional sizing.
- Risk-per-trade sizing from equity and stop distance.
- Max position percent, gross exposure, and net exposure enforcement.
- Deterministic insufficient-capital behavior through reject or cap policy.
- Stable `PortfolioTarget` records keyed by `instrument_id` and source signal.

## Target Schema

Portfolio targets are structural records. They include target identity,
`instrument_id`, timing, session/bar identity, direction, target notional,
target quantity, target weight, source signal identity, strategy version, data
version, quality flags, rejection status, and reasons.

Targets are not orders and are not accounting records. The reference 1-minute
bar engine remains the single PnL truth.

## Future Contracts

Sector/asset constraints and correlation-aware allocation are represented as
contract-only fields in this phase. They are intentionally not active optimizer
features yet.

The example config under `configs/portfolio/examples/` is a tiny deterministic
validation example only. It is not market evidence.
