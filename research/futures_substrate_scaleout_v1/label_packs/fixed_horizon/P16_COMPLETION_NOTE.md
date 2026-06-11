# FUTSUB-P16 Full-Grid Completion Note (coordinator, 2026-06-11)

Context: the FUTSUB-P21 guard audit (BLOCKED, run-local review) verified from
this pack's own committed summary that the full-window fixed-horizon grid had
never been materialized (18/144 bounded-2024 units only) and found one
duplicate `ES_2024_fwd_ret_5m` registry row.

Resolution (per the P21 review's routed repair #1):

1. **Full grid materialized 2026-06-11**: `alpha scaleout label-pack
   --config configs/labels/scaleout/fixed_horizon.json --execute
   --rollout full-window --engine v1 --workers 8` (sanctioned per-family
   policy: fixed_horizon future recomputes on the parity-gated V1 fast path).
   Outcome: **126 completed, 0 skipped, 18 "failed"** — all 18 failures are
   2024 units refused by the registry's fail-closed lineage protection
   ("existing registry record has a mismatched lineage"): they were already
   registered with REFERENCE-engine lineage by the original bounded run and
   were correctly NOT overwritten (preserve-don't-delete). Refreshed
   `coverage_summary.md` reflects this run honestly.
2. **2024 evidence addendum**: a same-config reference-engine pass over the
   2024 slice recorded all 18 units as `skipped` from checkpoint + registry
   truth with their registered row counts —
   `coverage_summary_2024_reference_addendum.md`. Registry surface is
   therefore **144/144 units** (126 v1-lineage + 18 reference-lineage; both
   engines parity-gated, identities engine-invariant).
3. **Duplicate resolved via sanctioned deprecation** (no deletion):
   `lver_66b5e92e…` (orphan of an aborted first bounded pass, registered
   2026-06-09T20:57:56Z) deprecated with reason + provenance, replacement
   `lver_3eda078c…` (the consistent 21:03:17Z batch registration).
   Registry backup taken (`labels.sqlite.bak.20260611T140500Z`, local-only).

The P21 re-run should read this note, the refreshed summary, the 2024
addendum, and `../cost_adjusted/guard_drop_counts.md` (PR #357) to replace
its `INPUT_GAP`/`COUNT_GAP` cells with real counts. No alpha/profitability
claim; counts and registry states only.
