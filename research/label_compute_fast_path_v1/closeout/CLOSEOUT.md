# LCFP-P09 Closeout

Campaign: `LABEL_COMPUTE_FAST_PATH_V1`

Verdict: `COMPLETE`

This is the campaign closeout verdict document. It is not a phase PASS marker:
Ralph still owns review routing, verdict parsing, PR creation, CI, merge gates,
merge, and the final done-check.

## Status Vocabulary

- `code_status`: complete for the LCFP V1 fast label producer path and its
  targeting/checkpoint/worker/registry integration surfaces. The reference label
  engine remains the correctness oracle forever.
- `fast_label_path_v1_status`: parity-gated and benchmark-selected by family.
  LCFP-P08 selects the fast engine only for `fixed_base` and `path`; it selects
  the reference engine for `fixed_extended`, `close_out`, and `cost_adjusted`
  because the reference engine remains faster on the bounded benchmark.
- `execute_status`: bounded execution evidence exists. LCFP-P06 executed a
  bounded-real smoke in an isolated local-only data root with checkpoint/restart,
  force-recompute, serial registry registration, and resolver smoke. LCFP-P08
  executed the bounded real benchmark gate with real reference and fast runners.
  LCFP did not execute, reset, resume, or materialize FUTSUB P16-P20.
- `registry_status`: serial registry write and strict resolver smoke evidence
  exists. Existing reference-engine outputs were preserved; the P06 main-registry
  lineage conflict failed closed instead of silently mixing engines. P08 backed
  up the main label registry before benchmark work and used local-only scratch
  roots for benchmark writes.
- `artifact_status`: value-free committed evidence only. Per-row values,
  Parquet payloads, SQLite registries, run artifacts, logs, caches, and raw or
  canonical data remain local-only and were not added by this phase.

## Parity Evidence

Evidence source:
[`research/label_compute_fast_path_v1/parity/parity_report.md`](../parity/parity_report.md).

LCFP-P07 reports synthetic, CI-runnable parity for 8,142 compared records across
22 label definitions:

| Family | Compared records | Value tolerance | Observed max abs diff |
| --- | ---: | --- | ---: |
| `fixed_horizon` | 8,074 | exact | 0 |
| `session_maintenance` | 6 | exact | 0 |
| `cost_adjusted` | 10 | abs=1e-12, rel=1e-12 | 0 |
| `path` | 52 | abs=1e-12, rel=1e-12 | 0 |

The report covers the acceptance-required dimensions: label value,
`label_available_ts` exact parity, `label_spec_id` and `label_version_id`
identity parity, roll-crossing guard behavior, maintenance-crossing guard
behavior, same-bar `SameBarBarrierPolicy` variants for path labels, gap and BBO
missingness flags, session-gap behavior, `HorizonOverlapMetadata`, and
no-lookahead constraints. The report names no residual gap for the required P07
synthetic parity dimensions and makes no benchmark, alpha, profitability,
tradability, paper, live, broker, or deployment claim.

## Benchmark Evidence

Evidence source:
[`research/label_compute_fast_path_v1/benchmark/benchmark_summary.md`](../benchmark/benchmark_summary.md).

LCFP-P08 measured a bounded, self-validating real-data slice: ES 2024-06-01 to
2024-07-01, 26,304 OHLCV rows, 26,304 BBO rows, one asserted contract-roll
event, and 48 asserted session/maintenance gaps. The benchmark used the real P01
reference runner and real fast materializer; the reference engine was not timed
on the full window. Full-window figures in the summary are extrapolations from
the bounded rows/sec basis.

Per-family selected engine policy from the committed P08 summary:

| Family | Selected engine | Requested workers | Measured speedup | Reason |
| --- | --- | ---: | ---: | --- |
| `fixed_base` | `fast` | 8 | 1.03x | Fast compute narrowly beat the same-process reference rerun. |
| `fixed_extended` | `reference` | n/a | 0.55x | Reference remains faster. |
| `close_out` | `reference` | n/a | 0.40x | Reference remains faster. |
| `cost_adjusted` | `reference` | n/a | 0.72x | Reference remains faster. |
| `path` | `fast` | 8 | 10.23x | Fast compute cleared the material-speedup gate. |

Selected thread controls were `POLARS_MAX_THREADS=2`, `OMP_NUM_THREADS=2`,
`RAYON_NUM_THREADS=2`, and `NUMBA_NUM_THREADS=2`. Resolver smoke and parity
passed for every family at every worker count in the bounded sweep. Worker
reductions were recorded where runnable unit counts were smaller than requested
workers.

## Acceptance Validation

Executor validation on 2026-06-10:

- `python tools/verify.py --smoke`: passed with exit 0 in a clean
  `FRONTIER_*` environment.
- `python tools/hooks/canary_runner.py`: passed with exit 0; all Frontier
  canaries passed.
- `python tools/verify.py --all`: first run failed in the inherited
  `ALPHA_DATA_ROOT` environment on
  `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
  because the runtime cache resolved to `alpha_data_root` instead of
  `run_artifacts`. This is the known environment-only cache-policy red when
  `ALPHA_DATA_ROOT` is exported, not an LCFP code/doc failure. Clean rerun with
  `ALPHA_DATA_ROOT` unset passed: `3009 passed, 70 skipped in 49.64s`. The
  clean run's status doctor reported `WARN` because this worktree has no LCFP
  run dir with `state.json`, but `verify.py --all` exited 0.
- `test -f research/label_compute_fast_path_v1/closeout/CLOSEOUT.md`: passed.
- `test -f handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`:
  passed.
- `git ls-files runs`: passed with empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`: passed with empty output.

If a later coordinator or reviewer observes a non-environmental red in the
acceptance checks, this verdict must be downgraded to `BLOCKED` or
`COMPLETE_WITH_WARNINGS` with the exact failure named. This executor did not
silently accept any validation red.

## FUTSUB Reintegration

Executable coordinator instructions live at
[`handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`](../../../handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md).

That handoff records the exact FUTSUB amendment text, the P16-P20 reset/rerun
recipe, the stopped-run resume sequence, and the preserve-don't-delete rules for
reference-label registry rows and values. All of those actions are coordinator
actions after LCFP closes. This phase did not amend FUTSUB files, edit
`ACTIVE_CAMPAIGN.md`, clear a STOP file, edit run state, remove worktrees,
delete registry rows, or write label values.

## Recommended Active Campaign Repoint

Recommended coordinator action after LCFP acceptance:

- Repoint `ACTIVE_CAMPAIGN.md` back to
  `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.
- Resume run
  `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` only after
  applying the reintegration handoff, backing up local registries, resetting
  FUTSUB P16-P20 state as described there, and clearing the STOP condition.

This closeout records the recommendation only. The coordinator owns the repoint.

## No-Claims Boundary

LCFP is substrate engineering. This closeout makes no alpha, profitability,
tradability, execution-quality, live-trading, paper-trading, broker, order
routing, deployment, production-trading, capital-allocation, or promotion claim.
