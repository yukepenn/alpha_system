# ARGOV-P10 Handoff - RejectedIdeaLedger / Research Graveyard

## Summary

Implemented `RejectedIdeaRecord` in
`alpha_system.governance.rejected_idea` as governance metadata only. The record
uses a frozen slots dataclass, deterministic `rej_...` governance IDs, canonical
serialization, and fail-closed `GovernanceValidationError` validation.

The record carries the campaign-required fields:

- `rejected_id`
- `alpha_spec_id_or_hypothesis_id`
- `reason_category`
- `evidence_references`
- `duplicate_links`
- `leakage_cost_weakness_notes`
- `reviewer`
- `created_at`

`rejected_id` is generated from all non-ID content fields and is recomputed
during validation. `alpha_spec_id_or_hypothesis_id` accepts only valid
`AlphaSpec` or `HypothesisCard` governance IDs. `created_at` is validated as a
UTC `YYYY-MM-DDTHH:MM:SSZ` timestamp.

Implemented a closed `RejectedIdeaReasonCategory` enum with these categories:

- `duplicate`
- `leakage`
- `weak_evidence`
- `cost`
- `failed_diagnostics`
- `out_of_scope`
- `other`

Unknown categories fail closed and are not coerced into `other`. Category
semantics are documented in code and in
`docs/governance/REJECTED_IDEA_LEDGER.md`.

Implemented `ResearchGraveyardLedger` as an in-memory append-only ledger with:

- `append(...)`
- `list_records()`
- `lookup_by_id(...)`
- `lookup_by_referenced_idea(...)`
- canonical JSON snapshot round-trip helpers

The ledger has no delete, remove, or overwrite API. Appending a duplicate
`rejected_id` raises a structured validation error rather than replacing an
existing rejection.

Implemented explicit linked reconsideration via
`RejectedIdeaReconsideration` and `append_reconsideration(...)`. Reconsideration
links are appended separately, must point to an existing rejected record, and do
not mutate or erase the original rejection. The data model records that a
rejected idea does not imply a permanent ban through the
`REJECTION_IS_PERMANENT_BAN = False` constant and the
`RejectedIdeaRecord.implies_permanent_ban` property.

Added `docs/governance/REJECTED_IDEA_LEDGER.md` documenting the object, reason
categories, fail-closed behavior, durability guarantee, append-only ledger, and
explicit reconsideration semantics. Updated the README snapshot for `ARGOV-P10`,
the next phase `ARGOV-P11`, the new module, the new doc, and unchanged safety
boundaries.

No fixtures were added in this phase.

## Staged Files

Exact files staged after explicit staging:

- `README.md`
- `docs/governance/REJECTED_IDEA_LEDGER.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P10.md`
- `src/alpha_system/governance/rejected_idea.py`
- `tests/unit/governance/test_rejected_idea.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before staging. Output:

```text
 M README.md
 M src/alpha_system/governance/rejected_idea.py
?? docs/governance/REJECTED_IDEA_LEDGER.md
?? tests/unit/governance/test_rejected_idea.py
```

- `python -c "import alpha_system.governance.rejected_idea"` - failed with exit
  1:

```text
ModuleNotFoundError: No module named 'alpha_system'
```

  Reason: the current shell environment does not put `src/` on `sys.path` for a
  bare `python -c` invocation. This matches the import-path behavior documented
  in prior phase handoffs. As a diagnostic confirmation, `PYTHONPATH=src python
  -c "import alpha_system.governance.rejected_idea"` passed with exit 0, and
  pytest uses `pyproject.toml` `pythonpath = ["src"]`.

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_rejected_idea.py -q` - passed:

```text
........................................                                 [100%]
40 passed in 0.03s
```

- `python -m pytest tests/unit/governance -q` - passed:

```text
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 64%]
........................................................................ [ 85%]
................................................                         [100%]
336 passed in 0.21s
```

- `test -f docs/governance/REJECTED_IDEA_LEDGER.md` - passed with exit 0 and
  no output.

- `test -f README.md` - passed with exit 0 and no output.

- `git ls-files runs` - passed with empty output.

- `find data -type f ! -name README.md ! -name ".gitkeep" -print` - passed
  with empty output.

- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` -
  passed with empty output.

- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - passed
  with empty output.

Additional local validation and formatting:

- `python -m ruff format src/alpha_system/governance/rejected_idea.py
  tests/unit/governance/test_rejected_idea.py` - passed; final run reported
  files formatted.

- `python -m ruff check --fix tests/unit/governance/test_rejected_idea.py` -
  fixed import ordering only.

- `python -m ruff check src/alpha_system/governance/rejected_idea.py
  tests/unit/governance/test_rejected_idea.py` - passed:

```text
All checks passed!
```

- `python -m ruff format --check src/alpha_system/governance/rejected_idea.py
  tests/unit/governance/test_rejected_idea.py` - passed:

```text
2 files already formatted
```

- `git diff --check` - passed with exit 0 and no output.

Skipped checks: none of the spec-requested executor validation commands were
skipped. Claude review, reviewer execution, `review.md`, and `verdict.json`
were not run or created by Codex because the executor prompt reserves review
and verdict handling for Ralph and the independent reviewer.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path after explicit
  staging.
- The data, metadata, and Parquet artifact audits returned empty output.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB
  journal, WAL, Parquet, Arrow, Feather, log, cache, model binary, heavy
  artifact, or run artifact is staged.
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
  label computations, metric computations from market data, real-data
  ingestion, alpha search, strategy optimization, portfolio allocation, CLI, or
  registry persistence scope was introduced.
- No `PromotionDecision`, promotion-gate state machine, `EvidenceBundle`, or
  registry/DB persistence work was implemented.
- No edits were made to forbidden broker/live/paper/order-router paths, data
  roots, metadata DB paths, artifact roots, or `runs/**`.
- Tests were added only under authorized governance paths. Existing tests were
  not weakened, skipped, deleted, or relaxed.
- No fixtures were added in this phase.
- No alpha, profitability, tradability, candidate, validated, factor-library,
  promotion-success, or production-readiness claim was introduced.
- The README snapshot was updated for `ARGOV-P10` and the next phase
  `ARGOV-P11`.

## Review Note

Fresh independent Claude Opus review is still required for this YELLOW phase.
Codex did not call Claude, did not run reviewer, did not create review
artifacts, did not create `verdict.json`, and did not mark the phase PASS.
