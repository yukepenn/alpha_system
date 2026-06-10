# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/LABEL_COMPUTE_FAST_PATH_V1`
Workflow: `workflow2`
Run: `workflow2 not started` - contract bundle authored; live WF2 run not yet started
Status: `contract authored (ready to plan/run)` - the 6-file campaign bundle is
present and YAML parses. No phase has run yet. `LCFP-P00` (coordinator-owned,
`must_run_alone`) will re-confirm this pointer at run start.

Current phase: `none` - run not started
Next phase: `LCFP-P00` - Campaign Bootstrap + FUTSUB Pause Handoff
Completed phases: `0/10`

Campaign `LABEL_COMPUTE_FAST_PATH_V1` builds a single-machine, local, columnar
(Polars/NumPy/Numba where correct), batch/vectorized, incremental,
**reference-parity-gated**, registry-safe **fast producer path for labels** —
the label analogue of the completed `FEATURE_COMPUTE_FAST_PATH_V1` (17/17, run
`2026-06-08T160146Z`). It extends the existing partial fast label module
(`src/alpha_system/labels/fast/**`, built by FCFP-P10, fixed-horizon coverage
only) to the full governed label surface: fixed + extended horizons,
session-close / maintenance-flat, cost-adjusted, and path labels, plus targeted
incremental worker-parallel execution, a parity / no-lookahead / guard suite,
and a benchmark/readiness gate. The per-row reference label engine remains the
correctness **oracle forever**; the fast path becomes the production label
materialization path ONLY after acceptance. **Policy supersession (explicit):**
FUTSUB-P18/P19 specs listed "a V1 fast label path" as a non-goal; LCFP
deliberately supersedes that policy, and FUTSUB P16–P20 will be amended to use
the fast path via the LCFP-P09 reintegration handoff. It is substrate/infra
engineering only: NOT Ray/GPU/cluster, NOT a label-compiler platform, NOT alpha
mining, NOT FactorLibrary/AlphaBook/Strategy Reference, NOT paper/live/broker;
no alpha, profitability, or tradability claim.

```text
reference label engine (oracle, kept)
  -> FUTSUB pause handoff (preserve everything, delete nothing)
  -> inventory + bounded reference baseline benchmark
  -> shared label panel / terminal-index / guard / label_available_ts contract
  -> fast fixed+extended horizon labels (one pass, 1m..240m)
  -> fast session-close / maintenance-flat / cost-adjusted labels
  -> fast path labels (MFE/MAE/target-before-stop/triple-barrier)
  -> targeting / checkpoint / workers / serial registry / resolver smoke
  -> parity / no-lookahead / guard test suite
  -> benchmark + production readiness gate (workers 1/2/4/8)
  -> FUTSUB reintegration handoff + closeout
```

## Paused predecessor

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is **paused** at FUTSUB-P19
(19/34, run `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`,
STOP active) — deliberately stopped because reference-engine label
materialization is too slow at full-window scale. P14–P19 are merged; P19
cost-adjusted labels are ~60% materialized (checkpointed/durable; preserved —
nothing deleted). Resume is planned after LCFP closes: the coordinator amends
FUTSUB per `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`
(LCFP-P09), resets/reruns P16–P20 on the fast label path, clears STOP, resumes
the run, and repoints this file back to FUTSUB.

## Campaign Identity

- Campaign ID: `LABEL_COMPUTE_FAST_PATH_V1`
- Campaign path: `campaigns/LABEL_COMPUTE_FAST_PATH_V1`
- Repo: `alpha_system` / `~/projects/alpha_system`
- Workflow: `workflow2` (Ralph strict autonomous loop; `dag_wave`; registry-touching
  phases serialized by a shared `materialization_registry` resource_class; serial merge)
- Project profile: `trading_research` / `research` / `label_compute_fast_path`
- Phase count: 10 phases (`LCFP-P00` ... `LCFP-P09`)
- Lane policy: Green/Yellow only; **no Red scope**
- Precedent: `campaigns/FEATURE_COMPUTE_FAST_PATH_V1` (FCFP, 17/17) + ADR-0007

## Contract Bundle

- `campaigns/LABEL_COMPUTE_FAST_PATH_V1/GOAL.md`
- `campaigns/LABEL_COMPUTE_FAST_PATH_V1/PHASE_PLAN.md`
- `campaigns/LABEL_COMPUTE_FAST_PATH_V1/campaign.yaml`
- `campaigns/LABEL_COMPUTE_FAST_PATH_V1/ACCEPTANCE.md`
- `campaigns/LABEL_COMPUTE_FAST_PATH_V1/RISK_REGISTER.md`
- `campaigns/LABEL_COMPUTE_FAST_PATH_V1/RUNBOOK.md`

## Boundaries

In scope: extending `labels/fast/**` (shared panel/terminal/guard contract;
fixed+extended horizon, session/maintenance/cost, and path label packs);
targeting/checkpoint/worker CLI integration with strictly serial registry
writes; the parity/no-lookahead/guard suite; the benchmark/readiness gate; the
FUTSUB reintegration handoff. Out of scope: rerunning FUTSUB P16–P20 / resuming
the FUTSUB run (coordinator action after closeout); trusting fast labels
without parity; weakening roll_guard or the maintenance guard; future-observed
contract changes; labels as features; parallel SQLite writes; full-history
JSONL payloads (Parquet-first); editing cost/value/accounting math
(`backtest/costs.py` is read-only); alpha mining / new label families / param
search; Strategy Reference / FactorLibrary / AlphaBook; paper/live/broker/order;
external provider calls; raw/canonical/value or local-DB commits; any
alpha/profitability/tradability claim. The reference label engine is never
deleted or weakened.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
phase selection, execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. Resume continues from recorded run state.
Registry-touching phases (LCFP-P06/P08) share
`resource_class: materialization_registry` and never run concurrently; merges
are always serial. Pointer ownership: `LCFP-P00` re-confirms this pointer at run
start; at closeout the COORDINATOR (not a phase branch) repoints it back to
FUTSUB per the LCFP-P09 reintegration handoff — LCFP-P09's `allowed_paths`
exclude `ACTIVE_CAMPAIGN.md`, and phase branches never write it.
