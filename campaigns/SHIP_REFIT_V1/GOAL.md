# SHIP_REFIT_V1 — Goal

## Mission

Lower the **future marginal cost of an honest verdict**. This is the refit earned by
the FUTSUB voyage — not cosmetic cleanup, not generic architecture polish. The voyage
produced a trustworthy 0-survivor negative, but it cost ~5.7 days of wall-clock,
dominated by two avoidable failure classes: codex provider hangs that needed manual
rescue, and a diagnostics/calibration slow-path that materialized a shuffled-label copy
per surrogate seed (VHDX bloat + a ~150h over-provision incident). The voyage also
exposed a **trust gap**: there is no minimum-detectable-effect / power machinery, so a
REJECT and a "never-could-have-resolved" REJECT are formally indistinguishable.

## North Star Alignment

Make future `idea -> verdict` loops cheaper, safer, faster, more standard, and less
dependent on heroic captain intervention — so honest search can run more often, yielding
survivors or clean rejects, on the route to robust OOS, cost-adjusted, capacity-aware,
low-correlation intraday Sharpe.

## Compass v4.5 Justification

Every phase satisfies rule (4): **lower the future marginal cost of an honest verdict in
a concrete, measured way.**

- **P01 Provider-Watchdog** — removes a measured repeated blocker (hang recovery from up
  to 6h to < 2 min).
- **P02 Diagnostics-Fast-Path** — removes the per-seed materialization bloat; a
  surrogate-FDR rerun drops to bounded low-hour/sub-hour time at byte-identical parity.
- **P03 Detection-Power / N_eff rigor** — closes the trust gap so a REJECT is
  distinguishable from underpowered and a rare ACCEPT can be underwritten.
- **P04 (non-gating)** — bounded ops hardening (cleanup automation, runs/ rotation,
  done-check provenance fix, persistent logs).

## Explicitly Out of Scope

Researcher UX / Feature Fast Lane (deferred Option D, gated on a survivor); FactorLibrary;
AlphaBook; broad Mining V2; paid data; paper/live/broker. No new dependency
(numpy/pandas/polars stay absent). No weakening of the truth chain.

## Definition of Campaign Done

P01–P03 merged with their measured acceptance gates met; P04 merged or explicitly
deferred without gating; truth-chain invariants intact (canary fires, surrogate-FDR
zero-pass + constant-factor exclusion preserved, fast-path parity holds); `RUN_SUMMARY`
written. The deliverable is a hardened, power-qualified verdict engine ready for the next
**differentiated** kill-shot.
