# SHIP_REFIT_V1 Overview

`SHIP_REFIT_V1` is a Workflow 2 refit campaign for the research harness. Its
purpose is to lower the future marginal cost of an honest verdict by hardening
driver resilience, diagnostics calibration, and power reporting before the next
differentiated kill-shot.

## Scope

- `SHIP_REFIT-P00`: bootstrap the campaign bundle, pointer snapshot, overview,
  and evidence scaffold.
- `SHIP_REFIT-P01`: add provider-watchdog and job-runner resilience; see
  `docs/ship_refit_v1/PROVIDER_WATCHDOG.md`.
- `SHIP_REFIT-P02`: add the diagnostics fast path with parity gating; see
  `docs/ship_refit_v1/DIAGNOSTICS_FAST_PATH.md`.
- `SHIP_REFIT-P03`: add detection-power and effective-sample rigor.
- `SHIP_REFIT-P04`: add non-gating cleanup and provenance hardening.

## Evidence Scaffold

The value-free evidence root is `research/ship_refit_v1/`. It is reserved for
reviewable summaries and indexes from later phases. It must not hold raw data,
canonical data, generated values, local-only run artifacts, provider responses,
secrets, databases, logs, or market-performance claims.

## Boundaries

This campaign is research-harness engineering only. It does not authorize live
trading, paper trading, broker operations, order routing, deployment, account
operations, funding decisions, new alpha ideation, new dependencies, or
profitability/tradability claims. The reference compute engine remains the only
value/accounting truth.
