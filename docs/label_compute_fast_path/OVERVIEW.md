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

LCFP-P02 adds the shared `alpha_system.labels.fast` panel and terminal contract
that P03/P04/P05 consume. It builds one immutable symbol-year panel with
trade-price, high/low, BBO proxy, cost-input, session, ex-ante roll, and
maintenance metadata; resolves terminal indices once for fixed-horizon,
session-close, maintenance-flat, and roll-truncation modes; and derives
`label_available_ts` plus gap/quality metadata without computing label values.
The detailed surface is documented in
[PANEL_TERMINAL_CONTRACT.md](PANEL_TERMINAL_CONTRACT.md).

LCFP-P03 consumes that contract for fixed-minute labels. The fixed-horizon fast
pack computes governed trade-price 1/3/5/10/15/30/60/120/240m labels and the
existing governed midprice minute labels from the shared panel while preserving
reference-derived `label_version_id` identity. Symbolic close-out labels
`session_close` and `maintenance_flat` are recognized but routed to LCFP-P04.

LCFP-P04 consumes the same shared panel for governed close-out and
cost-adjusted labels. `build_session_maintenance_label_pack(...)` computes
`session_close` and `maintenance_flat` with the P02 terminal-index model.
`build_cost_adjusted_label_pack(...)` computes `cost_adjusted_fwd_ret` and
`spread_adjusted_fwd_ret` from exact BBO horizons while applying the sanctioned
`alpha_system.backtest.costs` primitives read-only. BBO spread remains a proxy
input only; there is no execution-quality claim.

LCFP-P05 consumes the same shared panel and guarded terminal model for path
labels. `build_path_label_pack(...)` covers governed `mfe`, `mae`,
`target_before_stop`, and `triple_barrier` definitions. First-touch scans are
bounded by the retained P02 terminal; same-bar target/stop ambiguity follows
`SameBarBarrierPolicy` exactly; unsupported panel/terminal shapes route to the
reference path family rather than changing label semantics. The detailed table
is documented in [PATH_LABEL_PACKS.md](PATH_LABEL_PACKS.md).

LCFP-P06 routes these packs through targeted materialization surfaces:
`alpha scaleout label-pack` and `alpha label materialize --fast-path`. The
selection dimensions are label group, horizon group, symbols, years, and
DatasetVersion ids. Dry-run remains write-free. Execute mode writes local
Parquet values plus deterministic worker manifests under `ALPHA_DATA_ROOT`,
then a single parent-process writer registers completed units through the
official label registry path in deterministic unit order. Checkpoints and live
registry truth skip completed units by default; `--force` recomputes selected
units. Label worker precedence is `--workers`, then `ALPHA_LABEL_CPU_WORKERS`,
then `ALPHA_CPU_WORKERS`, then serial default.

LCFP-P07 consolidates the correctness gate into
`tests/unit/label_compute_fast_path/test_parity_matrix_suite.py` and
`tests/no_lookahead/label_fast_path/test_fast_label_available_ts.py`. The suite
reuses the existing parity harness, verifies every fast label family against
the reference oracle on synthetic fixtures, exercises roll/maintenance guards,
same-bar path policies, BBO missingness, horizon overlap metadata, exact
`label_available_ts`, and exact identity parity, and records value-free evidence
in `research/label_compute_fast_path_v1/parity/parity_report.md`.

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
