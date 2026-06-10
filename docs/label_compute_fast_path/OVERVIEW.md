# Label Compute Fast Path Overview

`LABEL_COMPUTE_FAST_PATH_V1` extends the existing partial fast label module into
a governed producer path for fixed and extended horizon labels, session-close
and maintenance-flat labels, cost-adjusted labels, and path labels.

The fast path is a producer path only. It emits label values through the
sanctioned label materialization and registry contracts; it does not define a
second identity system, a second cost or value-accounting truth, or a trading
system. `label_version_id` semantics stay content-addressed from the governed
label contract, and resolver exact-id behavior stays fail-closed.

## Correctness Contract

The per-row reference label engine remains the oracle forever. A fast label
output is trusted only when it matches the reference on the required parity
dimensions:

- label value, exact where expected or with documented numeric tolerance;
- `label_available_ts`, exact against `LabelAvailabilityPolicy`;
- roll-crossing behavior, exact against `RollCrossPolicy`;
- maintenance-crossing behavior, exact against the reference guard;
- same-bar path-label ambiguity behavior where applicable;
- gap, missingness, quality, and overlap metadata;
- `label_version_id` identity.

No-lookahead is mandatory: input availability must not exceed the output
decision time, and a label must not be available before its guarded terminal.

## Execution Contract

LCFP keeps registry writes serial through the official keystone path. Worker
parallelism, when introduced, is compute-only over independent units. Local
Parquet values, registries, checkpoints, and run artifacts remain outside git.
Committed research evidence is value-free: counts, elapsed time, rows per
second, file counts, registry deltas, parity summaries, and readiness decisions.

LCFP-P01 establishes two read-only evidence inputs for later design and
benchmark phases: the label-engine inventory under
`research/label_compute_fast_path_v1/inventory/` and the bounded reference
baseline under `research/label_compute_fast_path_v1/baseline/`. The baseline
times the reference engine on a bounded slice only; full-window figures are
extrapolated from measured rows per second.

## FUTSUB Supersession

The paused `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` FUTSUB-P18/P19 specs
treated a V1 fast label path as out of scope. This campaign deliberately
supersedes that historical policy, but only after LCFP acceptance. Until the
LCFP acceptance gates pass, the reference engine remains the production label
materialization path.

After LCFP-P09, the coordinator may amend FUTSUB P16-P20 to use the accepted
fast label path, preserve existing reference-produced values and registry rows
unless they are superseded and verified through the official process, clear the
FUTSUB STOP condition, and resume the predecessor run. Phase branches do not
perform that reintegration.

This campaign is research-only substrate engineering and makes no alpha,
profitability, tradability, execution-quality, broker, live-trading,
paper-trading, order-routing, deployment, or production-trading claim.
