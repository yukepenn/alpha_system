---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P035000_REAL_FEE_CONSTANTS
lane: yellow
status: in_progress
---

# P035000_REAL_FEE_CONSTANTS: replace placeholder fee constants with the public CME + broker schedule

## Purpose

Compass v4.4 Stage I pulled-forward item / §3.C readiness precondition 6:
Layer-1 fee parameters in the cost stack are placeholders, making every
net-edge number symbolic. Replace them with real, versioned, source-cited
constants. Zero external spend.

## Scope (in-bounds)

1. Locate the cost-model fee configuration (search src/ + configs/ for the
   cost model: fees/commission/cost_profile — find where zero_cost/base/
   stress_1/stress_2/double_cost profiles source their per-contract fee
   constants).
2. Replace placeholders with a VERSIONED fee schedule (new version id, old
   version retained — fees are versioned per compass §4 cost-stack doctrine)
   for: ES, NQ, RTY (minis) and MES, MNQ, M2K (micros). Components, each a
   separate named constant with a source citation comment: CME exchange fee,
   clearing fee, NFA regulatory fee, and a representative discount-broker
   commission (state the assumption, e.g. "retail discount tier"; use
   publicly documented schedules as of 2026; if exact 2026 numbers are not
   verifiable offline, use the latest verifiable public schedule and mark
   the as-of date — honest sourcing beats fake precision). All-in per-side
   totals should land in the publicly typical ranges (~$0.25-0.85/side
   micros, ~$1.50-3.00/side minis); if your sourced numbers fall outside,
   document why rather than forcing them in.
3. Tests: pin the per-symbol all-in constants (regression against silent
   drift); assert micros < minis per-side; assert the base profile consumes
   the new version while zero_cost stays zero; assert old version still
   resolvable (history append-only).
4. Doc touch: cost-stack section of the relevant docs (search for the cost
   profile documentation) gains a one-paragraph "fee schedule v2 (real
   constants, sourced)" note.

## Hard constraints

- No behavior change to spread/slippage layers; ONLY fee constants + version
  plumbing. No purchases, no network calls in code or tests.
- Versioned: never overwrite the placeholder version in place.
- Explicit staging; research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k "cost or fee" -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance tests/integration -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
```

## Done criteria

Real sourced constants live under a new fee-schedule version consumed by the
base profile; pins + ordering tests green; old version intact; full
validation green; truthful handoff (with sources listed); fresh adversarial
review PASS/PASS_WITH_WARNINGS under reviews/DISCOVERY_RIGOR_FLOOR_V1/.
