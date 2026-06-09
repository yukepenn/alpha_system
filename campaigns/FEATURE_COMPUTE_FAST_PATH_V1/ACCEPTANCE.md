# ACCEPTANCE — FEATURE_COMPUTE_FAST_PATH_V1

## Campaign done

- All 16 phases (FCFP-P00..P15) complete; each phase's checks pass and review artifacts exist
  for YELLOW phases.
- FCFP-P15 `CLOSEOUT.md` carries a `{COMPLETE | COMPLETE_WITH_WARNINGS | BLOCKED}` verdict and
  the `producer_fast_path_v1_status` evidence.
- `python tools/verify.py --all` and `python tools/hooks/canary_runner.py` pass (env-only reds
  documented).
- A FUTSUB resume-on-V1 handoff exists (`handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FUTSUB_RESUME_ON_V1.md`).
- `git ls-files runs` is empty; the parquet/sqlite/arrow/feather/dbn/zst globs are empty.

## Parity gate (per family/label pack; the core acceptance)

For each pack, a synthetic-fixture, CI-runnable test proves V1 == reference on:

- feature/label **value** — exact where expected; documented numeric tolerance where float
  differences are expected (e.g. rolling-std summation order). Unexplained differences are blockers.
- **available_ts** (and **label_available_ts** for labels) — exact.
- **gap rows** — `insufficient_window` / `input_gap` / `session_reset` reproduced exactly.
- **missingness / quality flags** — exact.
- **roll-splice and maintenance-crossing guard** behavior (labels) — exact.
- **feature_version_id / label_version_id** — identical to the reference identity (the fast
  engine produces values, never new identities).

## Benchmark gate (FCFP-P13)

A value-free benchmark summary reports, per pack: elapsed, rows/sec, canonical reads per
symbol-year, outputs per read, speedup vs reference, and the estimated full-accepted-window
runtime. V1 must be materially faster than the reference engine and must reduce redundant
canonical scans.

**Bounded measurement window (required).** The benchmark MUST run on a bounded,
representative slice — a single configurable window defaulting to **one roll-containing
month** (e.g. ES/NQ/RTY December 2024, which spans a contract roll plus holiday/maintenance
session gaps) — NOT a full symbol-year. The reference engine is the ~500x-slower correctness
oracle and MUST NOT be timed on a full symbol-year (doing so adds tens of minutes of pure
wall-clock with zero correctness payoff). The estimated full-accepted-window runtime is
**extrapolated** from the slice's measured rows/sec and the known full-window row counts; the
benchmark records the slice row count, the window, and the extrapolation basis. The slice MUST
be self-validating: it asserts it contains at least one contract-roll event and at least one
session gap (so the bounded window still exercises the structurally important branches), and
widens or fails with a clear message otherwise.

**Real-data parity confirmation (required, complements the synthetic parity gate).** On the
same bounded slice, the benchmark MUST also assert V1 == reference on **value**
(documented numeric tolerance where float differences are expected), **available_ts /
label_available_ts**, **gap/quality flags**, and **feature_version_id / label_version_id**.
This is a real-data confirmation layered on top of the exhaustive synthetic-fixture parity
gate (§Parity gate), not a replacement for it; unexplained diffs are blockers. The benchmark
is no longer timing-only — it proves the bounded slice matches before reporting any speedup.

## Capability gate (incremental)

- Targeted materialization by family / feature_id / feature_group / label_id / symbols / years /
  dataset_version_ids works; dry-run produces row/unit/time estimates; execute runs selected
  units only; completed units are skipped via checkpoint + registry truth.
- Adding one new feature materializes only that feature's grid, not all families.

## Registry / artifact gate

- Serial registry writes through the official keystone path; no manual SQLite; exact resolver
  semantics preserved; keystone identity preserved; Parquet-first (JSONL audit/sample only).
- `producer_engine_id` + `value_schema_version` recorded; existing reference-engine outputs
  preserved and reconciled (no silent engine mixing).
- No raw/canonical/feature value/label value/local DB/heavy artifact committed; explicit staging
  only; clean merge gate.

## Integration gate (FCFP-P14)

- The scaleout driver routes to the V1 PackMaterializer by default (reference engine selectable
  as oracle/fallback); checkpoint/restart + idempotency preserved; a representative bounded-real
  V1 slice materializes and resolver-smoke passes.

## Status vocabulary (report separately)

`code_status` / `producer_fast_path_v1_status` / `execute_status` / `registry_status` /
`consumer_query_status` / `artifact_status`. Do not say "fast" unless the benchmark proves it; do
not say "materialized" unless execute + registry are true.

## Explicitly NOT in acceptance

Resuming the FUTSUB full-window backfill (that is a coordinator action under FUTSUB on V1 after
this campaign closes); any alpha/profitability/tradability claim; any new feature/label family;
Ray/GPU/cluster; feature-compiler platform.
