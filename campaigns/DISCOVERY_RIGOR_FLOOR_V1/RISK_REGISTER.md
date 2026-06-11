# DISCOVERY_RIGOR_FLOOR_V1 — Risk Register

| # | Risk | Likelihood | Impact | Mitigation / Gate |
|---|------|-----------|--------|-------------------|
| R1 | Historical Core Pilot evidence mutated (verdicts, ledgers, survivors.json) | Low | Critical | Those paths are forbidden_paths in every phase; annotations are new files in verdict_annotations/; acceptance requires empty git diff over historical dirs; stop_condition BLOCKED on any mutation. |
| R2 | A gate lands open-by-default (enforcement theater) | Medium | Critical | Every gate ships with a bypass canary that fails when neutered; RIGOR-P07 integration audit drives a synthetic study through ALL gates and commits the gate→canary table; reviewer must verify fail-closed paths in the diff. |
| R3 | Surrogate runs contaminate production ledgers/registries | Low | High | Isolated local namespaces only; surrogate_flag threading; tests assert production paths untouched; values local-only. |
| R4 | reason_code becomes free-text drift | Low | Medium | StrEnum validation rejects non-taxonomy values; INCONCLUSIVE without code is a validation error; tests cover both. |
| R5 | Family budgets break existing Core Pilot callers | Medium | Medium | family_budget optional at schema level; entry hook enforces only where declared; regression tests pin current TrialLedger/StudySpec behavior. |
| R6 | promotion_gate.py merge conflicts across P01/P02/P03 | High | Low | conflicts_with serializes the three phases; serial merge queue. |
| R7 | Planted-fake-alpha canary too weak (contamination survives by accident of fixture) | Medium | High | Canary asserts REJECTED outcome, not score deltas; fixture injects unambiguous lookahead (label uses future bar); reviewer scrutinizes the fixture's contamination mechanism. |
| R8 | Surrogate calibration passes a shuffled run and gets rationalized away | Medium | Critical | Declared zero-pass threshold in the committed report; any pass = LEAKAGE_BLOCKED finding requiring diagnosis BEFORE kill-shot resume; rigor_policy encodes this; no waiver path this campaign. |
| R9 | Scope creep into Mining-V2 territory (duplicate-exposure registry, fast lanes, FactorLibrary) | Medium | Medium | Explicit non-goals + REUSE-MAP ruling recorded in GOAL.md; reviewer checks scope match. |
| R10 | FUTSUB run state touched while gated | Low | High | runs/** never staged; FUTSUB research dirs forbidden; resume is coordinator-only post-campaign per the P07 handoff. |
| R11 | Power estimator treated as a promotion gate | Low | Medium | Documented planning-heuristic-only in code + docs; requeue scan emits eligibility, never verdict changes. |

Standing rule: gates are never weakened, tolerances never added, tests never
narrowed to pass; BLOCKED is the honest terminal state for impossible scope.
