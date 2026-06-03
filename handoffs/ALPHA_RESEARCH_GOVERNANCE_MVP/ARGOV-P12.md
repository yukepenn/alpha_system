# ARGOV-P12 Handoff - ReviewerVerdict and Independence Rules

## Summary

Implemented `ReviewerVerdict` in `alpha_system.governance.reviewer_verdict` as
governance metadata only. The object uses a frozen slots dataclass, the campaign
required serialized fields, deterministic `rver_...` ID generation from verdict
content, canonical serialization, and fail-closed `GovernanceValidationError`
validation.

The serialized required fields are:

- `reviewer_id`
- `role`
- `independence_statement`
- `verdict`
- `blocking_issues`
- `warnings`
- `checked_artifacts`
- `checked_commands`
- `timestamp`

`verdict` is constrained to `PASS`, `PASS_WITH_WARNINGS`, `REWORK`, and `BLOCKED`.
Only `PASS` and `PASS_WITH_WARNINGS` are merge eligible. Missing fields, null
fields, unknown fields, invalid types, empty reviewer identity, empty role, empty
`independence_statement`, invalid timestamps, empty checked artifact/command lists,
invalid list items, duplicate list items, and invalid ID-generation content fail
closed with structured validation issues.

Implemented reviewer-independence enforcement in
`alpha_system.governance.promotion_gate`:

- `EVIDENCE_READY -> REVIEWED` requires a present validated `ReviewerVerdict`.
- `reviewer_id` must differ from `implementer_id`.
- `role` must differ from `implementer_role`.
- missing implementer identity or role fails closed.
- reviewer self-approval is blocked.
- `REVIEWED -> REJECTED | WATCH | CANDIDATE | VALIDATED` requires the independent
  verdict referenced by the `PromotionDecision`.
- `CANDIDATE` and `VALIDATED` additionally require a merge-eligible verdict and a
  matching `EvidenceBundle.reviewer_verdict_reference`.

ARGOV-P11 promotion-gate behavior is preserved. The gate still blocks missing
`PromotionDecision`, missing `EvidenceBundle`, missing or incomplete
`TrialLedgerRecord` metadata, failed-run omission, unrecorded locked-test
contamination, undeclared transitions, and prohibited MVP states.

Added `docs/governance/REVIEWER_INDEPENDENCE.md` and updated
`docs/governance/PROMOTION_GATE.md`, `docs/governance/GOVERNANCE_STATE_MACHINE.md`,
and `README.md` to describe the P12 object, gate wiring, self-approval block, next
planned phase `ARGOV-P13 - Negative-Control Canary Catalog`, and unchanged safety
boundaries. No review artifact was created by Codex; independent review remains
Ralph/Claude-owned.

No fixtures were added in this phase.

## Staged Files

Exact files staged after explicit staging:

- `README.md`
- `docs/governance/GOVERNANCE_STATE_MACHINE.md`
- `docs/governance/PROMOTION_GATE.md`
- `docs/governance/REVIEWER_INDEPENDENCE.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P12.md`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/promotion_gate.py`
- `src/alpha_system/governance/reviewer_verdict.py`
- `tests/unit/governance/test_promotion_gate_state_machine.py`
- `tests/unit/governance/test_reviewer_independence.py`
- `tests/unit/governance/test_reviewer_verdict.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before staging with only allowed ARGOV-P12 paths:

```text
 M README.md
 M docs/governance/GOVERNANCE_STATE_MACHINE.md
 M docs/governance/PROMOTION_GATE.md
 M src/alpha_system/governance/__init__.py
 M src/alpha_system/governance/promotion_gate.py
 M src/alpha_system/governance/reviewer_verdict.py
 M tests/unit/governance/test_promotion_gate_state_machine.py
?? docs/governance/REVIEWER_INDEPENDENCE.md
?? tests/unit/governance/test_reviewer_independence.py
?? tests/unit/governance/test_reviewer_verdict.py
```

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_reviewer_verdict.py -q` - passed:

```text
.......................                                                  [100%]
23 passed in 0.02s
```

- `python -m pytest tests/unit/governance/test_reviewer_independence.py -q` -
  passed:

```text
.........                                                                [100%]
9 passed in 0.02s
```

- `python -m pytest tests/unit/governance -q` - passed:

```text
........................................................................ [ 16%]
........................................................................ [ 32%]
........................................................................ [ 49%]
........................................................................ [ 65%]
........................................................................ [ 82%]
........................................................................ [ 98%]
.....                                                                    [100%]
437 passed in 0.24s
```

- `test -f docs/governance/REVIEWER_INDEPENDENCE.md` - passed with exit 0 and
  no output.

- `test -f src/alpha_system/governance/reviewer_verdict.py` - passed with exit 0
  and no output.

- `git ls-files runs` - passed with empty output.

Additional local validation:

- `git diff --check` - passed with exit 0 and no output.
- A supplemental stale-wording search for the old reviewer-verdict seam text was
  rerun with safe quoting and returned no matches.

Post-staging validation:

- `git diff --cached --name-only` - passed after explicit staging with exactly
  this curated set:

```text
README.md
docs/governance/GOVERNANCE_STATE_MACHINE.md
docs/governance/PROMOTION_GATE.md
docs/governance/REVIEWER_INDEPENDENCE.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P12.md
src/alpha_system/governance/__init__.py
src/alpha_system/governance/promotion_gate.py
src/alpha_system/governance/reviewer_verdict.py
tests/unit/governance/test_promotion_gate_state_machine.py
tests/unit/governance/test_reviewer_independence.py
tests/unit/governance/test_reviewer_verdict.py
```

- `git diff --cached --check` - passed with exit 0 and no output.

- `git diff --cached --name-only | rg '^runs/'` - passed with no matches. `rg`
  returned exit 1 because no staged path matched `runs/`.

- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/.*\.(sqlite|sqlite3|db|db-journal|wal)$|^artifacts/|\.(parquet|arrow|feather|pkl|onnx|npy|log)$)'`
  - passed with no matches. `rg` returned exit 1 because no staged path matched
  forbidden artifact patterns.

No requested validation command was skipped.

## Artifact Policy

Explicit staging was used by path. `git add .`, `git add -A`, force push,
destructive cleanup, run-local handoff staging, and `runs/**` staging were not
used. `git ls-files runs` returned empty output. No raw data, canonical data,
factor data, label data, cache, SQLite or DB file, log, generated report bundle,
Parquet, Arrow, Feather, model binary, credential, or heavy artifact path is
staged.

## Scope And Claims

No broker, live, paper, order-routing, real-data-ingestion, alpha-search,
strategy-optimization, portfolio-allocation, production-deployment, PR creation,
merge, reviewer invocation, `review.md`, or `verdict.json` scope was introduced.

`ReviewerVerdict`, `PASS`, `PASS_WITH_WARNINGS`, `CANDIDATE`, and `VALIDATED`
remain governance metadata only. This phase introduced no market-truth, alpha
validity, profitability, tradability, live approval, capital allocation, or
production-readiness claims.
