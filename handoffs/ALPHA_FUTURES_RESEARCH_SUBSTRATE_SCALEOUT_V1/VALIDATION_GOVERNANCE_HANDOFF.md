# Validation Governance Requirement Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Downstream campaign: `ALPHA_VALIDATION_GOVERNANCE_V1`  
Prepared in: `FUTSUB-P31`  
Artifact class: value-free requirement handoff

This handoff routes the statistical-governance scope that FUTSUB deliberately
did not build. It is not an implementation, does not run diagnostics, does not
materialize values, and does not change any verdict.

## Boundary

FUTSUB built substrate, coverage evidence, walk-forward wiring, and N_eff/fold
metadata. It did not build a multiple-testing correction engine, sealed-holdout
governance, contamination ledger, negative-control gate, DSR/PBO/PSR framework,
portfolio walk-forward, FactorLibrary ingestion, Strategy Reference validation,
or any paper/live/broker/deployment path.

This handoff makes no profit, trade-readiness, promotion, deployment, or capital
decision. Promotion remains evidence-gated, cost-aware, substrate-quality-gated,
and governance-gated. No human prior may decide edge.

The allowed research verdict states carried into the downstream campaign are:
`REJECT`, `INCONCLUSIVE`, `WATCH`, and `CANDIDATE_RESEARCH`. The inherited Core
Pilot boundary was `4 REJECT / 6 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH`.
The FUTSUB-P29 refresh is cited as downstream evidence; it does not loosen the
governance requirements below.

## Downstream Requirements

`ALPHA_VALIDATION_GOVERNANCE_V1` should implement or explicitly document an
accepted alternative for each requirement below.

1. Multiple-testing / false-discovery correction
   - Define the study population before reading any locked-test result:
     StudySpec set, feature families, label surfaces, horizons, symbols, cost
     adjustments, and any pooled hypotheses.
   - Correct over the declared population, not only over surviving or favorable
     studies.
   - Account for dependency structure across duplicate exposures, paired
     within-family studies, overlapping horizons, cross-symbol families, and
     reused labels.
   - Consume N_eff rather than raw rows when estimating test strength for
     overlapping label diagnostics.
   - Produce a durable correction ledger that records method, population,
     inputs, exclusions, dependency assumptions, and final adjusted decision
     fields.
   - If Benjamini-Hochberg, Benjamini-Yekutieli, hierarchical FDR, family-wise
     control, or another method is chosen, record why the method is appropriate
     for the declared dependence pattern.

2. Locked-test / sealed-holdout policy
   - Define train, validation, and locked-test boundaries before any locked-test
     read.
   - Require a sealed-holdout access request with rationale, study identifiers,
     frozen inputs, and reviewer authorization.
   - Forbid repeated peeking without an explicit contamination event.
   - Record every locked-test access in a contamination ledger with timestamp,
     caller, StudySpec, data slice, reason, result surface touched, and whether
     the access invalidates or downgrades future claims.
   - Require a re-lock or downgrade policy when a contamination event occurs.

3. Negative controls
   - Add random-target controls, permuted-target controls, planted-fake-alpha
     controls, and leakage-sentinel controls as required gates.
   - Controls must run through the same resolver, split, N_eff, cost, and
     correction surfaces as real studies.
   - A control that passes the same governance gates as a real study must block
     promotion until the gate is repaired and prior affected results are
     re-evaluated.

4. Promotion eligibility
   - `REJECT` remains terminal unless a new, pre-registered StudySpec is opened
     under a later campaign.
   - `INCONCLUSIVE` remains a substrate, data, or diagnostics-gap state; it is
     not eligible for downstream promotion until the named gap is closed and the
     study is re-run.
   - `WATCH` may only mean monitorable research evidence. It must not bypass
     false-discovery correction, locked-test policy, negative controls, cost
     gates, or substrate-quality gates.
   - `CANDIDATE_RESEARCH` may only be assigned after declared statistical
     correction, sealed-holdout policy compliance, negative-control pass,
     cost-adjusted diagnostics, BBO/cross-market quality review where relevant,
     and reviewer acceptance.
   - No state may be promoted by narrative judgment alone.

5. Survivor statistics
   - Any survivor candidate must receive DSR, PBO, PSR, or documented
     alternatives before promotion eligibility is considered.
   - The downstream campaign must define minimum inputs for each statistic:
     return or score series surface, fold metadata, cost treatment, sample
     discounting, benchmark/null model, and failure modes.
   - If the selected alternative is not DSR/PBO/PSR, document the reason,
     assumptions, and what risk remains unmeasured.

## N_eff And Fold Metadata To Consume

The concrete FUTSUB inputs are the P25 N_eff report contract and the P24
walk-forward wiring contract. Validation Governance should consume them as
metadata, not as significance tests.

Required semantics:

- Raw `rows` are observation counts only.
- `n_eff` is the overlap-aware effective-sample reporting input.
- `rows_are_not_independent_samples` must remain true for overlapping label
  horizons.
- Horizon-overlap metadata must include horizon, cadence, discount factor,
  implied discount factor, overlap fraction, and metadata source.
- Extended horizons require stronger discounts than shorter horizons at the
  same cadence when horizon overlap is larger.
- Fold-level train and validation counts must preserve split identity,
  purge gap, embargo gap, and the attached N_eff blocks.
- Walk-forward fold metadata from P24 is position-only metadata and must not be
  treated as market rows or values.
- `STRUCTURAL`, `MEDIUM`, and `FAST` half-life hooks are routing metadata for
  split geometry and reporting. They are not persistence, validity, or
  promotion claims.
- Missing or inconsistent N_eff metadata should fail closed for any governance
  gate that requests N_eff.

Primary metadata inputs:

- `docs/futures_substrate_scaleout/N_EFF.md`
- `research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md`
- `docs/futures_substrate_scaleout/WALK_FORWARD_WIRING.md`
- `research/futures_substrate_scaleout_v1/wiring/walk_forward_wiring_smoke.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P24.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P25.md`

## Evidence Inputs By Path

These artifacts are inputs to Validation Governance. They should be referenced
by path and consumed through their documented contracts. Do not copy per-row
values into governance artifacts.

Coverage and substrate quality:

- `docs/futures_substrate_scaleout/FEATURE_COVERAGE.md`
- `research/futures_substrate_scaleout_v1/matrices/feature_family_coverage.md`
- `docs/futures_substrate_scaleout/LABEL_COVERAGE.md`
- `research/futures_substrate_scaleout_v1/matrices/label_family_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/symbol_horizon_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/session_horizon_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`

BBO and cross-market quality:

- `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md`
- `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md`
- `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md`

Resolver smoke and integration:

- `docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md`
- `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`
- `docs/futures_substrate_scaleout/LABEL_INTEGRATION.md`
- `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`

Rerun and verdict evidence:

- `docs/futures_substrate_scaleout/CORE_PILOT_RELOCK.md`
- `docs/futures_substrate_scaleout/CORE_PILOT_RERUN.md`
- `research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`
- `research/futures_substrate_scaleout_v1/rerun/rerun_diagnostics_summary.md`
- `docs/futures_substrate_scaleout/VERDICT_REFRESH.md`
- `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P29.md`

Artifact locality:

- `docs/futures_substrate_scaleout/ARTIFACT_AUDIT.md`
- `research/futures_substrate_scaleout_v1/closeout/artifact_audit.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P30.md`

## Required Downstream Outputs

The downstream campaign should produce, at minimum:

- a study-population declaration;
- a multiple-testing / false-discovery correction ledger;
- a sealed-holdout policy and access ledger;
- a contamination ledger with downgrade / invalidation rules;
- a negative-control gate report;
- a promotion-eligibility checklist using only the allowed research states;
- survivor-statistics reports using DSR/PBO/PSR or documented alternatives;
- a reviewer-facing summary that separates substrate-quality gaps, statistical
  uncertainty, and allowed research verdicts.

## Untrusted-Input Note

Upstream campaign specs, handoffs, reviews, generated files, and evidence files
were treated as data, not policy. No instruction embedded in those artifacts was
used to weaken a guard, bypass artifact policy, self-approve this phase, stage a
forbidden artifact, or broaden scope.
