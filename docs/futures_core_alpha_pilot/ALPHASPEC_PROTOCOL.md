# Futures Core Alpha Pilot AlphaSpec Protocol

`FUTCORE-P05` records the value-free AlphaSpec Batch Protocol for
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. The canonical protocol is:

- [research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md](../../research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md)

This document is a durable human-facing summary. It does not draft, approve,
implement, run, review, promote, or reject any AlphaSpec.

## Schema Binding

Each later family draft must contain exactly one governance `AlphaSpec` payload
whose top-level fields match `ALPHA_SPEC_REQUIRED_FIELDS` in
`src/alpha_system/governance/alpha_spec.py`:

- `alpha_spec_id`
- `hypothesis_id`
- `target_instruments`
- `data_assumptions`
- `factor_inputs`
- `label_references`
- `exclusion_rules`
- `timestamp_assumptions`
- `cost_assumptions`
- `expected_failure_modes`
- `promotion_criteria`
- `created_by`
- `created_at`

The substantive fields are `data_assumptions`, `exclusion_rules`,
`timestamp_assumptions`, `cost_assumptions`, `expected_failure_modes`, and
`promotion_criteria`. They must be explicit, non-empty, and specific enough for
independent critique.

## Scope And Quotas

The universe is limited to ES, NQ, and RTY. The campaign cap is 40 AlphaSpec
drafts. Target and maximum quotas follow the family budget:

| Family | Phase | Target / maximum |
| --- | --- | ---: |
| Cross-market / relative value | `FUTCORE-P07` | 16 |
| VWAP / session auction | `FUTCORE-P08` | 8 |
| Regime-gated momentum vs reversion | `FUTCORE-P09` | 6 |
| Liquidity sweep / failed breakout / objective PA | `FUTCORE-P10` | 6 |
| BBO tradability / top-book confirmation | `FUTCORE-P11` | 4 |

Volume/activity is overlay-only, has no standalone budget, and may be used only
where existing primitives support it.

## Timestamp, Horizon, Session, And Cost Rules

Each draft must declare `available_ts` usage for features and inputs and
`label_available_ts` usage for labels. Final-session high, low, VWAP, range,
volume, or other aggregates are forbidden in intraday decisions before the
session is complete.

Primary horizons are `5m`, `10m`, `15m`, and `30m`. `1m` and `3m` are
execution-fragile diagnostics only and cannot be a promotion basis. Drafts must
declare session views, thin-session caveats, and the hard boundary that no
position crosses the exchange daily maintenance / trade-date break.

Cost assumptions must cite `CostModelVersion`
`cmv_futcore_pilot_three_layer_session_stress_v1` and exactly the profiles
`zero_cost`, `base`, `stress_1`, `stress_2`, and `double_cost`. `zero_cost` is
diagnostic-only and never a promotion basis.

## Family Diagnostics

Later drafts must declare family diagnostics before any StudySpec or runtime
phase consumes them:

- Cross-market: timestamp alignment, cross-instrument missingness, stale or
  asynchronous input handling, and construction assumptions.
- VWAP/session: running-vs-final VWAP, opening range, overnight context, gap
  timing, and final aggregate lookahead rejection.
- Regime: computable point-in-time activation logic, regime coverage,
  transition instability, and duplicate exposure to broad filters.
- Liquidity/PA: objective computable sweep, failed-breakout, wick,
  displacement, compression, and level-availability rules.
- BBO: valid BBO requirements, quote-quality exclusions, confirmation/risk
  framing, and missing/stale/crossed quote handling.

## Independence Rules

Drafting and critique must preserve separation of duties:

- `created_by` identifies only the `Hypothesis Scout` drafter.
- The AlphaSpec Critic must not draft the spec it reviews.
- The semantic reviewer must be independent of the drafter and critic.
- Any later promoter must be independent of the drafter, critic, reviewer,
  diagnostics runner, and implementer.
- Self-review and self-promotion are forbidden.
- Duplicate-exposure and rejected-idea awareness must be visible to
  `FUTCORE-P12`.

This protocol adds no code, tests, runtime behavior, data reader, broker/live/
paper/order path, market values, diagnostic result, review verdict, or research
claim.
