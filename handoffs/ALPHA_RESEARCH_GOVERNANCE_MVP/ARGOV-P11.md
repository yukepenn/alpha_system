# ARGOV-P11 Handoff - PromotionDecision and PromotionGate State Machine

## Summary

Implemented `PromotionDecision` in `alpha_system.governance.promotion` as
governance metadata only. The object uses a frozen slots dataclass, deterministic
`prom_...` governance IDs, canonical serialization, and fail-closed
`GovernanceValidationError` validation.

The record carries the campaign-required fields:

- `promotion_id`
- `alpha_spec_id`
- `evidence_bundle_id`
- `trial_ledger_refs`
- `previous_state`
- `next_state`
- `decision`
- `rationale`
- `reviewer_verdict_id`
- `warnings`
- `timestamp`

`promotion_id` is generated from all non-ID content fields and is recomputed
during validation. `previous_state` must be `REVIEWED`. `next_state` and
`decision` must match one of `REJECTED`, `WATCH`, `CANDIDATE`, or `VALIDATED`.
`reviewer_verdict_id` is validated as an opaque `rver_...` ID seam for
`ARGOV-P12`; this phase does not implement reviewer-independence or self-approval
enforcement.

Implemented `alpha_system.governance.promotion_gate` with the MVP lifecycle
state machine:

```text
DRAFT -> REGISTERED
REGISTERED -> IMPLEMENTATION_ALLOWED
IMPLEMENTATION_ALLOWED -> IMPLEMENTED
IMPLEMENTED -> DIAGNOSTICS_ALLOWED
DIAGNOSTICS_ALLOWED -> DIAGNOSTICS_RUN
DIAGNOSTICS_RUN -> EVIDENCE_READY
EVIDENCE_READY -> REVIEWED
REVIEWED -> REJECTED | WATCH | CANDIDATE | VALIDATED
any -> REJECTED
```

The state machine composes the existing validated governance objects where they
exist: `HypothesisCard`, `AlphaSpec`, `StudySpec`, `TrialLedgerRecord`,
`EvidenceBundle`, and `RejectedIdeaRecord`.

Candidate and validated promotion now fail closed without:

- a valid `PromotionDecision`;
- a valid `EvidenceBundle`;
- complete validated `TrialLedgerRecord` metadata;
- matching `alpha_spec_id`, `evidence_bundle_id`, and trial reference sets;
- visibility of failed or abandoned trial records;
- explicit metadata for any locked-test contamination.

`any -> REJECTED` requires a valid `RejectedIdeaRecord` and explicit rejection
reason. `REVIEWED -> REJECTED` also requires a matching `PromotionDecision`.

The prohibited MVP states `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and
`PRODUCTION_READY` are not members of the reachable state set and are not
transition targets. Attempts to use them fail closed with a structured
`prohibited_mvp_state` issue. `PromotionDecision` exposes explicit false
properties for live approval, capital allocation, and production readiness.

Added:

- `docs/governance/PROMOTION_GATE.md`
- `docs/governance/GOVERNANCE_STATE_MACHINE.md`

Updated `README.md` with the P11 snapshot, next planned phase
`ARGOV-P12 - ReviewerVerdict and Independence Rules`, the new durable modules,
the two new docs, and unchanged safety boundaries.

No fixtures were added in this phase.

## Staged Files

Exact files staged after explicit staging:

- `README.md`
- `docs/governance/GOVERNANCE_STATE_MACHINE.md`
- `docs/governance/PROMOTION_GATE.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P11.md`
- `src/alpha_system/governance/promotion.py`
- `src/alpha_system/governance/promotion_gate.py`
- `tests/unit/governance/test_promotion.py`
- `tests/unit/governance/test_promotion_gate_state_machine.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before staging with only allowed P11 paths:

```text
 M README.md
 M src/alpha_system/governance/promotion.py
?? docs/governance/GOVERNANCE_STATE_MACHINE.md
?? docs/governance/PROMOTION_GATE.md
?? src/alpha_system/governance/promotion_gate.py
?? tests/unit/governance/test_promotion.py
?? tests/unit/governance/test_promotion_gate_state_machine.py
```

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_promotion.py tests/unit/governance/test_promotion_gate_state_machine.py -q`
  - passed:

```text
.....................................................................    [100%]
69 passed in 0.07s
```

- `python -m pytest tests/unit/governance -q`
  - passed:

```text
........................................................................ [ 17%]
........................................................................ [ 35%]
........................................................................ [ 53%]
........................................................................ [ 71%]
........................................................................ [ 88%]
.............................................                            [100%]
405 passed in 0.22s
```

- `test -f docs/governance/PROMOTION_GATE.md` - passed with exit 0 and no
  output.

- `test -f docs/governance/GOVERNANCE_STATE_MACHINE.md` - passed with exit 0
  and no output.

- `test -f README.md` - passed with exit 0 and no output.

- `git ls-files runs` - passed with empty output.

- `find data -type f ! -name README.md ! -name .gitkeep -print` - passed with
  empty output.

- `find metadata -type f ! -name README.md ! -name .gitkeep -print` - passed
  with empty output.

- `find artifacts -type f -size +1M -print` - passed with empty output.

- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - passed
  with empty output.

Additional local validation and formatting:

- `python -m ruff format src/alpha_system/governance/promotion.py src/alpha_system/governance/promotion_gate.py tests/unit/governance/test_promotion.py tests/unit/governance/test_promotion_gate_state_machine.py`
  - passed; final formatting run reported files formatted.

- `python -m ruff check src/alpha_system/governance/promotion.py src/alpha_system/governance/promotion_gate.py tests/unit/governance/test_promotion.py tests/unit/governance/test_promotion_gate_state_machine.py`
  - passed:

```text
All checks passed!
```

- `python -m ruff format --check src/alpha_system/governance/promotion.py src/alpha_system/governance/promotion_gate.py tests/unit/governance/test_promotion.py tests/unit/governance/test_promotion_gate_state_machine.py`
  - passed:

```text
4 files already formatted
```

- `git diff --check` - passed with exit 0 and no output.

Post-staging validation:

- `git diff --cached --name-only` - passed after explicit staging with exactly
  this curated set:

```text
README.md
docs/governance/GOVERNANCE_STATE_MACHINE.md
docs/governance/PROMOTION_GATE.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P11.md
src/alpha_system/governance/promotion.py
src/alpha_system/governance/promotion_gate.py
tests/unit/governance/test_promotion.py
tests/unit/governance/test_promotion_gate_state_machine.py
```

- `git diff --cached --check` - passed with exit 0 and no output.

- `git diff --cached --name-only | rg ^runs/` - passed with no matches. `rg`
  returned exit 1 because no staged path matched `runs/`.

- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/.*\.(sqlite|sqlite3|db|db-journal|wal)$|^artifacts/|\.(parquet|arrow|feather|pkl|onnx|npy|log)$)'`
  - passed with no matches. `rg` returned exit 1 because no staged path matched
  forbidden artifact patterns.

One malformed supplemental diagnostic command was attempted without quoting the
shell glob:

```text
find . -name *.parquet -not -path ./tests/fixtures/* -print
```

It failed with shell expansion before `find` evaluation. The exact quoted
spec-command shown above was rerun and passed with empty output.

CI repair after PR #57:

- GitHub Actions `validate` failed because pytest imported the existing
  `tests/test_state_machine.py` module, then attempted to collect the new P11
  state-machine test module with the same basename.
- Repaired by renaming only the new P11 test module to
  `tests/unit/governance/test_promotion_gate_state_machine.py`.
- `python -m pytest` passed after the rename:

```text
1242 passed in 15.80s
```

- `python -m pytest tests/unit/governance/test_promotion.py tests/unit/governance/test_promotion_gate_state_machine.py -q`
  passed:

```text
.....................................................................    [100%]
69 passed in 0.07s
```

Skipped checks: none of the spec-requested executor validation commands were
skipped. Claude review, reviewer execution, `review.md`, and `verdict.json` were
not run or created by Codex because the executor prompt reserves review and
verdict handling for Ralph and the independent reviewer.

## Artifact Policy

- `git ls-files runs` returned empty.
- The data, metadata, artifact-size, and quoted Parquet audits returned empty
  output.
- The staged set contains no `runs/` path after explicit staging.
- No raw/canonical/factor/label/cache data, local DB, DB journal, WAL, Parquet,
  Arrow, Feather, log, cache, model binary, heavy artifact, or run artifact is
  staged.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created or staged by Codex.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No commit was created by Codex in this executor step.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No broker, live, paper, order-routing, production deployment, PR creation, or
  merge scope was introduced.
- No diagnostics, studies, backtests, variant searches, factor computations,
  label computations, metric computations from market data, real-data ingestion,
  alpha search, strategy optimization, portfolio allocation, CLI, or registry
  persistence scope was introduced.
- No edits were made to forbidden broker/live/paper/order-router paths, data
  roots, metadata DB paths, artifact roots, or `runs/**`.
- Tests were added only under authorized governance paths. Existing tests were
  not weakened, skipped, deleted, or relaxed.
- No fixtures were added in this phase.
- No alpha, profitability, tradability, live-approval, capital-allocation,
  production-readiness, or market-truth claim was introduced.
- The reviewer-independence enforcement seam exists through
  `reviewer_verdict_id`; full independence and self-approval enforcement remain
  deferred to `ARGOV-P12`.

## Review Note

Fresh independent Claude Opus review is still required for this YELLOW phase.
Codex did not call Claude, did not run reviewer, did not create review artifacts,
did not create `verdict.json`, and did not mark the phase PASS.
