# ACCEPTANCE — SHIP_REFIT_V1

## Campaign-level invariants (every phase)

- `python tools/hooks/canary_runner.py` is **all-PASS**, including `planted_fake_alpha`
  and the TRUE-alpha detection pair — the truth chain must keep firing.
- The surrogate-FDR **zero-pass criterion** and the **constant-factor (zero-variance)
  exclusion** are preserved; the `spec_index -> seed` mapping is unchanged.
- **No new runtime dependency**: numpy / pandas / polars must remain unimportable
  (`pyproject` `dependencies = []`).
- `git ls-files runs` returns empty; no Parquet/Arrow/SQLite/DB/raw/canonical/secret is
  staged; explicit staging only (no `git add .` / `-A`).
- No edit under any `forbidden_paths` (execution/broker/live/signals/strategies/
  portfolio/l2/backtest/agent_factory + data + binary stores).

## Per-phase acceptance

### P00 (GREEN)
Bundle present + internally consistent; `campaign.yaml` parses; root pointer selects
SHIP_REFIT_V1; smoke + canaries pass; runs/ untracked.

### P01 — Provider-Watchdog (YELLOW)
- A **synthetic futex-hang fixture** is detected and recovered in **< 2 minutes** (was up
  to 6h) via the existing `handle_provider_nonzero` / `WAITING_PROVIDER_LIMIT` resume path.
- A **benign slow provider** (CPU ticks advancing or events growing) is **NOT** killed.
- `frontier.yaml` `timeout_seconds` == `3600`.
- `PROVIDER_HANG_DETECTED` is emitted on detection; first-light check callable.
- Watchdog regression tests pass; canaries all-PASS.

### P02 — Diagnostics Fast-Path (YELLOW)
- **PARITY GATE (hard):** byte-identical `diagnostic_summary` hashes, fast-path vs
  reference path, on a fixed locked sample for **≥ 10 seeds**. Fast-path is INVALID
  otherwise.
- No per-seed shuffled-label copy is written to disk; permutation-index indirection used.
- Measured calibration **wall-clock AND disk write-count reduced ≥ 10×** at parity.
- Constant-factor exclusion + `spec_index -> seed` mapping preserved; numpy/pandas/polars
  still absent; canaries all-PASS.

### P03 — Detection-Power / N_eff (YELLOW)
- Every REJECT/ACCEPT carries an explicit **"could have detected IC down to X"** power
  statement.
- `n_eff.py` folds **at least purge/embargo** (no longer purely first-order).
- The coordinator **A-vs-B settler** result is recorded; if it returned NONZERO, the
  minimal interaction/gating detector is added and tested before done.
- Detection threshold + surrogate-FDR zero-pass unchanged unless the settler required the
  interaction detector; canaries all-PASS.

### P04 — Cleanup / Provenance (GREEN, non-gating)
Post-merge step prunes stale worktrees; runs/ growth bounded by rotation; executor
done-check no longer attempts reviewer-owned `reviews/` paths; logs persist outside
`/tmp`. The campaign was **not** gated on this wave.

## Campaign done

P01–P03 merged with the above met; P04 merged or explicitly deferred without gating;
`RUN_SUMMARY` written; no profitability/tradability claim anywhere.
