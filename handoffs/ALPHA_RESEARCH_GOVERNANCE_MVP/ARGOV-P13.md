# ARGOV-P13 Handoff - Negative-Control Canary Catalog

## Summary

Implemented the governance negative-control catalog and `NegativeControlResult`
contract in `alpha_system.governance.canaries`.

The catalog is the enumerable MVP source of truth for these four canary types:

- `random_target` - statistical sanity guard; expected failure is
  `guard_rejects_or_flags_random_target_signal`.
- `permuted_labels` - label-integrity guard; expected failure is
  `guard_rejects_or_flags_permuted_label_signal`.
- `future_shift` - no-lookahead guard; expected failure is
  `guard_rejects_or_flags_future_shift_lookahead`.
- `optimistic_fill` - execution-assumption guard; expected failure is
  `guard_rejects_or_flags_optimistic_fill_assumption`.

Each catalog entry records identity, guard family, injected fault, expected
failure, `StudySpec.negative_controls` naming, `EvidenceBundle` result-record
relationship, and risk references. `future_shift` explicitly covers R-011;
all controls carry the R-010 fail-closed expectation that a correct guard rejects
or flags the injected known-bad fault.

`NegativeControlResult` carries exactly:

- `canary_id`
- `canary_type`
- `expected_failure`
- `observed_result`
- `pass_fail`
- `related_study_or_evidence`
- `notes`

The object uses deterministic `nctrl_...` IDs, canonical JSON round trips,
the existing governance ID/serialization/validation primitives, and structured
`GovernanceValidationError` failures. Validation fails closed on missing, null,
unknown, malformed, non-substantive, uncatalogued, mismatched, or inconsistent
fields. `canary_type` is constrained to the catalog. `expected_failure` must
match the selected catalog entry. `related_study_or_evidence` must reference a
`StudySpec` or `EvidenceBundle` ID. `pass_fail` is `PASS` only when
`observed_result` matches `expected_failure`; mismatches are valid only as
`FAIL`, so a failed guard check is recordable and cannot silently pass.

Added README-only scaffolds under `evals/canaries/` for:

- `evals/canaries/random_target/README.md`
- `evals/canaries/permuted_labels/README.md`
- `evals/canaries/future_shift/README.md`
- `evals/canaries/optimistic_fill/README.md`

Added `docs/governance/NEGATIVE_CONTROLS.md` and minimally updated the
`StudySpec` and `EvidenceBundle` docs to name the catalog relationship. Updated
`README.md` with the ARGOV-P13 snapshot, next planned phase `ARGOV-P14 -
No-Lookahead / Label Leakage / Optimistic Fill Canary Harness`, the new
`alpha_system.governance.canaries` module family, the negative-controls doc, and
unchanged safety boundaries.

No fixtures were added.

## Staged Files

Exact files staged after explicit staging:

- `README.md`
- `docs/governance/EVIDENCE_BUNDLE.md`
- `docs/governance/NEGATIVE_CONTROLS.md`
- `docs/governance/STUDY_SPEC.md`
- `evals/canaries/future_shift/README.md`
- `evals/canaries/optimistic_fill/README.md`
- `evals/canaries/permuted_labels/README.md`
- `evals/canaries/random_target/README.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P13.md`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/canaries/__init__.py`
- `src/alpha_system/governance/canaries/catalog.py`
- `src/alpha_system/governance/canaries/negative_control_result.py`
- `tests/unit/governance/test_negative_controls.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before staging with only allowed ARGOV-P13 paths:

```text
 M README.md
 M docs/governance/EVIDENCE_BUNDLE.md
 M docs/governance/STUDY_SPEC.md
 M src/alpha_system/governance/__init__.py
 M src/alpha_system/governance/canaries/__init__.py
?? docs/governance/NEGATIVE_CONTROLS.md
?? evals/canaries/future_shift/
?? evals/canaries/optimistic_fill/
?? evals/canaries/permuted_labels/
?? evals/canaries/random_target/
?? src/alpha_system/governance/canaries/catalog.py
?? src/alpha_system/governance/canaries/negative_control_result.py
?? tests/unit/governance/test_negative_controls.py
```

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_negative_controls.py -q` -
  passed:

```text
...................                                                      [100%]
19 passed in 0.03s
```

- `python -m pytest tests/unit/governance -q` - passed:

```text
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 47%]
........................................................................ [ 63%]
........................................................................ [ 78%]
........................................................................ [ 94%]
........................                                                 [100%]
456 passed in 0.26s
```

- `test -f docs/governance/NEGATIVE_CONTROLS.md` - passed with exit 0 and no
  output.

- `git ls-files runs` - passed with empty output.

Post-staging artifact audit:

- `git status --short` - passed after explicit staging with only curated
  ARGOV-P13 paths:

```text
M  README.md
M  docs/governance/EVIDENCE_BUNDLE.md
A  docs/governance/NEGATIVE_CONTROLS.md
M  docs/governance/STUDY_SPEC.md
A  evals/canaries/future_shift/README.md
A  evals/canaries/optimistic_fill/README.md
A  evals/canaries/permuted_labels/README.md
A  evals/canaries/random_target/README.md
A  handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P13.md
M  src/alpha_system/governance/__init__.py
M  src/alpha_system/governance/canaries/__init__.py
A  src/alpha_system/governance/canaries/catalog.py
A  src/alpha_system/governance/canaries/negative_control_result.py
A  tests/unit/governance/test_negative_controls.py
```

- `git diff --cached --name-only` - passed with exactly the staged files listed
  in this handoff.

- `git diff --cached --name-only | rg '^runs/'` - passed with no matches. The
  audited command reported `NO_RUNS_STAGED`.

- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/.*\.(sqlite|sqlite3|db|db-journal|wal)$|^artifacts/|\.(parquet|arrow|feather|pkl|onnx|npy|log)$)'`
  - passed with no matches. The audited command reported
  `NO_FORBIDDEN_ARTIFACTS_STAGED`.

No requested validation command was skipped.

## README Snapshot

`README.md` now states that ARGOV-P13 executor deliverables are complete for
Ralph-owned validation and independent review, names the four catalogued
negative controls, records `NegativeControlResult` and the
`alpha_system.governance.canaries` module family, points the next planned phase
to `ARGOV-P14`, includes `docs/governance/NEGATIVE_CONTROLS.md`, and preserves
the governance-only safety boundary. It records no phase PASS verdict.

## Artifact Policy

Explicit staging was used by path. `git add .`, `git add -A`, force push,
destructive cleanup, run-local handoff staging, and `runs/**` staging were not
used. `git ls-files runs` returned empty output. No raw data, canonical data,
factor data, label data, cache, SQLite or DB file, log, generated report bundle,
Parquet, Arrow, Feather, model binary, credential, or heavy artifact path is
staged.

## Scope And Claims

No executable canary harness, no `src/alpha_system/governance/canaries/harness.py`,
no `tests/no_lookahead/**`, and no `tools/hooks/canary_runner.py` change was
introduced. The canary scaffolds are README-only placeholders for ARGOV-P14.

No broker, live, paper, order-routing, real-data-ingestion, alpha-search,
strategy-optimization, portfolio-allocation, production-deployment, PR creation,
merge, reviewer invocation, `review.md`, or `verdict.json` scope was introduced.

The catalog and `NegativeControlResult` validate guard behavior only. This phase
introduced no alpha validity, profitability, tradability, capital-allocation,
live-readiness, or production-readiness claim.
