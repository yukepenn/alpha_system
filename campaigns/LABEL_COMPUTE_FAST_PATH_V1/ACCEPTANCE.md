# ACCEPTANCE — LABEL_COMPUTE_FAST_PATH_V1

## Campaign done

- All 10 phases (LCFP-P00..P09) complete; each phase's checks pass and review artifacts exist
  for YELLOW phases.
- LCFP-P09 `CLOSEOUT.md` carries a `{COMPLETE | COMPLETE_WITH_WARNINGS | BLOCKED}` verdict and
  the `fast_label_path_v1_status` evidence.
- `python tools/verify.py --all` and `python tools/hooks/canary_runner.py` pass (env-only reds
  documented).
- An executable FUTSUB reintegration handoff exists
  (`handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`).
- `git ls-files runs` is empty; the parquet/sqlite/arrow/feather/dbn/zst globs are empty.

The campaign is **accepted only if ALL of the following hold**. Only after acceptance does the
fast label path become the sanctioned production label materialization path (superseding the
FUTSUB-P18/P19 "reference-engine-only" non-goal).

## Parity gate (the core acceptance; LCFP-P07)

For every fast label family, a synthetic-fixture, CI-runnable suite proves **fast == reference
on the required parity set**:

- **label value** — exact where expected; documented numeric tolerance where float differences
  are expected. Unexplained differences are blockers.
- **label_available_ts** — EXACT match against the per-family `LabelAvailabilityPolicy`
  derivation.
- **roll-crossing guard behavior** — EXACT (`RollCrossPolicy` drop/truncate/flag/invalid,
  DROP default, ex-ante calendar); the required parity set includes roll-crossing cases.
- **maintenance-crossing guard behavior** — EXACT; the required parity set includes
  maintenance-crossing cases.
- **same-bar barrier ambiguity** (path labels) — EXACT `SameBarBarrierPolicy` semantics.
- **gap rows / missingness / quality flags** — `insufficient_window` / `input_gap` /
  `session_reset` / BBO-missingness reproduced exactly.
- **horizon-overlap / N_eff metadata** (`HorizonOverlapMetadata`) — preserved.
- **identity parity** — `label_version_id` identical to the reference content-addressed
  identity from `LabelContractSpec`; the fast path emits values only, never new identities.

## Family coverage gate (P03/P04/P05)

- **Fixed + extended horizons** (1m/3m/5m/10m/15m/30m/60m/120m/240m) compute **batched in one
  pass** per symbol-year where feasible (one panel load, one guard application).
- **Session-close and maintenance-flat** labels have fast implementations on the shared
  terminal-index model.
- **Cost-adjusted labels** (`COST_ADJUSTED_FWD_RET`, `SPREAD_ADJUSTED_FWD_RET`) are
  **cost-profile-consistent**: they vectorize the existing `backtest/costs.py` profiles
  (consumed read-only — no second cost truth) and the BBO spread proxy.
- **Path labels** (MFE/MAE/target-before-stop/triple-barrier) have fast kernels where
  correctness is provable, or a **documented safe fallback** to the reference per label.

## Benchmark / readiness gate (LCFP-P08)

- A value-free summary reports, per family: elapsed, rows/sec, canonical reads, file counts,
  registry deltas, speedup vs the P01 reference baseline, and the extrapolated
  full-accepted-window runtime estimate.
- **Bounded measurement window (required).** One self-validating roll-containing month by
  default (asserts ≥ 1 contract-roll event and ≥ 1 session/maintenance gap; widens or fails
  with a clear message). The reference engine is NEVER timed on a full window; full-window
  numbers are extrapolations with a recorded basis.
- **Real wiring (required).** The benchmark entrypoint actually invokes the real reference and
  fast runners (the executor has `ALPHA_DATA_ROOT`); stubbed timing callbacks or a
  blocked-only summary are failures unless the data root is genuinely absent.
- **Worker policy benchmarked**: workers swept over `{1,2,4,8}` where safe, with resolver
  smoke and parity confirmation (value / label_available_ts / guards / identity) on the same
  slice per worker count; a production worker policy is selected and documented.

## Capability gate (LCFP-P06)

- Targeted incremental materialization works by label_group / horizon_group / symbols /
  years / dataset_version_ids; dry-run produces row/unit/time estimates; execute runs selected
  units only; checkpoint/restart works; force-recompute works; registry-valid units are
  skipped.
- Resolver smoke passes on fast-produced values for a representative bounded-real slice.

## Registry / artifact gate

- Registry writes are **strictly serial** through the official labels keystone path; no
  parallel SQLite writes; no manual SQLite; exact resolver semantics preserved; Parquet-first
  (JSONL is sample/manifest/audit tier only — **no full-history JSONL payloads**).
- `producer_engine_id` + `value_schema_version` recorded; existing reference-engine label
  outputs preserved (preserve-don't-delete; no silent engine mixing).
- Artifact audit passes: no raw/canonical/feature-value/label-value/local-DB/heavy artifact
  committed; explicit staging only; clean merge gate.

## Reintegration gate (LCFP-P09)

- The FUTSUB reintegration plan is **executable**: exact amendment text for the FUTSUB
  campaign/spec files (including retiring the superseded reference-engine-only non-goal),
  the P16–P20 reset/rerun recipe on the fast path with the selected worker policy, the
  stopped-run resume recipe, and preserve-don't-delete state-cleanup rules for stale
  reference-label registry rows/values (superseded-and-verified only).

## Status vocabulary (report separately)

`code_status` / `fast_label_path_v1_status` / `execute_status` / `registry_status` /
`artifact_status`. Do not say "fast" unless the benchmark proves it; do not say "materialized"
unless execute + registry are true; do not call the fast path "production" before this
acceptance passes.

## Explicitly NOT in acceptance

Rerunning FUTSUB P16–P20 / resuming the FUTSUB run (coordinator action after this campaign
closes); any alpha mining, study rerun, promotion, or alpha/profitability/tradability claim;
any new label family; Ray/GPU/cluster; label-compiler/DSL platform; Strategy Reference /
FactorLibrary / AlphaBook scope; paper/live/broker/order anything.
