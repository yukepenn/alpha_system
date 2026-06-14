# Conditional Probe Contract

`SSRL-P02` adds a bounded exploratory probe for `SetupSpec` declarations where
entry context and event trigger are separate factor predicates.

The probe contract is intentionally narrow:

- `entry_context` compiles into a predicate over the context factor.
- `event_trigger` compiles into a predicate over a different trigger factor.
- Rows are scored only after the context predicate selects the bucket.
- Outcomes come from existing materialized path-label fields:
  `target_before_stop`, `mfe`, and `mae`.
- Target, stop, hold time, and horizon are fixed by the bound `SetupSpec` and
  path label; there is no geometry sweep.
- Every readout is stamped `EXPLORATORY`, has `promotion_eligible: false`, and is
  refused by the promotion guard if supplied to the trusted path.
- Every readout carries a VariantLedger/family-budget binding, a surrogate-FDR
  zero-pass gate, and a per-factor IC MDE/power statement.

This is not a strategy backtester, simulation bridge, promotion path,
alpha-quality claim, economic-usefulness claim, paper/live/broker workflow, or
deployment path.
