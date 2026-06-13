# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/STRATEGY_SHAPED_RESEARCH_LANE_V0`
Workflow: `workflow2`
Status: `ready-to-launch`. SHIP_REFIT_V1 is COMPLETE (verdict engine hardened:
provider-watchdog, diagnostics fast-path 11.4× byte-parity, per-factor MDE/power
+ purge/embargo N_eff). The corrective war council verified alpha_system has **no
generic strategy-shaped research path** (single-primary-factor engine; context==trigger;
no SetupSpec class). This campaign removes that foundational platform blocker.

## Why STRATEGY_SHAPED_RESEARCH_LANE_V0 next

A capability investment (decoupled from any alpha bet): let any human OR AI researcher
express a strategy-shaped hypothesis — context, trigger (SEPARATE from context),
confirmation, invalidation, stop/target/hold-time, horizon, path-label binding — as one
governed `SetupSpec`/`MechanismCard`, explore it as a QUARANTINED EXPLORATORY probe over
the existing path labels + already-wired path-outcome diagnostics, under a pre-registered
FDR budget, and hand promising results to the trusted lane WITHOUT becoming promotion
evidence.

## Phases (minimal; sequential)

- `SSRL-P00` (GREEN) — bootstrap + REUSE-MAP/scope lock.
- `SSRL-P01` (YELLOW) — SetupSpec + MechanismCard contract classes.
- `SSRL-P02` (YELLOW) — context≠trigger conditional probe (additive, path-label outcomes, EXPLORATORY).
- `SSRL-P03` (YELLOW) — first-light example on a small slice + the de-stack probe.
- `SSRL-P04` (YELLOW) — trusted-handoff scaffold + AI-researcher happy-path + PA_GRAMMAR naming docs.

## Hard invariants

EXPLORATORY ≠ promotion evidence (trusted path refuses it); NO research→reference-sim
bridge (reference engine stays the survivor-only PnL truth — no second PnL truth);
single-factor path UNCHANGED (additive only); pre-registered FDR / no grid; NO multi-bar
sequence, NO geometry sweeps, NO feature fast lane (all deferred behind a later trigger);
no new dependency; no new paid data; no paper/live/broker.

## Boundaries

Data ≠ Feature ≠ Factor ≠ Signal ≠ Strategy ≠ Portfolio ≠ Execution. Sandbox/exploratory
≠ promotion evidence. Runtime diagnostics ≠ Strategy Reference validation. Validated
research ≠ paper/live approval. `FactorLibrary` reserved for surviving-alpha memory (a PA
content substrate, if earned, is `PA_GRAMMAR_SUBSTRATE_V1`, separate).

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request (checked before each stage). For live
phase status trust `python tools/frontier/status_doctor.py` / `runs/<run_id>/state.json`,
never this file. Phase branches never write this pointer; the coordinator owns it.
