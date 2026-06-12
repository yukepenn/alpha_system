---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P034000_POOLED_TRACK_B
lane: yellow
status: in_progress
---

# P034000_POOLED_TRACK_B: pooled-evaluation support + mandatory Track-B registration

## Purpose

Compass v4.4 §3.C: Track B's pooled minimum is now MANDATORY (≥1 cross-symbol
+ ≥1 cross-horizon pooled hypothesis registered BEFORE any Track A metric).
The compass's own honest prior names pooled weak edges the most probable
positive kill-shot outcome, yet `pooled` appears nowhere in src/ — the most
probable win has no mechanism. This phase builds the smallest honest pooled
layer per §2.1 rules.

## Scope (in-bounds)

1. `PooledHypothesisRecord` (governance module, beside study_spec.py —
   compose, don't fork): pooled_hypothesis_id (content-addressed over the
   contract), mechanism_rationale (required non-vague text), pool_kind
   (cross_symbol | cross_horizon | cross_family), fixed member list
   (study_spec_ids or component refs — membership immutable post-registration),
   fixed aggregation rule (start with equal_weight_mean; rule is an enum, not
   free code), fixed horizon/session/symbol set, registered_at,
   registered_before_metrics attestation field, variant_ledger linkage (ONE
   VariantLedger entry per pooled hypothesis — wire through the existing
   VariantLedger API from RIGOR-P02).
2. Validation (fail-closed): §2.1 FORBIDDEN list enforced structurally —
   membership/weights/horizons immutable after registration (content-address
   makes edits a NEW hypothesis; the registry must refuse re-registration of
   a modified payload under the same id and surface the diff); registration
   timestamp must precede any linked Track-A metric artifact (consume a
   metrics-started marker file path that the kill-shot runner will write;
   absent marker = registration allowed).
3. CLI: `alpha governance register-pooled-hypothesis <json>` +
   `alpha governance pooled-hypotheses list --json` (read-only).
4. Aggregation function (pure, tested): given per-component study metric
   records (value-free schema: metric name, point estimate, se/N_eff
   metadata), produce the pooled estimate under the declared rule, reporting
   BOTH pooled result and components (per §2.1 ALLOWED list). No PnL truth,
   no new metric engine — this aggregates existing study outputs.
5. Readiness check: a function + test the P07 readiness checklist can call —
   `track_b_minimum_satisfied()` = ≥1 registered cross_symbol AND ≥1
   cross_horizon pooled hypothesis linked to the kill-shot study set.
6. Two TEMPLATE registrations (committed under
   research/discovery_rigor_floor_v1/track_b/ as DRAFT examples, clearly
   marked NOT-REGISTERED): one cross-symbol (same mechanism pooled over
   ES/NQ/RTY), one cross-horizon (same mechanism pooled over 5m/15m/30m),
   referencing the 6 re-locked rerun-candidate sspec ids from
   research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md.

## Hard constraints

- COMPOSE with TrialLedger/VariantLedger/StudySpec — zero schema rebuilds;
  no changes to existing gate semantics; promotion_gate.py only gains the
  readiness-check helper if needed, never altered behavior for existing paths.
- No runtime/study-execution changes in this phase; no src/alpha_system/
  {features,labels,runtime}/** edits.
- Research-only language (pooled results are evidence for review, never
  promotion by themselves). Explicit staging; no runs/values.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
```

## Done criteria

Registration is content-addressed and immutable; forbidden recompositions
structurally impossible (test-proven: modified payload → new id + refusal
under old id); pre-metric ordering enforced against the marker; aggregation
reports pool + components; readiness check callable; templates committed as
DRAFT; validation green; truthful handoff; fresh adversarial review
PASS/PASS_WITH_WARNINGS under reviews/DISCOVERY_RIGOR_FLOOR_V1/.
