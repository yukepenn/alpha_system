# Session / Maintenance / Cost Fast Packs

LCFP-P04 adds two commit-eligible pack surfaces under
`alpha_system.labels.fast`:

- `build_session_maintenance_label_pack(...)` for governed
  `session_close` and `maintenance_flat` fixed-family definitions.
- `build_cost_adjusted_label_pack(...)` for governed
  `cost_adjusted_fwd_ret` and `spread_adjusted_fwd_ret` definitions.

Both packs emit `LabelValueRecord` values only. They preserve
`label_version_id` identity from each reference-derived `LabelContractSpec` and
do not write registries by themselves.

## Session And Maintenance

The close-out pack reuses the LCFP-P02 shared panel and terminal-index model:

- `TerminalKind.SESSION_CLOSE` selects the last same-contract RTH row at or
  before 15:00 America/Chicago for the CME trade date.
- `TerminalKind.MAINTENANCE_FLAT` selects the last same-contract row at or
  before the 16:00 America/Chicago maintenance boundary for the CME trade date.
- Roll and maintenance guard dispositions come from the same terminal path as
  fixed-minute labels.

The reference oracle remains
`alpha_system.labels.families.fixed_horizon` for `SESSION_CLOSE` and
`MAINTENANCE_FLAT`.

## Cost Consistency

The cost-adjusted pack computes BBO exact-horizon records from the shared panel
and applies the sanctioned cost primitives from
`alpha_system.backtest.costs` read-only:

- `SpreadCost` supplies half-spread and full-spread fill cost profiles.
- `BpsCost` supplies the fixed-bps component for
  `cost_adjusted_fwd_ret`.
- `CostInput` supplies the fill notional and BBO inputs consumed by those
  profiles.

The fast path does not edit `backtest/costs.py`, duplicate cost arithmetic, or
make execution-quality claims. BBO spread remains a proxy input and missing or
quarantined BBO rows remain gap records with reference-family quality flags.

## Parity Coverage

The P04 synthetic parity tests cover:

- normal session-close and maintenance-flat rows;
- post-session rows with no retained session-close terminal;
- roll-crossing close-out rows dropped by the shared roll guard;
- normal cost-adjusted and spread-adjusted rows;
- a cost-adjusted window crossing the daily maintenance break, matching the
  reference family's retained-record behavior;
- terminal BBO gap rows;
- entry BBO missing rows;
- exact `label_available_ts`, `label_spec_id`, quality flags, and
  `label_version_id` parity against the reference families.

Cost-adjusted value assertions use a `1e-12` absolute/relative tolerance because
the reference computes from `Decimal` input rows while the fast path consumes a
Polars float panel before reconstructing Decimal cost inputs. This tolerance is
limited to floating representation noise and does not widen guard, timestamp,
identity, or flag parity.
