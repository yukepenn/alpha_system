# ALPHA_RESEARCH_GOVERNANCE_MVP Acceptance Criteria

## Acceptance Philosophy

Acceptance for this campaign is **semantic, not mechanical**. Passing tests are
necessary but never sufficient. A phase or gate is accepted only when the governance
machinery genuinely **fails closed**, the gates genuinely **block** missing
prerequisites, failures and rejections are genuinely **visible and durable**, reviewer
independence is genuinely **enforced**, and no prohibited scope or claim is present.

The campaign installs the admissibility protocol for future AI alpha research. It owns
evidence and truth, not market results. Therefore acceptance explicitly rejects any
outcome where the schema exists but invalid input is silently accepted, where a candidate
can exist without an evidence bundle, where promotion can happen without a trial ledger or
an independent reviewer verdict, where failed or rejected ideas can be hidden, or where any
alpha/profitability/tradability claim appears.

The final verdict for the campaign is one of `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or
`BLOCKED`. A truthful `BLOCKED` is acceptable and strongly preferred over a false
`COMPLETE`.

## Campaign-Level Acceptance Criteria

1. All 20 phases (`ARGOV-P00` … `ARGOV-P19`) are complete with merged `PASS` or `PASS_WITH_WARNINGS` verdicts, or a truthful `BLOCKED` is recorded.
2. Every governance object defined in `campaign.yaml` (`governance_objects`) exists, validates fail-closed, and carries all required fields.
3. The governance state machine enforces every block defined in `campaign.yaml` (`governance_state_machine`).
4. The prohibited MVP states `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and `PRODUCTION_READY` are unreachable.
5. The synthetic end-to-end governance dry run passes with negative controls failing closed.
6. The Workflow 2 handoff/review/verdict integration is present and exercised.
7. The final semantic done-check passes (or records a truthful `BLOCKED`), and `CLOSEOUT.md` records the final verdict.
8. No raw data, heavy artifacts, local DBs, caches, logs, or `runs/**` are committed.
9. No broker/live/paper, real-data, or alpha-search scope exists, and no alpha/profitability/tradability claim exists anywhere.

## Object-Level Acceptance Criteria

Each governance object is accepted only when it carries all required fields (per
`campaign.yaml` → `governance_objects`), validates fail-closed on missing/invalid input,
round-trips through serialization deterministically, and does not imply more than its
stated purpose:

* `HypothesisCard` — falsification criteria present; implies neither approval nor validity.
* `AlphaSpec` — pre-registered, references a HypothesisCard; implies neither candidate status nor library entry.
* `FeatureRequest` — duplicate/equivalent exposure notes present from a read-only registry check; implies no implementation permission.
* `LabelSpec` — forbidden-feature-overlap and leakage checks present; implies no label quality.
* `StudySpec` — variant budget, locked-test policy, and negative controls present; implies no diagnostics passed.
* `TrialLedgerRecord` — failure_reason, oos_touched_flag, and locked_test_contamination_flag present; implies no success.
* `EvidenceBundle` — manifest, hashes, versions, negative-control results, and reviewer-verdict reference present; implies no promotion.
* `RejectedIdeaRecord` — reason category and evidence references present; implies no permanent ban.
* `PromotionDecision` — previous/next state, evidence and trial refs, and reviewer-verdict id present; implies no live/capital/production status.
* `ReviewerVerdict` — independence statement present; implies no market truth.
* `NegativeControlResult` — canary type, expected_failure, observed_result, pass_fail present; implies no alpha validity.
* `AlphaBookRecord` (stub) — pointer fields only; implies no capital/live/production status.

## State-Machine-Level Acceptance Criteria

* `DRAFT → REGISTERED` requires a valid HypothesisCard and AlphaSpec.
* `REGISTERED → IMPLEMENTATION_ALLOWED` requires AlphaSpec validation and no blocking duplicate/leakage issue.
* `IMPLEMENTED → DIAGNOSTICS_ALLOWED` requires a valid StudySpec.
* `DIAGNOSTICS_RUN → EVIDENCE_READY` requires an EvidenceBundle with manifest and trial refs.
* `EVIDENCE_READY → REVIEWED` requires an independent ReviewerVerdict.
* `REVIEWED → REJECTED/WATCH/CANDIDATE/VALIDATED` requires a PromotionDecision and gate checks.
* `any → REJECTED` requires a RejectedIdeaRecord and reason.
* No transition reaches `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, or `PRODUCTION_READY`.

## Evidence-Level Acceptance Criteria

* No candidate state exists without an EvidenceBundle.
* Every EvidenceBundle carries a manifest, code/config hashes, data/factor/label versions, a diagnostics summary, negative-control results, limitations, and a reviewer-verdict reference.
* Evidence artifacts referenced by the manifest remain local-only; only curated summaries are committed.

## Ledger-Level Acceptance Criteria

* Every trial — success or failure — is recorded in the TrialLedger; failed runs cannot be omitted.
* Variant counts and multiple-testing metadata are accumulated and visible.
* OOS reuse and locked-test contamination are flagged metadata; promotion is blocked when contamination is unrecorded.
* Rejected ideas are first-class RejectedIdeaRecord entries, not prose; reconsideration is explicit and linked.

## Canary-Level Acceptance Criteria

* The negative-control catalog includes random, permuted, future-shift (lookahead), and optimistic-fill canaries.
* The canary harness exercises no-lookahead, label-leakage, and optimistic-fill controls over synthetic fixtures.
* Every canary fails closed: a passing guard detects the injected fault. `python tools/hooks/canary_runner.py` passes.

## Registry-Level Acceptance Criteria

* Governance objects persist and resolve through the existing local registry/persistence layer.
* Integration tests use a temporary DB; no `metadata/*.sqlite` or DB file is staged or committed (`find metadata -type f` returns only README/.gitkeep).

## CLI / Tool-Level Acceptance Criteria

* Governance CLI commands exist (validate-spec, register-trial, build-evidence, review, promote) and pass smoke tests.
* The CLI enforces the governance gates; it cannot be used to bypass spec/study/evidence/verdict requirements.
* Validation tools under `tools/governance/**` exist and are tested.

## Workflow 2 Integration Acceptance

* Governance handoff/review/verdict artifacts integrate with the Workflow 2 conventions.
* Run-local artifacts remain under `runs/**` and are never committed; commit-eligible handoffs/reviews live under `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/**` and `reviews/ALPHA_RESEARCH_GOVERNANCE_MVP/**`.

## Artifact-Policy Acceptance

* `git ls-files runs` returns empty.
* `find data -type f ! -name README.md ! -name .gitkeep` returns empty.
* `find metadata -type f ! -name README.md ! -name .gitkeep` returns empty.
* `find artifacts -type f -size +1M` returns empty.
* No `*.parquet`/`*.arrow`/`*.feather` outside documented tiny `tests/fixtures/**`.
* Explicit staging only; no `git add .` / `git add -A`; no force push.

## Review-Level Acceptance

* Every YELLOW phase has a fresh Claude Opus review and a `verdict.json`.
* Merged phases have `PASS` or `PASS_WITH_WARNINGS` verdicts.
* Reviews verify governance completeness, fail-closed behavior, reviewer independence, ledger/evidence/promotion gating, canary fail-closed behavior, artifact policy, and absence of prohibited scope and claims.

## Prohibited Acceptance Shortcuts

The campaign is **not** accepted if any of the following is true:

* tests pass but no semantic review was performed;
* a schema exists but invalid specs do not fail closed;
* a candidate can be promoted without a TrialLedger;
* a candidate is accepted without an EvidenceBundle;
* failed ideas are omitted from the ledger;
* rejected ideas exist only in prose, not in the ledger;
* OOS is reused without contamination metadata;
* duplicate/equivalent exposure is not tracked;
* negative controls are not implemented or do not fail closed;
* no-lookahead canaries are missing;
* a reviewer can approve their own implementation;
* raw data or heavy artifacts are committed;
* a local DB is committed;
* any alpha/profitability/tradability/production-readiness claim is introduced;
* any broker/live/paper/order-routing or real-data/alpha-search scope is introduced.

## Required Final Validation Commands

```bash
cd ~/projects/alpha_system
git status --short
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
python -m pytest tests/no_lookahead -q
python tools/hooks/canary_runner.py

git ls-files runs
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

## Required Semantic Done-Check

Beyond passing tests, the final done-check (Claude Opus) must affirm that:

* the gates genuinely block missing prerequisites (no-AlphaSpec/no-StudySpec/no-EvidenceBundle/no-TrialLedger/no-ReviewerVerdict);
* failed and rejected ideas are durable and visible;
* reviewer independence and self-approval blocking are real;
* negative controls fail closed;
* no prohibited MVP state is reachable;
* no prohibited scope or claim exists;
* the artifact audit is clean.

## Final Closeout Requirements

* `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/CLOSEOUT.md` exists and records the final verdict and any warnings.
* `ACTIVE_CAMPAIGN.md` reflects campaign completion.
* Durable lessons are added to `project-skill` when applicable.

## Final Acceptance Verdicts

### `COMPLETE`
All campaign-level criteria met, all gates passed, semantic done-check clean, artifact
audit clean, no prohibited scope or claims.

### `COMPLETE_WITH_WARNINGS`
All hard criteria met, but non-blocking warnings (e.g. documented deferrals, minor
limitations) are recorded in `CLOSEOUT.md`.

### `BLOCKED`
A hard criterion cannot be met (e.g. a gate cannot be made to fail closed, or a required
object cannot be completed in scope). The blocker is recorded truthfully; fake completion
is forbidden.
