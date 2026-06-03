# ARGOV-P04 Handoff — HypothesisCard and Pre-Registration Protocol

## Summary

Implemented the `HypothesisCard` governance contract in
`alpha_system.governance.hypothesis_card` using the ARGOV-P02 primitives for
deterministic content-bound IDs, canonical serialization, and fail-closed
structured validation.

The contract requires all campaign-declared `HypothesisCard` fields, validates
`hypothesis_id` as a deterministic content-bound `hyp_...` ID, validates
timezone-aware `created_at`, rejects unknown fields, rejects empty/null/malformed
or vague content, and round-trips through canonical JSON without defaults,
coercion, or dropped fields. `falsification_criteria` is mandatory and must
contain substantive entries with an explicit rejection or blocking condition.

The pre-registration protocol is `validate_pre_registration(...)` /
`assert_pre_registered(...)`. It is a pure precondition check for
`DRAFT -> REGISTERED`: missing or invalid `HypothesisCard`, missing or invalid
`AlphaSpec`, unsupported transition names, or mismatched `hypothesis_id` blocks
registration with structured validation errors. A valid linked pair returns a
`RegisteredResearchPair`. The check performs no I/O, persistence, implementation,
study execution, registry write, candidate entry, or factor-library entry.

Docs and template deliverables were added:

- `docs/governance/PRE_REGISTRATION.md`
- `templates/governance/hypothesis_card.template.yaml`

The README snapshot was updated in place to reflect ARGOV-P04 as
active/just-completed, ARGOV-P05 as next planned, the new module/docs/template,
and unchanged safety boundaries. It contains no generated run details, local
artifact paths, verdict text, or prohibited claims.

## Staged Files

Exact staged files after explicit staging:

- `README.md`
- `docs/governance/PRE_REGISTRATION.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P04.md`
- `src/alpha_system/governance/hypothesis_card.py`
- `templates/governance/hypothesis_card.template.yaml`
- `tests/fixtures/governance/hypothesis_card_valid.json`
- `tests/unit/governance/test_hypothesis_card.py`
- `tests/unit/governance/test_pre_registration.py`

No `runs/**` path is staged.

## Validation Results

Final validation after the last source edit:

- `git status --short` — passed before handoff creation/staging. Output showed
  only ARGOV-P04 allowed paths:

```text
 M README.md
 M src/alpha_system/governance/hypothesis_card.py
?? docs/governance/PRE_REGISTRATION.md
?? templates/governance/hypothesis_card.template.yaml
?? tests/fixtures/governance/hypothesis_card_valid.json
?? tests/unit/governance/test_hypothesis_card.py
?? tests/unit/governance/test_pre_registration.py
```

- `python tools/verify.py --smoke` — passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_hypothesis_card.py tests/unit/governance/test_pre_registration.py -q` — passed:

```text
.....................                                                    [100%]
21 passed in 0.03s
```

- `python -m pytest tests/unit/governance -q` — passed:

```text
............................................................             [100%]
60 passed in 0.04s
```

- `test -f src/alpha_system/governance/hypothesis_card.py` — passed with exit 0
  and no output.

- `test -f docs/governance/PRE_REGISTRATION.md` — passed with exit 0 and no
  output.

- `test -f templates/governance/hypothesis_card.template.yaml` — passed with
  exit 0 and no output.

- `PYTHONPATH=src python -c "import alpha_system.governance.hypothesis_card"` —
  passed with exit 0 and no output.

- `git ls-files runs` — passed with empty output.

- `find data -type f ! -name README.md ! -name ".gitkeep" -print` — passed with
  empty output.

- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — passed
  with empty output.

- `find artifacts -type f -size +1M -print` — passed with empty output.

- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` — passed
  with empty output.

- `git diff --cached --name-only` — passed after explicit staging. Output:

```text
README.md
docs/governance/PRE_REGISTRATION.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P04.md
src/alpha_system/governance/hypothesis_card.py
templates/governance/hypothesis_card.template.yaml
tests/fixtures/governance/hypothesis_card_valid.json
tests/unit/governance/test_hypothesis_card.py
tests/unit/governance/test_pre_registration.py
```

An interim narrow test run before docs and README edits also passed:

```text
.....................                                                    [100%]
21 passed in 0.03s
```

Skipped checks: none of the spec-requested commands were skipped.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path after explicit
  staging.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB
  journal, WAL, Parquet, Arrow, Feather, log, cache, model binary, heavy
  artifact, or run artifact is staged.
- No run-local `handoff.md` under
  `runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP/phases/ARGOV-P04/`
  was created or staged.
- No run-local `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created or staged by Codex.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No broker, live, paper, order-routing, production-deployment,
  real-data-ingestion, alpha-search, factor-computation, label materialization,
  diagnostics, backtest, registry/persistence, CLI, reviewer-verdict,
  promotion, or report-builder scope was introduced.
- ARGOV-P02 primitives and the ARGOV-P03 `AlphaSpec` contract/no-code gate were
  consumed read-only and not weakened.
- Tests were added only under the authorized governance paths. No tests were
  weakened, skipped, or relaxed.
- No alpha, profitability, tradability, paper-readiness, live-readiness,
  broker-readiness, capital-allocation, production-readiness,
  deployment-readiness, implementation-approval, candidate-status, or
  factor-library-entry claim was introduced.

## Review Boundary

No Claude review was run by Codex. No `review.md` or `verdict.json` was created.
Ralph owns validation orchestration, independent review routing, verdict
parsing, PR creation, CI, merge gates, semantic done-checks, and phase PASS
marking.
