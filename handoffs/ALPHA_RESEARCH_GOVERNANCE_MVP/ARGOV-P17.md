# ARGOV-P17 Handoff - Unsupported-Claim Guard and Governance Report Templates

## Summary

Implemented the governance unsupported-claim guard in
`src/alpha_system/governance/claims.py` and exported the module from
`alpha_system.governance`. The guard scans governance text artifacts and rejects
unsupported claim language with structured `UnsupportedClaimViolation` records and
`UnsupportedClaimError`, a `GovernanceValidationError` subclass.

Coverage categories:

- `alpha_validity`
- `profitability`
- `tradability`
- `robustness`
- `production_readiness`
- `paper_readiness`
- `live_readiness`
- `broker_readiness`
- `real_data_readiness`

The guard fails closed on malformed or undecidable input. It accepts only decoded,
non-empty strings and rejects non-string roots, empty strings, replacement characters,
NUL bytes, and other non-whitespace control characters.

The allowlist is explicit and documented. It permits only local, non-asserting contexts:
explicit no-claims or no-assertion statements; blocked-language policy, taxonomy, or
vocabulary catalogs; guard or detector statements that reject blocked claim vocabulary;
and governance identifiers `AlphaSpec` and `alpha_spec_id`. The allowlist is
sentence-local and is not a whole-file bypass.

## Bounded Repair Attempt 1

Addressed the in-scope REWORK findings by tightening the sentence-local allowlist:

- Removed repository/package and shortened alpha identifier names from the governance
  identifier context. Only `AlphaSpec` and `alpha_spec_id` remain allowlisted.
- Narrowed the guard-behavior context to sentences that name a guard or detector, use a
  blocking/detection/rejection/prevention verb, and explicitly describe claim vocabulary,
  terms, phrases, assertions, categories, or taxonomy. General validation, policy, and
  template requirement text no longer creates an allowlist context.
- Updated `docs/governance/UNSUPPORTED_CLAIM_GUARD.md` to document the exact narrowed
  allowlist and to state that generic repository/package/alpha identifiers and generic
  validation/template requirement phrasing are not allowlisted.
- Added regression tests proving those co-location patterns still produce structured
  unsupported-claim violations.

## Report Templates

Added `templates/governance/evidence_governance_report.template.md`. The template
requires:

- evidence references;
- limitations;
- standardized no-claims language;
- required checks for evidence visibility, limitation visibility, failed-run visibility,
  and unsupported-claim guard validation before use.

Updated `templates/governance/README.md` to list the report template. No optional report
builder was added because the template and tests satisfy the phase scope without adding a
new generated-report surface.

## Documentation And README

Added `docs/governance/UNSUPPORTED_CLAIM_GUARD.md` documenting the prohibited taxonomy,
fail-closed contract, explicit allowlist, and template enforcement. Updated
`docs/governance/README.md` and the root `README.md` snapshot to include ARGOV-P17
deliverables, next phase `ARGOV-P18 - Synthetic End-to-End Governance Dry Run`, new durable
modules/templates/docs, and unchanged safety boundaries.

## Staged Files

Exact files staged explicitly:

```text
README.md
docs/governance/README.md
docs/governance/UNSUPPORTED_CLAIM_GUARD.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P17.md
src/alpha_system/governance/__init__.py
src/alpha_system/governance/claims.py
templates/governance/README.md
templates/governance/evidence_governance_report.template.md
tests/unit/governance/test_claims_guard.py
```

No `runs/**` path is included.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before handoff/staging with only allowed ARGOV-P17 paths:

```text
 M README.md
 M docs/governance/README.md
 M src/alpha_system/governance/__init__.py
 M src/alpha_system/governance/claims.py
 M templates/governance/README.md
?? docs/governance/UNSUPPORTED_CLAIM_GUARD.md
?? templates/governance/evidence_governance_report.template.md
?? tests/unit/governance/test_claims_guard.py
```

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance -q` - passed:

```text
499 passed in 1.87s
```

- `test -f docs/governance/UNSUPPORTED_CLAIM_GUARD.md` - passed with exit 0 and no output.

- `test -d templates/governance` - passed with exit 0 and no output.

- `git ls-files runs` - passed with empty output.

Supplementary artifact-audit commands:

- `git diff --name-only` - passed before staging with tracked modified paths:

```text
README.md
docs/governance/README.md
src/alpha_system/governance/__init__.py
src/alpha_system/governance/claims.py
templates/governance/README.md
```

- `find data -type f ! -name README.md ! -name ".gitkeep" -print` - passed with empty
  output.

- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` - passed with empty
  output.

- `find artifacts -type f -size +1M -print` - passed with empty output.

- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - passed with empty
  output.

Additional local validation:

- `python -m pytest tests/unit/governance/test_claims_guard.py -q` - passed after repair:

```text
28 passed in 0.03s
```

- `python tools/verify.py --smoke` - passed after repair with exit 0 and no output.

- `python -m pytest tests/unit/governance -q` - passed after repair:

```text
503 passed in 1.83s
```

- `test -f docs/governance/UNSUPPORTED_CLAIM_GUARD.md` - passed after repair with exit 0
  and no output.

- `test -d templates/governance` - passed after repair with exit 0 and no output.

- `git ls-files runs` - passed after repair with empty output.

- `python -m ruff format src/alpha_system/governance/claims.py tests/unit/governance/test_claims_guard.py`
  - passed after repair:

```text
2 files left unchanged
```

- `python -m ruff check src/alpha_system/governance/claims.py tests/unit/governance/test_claims_guard.py`
  - passed after repair:

```text
All checks passed!
```

- `git diff --name-only` - passed after repair with only these unstaged repair paths:

```text
docs/governance/UNSUPPORTED_CLAIM_GUARD.md
src/alpha_system/governance/claims.py
tests/unit/governance/test_claims_guard.py
```

- `find data -type f ! -name README.md ! -name .gitkeep -print` - passed after repair
  with empty output.

- `find metadata -type f ! -name README.md ! -name .gitkeep -print` - passed after
  repair with empty output.

- `find artifacts -type f -size +1M -print` - passed after repair with empty output.

- `find . -name '*.parquet' -not -path './tests/fixtures/*' -print` - passed after
  repair with empty output.

- `python -m pytest tests/unit/governance/test_claims_guard.py -q` - passed:

```text
24 passed in 0.03s
```

- `python -m ruff format src/alpha_system/governance/claims.py src/alpha_system/governance/__init__.py tests/unit/governance/test_claims_guard.py`
  - passed; final formatting run reported one reformatted file and two unchanged files.

- `python -m ruff check --fix src/alpha_system/governance/claims.py tests/unit/governance/test_claims_guard.py`
  - passed after fixing import ordering.

- `python -m ruff check src/alpha_system/governance/claims.py src/alpha_system/governance/__init__.py tests/unit/governance/test_claims_guard.py`
  - passed:

```text
All checks passed!
```

- `git diff --check` - passed with exit 0 and no output.

Skipped checks: none of the spec-requested executor validation commands were skipped.
Claude review, reviewer execution, `review.md`, and `verdict.json` were not run or
created by Codex because the executor prompt reserves review and verdict handling for
Ralph and the independent reviewer.

## Test Coverage

Added `tests/unit/governance/test_claims_guard.py` covering:

- one blocking phrase for every required prohibited category;
- structured violation output and `UnsupportedClaimError.to_dict()`;
- fail-closed rejection for non-string, empty, replacement-character, and control-character
  inputs;
- permitted no-claims, policy/taxonomy, guard-behavior, and governance-identifier language;
- regression coverage that identifier and validation/template requirement co-location does
  not suppress prohibited-claim detection;
- documentation coverage of the taxonomy and allowlist;
- governance template claim-guard acceptance;
- report template evidence, limitations, no-claims, and required-checks sections.

## Artifact Policy

- `git ls-files runs` returned empty output.
- No `runs/**` path is staged.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or repair artifact
  was created or staged by Codex.
- No raw data, canonical data, factor data, label data, cache data, SQLite/DB/WAL file,
  Parquet, Arrow, Feather, log, generated report bundle, model binary, credential, or heavy
  artifact is staged.

## Staging Discipline

Explicit staging only. `git add .`, `git add -A`, force push, PR creation, merge,
reviewer invocation, and destructive cleanup were not used. The initial executor step did
not create a commit; this bounded repair attempt uses explicit path staging before the
curated ARGOV-P17 commit.

Post-staging validation:

- `git diff --cached --name-only` - passed with exactly this curated staged set:

```text
README.md
docs/governance/README.md
docs/governance/UNSUPPORTED_CLAIM_GUARD.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P17.md
src/alpha_system/governance/__init__.py
src/alpha_system/governance/claims.py
templates/governance/README.md
templates/governance/evidence_governance_report.template.md
tests/unit/governance/test_claims_guard.py
```

- `git diff --cached --check` - passed with exit 0 and no output.

- `git diff --cached --name-only | rg '^runs/'` - passed with no matches. `rg` returned
  exit 1 because no staged path matched `runs/`.

- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/|^artifacts/|\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|pkl|joblib|onnx|npy|npz|log)$|/cache/|/__pycache__/|/\.pytest_cache/)'`
  - passed with no matches. `rg` returned exit 1 because no staged path matched a forbidden
  artifact pattern.

- `git status --short` - passed with only explicitly staged ARGOV-P17 files:

```text
M  README.md
M  docs/governance/README.md
A  docs/governance/UNSUPPORTED_CLAIM_GUARD.md
A  handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P17.md
M  src/alpha_system/governance/__init__.py
M  src/alpha_system/governance/claims.py
M  templates/governance/README.md
A  templates/governance/evidence_governance_report.template.md
A  tests/unit/governance/test_claims_guard.py
```

## Scope Confirmation

No broker, live, paper, order-routing, real-data ingestion, alpha-search, or deployment
scope was introduced. No alpha, profitability, tradability, robustness,
production-readiness, paper-readiness, live-readiness, broker-readiness, or real-data-
readiness claim was introduced. The README snapshot was updated per the phase policy.
