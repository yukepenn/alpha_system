# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/SHIP_REFIT_V1`
Workflow: `workflow2`
Status: `ready-to-launch`. The FUTSUB substrate-scaleout campaign is COMPLETE
(34/34, run `2026-06-07T235209Z_...`); its first kill-shot produced **0
survivors** (4 distinct legacy mechanisms REJECT at near-zero IC — a conservative,
power-qualified negative, method integrity intact). The ultracode war council
adjudicated the next path as `SHIP_REFIT_V1` (scoped) — the voyage-earned refit
that lowers the future marginal cost of an honest verdict.

## Why SHIP_REFIT_V1 next (not broad mining)

Survivor-gate = 0 ⇒ DIAGNOSE, do not build by inertia. The dominant voyage cost
was verdict **cost** (codex provider hangs; per-seed materialized shuffled-label
calibration bloat) AND verdict **trust** (no MDE/power machinery; first-order
N_eff). SHIP_REFIT closes both before the next, *differentiated* kill-shot.

## Campaign Identity

- Campaign ID: `SHIP_REFIT_V1`
- Contract bundle: `campaigns/SHIP_REFIT_V1/`
- Scheduler: `dag_wave`, serial merge queue (DAG linearizes to sequential —
  P01 holds a global path).

## Phases (3 load-bearing + bootstrap + non-gating cleanup)

- `SHIP_REFIT-P00` (GREEN) — bootstrap / pointer.
- `SHIP_REFIT-P01` (YELLOW) — Provider-Watchdog / job-runner resilience
  (hang recovery from up to 6h to <2 min).
- `SHIP_REFIT-P02` (YELLOW) — Diagnostics-Fast-Path (pure-Python permutation-index,
  byte-identical parity gate, ≥10× calibration speedup).
- `SHIP_REFIT-P03` (YELLOW) — Detection-Power / N_eff rigor (MDE + purge/embargo +
  per-factor power statement). A-vs-B settler = NULL ⇒ bounded, no interaction detector.
- `SHIP_REFIT-P04` (GREEN, non-gating) — cleanup / provenance second wave.

## Boundaries

In scope: harness/diagnostics hardening only. Out of scope: new alpha ideation,
FactorLibrary/AlphaBook/Research Runner, researcher-UX/Feature-Fast-Lane, paid
data, paper/live/broker, any new dependency (numpy/pandas/polars stay absent).
No profitability/tradability claim. Truth-chain invariants preserved (canary
fires, surrogate-FDR zero-pass + constant-factor exclusion held, fast-path
parity-gated).

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
every stage transition. Resume continues from recorded run state. For live phase
status, trust `python tools/frontier/status_doctor.py` /
`runs/<run_id>/state.json`, never this file. Phase branches never write this
pointer; the coordinator owns it.
