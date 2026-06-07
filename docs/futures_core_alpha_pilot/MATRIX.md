# Session Horizon Regime Matrix

`FUTCORE-P22` adds the value-free session x horizon x regime consolidation for
the futures core alpha pilot.

Primary evidence:

- `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`

The matrix consolidates P16-P21 diagnostics by reference only. It records
StudySpec ids, source report ids/hashes, runtime statuses, coverage counts,
session/horizon/regime flags, fragile-horizon markers, thin-session
research-only markers, and P21 cost/thin-session flags.

It adds no new commands, diagnostics runners, readers, primitives, tests,
review verdicts, promotion decisions, paper/live/broker/order behavior, or
profitability/tradability claims. `zero_cost` remains diagnostic-only and never
a promotion basis.
