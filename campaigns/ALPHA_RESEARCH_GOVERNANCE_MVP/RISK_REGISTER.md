# ALPHA_RESEARCH_GOVERNANCE_MVP Risk Register

## Purpose

This register records the campaign-specific risks for the admissibility and
evidence-governance protocol, with detection methods, mitigations, owners, related
phases, and blocking conditions. Because this campaign is the gate that future AI alpha
research must pass through, most risks here are about **governance integrity** — the
machinery silently failing open, or prohibited scope/claims slipping in — rather than
market risk. Ralph must treat every "Blocking condition" as a hard STOP/merge-block.

## Severity Scale

* **S1 Critical** — corrupts the admissibility guarantee or commits forbidden artifacts; campaign cannot be accepted.
* **S2 High** — materially weakens a gate, guard, or audit trail.
* **S3 Medium** — local correctness or clarity issue with contained impact.
* **S4 Low** — cosmetic or documentation-only issue.

## Likelihood Scale

* **L1 Rare** — unlikely given current controls.
* **L2 Possible** — plausible without explicit attention.
* **L3 Likely** — expected if not actively prevented.

## Risk Status Values

* **Open** — active and monitored.
* **Mitigated** — controls in place; residual risk accepted.
* **Closed** — no longer applicable.

## Risk Table Summary

| ID | Risk | Severity | Likelihood | Related Phases | Status |
| -- | ---- | -------- | ---------- | -------------- | ------ |
| R-001 | AlphaSpec too vague | S2 | L3 | P03, P04 | Open |
| R-002 | Pre-registration bypass | S1 | L2 | P03, P04, P11 | Open |
| R-003 | FeatureRequest duplicates existing factor | S2 | L3 | P05 | Open |
| R-004 | LabelSpec permits leakage | S1 | L2 | P06, P14 | Open |
| R-005 | StudySpec allows uncontrolled variant mining | S2 | L3 | P07, P08 | Open |
| R-006 | TrialLedger omits failed runs | S1 | L3 | P08, P11 | Open |
| R-007 | EvidenceBundle missing manifest / hashes / versions | S1 | L2 | P09 | Open |
| R-008 | PromotionGate allows unreviewed candidate | S1 | L2 | P11, P12 | Open |
| R-009 | Reviewer independence broken | S1 | L2 | P12 | Open |
| R-010 | Negative controls do not fail closed | S1 | L2 | P13, P14 | Open |
| R-011 | No-lookahead audit incomplete | S1 | L2 | P06, P14 | Open |
| R-012 | Locked-test contamination unrecorded | S2 | L2 | P07, P08, P11 | Open |
| R-013 | Raw data or heavy artifacts committed | S1 | L2 | all | Open |
| R-014 | Alpha claim appears in docs | S1 | L2 | P17, all | Open |
| R-015 | Workflow 2 handoff missing | S2 | L2 | all, P19 | Open |
| R-016 | campaign.yaml / PHASE_PLAN mismatch | S1 | L2 | P00, all | Open |
| R-017 | Agent permissions too broad | S2 | L2 | P15, P16 | Open |
| R-018 | Real data / broker / live scope creep | S1 | L2 | all | Open |
| R-019 | Tests weakened to pass | S1 | L2 | all | Open |
| R-020 | Human approval bypassed for future capital/live decisions | S1 | L1 | P11, P19 | Open |

---

# Detailed Risk Entries

## R-001 — AlphaSpec too vague

### Description
An AlphaSpec is registered with empty or hand-wavy fields (vague data assumptions, no exclusion rules, no expected failure modes, no promotion criteria), so the no-code gate passes on content that is not actually a pre-registration.

### Impact
Implementation proceeds against an under-specified idea, defeating the admissibility guarantee. S2.

### Likelihood
L3 — agents tend to write minimal specs to unblock themselves.

### Detection
* AlphaSpec validation requiring non-trivial required fields.
* Claude Opus review of spec substance.
* End-to-end dry run asserting weak specs are rejected.

### Mitigation
Fail-closed validation with substantive required fields; reviewer checks that data/timestamp/cost assumptions, exclusion rules, expected failure modes, and promotion criteria are concrete.

### Owner
Claude Opus (review) / Codex (validation).

### Related Phases
ARGOV-P03, ARGOV-P04.

### Blocking Condition
A spec with missing/empty required fields validates as registered.

---

## R-002 — Pre-registration bypass

### Description
Code or diagnostics proceed without a registered HypothesisCard + AlphaSpec, or the registration timestamp is back-dated after results are known.

### Impact
Eliminates the falsification anchor; turns the system into post-hoc rationalization. S1.

### Likelihood
L2.

### Detection
* `DRAFT → REGISTERED` requires both card and spec.
* State-machine tests; promotion gate cross-checks registration precedes implementation.
* Claude review of ordering.

### Mitigation
No-code gate keyed to registration; registration linkage enforced; timestamps recorded at registration.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P03, ARGOV-P04, ARGOV-P11.

### Blocking Condition
Implementation or diagnostics reachable without prior pre-registration.

---

## R-003 — FeatureRequest duplicates existing factor

### Description
A FeatureRequest re-creates an exposure already present in the factor registry, producing silent duplicate factors and inflating apparent breadth.

### Impact
Duplicate/equivalent exposures distort breadth and multiple-testing accounting. S2.

### Likelihood
L3.

### Detection
* Duplicate/equivalent exposure guard reading the factor registry read-only.
* Tests with synthetic duplicate fixtures.
* Claude review.

### Mitigation
Mandatory duplicate-exposure notes; guard surfaces likely duplicates as blocking-or-warning metadata.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P05.

### Blocking Condition
FeatureRequest accepted with no duplicate-exposure check against the registry.

---

## R-004 — LabelSpec permits leakage

### Description
A LabelSpec allows a label to be used as a feature, or permits features computed after the label availability time, leaking future information.

### Impact
Future leakage invalidates any downstream study. S1.

### Likelihood
L2.

### Detection
* Label-leakage guard; forbidden-feature-overlap checks.
* `tests/no_lookahead` cases.
* Canary harness label-leakage canary (P14).

### Mitigation
Fail-closed leakage checks on overlap and availability time; no-lookahead tests; leakage canary fails closed.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P06, ARGOV-P14.

### Blocking Condition
Label-as-feature overlap or post-availability features pass validation.

---

## R-005 — StudySpec allows uncontrolled variant mining

### Description
A StudySpec declares no variant budget or an unbounded one, enabling silent variant mining without multiple-testing accounting.

### Impact
Overfitting via unrecorded variant search. S2.

### Likelihood
L3.

### Detection
* StudySpec requires a declared variant budget.
* TrialLedger accumulates variant counts; budget overruns flagged.
* Claude review.

### Mitigation
Mandatory variant budget and stopping rules; ledger cross-checks variant counts against the budget.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P07, ARGOV-P08.

### Blocking Condition
StudySpec validates with no variant budget, or variant overruns are not flagged.

---

## R-006 — TrialLedger omits failed runs

### Description
Failed or abandoned trials are not recorded, hiding the denominator of the search and inflating apparent success.

### Impact
Survivorship bias; false confidence. S1.

### Likelihood
L3.

### Detection
* Ledger tests asserting failed runs are recorded.
* Promotion gate cross-checks ledger completeness.
* Claude review and semantic done-check.

### Mitigation
Failed-run visibility enforced; promotion blocked if failed-run omission is possible.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P08, ARGOV-P11.

### Blocking Condition
A trial path exists that can omit failed runs from the ledger.

---

## R-007 — EvidenceBundle missing manifest / hashes / versions

### Description
An EvidenceBundle is accepted without a manifest, code/config hashes, or data/factor/label versions, breaking reproducibility.

### Impact
Irreproducible evidence; candidate cannot be audited. S1.

### Likelihood
L2.

### Detection
* Bundle validation requiring manifest, hashes, versions, negative-control results.
* Tests; Claude review.

### Mitigation
Fail-closed manifest contract; candidate state requires a complete bundle.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P09.

### Blocking Condition
A candidate exists with an incomplete or missing evidence manifest.

---

## R-008 — PromotionGate allows unreviewed candidate

### Description
The promotion gate transitions to CANDIDATE/VALIDATED without an EvidenceBundle, TrialLedger refs, or a ReviewerVerdict.

### Impact
Unreviewed/unsupported promotion enters the pipeline. S1.

### Likelihood
L2.

### Detection
* Promotion gate tests for each required precondition.
* End-to-end dry run asserts blocks.
* Claude review.

### Mitigation
Gate requires evidence + trial refs + independent verdict before candidate/validated.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P11, ARGOV-P12.

### Blocking Condition
Candidate/validated reachable without evidence, trial refs, or reviewer verdict.

---

## R-009 — Reviewer independence broken

### Description
The implementer reviews their own work, or the reviewer role equals the implementer role, defeating independent verification.

### Impact
Self-approval defeats the review gate. S1.

### Likelihood
L2.

### Detection
* Reviewer-independence tests; role comparison at the gate.
* Independence statement required on every verdict.
* Claude review.

### Mitigation
Gate rejects verdicts where reviewer == implementer; independence statement mandatory.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P12.

### Blocking Condition
A self-approved verdict can promote an idea.

---

## R-010 — Negative controls do not fail closed

### Description
Random/permuted/future-shift/optimistic-fill canaries pass when they should fail, so the guards they protect are silently broken.

### Impact
Broken guards go undetected; leakage/optimism slips through. S1.

### Likelihood
L2.

### Detection
* Canary tests asserting fail-closed behavior.
* `python tools/hooks/canary_runner.py`.
* End-to-end dry run.

### Mitigation
Each canary asserts the injected fault is caught; canary runner gates merge.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P13, ARGOV-P14.

### Blocking Condition
A negative control passes without detecting its injected fault.

---

## R-011 — No-lookahead audit incomplete

### Description
The no-lookahead / availability-time coverage is partial, leaving leakage paths unaudited.

### Impact
Lookahead leakage in future studies. S1.

### Likelihood
L2.

### Detection
* `tests/no_lookahead` coverage; future-shift canary.
* Claude review of coverage.

### Mitigation
No-lookahead tests plus a future-shift canary that fails closed; review confirms coverage.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P06, ARGOV-P14.

### Blocking Condition
No-lookahead coverage missing for label/feature availability semantics.

---

## R-012 — Locked-test contamination unrecorded

### Description
OOS or locked test data is reused without being flagged, contaminating the held-out evaluation silently.

### Impact
Held-out evaluation loses meaning; optimistic bias. S2.

### Likelihood
L2.

### Detection
* `oos_touched_flag` and `locked_test_contamination_flag` in the ledger.
* Promotion gate blocks unrecorded contamination.
* Claude review.

### Mitigation
Contamination flags mandatory; locked-test policy declared in StudySpec; promotion blocked when contamination is unrecorded.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P07, ARGOV-P08, ARGOV-P11.

### Blocking Condition
OOS/locked-test reuse can occur without a recorded contamination flag.

---

## R-013 — Raw data or heavy artifacts committed

### Description
Raw/canonical/factor/label data, parquet, local DBs, logs, caches, or `runs/**` are staged or committed.

### Impact
Repository pollution and policy violation; potential data exposure. S1.

### Likelihood
L2.

### Detection
* `git ls-files runs`; `find data`/`find metadata`/`find artifacts` audits.
* Parquet/DB grep; pre-merge artifact audit.
* Claude review.

### Mitigation
Explicit staging only; artifact audit before merge; never_commit globs enforced.

### Owner
Ralph / Codex.

### Related Phases
All phases.

### Blocking Condition
Any forbidden data/DB/artifact/`runs` path is staged.

---

## R-014 — Alpha claim appears in docs

### Description
Docs, templates, reports, or summaries assert alpha/profitability/tradability/production readiness.

### Impact
Unsupported market claim; violates research-interpretation policy. S1.

### Likelihood
L2.

### Detection
* Unsupported-claim guard; prohibited-claim tests; doc grep.
* Claude review.

### Mitigation
Claim guard fails closed on prohibited language; report templates carry no-claims language.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P17, all phases.

### Blocking Condition
Any prohibited alpha/profitability/tradability/production claim appears.

---

## R-015 — Workflow 2 handoff missing

### Description
A phase merges without a complete commit-eligible handoff, breaking the audit trail.

### Impact
Lost provenance and review context. S2.

### Likelihood
L2.

### Detection
* Handoff presence check per phase.
* Merge gate requires handoff validation.
* Claude review.

### Mitigation
`handoff_required: true` per phase; merge blocked without a valid handoff.

### Owner
Ralph / Codex.

### Related Phases
All phases, especially ARGOV-P19.

### Blocking Condition
A phase reaches merge without a valid handoff.

---

## R-016 — campaign.yaml / PHASE_PLAN mismatch

### Description
Phase IDs, names, lanes, dependencies, or acceptance-gate coverage diverge between `campaign.yaml` and `PHASE_PLAN.md`.

### Impact
Ambiguous contract; Ralph may select or gate incorrectly. S1.

### Likelihood
L2.

### Detection
* campaign.yaml validation script (gate coverage, unique ids).
* PHASE_PLAN cross-check; Claude review.

### Mitigation
Single source of truth for machine (`campaign.yaml`); cross-file consistency check before execution.

### Owner
Claude Opus / Codex.

### Related Phases
ARGOV-P00, all phases.

### Blocking Condition
Any ID/name/lane/dependency/gate mismatch between the two files.

---

## R-017 — Agent permissions too broad

### Description
The governance CLI/tools or registry integration grant agents the ability to bypass gates (e.g. force-promote, edit ledgers, self-approve).

### Impact
Gate bypass via tooling. S2.

### Likelihood
L2.

### Detection
* CLI/tool tests asserting gates cannot be bypassed.
* Registry write-path review.
* Claude review.

### Mitigation
CLI enforces gates; no force-promote/self-approve path; least-privilege write paths.

### Owner
Codex / Claude Opus.

### Related Phases
ARGOV-P15, ARGOV-P16.

### Blocking Condition
A CLI/tool/registry path bypasses a governance gate.

---

## R-018 — Real data / broker / live scope creep

### Description
Real data ingestion, IBKR connectivity, broker/live/paper code, order routing, L2 replay, ML/DL, strategy optimization, or portfolio allocation is introduced.

### Impact
Out-of-scope, high-risk scope enters before governance is complete. S1.

### Likelihood
L2.

### Detection
* Forbidden-path/global-forbidden audits; dependency audit.
* Claude review; stop conditions.

### Mitigation
Global forbidden paths; stop-and-escalate on broker/live/real-data scope.

### Owner
Ralph / Claude Opus.

### Related Phases
All phases.

### Blocking Condition
Any real-data/broker/live/paper/order-routing/L2-replay/ML scope appears.

---

## R-019 — Tests weakened to pass

### Description
Tests are removed, skipped, or relaxed to make a phase pass without authorization.

### Impact
False green; guarantees silently eroded. S1.

### Likelihood
L2.

### Detection
* Diff review of test changes; Claude review; semantic done-check.

### Mitigation
Test removals/relaxations require explicit phase scope and review; fake completion forbidden.

### Owner
Claude Opus / Codex.

### Related Phases
All phases.

### Blocking Condition
Tests weakened without explicit phase authorization and review.

---

## R-020 — Human approval bypassed for future capital/live decisions

### Description
The governance layer implies or enables a path to live approval, capital allocation, or production readiness without explicit human authorization.

### Impact
Crosses the human-judgment boundary the campaign is meant to protect. S1.

### Likelihood
L1 — explicitly out of scope, but high impact if it occurs.

### Detection
* State-machine tests proving prohibited states unreachable.
* Claude review of any state/decision wording.

### Mitigation
`LIVE_APPROVED`/`CAPITAL_ALLOCATED`/`PRODUCTION_READY` unreachable; PromotionDecision implies none of these; closeout reaffirms human ownership of capital/live decisions.

### Owner
Claude Opus / Human.

### Related Phases
ARGOV-P11, ARGOV-P19.

### Blocking Condition
Any reachable path to live/capital/production status, or any claim that the system is ready for capital/live.

---

## Blocking Risk Summary

The following are hard STOP/merge-block conditions: R-002, R-004, R-006, R-007, R-008,
R-009, R-010, R-011, R-013, R-014, R-016, R-018, R-019, R-020. Any of these makes the
affected phase ineligible for merge until resolved or truthfully blocked.

## Risk Review Cadence

* Per phase: Claude Opus review checks the risks tied to that phase's Related Phases.
* Per gate: the acceptance gate re-checks all blocking risks for its phases.
* Campaign closeout (ARGOV-P19): full register reviewed in the semantic done-check.

## Risk Ownership Summary

* **Ralph** — artifact policy, scope/stop enforcement, handoff and merge gating (R-013, R-015, R-018).
* **Codex** — fail-closed validation, ledger/evidence/gate implementation, CLI least-privilege (R-001, R-003, R-005, R-006, R-007, R-012, R-017).
* **Claude Opus** — semantic review of pre-registration, independence, leakage, claims, and done-check (R-002, R-004, R-008, R-009, R-010, R-011, R-014, R-016, R-019, R-020).
* **Human** — direction and final capital/live/risk judgment (R-020).
