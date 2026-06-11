# REFERENCE_LABEL_PARALLEL_COMPUTE_V1 — Acceptance

The campaign is DONE when every line below is deterministically checkable and
true:

1. **All five phases merged** (RLPC-P00…P04) with green checks; YELLOW phases
   carry fresh Claude review artifacts under
   `reviews/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/<phase>/` with verdicts citing
   deterministic evidence (test output, benchmark summary, audit results).
2. **Exact equivalence proven**: committed tests show workers=1 and workers>1
   produce identical record sets, `label_version_id`s, content hashes,
   registry rows/lineage, guard outcomes, and `label_available_ts` on the
   synthetic grid. No tolerance parameters exist for this comparison.
3. **Resume-safety proven**: committed tests show an interrupted parallel pass
   resumes without duplicate units or holes, and checkpoint-ledger rows map
   1:1 to registered units.
4. **Single-writer invariant enforced**: a committed test/canary fails if any
   worker-process code path opens the label registry; registration is
   parent-only and serial in deterministic unit order.
5. **Honest benchmark committed** (value-free):
   `research/reference_label_parallel_compute_v1/benchmark/benchmark_summary.md`
   with workers 1/2/4/8 on a bounded self-validating real cost_adjusted grid,
   component timings disclosed, and a deterministic release decision —
   `workers=8 RELEASED` iff measured speedup >= 3.0x, else `NOT_RELEASED`
   with a component-timing diagnosis. The reference engine is never timed on
   a full window. The production registry is never the benchmark target.
6. **FUTSUB wired consistently with the measurement**: the FUTSUB contract's
   ENGINE POLICY reflects the released policy (or is untouched if
   NOT_RELEASED), and
   `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_RESUME_ON_PARALLEL_REFERENCE.md`
   gives the coordinator an executable resume path for FUTSUB-P19.
7. **Truth chain intact**: `labels/engine.py`, `labels/families/**`,
   `roll_guard.py`, `version.py` untouched (git diff empty on those paths
   across the campaign); no second value/PnL truth; default workers remain 1
   without explicit opt-in.
8. **Artifact policy clean**: no `runs/**`, label values, Parquet, SQLite, or
   heavy artifacts committed anywhere in the campaign; explicit staging only;
   `git ls-files runs` empty.

Failure handling: a serial-vs-parallel difference, a registry write from a
worker, or an impossible validation is a BLOCKED stop — never a weakened gate,
never a tolerance bump, never a silently narrowed test.
