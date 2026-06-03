# ARGOV-P09 Handoff - EvidenceBundle and Manifest Contract

## Summary

Implemented `EvidenceBundle` in `alpha_system.governance.evidence_bundle` as
governance metadata only. The bundle uses the existing governance ID primitive,
canonical serialization, deterministic content IDs, and fail-closed structured
validation.

The bundle carries all campaign-required fields:

- `evidence_bundle_id`
- `alpha_spec_id`
- `study_spec_id`
- `trial_ids`
- `data_version`
- `factor_version`
- `label_version`
- `code_hash`
- `config_hash`
- `diagnostics_summary`
- `negative_control_results`
- `limitations`
- `artifact_manifest`
- `reviewer_verdict_reference`

`evidence_bundle_id` is a deterministic `evb_...` ID generated from all non-ID
content fields and verified during validation. `alpha_spec_id`, `study_spec_id`,
and every `trial_ids` entry are validated as `aspec_...`, `sspec_...`, and
`trial_...` governance IDs. Trial references must be non-empty and unique.
`code_hash`, `config_hash`, and each manifest `content_hash` must be lowercase
SHA-256 content hashes. `data_version`, `factor_version`, `label_version`,
diagnostics summary metadata, negative-control result metadata, limitations,
artifact manifest entries, and `reviewer_verdict_reference` are all mandatory
and fail closed when missing, null, empty, vague, malformed, or non-canonical.

`reviewer_verdict_reference` is stored as an opaque substantive reference only.
This phase does not resolve reviewer verdicts and does not implement reviewer
independence rules.

## Manifest Contract

Implemented `EvidenceArtifactManifestEntry` with exactly these required fields:

- `logical_name`
- `role`
- `reference`
- `content_hash`

`artifact_manifest` must be a non-empty list of well-formed entries. Manifest
references must be relative local-only paths or opaque local references; absolute
paths, parent-directory traversal, Windows absolute paths, backslash paths,
external URLs, embedded data references, missing references, missing hashes,
unknown fields, and malformed hashes fail closed.

The manifest records metadata only. It does not embed evidence artifact content,
read artifacts, require artifacts to exist, or require artifacts to be committed.
Manifest-referenced evidence artifacts remain local-only.

## Candidate-Gate Predicate

Implemented `validate_evidence_ready_gate(...)` and `assert_evidence_ready(...)`
as the phase-local no-EvidenceBundle-no-candidate precondition.

The gate evaluates only:

```text
DIAGNOSTICS_RUN -> EVIDENCE_READY
```

It returns a validated `EvidenceBundle` or raises `GovernanceValidationError`.
Missing bundles, invalid bundles, empty `trial_ids`, and missing or malformed
manifest entries are blocked. This phase does not implement the promotion state
machine, `PromotionDecision`, `ReviewerVerdict`, registry persistence, CLI,
report templates, diagnostics, backtests, factor computation, label
computation, or evidence materialization.

## Documentation

Added `docs/governance/EVIDENCE_BUNDLE.md` describing the object, required
fields, manifest contract, reproducibility role of hashes and versions, the
`DIAGNOSTICS_RUN -> EVIDENCE_READY` precondition, and the explicit
no-implication rule.

Updated `README.md` for the P09 snapshot: campaign progress now through
`ARGOV-P09`, active/just-completed phase `ARGOV-P09 - EvidenceBundle and
Manifest Contract`, next planned phase `ARGOV-P10 - RejectedIdeaLedger /
Research Graveyard`, durable module `alpha_system.governance.evidence_bundle`,
and unchanged safety boundaries.

## Staged Files

Exact files staged after explicit staging:

- `README.md`
- `docs/governance/EVIDENCE_BUNDLE.md`
- `docs/governance/README.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P09.md`
- `src/alpha_system/governance/evidence_bundle.py`
- `tests/unit/governance/test_evidence_bundle.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `test ! -f runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP/STOP && echo NO_STOP || echo STOP_PRESENT`
  - passed with exit 0:

```text
NO_STOP
```

- `git status --short`
  - passed before handoff creation/staging with only allowed P09 paths:

```text
 M README.md
 M docs/governance/README.md
 M src/alpha_system/governance/evidence_bundle.py
?? docs/governance/EVIDENCE_BUNDLE.md
?? tests/unit/governance/test_evidence_bundle.py
```

- `python tools/verify.py --smoke`
  - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance -q`
  - passed:

```text
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 72%]
........................................................................ [ 97%]
........                                                                 [100%]
296 passed in 0.19s
```

- `test -f docs/governance/EVIDENCE_BUNDLE.md`
  - passed with exit 0 and no output.

- `test -f src/alpha_system/governance/evidence_bundle.py`
  - passed with exit 0 and no output.

- `git ls-files runs`
  - passed with exit 0 and empty output.

Supplementary artifact-audit checks:

- `find data -type f ! -name README.md ! -name ".gitkeep" -print`
  - passed with exit 0 and empty output.

- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print`
  - passed with exit 0 and empty output.

- `find artifacts -type f -size +1M -print`
  - passed with exit 0 and empty output.

- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print`
  - passed with exit 0 and empty output.

Additional local validation and inspection:

- `python -m pytest tests/unit/governance/test_evidence_bundle.py -q`
  - passed:

```text
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 0.06s
```

- `python -m ruff format --check src/alpha_system/governance/evidence_bundle.py tests/unit/governance/test_evidence_bundle.py`
  - initially failed because the two new/touched Python files needed formatting:

```text
Would reformat: src/alpha_system/governance/evidence_bundle.py
Would reformat: tests/unit/governance/test_evidence_bundle.py
2 files would be reformatted
```

- `python -m ruff check src/alpha_system/governance/evidence_bundle.py tests/unit/governance/test_evidence_bundle.py`
  - initially failed only for import formatting and reported both issues as
    fixable.

- `python -m ruff format src/alpha_system/governance/evidence_bundle.py tests/unit/governance/test_evidence_bundle.py && python -m ruff check --fix src/alpha_system/governance/evidence_bundle.py tests/unit/governance/test_evidence_bundle.py`
  - passed after mechanical formatting/import fixes:

```text
2 files reformatted
Found 2 errors (2 fixed, 0 remaining).
```

- `python -m ruff format --check src/alpha_system/governance/evidence_bundle.py tests/unit/governance/test_evidence_bundle.py`
  - passed after formatting:

```text
2 files already formatted
```

- `python -m ruff check src/alpha_system/governance/evidence_bundle.py tests/unit/governance/test_evidence_bundle.py`
  - passed after formatting:

```text
All checks passed!
```

- `git diff --check`
  - passed with exit 0 and no output.

- `git diff --cached --name-only`
  - passed after explicit staging with exactly the curated file set:

```text
README.md
docs/governance/EVIDENCE_BUNDLE.md
docs/governance/README.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P09.md
src/alpha_system/governance/evidence_bundle.py
tests/unit/governance/test_evidence_bundle.py
```

- `git diff --cached --name-only | rg '^runs/' || true`
  - passed with empty output.

- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/.*\.(sqlite|sqlite3|db|db-journal|wal)$|^artifacts/|\.(parquet|arrow|feather|pkl|onnx|npy|log)$)' || true`
  - passed with empty output.

- `git diff --cached --check`
  - passed with exit 0 and no output.

- `test ! -f runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP/STOP && echo NO_STOP || echo STOP_PRESENT`
  - passed again after staging:

```text
NO_STOP
```

Skipped checks: none of the spec-requested executor validation commands were
skipped. Claude review, reviewer execution, `review.md`, and `verdict.json`
were not run or created by Codex because the executor prompt reserves review
and verdict handling for Ralph and the independent reviewer.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path after explicit
  staging.
- The data, metadata, artifact-size, and Parquet audits returned empty output.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB
  journal, WAL, Parquet, Arrow, Feather, log, cache, model binary, heavy
  artifact, or run artifact is staged.
- No evidence artifact was created or committed. Manifest references are
  metadata-only and remain local-only.
- The run-local handoff under
  `runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP/phases/ARGOV-P09/handoff.md`
  is local-only and must not be staged or committed.
- No run-local `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created by Codex.

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
  ingestion, alpha search, strategy optimization, portfolio allocation, CLI,
  registry persistence, or evidence materialization scope was introduced.
- No edits were made to forbidden broker/live/paper/order-router paths, data
  roots, metadata DB paths, artifact roots, or `runs/**`.
- Tests were added only under authorized governance paths. Existing tests were
  not weakened, skipped, deleted, or relaxed.
- No fixtures were added in this phase.
- No alpha, profitability, tradability, candidate, validated, factor-library,
  promotion-success, or production-readiness claim was introduced.
- `EVIDENCE_READY` is documented and implemented only as packaged evidence
  metadata; it implies no promotion or market claim.
