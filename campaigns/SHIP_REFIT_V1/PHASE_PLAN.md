# PHASE_PLAN — SHIP_REFIT_V1

5 phases (`SHIP_REFIT-P00` … `SHIP_REFIT-P04`) on a `dag_wave` scheduler with
`parallel_execution: true`, `max_parallel_phases: 2`, and a **serial merge queue**.
Phase ids, lanes, dependencies, allowed_paths, and DAG metadata are the source of truth
in `campaign.yaml`; this file mirrors them and adds the human-readable contract. Any
disagreement between the two files is a STOP condition.

## Scheduling Note (verified against `frontier-plan` plan-dag)

The phases write **disjoint module footprints** and write **no registry**, so P01 and P02
are *declared* `parallel_safe`. However, `plan-dag` **linearizes the DAG to effectively
sequential**, and this is intended/accepted:

- **P01** holds a **global/coordinator path** (`frontier.yaml`), so the scheduler
  conservatively forces it to **run alone** — it cannot share a wave.
- **P02** is parallel-capable but has **no eligible partner** (P01 runs alone; P03
  depends on P02).
- **P03** depends on P02 (folds power/MDE into the fast-path diagnostics); **P04**
  (non-gating) depends on P01+P02+P03 and trails.

Net effect: `P00 → P01 → P02 → P03 → P04`, one PR at a time. The negligible 5-phase
parallelism gain is not worth contorting the design (e.g. splitting the 1-line
`frontier.yaml` change into its own phase); correctness and disjoint review boundaries
win. `dag_wave`/`max_parallel_phases: 2` remain declared so future width is available.

P01 footprint: `tools/frontier/{command_runner,ralph_driver}.py`, `frontier.yaml`,
`tests/frontier/**`. P02 footprint: `src/alpha_system/governance/surrogate_run.py`,
`tools/discovery_rigor_floor/run_real_surrogate_calibration.py`,
`src/alpha_system/research/**`, `tests/**`.

## Scheduler Wave Map (as resolved by plan-dag)

```text
Wave 0 : SHIP_REFIT-P00     (bootstrap / contract / pointer; run-alone)
Wave 1 : SHIP_REFIT-P01     (driver watchdog; run-alone — holds frontier.yaml)
Wave 2 : SHIP_REFIT-P02     (diagnostics fast-path; parity-gated)
Wave 3 : SHIP_REFIT-P03     (power / N_eff rigor; depends on P02; settler-amended scope)
Wave 4 : SHIP_REFIT-P04     (non-gating cleanup / provenance; trails)
```

## Phases

### SHIP_REFIT-P00 — Campaign Bootstrap (GREEN)
Land the 6-file bundle, the `docs/ship_refit_v1/` scaffold, and the root pointer. YAML
parses; smoke + canaries pass; `git ls-files runs` empty.

### SHIP_REFIT-P01 — Provider-Watchdog / Job-Runner Resilience (YELLOW)
Liveness sampler in `command_runner.py` (CPU ticks via `/proc/<pid>/stat` + `events.jsonl`
growth); `start_new_session=True` + `os.killpg` on (wall>60s ∧ cpu_delta≈0 ∧ no events);
emit `PROVIDER_HANG_DETECTED`; route to the **existing** `handle_provider_nonzero` /
`WAITING_PROVIDER_LIMIT` resume path (8 call sites). Lower `frontier.yaml`
`timeout_seconds` 21600→3600. Fold in a ~10-line first-light check (resolver-smoke +
canary_runner). **Accept:** synthetic futex-hang recovers <2 min (was up to 6h); a benign
slow provider is not killed; canaries all-PASS.

### SHIP_REFIT-P02 — Diagnostics Fast-Path (YELLOW)
Replace per-seed `write_label_shuffled_copy` materialization (`surrogate_run.py`
~481-492, 865) with align-once panel + **permutation-INDEX** per seed (pure Python — no
numpy/pandas/polars) + batched IC/RankIC/bucket/detection-stat across K seeds. 1-line
default-K cap. **Accept:** PARITY GATE — byte-identical `diagnostic_summary` hashes vs the
reference path on a fixed locked sample (≥10 seeds); constant-factor exclusion +
spec_index→seed mapping preserved; wall-clock **and** disk write-count ↓≥10× at parity.

### SHIP_REFIT-P03 — Detection-Power / N_eff Rigor (YELLOW)
Per-study MDE / SE(IC) + a "could have detected IC down to X" power statement on every
verdict; fold ≥ purge/embargo into `n_eff.py`. **Settler result = NULL** (coordinator
2026-06-13): conditional uplift ~1e-6 at full power, gate is not interaction-blind → P03
stays **bounded**, no interaction detector. One bounded refinement folded in from the
settler's distinct *stacking-blindness* finding: **report MDE/power per-factor, not only
stacked** (stacked IC can dilute a single factor — e.g. the settler saw one vwap_session
factor diverge from the stacked ~0; treated as an unverified small-sample hypothesis for
the next kill-shot, not a survivor). **Accept:** every verdict carries a power statement;
N_eff folds purge/embargo; per-factor power reported; settler result recorded.

### SHIP_REFIT-P04 — Second-Wave Cleanup / Provenance (GREEN, non-gating)
Worktree `clean_stale`/`cleanup_after_merge` in the post-merge step + `just
frontier-clean`; runs/ rotation + STOP-prune; done-check provenance-path fix; `/tmp` →
`$ALPHA_SYSTEM_ROOT/.tmp`. **Accept:** stale worktrees pruned post-merge; runs/ bounded;
executors stop writing reviewer-owned paths; campaign NOT gated on this wave.
