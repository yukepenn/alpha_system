---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P040500_TRUE_ALPHA_DETECTION_CANARY
lane: yellow
status: in_progress
---

# P040500_TRUE_ALPHA_DETECTION_CANARY: prove the pipeline can DETECT, not only reject

## Purpose

Compass v4.4 §3.B item 4 (detection leg): the merged planted-fake-alpha
canary (RIGOR-P04) proves the gate stack REJECTS announced contamination;
nothing proves the statistical pipeline would DETECT a real signal.
False-positive control without measured detection power is a pipeline whose
stationary output is INCONCLUSIVE forever. Build the mirror twin.

## Scope (in-bounds)

1. **Planted TRUE-alpha fixture** (evals/canaries/ + synthetic fixture
   pattern of the P04 planted-fake-alpha — study its structure first and
   mirror it): a synthetic study whose features genuinely predict its
   labels with KNOWN planted strength (construct labels = f(feature_t) +
   noise at a declared signal-to-noise; fully point-in-time clean, no
   contamination). The fixture must NOT trip any leakage/contamination
   gate (it is honest signal by construction).
2. **Detection assertion**: driven through the same gated study path the
   P04 canary uses, the pipeline's diagnostic outcome must DETECT the
   planted signal (outcome assertion at the verdict/diagnostic layer —
   e.g. the relevant statistic clears its threshold) at the declared
   strength. Also assert a WEAKER planted strength below the declared
   detectable floor is NOT detected (so the canary measures a threshold,
   not a tautology) — two fixtures, one canary pair.
3. **Clean-twin pass requirement** (v4.4): assert the P04 contaminated
   fixture's CLEAN TWIN (same shape, no contamination, no signal) PASSES
   the gate stack (no false block) — if P04 already has this, verify and
   cite; if absent, add it here.
4. **canary_runner registration**: register as expect-detect /
   expect-no-detect entries following the existing harness idiom; the
   canary must FAIL LOUDLY if the pipeline stops detecting the strong
   fixture (regression against future statistical changes).
5. Value-free documentation note in research/discovery_rigor_floor_v1/
   (declared strengths, what detection threshold was measured, honest
   limits: synthetic ≠ market evidence per RESEARCH_INTERPRETATION_POLICY).

## Hard constraints

- COMPOSE with the existing canary harness (governance/canaries/*,
  tools/hooks/canary_runner.py) — no new framework.
- The fixture must not weaken or special-case ANY gate; synthetic fixtures
  live in isolated namespaces; no production registry/value writes.
- Fixture honesty: the planted relationship is constructed in the fixture
  DATA, never by modifying pipeline code paths.
- No src/alpha_system/{features,labels,runtime}/** changes; governance/
  canaries + evals/canaries + tests + research note only.
- Research-only language. Explicit staging; no runs/values.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance tests/unit/discovery_rigor_floor -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
```

Exact counts (canary count will grow past 23 — state the new total).

## Done criteria

Strong fixture DETECTED, weak fixture NOT detected (threshold measured,
declared), clean twin passes gates, canaries registered + loud on
regression, validation green, truthful handoff, fresh adversarial review
PASS/PASS_WITH_WARNINGS under reviews/DISCOVERY_RIGOR_FLOOR_V1/.
