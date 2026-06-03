# ALPHA_RESEARCH_GOVERNANCE_MVP Phase Plan

## Purpose

This phase plan is the human-readable, phase-by-phase contract for the
`ALPHA_RESEARCH_GOVERNANCE_MVP` campaign. It decomposes the admissibility and
evidence-governance protocol for AI alpha research into 20 Workflow 2 phases
(`ARGOV-P00` … `ARGOV-P19`), all in the **YELLOW** lane.

This file is authoritative for human reading. `campaign.yaml` is authoritative for
machine execution. Phase IDs, names, lanes, and dependencies in this file must match
`campaign.yaml` exactly. If they diverge, Ralph must STOP and the contract must be
repaired before execution continues.

This campaign builds the governance layer **on top of** the completed
`ALPHA_SYSTEM_V1` and `ASV1_RELEASE_HYGIENE` baselines. It does not search for alpha,
ingest real data, or touch broker/live/paper trading. See `GOAL.md` for strategic
framing and `ACCEPTANCE.md` for done criteria.

## Campaign Invariants

The following invariants hold across every phase and must never be violated:

1. **No `AlphaSpec` → no code.** Implementation requires a registered, validated spec.
2. **No `StudySpec` → no diagnostics.** Diagnostics require an approved study plan and budget.
3. **No `EvidenceBundle` → no candidate.** Candidate status requires a manifest-backed evidence package.
4. **No `TrialLedger` → no promotion.** Promotion requires complete trial accounting, including failures.
5. **No `ReviewerVerdict` → no factor library entry.** Promotion to validated requires an independent verdict.
6. **Failed ideas remain visible.** Failed runs and rejected ideas are first-class records, never deleted or buried.
7. **Variant mining is visible.** Variant counts and multiple-testing metadata are recorded.
8. **Locked-test reuse is contamination.** OOS reuse and locked-test contact are flagged metadata, not silently allowed.
9. **Reviewer independence.** The reviewer role must differ from the implementer role; no self-approval.
10. **Promotion is not live approval.** `VALIDATED` is not production; `CANDIDATE` is not capital allocation.
11. **No unsupported claims.** No alpha/profitability/tradability/production-readiness claims anywhere.
12. **No real data, no alpha search, no broker/live/paper scope** is introduced in this campaign.
13. **Artifact discipline.** No raw data, heavy artifacts, local DBs, caches, or `runs/**` are committed; explicit staging only.

## Global Phase Rules

### Workflow Rules

* Each phase runs as a fresh Workflow 2 iteration under the strict state machine:
  `RUN_INIT → CAMPAIGN_LOAD → PHASE_SELECT → SPEC_GENERATE → SPEC_VALIDATE → WORKTREE_CREATE → CODEX_EXECUTE → CHECKS_RUN → HANDOFF_VALIDATE → CLAUDE_REVIEW → VERDICT_PARSE → PR_CREATE → CI_WAIT → MERGE_GATE → MERGE → DONE_CHECK → NEXT_PHASE → CAMPAIGN_DONE_CHECK → RUN_SUMMARY`.
* Ralph owns state transitions, STOP checks, review routing, verdict parsing, PR/CI/merge gates, bounded repair routing, done-checks, and run summaries.
* Codex executes the generated spec, makes only scoped in-spec repairs, runs only authorized checks, and writes truthful handoffs.
* Claude Opus 4.8 xhigh is the fresh semantic reviewer for every YELLOW phase. Claude Sonnet 4.6 supports source-map, verifier, and mechanical audit work.

### Repo Path Rules

* The active repo and all Workflow 2 worktrees must run under `~/projects/alpha_system` on the WSL2 Linux filesystem.
* `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temp directories are forbidden active worktree locations.

### Git Rules

* Explicit staging only. `git add .` and `git add -A` are forbidden.
* No force push.
* A commit-eligible handoff is required per phase under `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/<PHASE_ID>.md`.
* Before any merge-gate evaluation, the staged set must contain no `runs/` path and no forbidden data/DB/cache/log/heavy-artifact path. `git ls-files runs` must return empty.

### Artifact Rules

* Commit-eligible: source code, configs, schemas, docs, tests, tiny synthetic fixtures, templates, handoffs, reviews, curated summaries.
* Never commit: `data/raw/**`, `data/canonical/**`, `data/factors/**`, `data/labels/**`, `data/cache/**`, `metadata/*.sqlite`, `*.db`, `*.wal`, `*.parquet`/`*.arrow`/`*.feather` outside documented tiny fixtures, logs, caches, `runs/**`, and generated heavy artifacts.
* `runs/**` is local-only runtime state. Run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, and `repair_attempts/` are never staged or committed; commit-eligible handoffs live under `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/**` and review artifacts under `reviews/ALPHA_RESEARCH_GOVERNANCE_MVP/**`.

### Domain Boundary Rules

* Governance objects are metadata and protocol machinery. They must not compute factor values, run real backtests, ingest real data, or make trading decisions.
* The duplicate-exposure guard reads the existing factor registry foundation; it must not mutate factor data or compute new factors.
* The label-leakage guard reasons over `LabelSpec` and feature references; it must not materialize labels.
* Registry integration persists governance objects through the existing local persistence layer without committing the database.

### Non-Negotiable Scope Rules

This campaign must not introduce: real alpha search, real data ingestion, IBKR or any
broker connectivity, an Agent Factory, AlphaBook V1 (only a stub pointer), live
trading, paper trading, order routing, L2 replay, ML/DL expansion, strategy
optimization, portfolio allocation, production execution, or any alpha/profitability/
tradability/production-readiness claim.

### Review Rules

* Every YELLOW phase requires fresh Claude Opus review with a `verdict.json`.
* Merge requires a `PASS` or `PASS_WITH_WARNINGS` verdict. `REWORK`, `BLOCKED`, and `FAIL` block merge.
* Review must verify governance completeness, fail-closed validation, reviewer-independence enforcement, ledger/evidence/promotion gating, canary fail-closed behavior, artifact policy, and absence of prohibited scope and claims.

### Repair Rules

* Bounded repair loop with `max_repair_attempts = 3`, tracked under `runs/<run_id>/phases/<phase_id>/repair_attempts/`.
* Codex repairs only valid in-scope review findings. Contradictory scope, repeated failures, missing authorization, or impossible validation route to a truthful `BLOCKED` handoff. Fake completion is forbidden.

### Validation Rules

* Run the narrowest meaningful test first, then broaden when shared behavior changes.
* Record any skipped check with its exact command, failure, and reason in the handoff.
* Default validation commands: `python tools/verify.py --smoke`, targeted `python -m pytest tests/unit/governance -q`, plus phase-specific checks and the artifact audit.

## Phase Table Summary

| Phase ID  | Phase Name                                                       |   Lane | Dependencies         | Review | Auto PR | Auto Merge |
| --------- | ---------------------------------------------------------------- | -----: | -------------------- | -----: | ------: | ---------: |
| ARGOV-P00 | Governance Campaign Bootstrap                                    | YELLOW | none                 |    yes |     yes |        yes |
| ARGOV-P01 | Governance Package Skeleton and Canonical Naming                 | YELLOW | ARGOV-P00            |    yes |     yes |        yes |
| ARGOV-P02 | Governance IDs, Serialization, and Validation Primitives         | YELLOW | ARGOV-P01            |    yes |     yes |        yes |
| ARGOV-P03 | AlphaSpec Contract and No-Code Gate                              | YELLOW | ARGOV-P02            |    yes |     yes |        yes |
| ARGOV-P04 | HypothesisCard and Pre-registration Protocol                     | YELLOW | ARGOV-P03            |    yes |     yes |        yes |
| ARGOV-P05 | FeatureRequest and Duplicate Exposure Guard                      | YELLOW | ARGOV-P03            |    yes |     yes |        yes |
| ARGOV-P06 | LabelSpec and Label Leakage Guard                                | YELLOW | ARGOV-P03            |    yes |     yes |        yes |
| ARGOV-P07 | StudySpec and Study Budget Protocol                              | YELLOW | ARGOV-P05, ARGOV-P06 |    yes |     yes |        yes |
| ARGOV-P08 | TrialLedger and Variant Accounting                               | YELLOW | ARGOV-P07            |    yes |     yes |        yes |
| ARGOV-P09 | EvidenceBundle and Manifest Contract                             | YELLOW | ARGOV-P07, ARGOV-P08 |    yes |     yes |        yes |
| ARGOV-P10 | RejectedIdeaLedger / Research Graveyard                          | YELLOW | ARGOV-P08            |    yes |     yes |        yes |
| ARGOV-P11 | PromotionDecision and PromotionGate State Machine                | YELLOW | ARGOV-P09, ARGOV-P10 |    yes |     yes |        yes |
| ARGOV-P12 | ReviewerVerdict and Independence Rules                           | YELLOW | ARGOV-P11            |    yes |     yes |        yes |
| ARGOV-P13 | Negative-Control Canary Catalog                                  | YELLOW | ARGOV-P12            |    yes |     yes |        yes |
| ARGOV-P14 | No-Lookahead / Label Leakage / Optimistic Fill Canary Harness    | YELLOW | ARGOV-P13            |    yes |     yes |        yes |
| ARGOV-P15 | Governance Registry Integration                                  | YELLOW | ARGOV-P11, ARGOV-P12 |    yes |     yes |        yes |
| ARGOV-P16 | Governance CLI and Validation Tools                              | YELLOW | ARGOV-P15            |    yes |     yes |        yes |
| ARGOV-P17 | Unsupported-Claim Guard and Governance Report Templates          | YELLOW | ARGOV-P16            |    yes |     yes |        yes |
| ARGOV-P18 | Synthetic End-to-End Governance Dry Run                          | YELLOW | ARGOV-P14, ARGOV-P16, ARGOV-P17 | yes | yes | yes |
| ARGOV-P19 | Workflow 2 Integration, Acceptance Audit, and Closeout           | YELLOW | ARGOV-P18            |    yes |     yes |        yes |

## Acceptance Gate Summary

Every phase belongs to exactly one acceptance gate. Gates have no gaps and no overlaps.

| Gate | Phases | Exit Requirement |
| ---- | ------ | ---------------- |
| `campaign_bootstrap` | ARGOV-P00 … ARGOV-P02 | Campaign control files present, governance package imports, IDs/serialization/fail-closed validation primitives exist |
| `governance_contracts` | ARGOV-P03 … ARGOV-P07 | AlphaSpec + no-code gate, HypothesisCard pre-registration, FeatureRequest duplicate-exposure guard, LabelSpec leakage guard, StudySpec budget protocol exist and fail closed on invalid input |
| `ledger_and_evidence` | ARGOV-P08 … ARGOV-P10 | TrialLedger with failed-run and contamination accounting, EvidenceBundle manifest contract, and first-class RejectedIdeaLedger exist |
| `promotion_and_review` | ARGOV-P11 … ARGOV-P12 | PromotionGate state machine and ReviewerVerdict with enforced independence exist; prohibited MVP states unreachable |
| `canary_and_validation` | ARGOV-P13 … ARGOV-P14 | Negative-control catalog and no-lookahead/leakage/optimistic-fill canary harness exist and fail closed |
| `registry_and_tools` | ARGOV-P15 … ARGOV-P17 | Registry integration, governance CLI/validation tools, unsupported-claim guard, and report templates exist |
| `end_to_end_and_closeout` | ARGOV-P18 … ARGOV-P19 | Synthetic end-to-end governance path passes with negative controls failing closed; Workflow 2 integration, acceptance audit, and closeout complete |

---

# Detailed Phase Specs

---

## ARGOV-P00 — Governance Campaign Bootstrap

### Phase ID
`ARGOV-P00`

### Phase Name
Governance Campaign Bootstrap

### Lane
YELLOW

### Dependencies
None.

### Purpose
Create the implementation entry point for the governance campaign: the governance docs
root, a governance overview, and the commit-eligible handoff, while confirming the
campaign contract bundle is present and consistent. This phase makes the repository
ready to execute the remaining governance phases.

### Scope
* Confirm and reference the campaign contract bundle under `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/`.
* Create `docs/governance/README.md` and `docs/governance/GOVERNANCE_OVERVIEW.md` describing the admissibility protocol, hard rules, object list, and state model at a high level.
* Create the commit-eligible handoff `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P00.md`.
* Ensure `ACTIVE_CAMPAIGN.md` points to this campaign.

### Non-Goals
* Do not create governance package source under `src/alpha_system/governance/**`.
* Do not add tests, configs, templates, or CLI.
* Do not create a campaign-local `ACTIVE_CAMPAIGN.md`.

### Expected Files / Directories
* `docs/governance/README.md`
* `docs/governance/GOVERNANCE_OVERVIEW.md`
* `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P00.md`

### Forbidden Changes
* No `src/alpha_system/governance/**`.
* No `tests/**`.
* No `runs/**` staged or committed.
* No raw data, heavy artifacts, or local DB files.
* No broker/live/paper/order-routing scope.
* No alpha/profitability/tradability claims.

### Validation Commands
```bash
git status --short
test -f ACTIVE_CAMPAIGN.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/GOAL.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/PHASE_PLAN.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACCEPTANCE.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RISK_REGISTER.md
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RUNBOOK.md
test ! -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACTIVE_CAMPAIGN.md
test -f handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P00.md
grep -q "ALPHA_RESEARCH_GOVERNANCE_MVP" ACTIVE_CAMPAIGN.md
python tools/verify.py --smoke
git ls-files runs
```

### Artifact Policy
Commit only campaign files, governance overview docs, and the commit-eligible handoff.
Never commit `runs/**`, raw data, heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* Governance docs root exists with an overview of the admissibility protocol.
* `ACTIVE_CAMPAIGN.md` points to `ALPHA_RESEARCH_GOVERNANCE_MVP`.
* No campaign-local `ACTIVE_CAMPAIGN.md` exists.
* Commit-eligible handoff exists and records validation results.
* No governance source, tests, or forbidden scope introduced.

### Handoff Requirements
`handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P00.md` must summarize created docs, exact
staged files, validation results, artifact-policy confirmation, explicit-staging
confirmation, and statements that no source/tests/forbidden scope/claims were added.

### Review Requirements
Claude Opus review required. Must verify contract-bundle consistency, no campaign-local
pointer, no source/test scope creep, and clean artifact policy.

### Auto-Merge Eligibility
Auto PR and auto merge by Ralph only when checks pass, handoff validates, verdict is
`PASS`/`PASS_WITH_WARNINGS`, artifact policy passes, no forbidden paths are staged, CI
passes if configured, and the semantic done-check passes.

---

## ARGOV-P01 — Governance Package Skeleton and Canonical Naming

### Phase ID
`ARGOV-P01`

### Phase Name
Governance Package Skeleton and Canonical Naming

### Lane
YELLOW

### Dependencies
`ARGOV-P00`.

### Purpose
Establish the importable `alpha_system.governance` package skeleton, the test root, the
configs/templates roots, and the canonical naming conventions for all governance
objects, IDs, files, and directories.

### Scope
* Create `src/alpha_system/governance/__init__.py` and empty/stub module placeholders for the object families (e.g. `ids`, `serialization`, `validation`, `alpha_spec`, `hypothesis_card`, `feature_request`, `label_spec`, `study_spec`, `trial_ledger`, `evidence_bundle`, `rejected_idea`, `promotion`, `reviewer_verdict`, `canaries`, `registry`, `claims`, `report`).
* Create `tests/unit/governance/` with a package-import smoke test.
* Create `configs/governance/` and `templates/governance/` roots with documented placeholders.
* Create `docs/governance/NAMING.md` defining canonical object names, ID prefixes, file naming, and directory layout.

### Non-Goals
* Do not implement object validation logic yet.
* Do not integrate with the registry/persistence layer.
* Do not add a CLI.

### Expected Files / Directories
* `src/alpha_system/governance/**` (skeleton modules)
* `tests/unit/governance/test_package_skeleton.py`
* `configs/governance/`, `templates/governance/` (with `.gitkeep`/`README.md`)
* `docs/governance/NAMING.md`

### Forbidden Changes
* No broker/live/paper/order-routing code.
* No real data, DB commits, or heavy artifacts.
* No changes to unrelated `src/alpha_system` subpackages.

### Validation Commands
```bash
git status --short
python -c "import alpha_system.governance"
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/NAMING.md
git ls-files runs
```

### Artifact Policy
Commit only package skeleton, tests, docs, and tiny synthetic fixtures. Never commit
`runs/**`, raw data, heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* `alpha_system.governance` imports cleanly.
* Package skeleton and test root exist with a passing import smoke test.
* Canonical naming documented.
* No object logic, registry integration, or forbidden scope introduced.

### Handoff Requirements
Summarize the skeleton, naming conventions, exact staged files, and validation results.

### Review Requirements
Claude Opus review must verify clean package boundaries, naming clarity, and no scope creep.

### Auto-Merge Eligibility
Standard YELLOW gates (see ARGOV-P00).

---

## ARGOV-P02 — Governance IDs, Serialization, and Validation Primitives

### Phase ID
`ARGOV-P02`

### Phase Name
Governance IDs, Serialization, and Validation Primitives

### Lane
YELLOW

### Dependencies
`ARGOV-P01`.

### Purpose
Implement the shared primitives every governance object depends on: deterministic IDs,
content hashes, serialization/deserialization, and **fail-closed** validation helpers
that reject incomplete or malformed objects rather than coercing them.

### Scope
* Implement `governance/ids.py` (typed ID prefixes, deterministic generation, parsing).
* Implement `governance/serialization.py` (canonical, stable serialization; round-trip).
* Implement `governance/validation.py` (fail-closed schema validation, required-field enforcement, structured validation errors).
* Add unit tests covering valid/invalid cases and the fail-closed default.

### Non-Goals
* Do not implement specific governance objects (AlphaSpec etc.) yet.
* Do not persist anything to the registry.

### Expected Files / Directories
* `src/alpha_system/governance/ids.py`, `serialization.py`, `validation.py`
* `tests/unit/governance/test_ids.py`, `test_serialization.py`, `test_validation.py`
* `tests/fixtures/governance/**` (tiny synthetic fixtures)

### Forbidden Changes
* No broker/live/paper scope; no real data; no DB commits.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
git ls-files runs
```

### Artifact Policy
Commit only primitives, tests, docs, and tiny synthetic fixtures. Explicit staging only.

### Done Criteria
* IDs, serialization, and validation primitives exist and are tested.
* Validation fails closed by default (missing/invalid fields raise structured errors).
* Round-trip serialization is deterministic.

### Handoff Requirements
Document the primitives, the fail-closed default, and validation results.

### Review Requirements
Claude Opus review must confirm fail-closed semantics and deterministic hashing/serialization.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P03 — AlphaSpec Contract and No-Code Gate

### Phase ID
`ARGOV-P03`

### Phase Name
AlphaSpec Contract and No-Code Gate

### Lane
YELLOW

### Dependencies
`ARGOV-P02`.

### Purpose
Define the `AlphaSpec` object and enforce the central rule **no AlphaSpec → no code**:
a validated, registered `AlphaSpec` is the precondition for any implementation work.

### Scope
* Implement `governance/alpha_spec.py` with all required fields (`alpha_spec_id`, `hypothesis_id`, `target_instruments`, `data_assumptions`, `factor_inputs`, `label_references`, `exclusion_rules`, `timestamp_assumptions`, `cost_assumptions`, `expected_failure_modes`, `promotion_criteria`, `created_by`, `created_at`).
* Implement the no-code gate: a validation entry point that blocks the `REGISTERED → IMPLEMENTATION_ALLOWED` transition unless the AlphaSpec validates.
* Create `docs/governance/ALPHA_SPEC.md` and `templates/governance/alpha_spec.template.yaml`.
* Add tests for valid specs, invalid specs (fail closed), and gate blocking.

### Non-Goals
* Do not imply candidate status or factor-library entry from an AlphaSpec.
* Do not implement diagnostics, studies, or promotion.

### Expected Files / Directories
* `src/alpha_system/governance/alpha_spec.py`
* `tests/unit/governance/test_alpha_spec.py`, `test_no_code_gate.py`
* `docs/governance/ALPHA_SPEC.md`, `templates/governance/alpha_spec.template.yaml`

### Forbidden Changes
* No factor computation; no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/ALPHA_SPEC.md
test -f templates/governance/alpha_spec.template.yaml
git ls-files runs
```

### Artifact Policy
Commit only AlphaSpec code, tests, docs, templates, and tiny fixtures. Explicit staging only.

### Done Criteria
* `AlphaSpec` exists with all required fields and validates fail-closed.
* The no-code gate blocks implementation without a valid AlphaSpec.
* Docs and template exist; AlphaSpec does not imply candidate/library status.

### Handoff Requirements
Document the AlphaSpec contract, the no-code gate behavior, and validation results.

### Review Requirements
Claude Opus review must confirm the no-code gate truly blocks and the spec is complete and fail-closed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P04 — HypothesisCard and Pre-registration Protocol

### Phase ID
`ARGOV-P04`

### Phase Name
HypothesisCard and Pre-registration Protocol

### Lane
YELLOW

### Dependencies
`ARGOV-P03`.

### Purpose
Define the `HypothesisCard` and the pre-registration protocol that anchors every idea to
an explicit rationale, expected mechanism, and falsification criteria recorded **before**
implementation.

### Scope
* Implement `governance/hypothesis_card.py` with required fields (`hypothesis_id`, `title`, `family`, `rationale`, `expected_mechanism`, `falsification_criteria`, `risks`, `author`, `created_at`).
* Implement pre-registration semantics: an AlphaSpec must reference a registered HypothesisCard, and the `DRAFT → REGISTERED` transition requires both.
* Create `docs/governance/PRE_REGISTRATION.md` and `templates/governance/hypothesis_card.template.yaml`.
* Add tests for required falsification criteria and pre-registration linkage.

### Non-Goals
* Do not imply implementation approval or alpha validity from a HypothesisCard.

### Expected Files / Directories
* `src/alpha_system/governance/hypothesis_card.py`
* `tests/unit/governance/test_hypothesis_card.py`, `test_pre_registration.py`
* `docs/governance/PRE_REGISTRATION.md`, `templates/governance/hypothesis_card.template.yaml`

### Forbidden Changes
* No real data; no broker/live scope; no claims.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/PRE_REGISTRATION.md
test -f templates/governance/hypothesis_card.template.yaml
git ls-files runs
```

### Artifact Policy
Commit only HypothesisCard code, tests, docs, templates, and tiny fixtures. Explicit staging only.

### Done Criteria
* `HypothesisCard` exists with required falsification criteria and validates fail-closed.
* Pre-registration linkage to AlphaSpec is enforced.
* Card does not imply approval or validity.

### Handoff Requirements
Document the card, pre-registration linkage, and validation results.

### Review Requirements
Claude Opus review must confirm falsification anchoring and that registration requires both card and spec.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P05 — FeatureRequest and Duplicate Exposure Guard

### Phase ID
`ARGOV-P05`

### Phase Name
FeatureRequest and Duplicate Exposure Guard

### Lane
YELLOW

### Dependencies
`ARGOV-P03`.

### Purpose
Define the `FeatureRequest` object and a duplicate/equivalent exposure guard so new
feature/factor inputs are checked against the existing factor registry foundation before
implementation, preventing silent duplicate factors.

### Scope
* Implement `governance/feature_request.py` with required fields (`feature_request_id`, `alpha_spec_id`, `requested_inputs`, `formula_sketch`, `availability_assumptions`, `duplicate_or_equivalent_exposure_notes`, `data_requirements`, `approval_status`).
* Implement a duplicate/equivalent exposure guard that reads the existing factor registry (read-only) and surfaces likely duplicate or equivalent exposures as blocking-or-warning metadata.
* Create `docs/governance/FEATURE_REQUEST.md` and `docs/governance/DUPLICATE_EXPOSURE.md`.
* Add tests including a synthetic duplicate-detection fixture.

### Non-Goals
* Do not compute factor values or mutate the factor registry.
* Do not grant implementation permission without validation.

### Expected Files / Directories
* `src/alpha_system/governance/feature_request.py`, `duplicate_exposure.py`
* `tests/unit/governance/test_feature_request.py`, `test_duplicate_exposure.py`
* `docs/governance/FEATURE_REQUEST.md`, `docs/governance/DUPLICATE_EXPOSURE.md`

### Forbidden Changes
* No factor-data mutation; no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/FEATURE_REQUEST.md
test -f docs/governance/DUPLICATE_EXPOSURE.md
git ls-files runs
```

### Artifact Policy
Commit only FeatureRequest code, the guard, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* `FeatureRequest` exists with required fields and validates fail-closed.
* The duplicate-exposure guard reads the factor registry read-only and flags duplicates/equivalents.
* FeatureRequest does not imply implementation permission.

### Handoff Requirements
Document the object, the guard, the read-only registry interaction, and validation results.

### Review Requirements
Claude Opus review must confirm read-only registry access and meaningful duplicate detection.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P06 — LabelSpec and Label Leakage Guard

### Phase ID
`ARGOV-P06`

### Phase Name
LabelSpec and Label Leakage Guard

### Lane
YELLOW

### Dependencies
`ARGOV-P03`.

### Purpose
Define the `LabelSpec` object and a label-leakage guard that prevents label-as-feature
overlap and future-information leakage into features.

### Scope
* Implement `governance/label_spec.py` with required fields (`label_spec_id`, `horizon`, `path_rules`, `cost_model`, `target_stop_rules`, `availability_time`, `forbidden_feature_overlap`, `leakage_checks`).
* Implement a leakage guard that rejects label/feature overlap and availability-time violations.
* Add no-lookahead style tests under `tests/no_lookahead/` plus unit tests.
* Create `docs/governance/LABEL_SPEC.md` and `docs/governance/LABEL_LEAKAGE_GUARD.md`.

### Non-Goals
* Do not materialize labels or imply label quality/predictive value.

### Expected Files / Directories
* `src/alpha_system/governance/label_spec.py`, leakage guard module
* `tests/unit/governance/test_label_spec.py`, `tests/no_lookahead/test_label_leakage_guard.py`
* `docs/governance/LABEL_SPEC.md`, `docs/governance/LABEL_LEAKAGE_GUARD.md`

### Forbidden Changes
* No label materialization; no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
python -m pytest tests/no_lookahead -q
test -f docs/governance/LABEL_SPEC.md
test -f docs/governance/LABEL_LEAKAGE_GUARD.md
git ls-files runs
```

### Artifact Policy
Commit only LabelSpec code, the guard, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* `LabelSpec` exists with required fields and validates fail-closed.
* The leakage guard blocks label-as-feature overlap and availability-time violations.
* Spec does not imply label quality or predictive value.

### Handoff Requirements
Document the object, leakage checks, no-lookahead tests, and validation results.

### Review Requirements
Claude Opus review must confirm leakage and availability-time enforcement.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P07 — StudySpec and Study Budget Protocol

### Phase ID
`ARGOV-P07`

### Phase Name
StudySpec and Study Budget Protocol

### Lane
YELLOW

### Dependencies
`ARGOV-P05`, `ARGOV-P06`.

### Purpose
Define the `StudySpec` object and a study-budget protocol so diagnostics run only against
an explicit plan with a declared variant budget, split protocol, metrics, cost
assumptions, locked-test policy, negative controls, and stopping rules.

### Scope
* Implement `governance/study_spec.py` with required fields (`study_spec_id`, `alpha_spec_id`, `label_spec_id`, `dataset_scope`, `split_protocol`, `metrics`, `cost_assumptions`, `variant_budget`, `locked_test_policy`, `negative_controls`, `stopping_rules`).
* Enforce **no StudySpec → no diagnostics**: the `IMPLEMENTED → DIAGNOSTICS_ALLOWED` transition requires a valid StudySpec.
* Encode the study-budget protocol (variant budget declared up front; overruns flagged).
* Create `docs/governance/STUDY_SPEC.md` and `docs/governance/STUDY_BUDGET.md`.

### Non-Goals
* Do not run diagnostics or imply diagnostics passed.

### Expected Files / Directories
* `src/alpha_system/governance/study_spec.py`
* `tests/unit/governance/test_study_spec.py`, `test_study_budget.py`
* `docs/governance/STUDY_SPEC.md`, `docs/governance/STUDY_BUDGET.md`, `templates/governance/study_spec.template.yaml`

### Forbidden Changes
* No diagnostics execution; no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/STUDY_SPEC.md
test -f docs/governance/STUDY_BUDGET.md
git ls-files runs
```

### Artifact Policy
Commit only StudySpec code, protocol, tests, docs, templates, and tiny fixtures. Explicit staging only.

### Done Criteria
* `StudySpec` exists with required fields including variant budget, locked-test policy, and negative controls, and validates fail-closed.
* Diagnostics are blocked without a valid StudySpec.
* Spec does not imply diagnostics passed.

### Handoff Requirements
Document the object, budget protocol, gate enforcement, and validation results.

### Review Requirements
Claude Opus review must confirm the diagnostics gate and the study-budget declaration.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P08 — TrialLedger and Variant Accounting

### Phase ID
`ARGOV-P08`

### Phase Name
TrialLedger and Variant Accounting

### Lane
YELLOW

### Dependencies
`ARGOV-P07`.

### Purpose
Define the `TrialLedgerRecord` and variant accounting so every attempt — including
failures and variants — is recorded with OOS-touched and locked-test contamination flags.

### Scope
* Implement `governance/trial_ledger.py` with required fields (`trial_id`, `alpha_spec_id`, `study_spec_id`, `run_id`, `variant_id`, `status`, `parameters`, `metrics_summary`, `failure_reason`, `oos_touched_flag`, `locked_test_contamination_flag`, `code_hash`, `config_hash`).
* Enforce failed-run visibility: failed trials cannot be omitted; variant counts are accumulated.
* Create `docs/governance/TRIAL_LEDGER.md`.
* Add tests for failed-run recording, variant accounting, and contamination flags.

### Non-Goals
* Do not imply success from any recorded trial.
* Do not run studies or backtests.

### Expected Files / Directories
* `src/alpha_system/governance/trial_ledger.py`
* `tests/unit/governance/test_trial_ledger.py`
* `docs/governance/TRIAL_LEDGER.md`

### Forbidden Changes
* No real data; no broker/live scope; no hidden-failure paths.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/TRIAL_LEDGER.md
git ls-files runs
```

### Artifact Policy
Commit only TrialLedger code, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* `TrialLedgerRecord` exists with required fields and validates fail-closed.
* Failed runs and variant counts are recorded; OOS-touched and contamination flags exist.
* No record implies success.

### Handoff Requirements
Document the ledger, failed-run visibility, contamination flags, and validation results.

### Review Requirements
Claude Opus review must confirm failed runs cannot be hidden and contamination flags are present.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P09 — EvidenceBundle and Manifest Contract

### Phase ID
`ARGOV-P09`

### Phase Name
EvidenceBundle and Manifest Contract

### Lane
YELLOW

### Dependencies
`ARGOV-P07`, `ARGOV-P08`.

### Purpose
Define the `EvidenceBundle` and its manifest contract — the minimum evidence package a
candidate must carry, including hashes, versions, diagnostics summary, negative-control
results, limitations, and a reviewer-verdict reference.

### Scope
* Implement `governance/evidence_bundle.py` with required fields (`evidence_bundle_id`, `alpha_spec_id`, `study_spec_id`, `trial_ids`, `data_version`, `factor_version`, `label_version`, `code_hash`, `config_hash`, `diagnostics_summary`, `negative_control_results`, `limitations`, `artifact_manifest`, `reviewer_verdict_reference`).
* Enforce **no EvidenceBundle → no candidate**: a bundle with a valid manifest and trial refs is required for the candidate state.
* Create `docs/governance/EVIDENCE_BUNDLE.md`.

### Non-Goals
* Do not imply promotion unless the gate accepts the bundle.
* Do not commit heavy artifacts; the manifest references local-only artifacts.

### Expected Files / Directories
* `src/alpha_system/governance/evidence_bundle.py`
* `tests/unit/governance/test_evidence_bundle.py`
* `docs/governance/EVIDENCE_BUNDLE.md`

### Forbidden Changes
* No heavy artifact commits; no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/EVIDENCE_BUNDLE.md
git ls-files runs
```

### Artifact Policy
Commit only EvidenceBundle code, the manifest contract, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* `EvidenceBundle` exists with required fields including manifest, hashes, versions, and negative-control results, and validates fail-closed.
* A bundle is required for candidate status.
* The bundle does not imply promotion.

### Handoff Requirements
Document the bundle, manifest contract, required hashes/versions, and validation results.

### Review Requirements
Claude Opus review must confirm the manifest, hashes, versions, and trial refs are mandatory.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P10 — RejectedIdeaLedger / Research Graveyard

### Phase ID
`ARGOV-P10`

### Phase Name
RejectedIdeaLedger / Research Graveyard

### Lane
YELLOW

### Dependencies
`ARGOV-P08`.

### Purpose
Make rejected, duplicate, leaky, and weak ideas first-class `RejectedIdeaRecord` ledger
entries (a research graveyard), so failures are durable and auditable rather than buried
in prose.

### Scope
* Implement `governance/rejected_idea.py` with required fields (`rejected_id`, `alpha_spec_id_or_hypothesis_id`, `reason_category`, `evidence_references`, `duplicate_links`, `leakage_cost_weakness_notes`, `reviewer`, `created_at`).
* Support `any state → REJECTED` with a recorded reason, and explicit, linked future reconsideration (no silent revival).
* Create `docs/governance/REJECTED_IDEA_LEDGER.md`.

### Non-Goals
* Do not imply a permanent ban; reconsideration must be explicit and linked.

### Expected Files / Directories
* `src/alpha_system/governance/rejected_idea.py`
* `tests/unit/governance/test_rejected_idea.py`
* `docs/governance/REJECTED_IDEA_LEDGER.md`

### Forbidden Changes
* No real data; no broker/live scope; no deletion of failed records.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/REJECTED_IDEA_LEDGER.md
git ls-files runs
```

### Artifact Policy
Commit only RejectedIdeaRecord code, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* `RejectedIdeaRecord` exists with required fields and validates fail-closed.
* Rejected ideas are first-class ledger entries with reason categories.
* Reconsideration is explicit and linked; rejection is not a permanent ban.

### Handoff Requirements
Document the graveyard ledger, reason categories, reconsideration semantics, and validation results.

### Review Requirements
Claude Opus review must confirm rejected ideas are durable records, not prose-only.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P11 — PromotionDecision and PromotionGate State Machine

### Phase ID
`ARGOV-P11`

### Phase Name
PromotionDecision and PromotionGate State Machine

### Lane
YELLOW

### Dependencies
`ARGOV-P09`, `ARGOV-P10`.

### Purpose
Define the `PromotionDecision` object and the promotion-gate state machine that governs the
research-idea lifecycle and blocks promotion unless trial ledger, evidence bundle, and
(in later phases) a reviewer verdict are present.

### Scope
* Implement `governance/promotion.py` with the `PromotionDecision` object (required fields: `promotion_id`, `alpha_spec_id`, `evidence_bundle_id`, `trial_ledger_refs`, `previous_state`, `next_state`, `decision`, `rationale`, `reviewer_verdict_id`, `warnings`, `timestamp`).
* Implement the governance state machine (`DRAFT … VALIDATED`) with the transition logic and blocks defined in `campaign.yaml` (`governance_state_machine`).
* Make the prohibited MVP states `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, `PRODUCTION_READY` unreachable.
* Create `docs/governance/PROMOTION_GATE.md` and `docs/governance/GOVERNANCE_STATE_MACHINE.md`.

### Non-Goals
* Do not imply live approval, capital allocation, or production readiness.
* Reviewer-independence enforcement is wired in ARGOV-P12.

### Expected Files / Directories
* `src/alpha_system/governance/promotion.py`, state-machine module
* `tests/unit/governance/test_promotion.py`, `test_state_machine.py`
* `docs/governance/PROMOTION_GATE.md`, `docs/governance/GOVERNANCE_STATE_MACHINE.md`

### Forbidden Changes
* No reachable prohibited MVP states; no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/PROMOTION_GATE.md
test -f docs/governance/GOVERNANCE_STATE_MACHINE.md
git ls-files runs
```

### Artifact Policy
Commit only promotion code, the state machine, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* `PromotionDecision` and the state machine exist and validate fail-closed.
* Promotion is blocked without trial ledger and evidence bundle.
* Prohibited MVP states are unreachable.

### Handoff Requirements
Document the decision object, transitions, blocks, and unreachable prohibited states.

### Review Requirements
Claude Opus review must confirm gating logic and that `LIVE_APPROVED`/`CAPITAL_ALLOCATED`/`PRODUCTION_READY` are unreachable.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P12 — ReviewerVerdict and Independence Rules

### Phase ID
`ARGOV-P12`

### Phase Name
ReviewerVerdict and Independence Rules

### Lane
YELLOW

### Dependencies
`ARGOV-P11`.

### Purpose
Define the `ReviewerVerdict` object and enforce reviewer independence: the reviewer role
must differ from the implementer role, and implementers cannot self-approve. Promotion to
validated requires an independent verdict.

### Scope
* Implement `governance/reviewer_verdict.py` with required fields (`reviewer_id`, `role`, `independence_statement`, `verdict`, `blocking_issues`, `warnings`, `checked_artifacts`, `checked_commands`, `timestamp`).
* Wire independence enforcement into the promotion gate: a verdict whose reviewer equals the implementer is rejected; `REVIEWED → VALIDATED` requires an independent `PASS`/`PASS_WITH_WARNINGS` verdict.
* Create `docs/governance/REVIEWER_INDEPENDENCE.md`.

### Non-Goals
* Do not imply market truth or profitability from a verdict.

### Expected Files / Directories
* `src/alpha_system/governance/reviewer_verdict.py`
* `tests/unit/governance/test_reviewer_verdict.py`, `test_reviewer_independence.py`
* `docs/governance/REVIEWER_INDEPENDENCE.md`

### Forbidden Changes
* No self-approval paths; no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/REVIEWER_INDEPENDENCE.md
git ls-files runs
```

### Artifact Policy
Commit only ReviewerVerdict code, independence rules, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* `ReviewerVerdict` exists with required fields including an independence statement and validates fail-closed.
* Self-approval is blocked; validated promotion requires an independent verdict.
* Verdict does not imply market truth.

### Handoff Requirements
Document the verdict object, independence enforcement, and validation results.

### Review Requirements
Claude Opus review must confirm self-approval is impossible and independence is enforced at the gate.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P13 — Negative-Control Canary Catalog

### Phase ID
`ARGOV-P13`

### Phase Name
Negative-Control Canary Catalog

### Lane
YELLOW

### Dependencies
`ARGOV-P12`.

### Purpose
Catalog the negative controls — random, permuted, future-shift, and optimistic-fill
canaries — that future studies must run and that must fail closed. Defines the
`NegativeControlResult` object.

### Scope
* Implement `governance/canaries/catalog.py` and the `NegativeControlResult` object (required fields: `canary_id`, `canary_type`, `expected_failure`, `observed_result`, `pass_fail`, `related_study_or_evidence`, `notes`).
* Register canary types: random target, permuted labels, future-shift (lookahead), optimistic fill.
* Add safety canaries under `evals/canaries/**` consistent with the existing canary convention.
* Create `docs/governance/NEGATIVE_CONTROLS.md`.

### Non-Goals
* Do not imply alpha validity; canaries validate guard behavior only.
* The executable harness is built in ARGOV-P14.

### Expected Files / Directories
* `src/alpha_system/governance/canaries/catalog.py`, `negative_control_result.py`
* `evals/canaries/**`
* `tests/unit/governance/test_negative_controls.py`
* `docs/governance/NEGATIVE_CONTROLS.md`

### Forbidden Changes
* No real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/NEGATIVE_CONTROLS.md
git ls-files runs
```

### Artifact Policy
Commit only the canary catalog, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* The negative-control catalog and `NegativeControlResult` exist and validate fail-closed.
* Canary types (random, permuted, future-shift, optimistic-fill) are catalogued.
* Canaries are documented to fail closed.

### Handoff Requirements
Document the catalog, canary types, and validation results.

### Review Requirements
Claude Opus review must confirm the catalog is complete and the fail-closed expectation is explicit.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P14 — No-Lookahead / Label Leakage / Optimistic Fill Canary Harness

### Phase ID
`ARGOV-P14`

### Phase Name
No-Lookahead / Label Leakage / Optimistic Fill Canary Harness

### Lane
YELLOW

### Dependencies
`ARGOV-P13`.

### Purpose
Implement a minimal synthetic canary harness that exercises the catalogued negative
controls and proves they fail closed: a no-lookahead/future-shift canary, a label-leakage
canary, and an optimistic-fill canary, integrated with the existing canary runner.

### Scope
* Implement `governance/canaries/harness.py` with synthetic dry-run hooks for each canary type.
* Add `tests/no_lookahead/**` and `tests/unit/governance/**` cases asserting the canaries fail closed (a passing guard is one that catches the injected fault).
* Integrate with `tools/hooks/canary_runner.py` so governance canaries run alongside existing safety canaries.
* Document under `docs/governance/` (canary harness section).

### Non-Goals
* Do not use real data; synthetic fixtures only.
* Do not imply alpha validity.

### Expected Files / Directories
* `src/alpha_system/governance/canaries/harness.py`
* `tests/no_lookahead/test_governance_canaries.py`, `tests/unit/governance/test_canary_harness.py`
* `evals/canaries/**` (synthetic canary fixtures)

### Forbidden Changes
* No real data; no broker/live scope; no weakening of existing canaries.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
python -m pytest tests/no_lookahead -q
python tools/hooks/canary_runner.py
git ls-files runs
```

### Artifact Policy
Commit only harness code, tests, docs, and tiny synthetic fixtures. Explicit staging only.

### Done Criteria
* The canary harness runs synthetic no-lookahead, label-leakage, and optimistic-fill controls.
* Each canary fails closed (detects the injected fault); the canary runner passes.
* No real data or scope creep.

### Handoff Requirements
Document the harness, fail-closed assertions, canary-runner integration, and validation results.

### Review Requirements
Claude Opus review must confirm the canaries genuinely fail closed and integrate with the runner.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P15 — Governance Registry Integration

### Phase ID
`ARGOV-P15`

### Phase Name
Governance Registry Integration

### Lane
YELLOW

### Dependencies
`ARGOV-P11`, `ARGOV-P12`.

### Purpose
Connect governance objects to the existing local registry/persistence contract so specs,
ledgers, bundles, decisions, and verdicts persist and resolve by ID — **without** committing
the database.

### Scope
* Implement `governance/registry.py` (and any migration) integrating with the existing local persistence layer.
* Provide persistence and lookup for governance objects keyed by their IDs and lifecycle state.
* Add integration tests under `tests/integration/governance/` using a temp DB (never committed).
* Create `docs/governance/REGISTRY_INTEGRATION.md`.

### Non-Goals
* Do not commit `metadata/*.sqlite` or any DB file.
* Do not ingest real data.

### Expected Files / Directories
* `src/alpha_system/governance/registry.py` (+ migration if needed)
* `tests/integration/governance/test_registry_integration.py`
* `docs/governance/REGISTRY_INTEGRATION.md`

### Forbidden Changes
* No DB commits (`metadata/*.sqlite`, `*.db`); no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
test -f docs/governance/REGISTRY_INTEGRATION.md
find metadata -type f ! -name README.md ! -name .gitkeep -print
git ls-files runs
```

### Artifact Policy
Commit only registry integration code, migrations, tests, docs, and tiny fixtures. Never
commit `metadata/*.sqlite` or DB files. Explicit staging only.

### Done Criteria
* Governance objects persist and resolve through the existing registry layer using a temp DB in tests.
* No DB file is staged or committed (`find metadata` returns only README/.gitkeep).
* Integration tests pass.

### Handoff Requirements
Document the integration, temp-DB test approach, the `find metadata` audit, and validation results.

### Review Requirements
Claude Opus review must confirm persistence works and no DB is committed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P16 — Governance CLI and Validation Tools

### Phase ID
`ARGOV-P16`

### Phase Name
Governance CLI and Validation Tools

### Lane
YELLOW

### Dependencies
`ARGOV-P15`.

### Purpose
Expose a governance CLI surface and validation tools so operators and agents can validate
specs, register trials, build evidence bundles, record reviews, and request promotions.

### Scope
* Add governance CLI commands under `src/alpha_system/cli/**` (e.g. `validate-spec`, `register-trial`, `build-evidence`, `review`, `promote`).
* Add validation helpers under `tools/governance/**`.
* Add unit and integration tests including CLI smoke tests.
* Create `docs/governance/CLI.md`.

### Non-Goals
* Do not run real studies, ingest real data, or make trading decisions.

### Expected Files / Directories
* `src/alpha_system/cli/**` (governance commands)
* `tools/governance/**`
* `tests/unit/governance/test_cli.py`, `tests/integration/governance/test_cli_smoke.py`
* `docs/governance/CLI.md`

### Forbidden Changes
* No real data; no broker/live scope; no DB commits.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
test -f docs/governance/CLI.md
git ls-files runs
```

### Artifact Policy
Commit only CLI code, validation tools, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* Governance CLI commands exist and pass smoke tests.
* Validation tools exist and are tested.
* No forbidden scope introduced.

### Handoff Requirements
Document the CLI surface, validation tools, smoke tests, and validation results.

### Review Requirements
Claude Opus review must confirm the CLI enforces the governance gates rather than bypassing them.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P17 — Unsupported-Claim Guard and Governance Report Templates

### Phase ID
`ARGOV-P17`

### Phase Name
Unsupported-Claim Guard and Governance Report Templates

### Lane
YELLOW

### Dependencies
`ARGOV-P16`.

### Purpose
Implement an unsupported-claim guard that blocks alpha/profitability/tradability/
production-readiness claims, and provide governance report templates that carry evidence,
limitations, and no-claims language.

### Scope
* Implement `governance/claims.py` (prohibited-claim detection, fail closed on violation), consistent with the existing research-interpretation/no-claims policy.
* Add governance report templates under `templates/governance/**` and report builders under `src/alpha_system/reports/**` if needed.
* Add tests for prohibited-claim detection.
* Create `docs/governance/UNSUPPORTED_CLAIM_GUARD.md`.

### Non-Goals
* Do not generate market claims; do not assert profitability/tradability anywhere.

### Expected Files / Directories
* `src/alpha_system/governance/claims.py`
* `templates/governance/**` (report templates)
* `tests/unit/governance/test_claims_guard.py`
* `docs/governance/UNSUPPORTED_CLAIM_GUARD.md`

### Forbidden Changes
* No alpha/profitability/tradability claims; no real data; no broker/live scope.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python -m pytest tests/unit/governance -q
test -f docs/governance/UNSUPPORTED_CLAIM_GUARD.md
test -d templates/governance
git ls-files runs
```

### Artifact Policy
Commit only claim-guard code, templates, tests, docs, and tiny fixtures. Explicit staging only.

### Done Criteria
* The unsupported-claim guard blocks prohibited claims and fails closed.
* Report templates carry evidence, limitations, and no-claims language.
* No claims introduced anywhere.

### Handoff Requirements
Document the guard, templates, prohibited-claim coverage, and validation results.

### Review Requirements
Claude Opus review must confirm the guard blocks the full prohibited-claim set.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P18 — Synthetic End-to-End Governance Dry Run

### Phase ID
`ARGOV-P18`

### Phase Name
Synthetic End-to-End Governance Dry Run

### Lane
YELLOW

### Dependencies
`ARGOV-P14`, `ARGOV-P16`, `ARGOV-P17`.

### Purpose
Run the complete governance path over synthetic fixtures: hypothesis → spec → feature/label
specs → study → trials → evidence → review → promotion, including negative controls and the
unsupported-claim guard, proving the gates and canaries behave correctly end to end.

### Scope
* Implement a synthetic end-to-end dry run (script/test) that walks an idea through every state using fixtures and the CLI/registry.
* Assert the gates block at each missing-prerequisite point and that negative controls fail closed.
* Produce a curated, committable dry-run summary (no heavy artifacts).
* Create `docs/governance/END_TO_END_DRY_RUN.md`.

### Non-Goals
* Do not use real data or claim any alpha/profitability result.

### Expected Files / Directories
* `tests/integration/governance/test_end_to_end_dry_run.py`
* `docs/governance/END_TO_END_DRY_RUN.md`
* `tests/fixtures/governance/**` (synthetic end-to-end fixtures)

### Forbidden Changes
* No real data; no heavy artifacts; no broker/live scope; no claims.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
python tools/hooks/canary_runner.py
test -f docs/governance/END_TO_END_DRY_RUN.md
find artifacts -type f -size +1M -print
git ls-files runs
```

### Artifact Policy
Commit only dry-run code, tests, docs, tiny synthetic fixtures, and a curated summary.
Never commit heavy artifacts or full generated bundles. Explicit staging only.

### Done Criteria
* The synthetic end-to-end governance path passes.
* Gates block missing prerequisites; negative controls fail closed.
* A curated dry-run summary exists; no heavy artifacts committed.

### Handoff Requirements
Document the end-to-end path, gate assertions, canary results, and validation results.

### Review Requirements
Claude Opus review must confirm the dry run exercises every gate and the canaries fail closed.

### Auto-Merge Eligibility
Standard YELLOW gates.

---

## ARGOV-P19 — Workflow 2 Integration, Acceptance Audit, and Closeout

### Phase ID
`ARGOV-P19`

### Phase Name
Workflow 2 Integration, Acceptance Audit, and Closeout

### Lane
YELLOW

### Dependencies
`ARGOV-P18`.

### Purpose
Integrate the governance layer with Workflow 2 handoff/review/verdict semantics, run the
acceptance audit against `ACCEPTANCE.md`, and close out the campaign with a final
semantic done-check and closeout document.

### Scope
* Wire governance handoff/review/verdict artifacts into the Workflow 2 conventions and document the integration.
* Run the full acceptance audit covering all gates and prohibited shortcuts.
* Produce `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/CLOSEOUT.md` and `docs/governance/WORKFLOW2_INTEGRATION.md`.
* Confirm artifact policy: no raw data, heavy artifacts, local DBs, or `runs/**` committed.

### Non-Goals
* Do not claim alpha/profitability/tradability/production readiness.
* Do not begin any next campaign.

### Expected Files / Directories
* `docs/governance/WORKFLOW2_INTEGRATION.md`
* `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/CLOSEOUT.md`
* Any final governance integration code/tests

### Forbidden Changes
* No real data; no broker/live scope; no claims; no next-campaign work.

### Validation Commands
```bash
git status --short
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
python tools/hooks/canary_runner.py
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/CLOSEOUT.md
test -f docs/governance/WORKFLOW2_INTEGRATION.md
find data -type f ! -name README.md ! -name .gitkeep -print
find metadata -type f ! -name README.md ! -name .gitkeep -print
git ls-files runs
```

### Artifact Policy
Commit only integration code, acceptance-audit notes, the closeout doc, tests, and docs.
Never commit `runs/**`, raw data, heavy artifacts, or local DB files. Explicit staging only.

### Done Criteria
* Workflow 2 integration is documented and exercised.
* The acceptance audit passes (or records a truthful `BLOCKED`).
* Final semantic done-check passes; `CLOSEOUT.md` exists with a final verdict (`COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`).
* Artifact audit is clean.

### Handoff Requirements
Summarize integration, acceptance-audit results, final verdict, and artifact audit.

### Review Requirements
Claude Opus review must perform the final semantic done-check across the whole campaign, not just per-phase tests.

### Auto-Merge Eligibility
Standard YELLOW gates; final verdict recorded in `CLOSEOUT.md`.

---

## Campaign-Wide Done Criteria

The campaign is done when:

* All 20 phases (`ARGOV-P00` … `ARGOV-P19`) are complete with `PASS`/`PASS_WITH_WARNINGS` verdicts.
* All acceptance gates in `ACCEPTANCE.md` pass.
* The governance objects, ledgers, evidence bundles, promotion gate, reviewer-independence rules, negative controls, registry integration, CLI, and claim guard exist, are tested, and fail closed where required.
* The synthetic end-to-end governance dry run passes with negative controls failing closed.
* The final semantic done-check passes and `CLOSEOUT.md` records the final verdict.
* No raw data, heavy artifacts, local DBs, caches, logs, or `runs/**` are committed.
* No broker/live/paper, real-data, or alpha-search scope exists; no alpha/profitability/tradability claims exist.

## Scope Boundary Reminders

Aggressive about evidence governance; conservative about market claims and trading scope.
This campaign installs the admissibility protocol only. It does not search for alpha,
ingest real data, connect to brokers, or claim profitability. Future campaigns
(`ALPHA_DATA_FOUNDATION_V1`, `ALPHA_FEATURE_LABEL_FOUNDATION_V1`,
`ALPHA_AGENT_FACTORY_MVP`, `ALPHA_FUTURES_CORE_ALPHA_V1`,
`ALPHA_PORTFOLIO_ALPHA_BOOK_V1`, `ALPHA_VALIDATION_GOVERNANCE_V1`) build on this gate but
are not started here.

## Forbidden Path Reminders

* Never commit: `data/raw/**`, `data/canonical/**`, `data/factors/**`, `data/labels/**`, `data/cache/**`, `metadata/*.sqlite`, `*.db`, `*.wal`, `*.parquet`/`*.arrow`/`*.feather` (outside documented tiny fixtures), logs, caches, `runs/**`, generated heavy artifacts.
* Never introduce: `src/alpha_system/execution/broker/**`, `live/**`, `paper/**`, `order_router*`, `src/alpha_system/broker/**`, `src/alpha_system/live/**`.
* Never use `git add .` or `git add -A`; never force push.

## Review and Merge Rules

* Every phase is YELLOW and requires fresh Claude Opus review with a `verdict.json`.
* Merge requires `PASS`/`PASS_WITH_WARNINGS`, passing checks, valid handoff, clean artifact policy, no forbidden paths, no STOP file, CI pass if configured, and a passing semantic done-check.
* `REWORK` routes to the bounded repair loop (max 3 attempts); `BLOCKED`/`FAIL` stop the phase with a truthful blocked handoff. Fake completion is forbidden.
