# REFERENCE_LABEL_PARALLEL_COMPUTE_V1 — Goal

## Why this campaign exists (Compass test: removes a blocker)

FUTSUB-P19's full-window cost_adjusted pass measured ~3h wall-clock on the
single-threaded reference engine, and every future cost/index label grid
inherits that ceiling. `docs/STRUCTURAL_BACKLOG.md` §6 recorded the fix and its
trigger ("first time a reference-family materialization is projected > ~1h");
the trigger is met. This campaign removes the throughput blocker without
touching label math.

## The measured premise (do not relitigate without new evidence)

LCFP-P08 (committed, parity-gated, worker-swept 1/2/4/8):

- The V1 fast pack LOSES for `cost_adjusted` (best 0.72x), `fixed_extended`
  (0.55x), `close_out` (0.40x) — per-row Decimal cost-kernel arithmetic +
  record validation is not vectorizable panel math, and the reference engine
  is already the fastest reference family at ~84k rows/sec.
- Eight fast workers together (61k rows/sec) lost to ONE reference process
  (84k rows/sec): the worker POOL is fine; the per-unit engine inside it was
  the slow part for these families.

## What this campaign does

Reuse the existing LCFP-P06 spawn-context worker pool exactly as-is, but let
`alpha scaleout label-pack --engine reference --workers N` run N **reference**
per-unit computations concurrently over disjoint units:

- Workers: unchanged reference per-unit pipeline (panel load → per-row
  reference math → validation → Parquet value write); never open any registry.
- Parent: serial keystone registry writes in deterministic unit order, then
  checkpoint-ledger append (identical to the v1 worker contract).
- Gates: exact serial==parallel equivalence (records, label_version_ids,
  hashes, registry rows, guards, label_available_ts — any diff is a BLOCKER),
  interruption-resume correctness, single-writer audit, then a bounded real
  benchmark (workers 1/2/4/8) with release at >=3.0x @ 8 workers or an honest
  NOT_RELEASED diagnosis.
- Closeout: amend FUTSUB's ENGINE POLICY to the measured released policy and
  hand the coordinator an executable resume path for P19 (~82/216 full-window
  cells remain; checkpoints durable).

## What this campaign is NOT

- NOT a new engine and NOT cost-kernel vectorization (backlog §6 option 2 —
  promoted only if this campaign's benchmark proves a ceiling below 3x).
- NOT an edit to `labels/engine.py`, `labels/families/**`, `roll_guard.py`,
  or `version.py` (forbidden paths; the reference engine stays the oracle).
- NOT Ray/GPU/cluster, NOT alpha ideation, NOT FactorLibrary/AlphaBook,
  NOT paper/live/broker. No alpha, profitability, or tradability claim.

## Success definition

`--engine reference --workers 8` is a released, parity-exact, resume-safe,
benchmark-justified production path for reference-policy label families, and
FUTSUB-P19 resumes on it.
