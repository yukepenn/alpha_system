# EvidenceBundle

`ARGOV-P09` adds `EvidenceBundle` metadata for packaging the minimum evidence
set a research idea must carry before later governance code may consider
candidate-related gates. The bundle is governance metadata only. It records
references, hashes, summaries, limitations, and review linkage; it does not run
diagnostics, compute factors or labels, run backtests, ingest real data, or
materialize evidence artifacts.

The invariant installed by this phase is:

```text
No EvidenceBundle -> no candidate.
```

The transition precondition provided here is:

```text
DIAGNOSTICS_RUN -> EVIDENCE_READY
```

`EVIDENCE_READY` only means the evidence package has been validated and
packaged. It is not promotion, candidate status, validation, factor-library
eligibility, alpha validity, profitability, tradability, capital allocation, or
production readiness.

## Bundle Fields

`EvidenceBundle` carries exactly these fields:

| Field | Meaning |
| --- | --- |
| `evidence_bundle_id` | Deterministic `EvidenceBundle` governance ID with the `evb` prefix, generated from all non-ID content fields. |
| `alpha_spec_id` | Valid `AlphaSpec` ID with the `aspec` prefix. |
| `study_spec_id` | Valid `StudySpec` ID with the `sspec` prefix. |
| `trial_ids` | Non-empty list of unique `TrialLedgerRecord` IDs with the `trial` prefix. |
| `data_version` | Explicit data-version reference used for the packaged evidence. |
| `factor_version` | Explicit factor-version reference used for the packaged evidence. |
| `label_version` | Explicit label-version reference used for the packaged evidence. |
| `code_hash` | Lowercase SHA-256 content hash string for the code version. |
| `config_hash` | Lowercase SHA-256 content hash string for the configuration version. |
| `diagnostics_summary` | Non-empty explicit summary metadata recorded from diagnostics. |
| `negative_control_results` | Non-empty list of explicit negative-control result metadata. |
| `limitations` | Non-empty list of declared limitations. |
| `artifact_manifest` | Non-empty local-only evidence artifact manifest. |
| `reviewer_verdict_reference` | Opaque reviewer-verdict reference. This phase stores the reference only and does not resolve independence rules. |

Validation is fail-closed. Missing fields, null fields, empty required strings,
empty `trial_ids`, empty `negative_control_results`, empty `limitations`, empty
`artifact_manifest`, malformed governance IDs, duplicate trial references,
invalid hashes, non-substantive summary metadata, non-canonical values, unknown
fields, and mismatched deterministic IDs raise `GovernanceValidationError`.

## Manifest Contract

`artifact_manifest` is a list of manifest entries. Each entry carries exactly:

| Field | Meaning |
| --- | --- |
| `logical_name` | Human-readable logical artifact name. |
| `role` | Evidence role, such as diagnostics summary or negative-control output. |
| `reference` | Relative local-only path or opaque local reference to the evidence artifact. |
| `content_hash` | Lowercase SHA-256 content hash of the referenced artifact content. |

The manifest records metadata about local-only evidence artifacts. It must not
embed artifact content, require artifact files to be committed, or point to
external URLs. Artifact references are validated as relative local-only paths or
opaque local references; absolute paths, parent-directory traversal, Windows
absolute paths, backslash paths, external URLs, and embedded data references
fail closed. The validator checks structure and hash shape only; it does not
read or materialize artifacts.

## Reproducibility Metadata

The data, factor, and label versions identify the concrete inputs represented
by the bundle. The code, config, and manifest-entry hashes bind the package to
specific content versions. These fields are mandatory so later governance gates
can compare evidence packages without relying on mutable local state.

`EvidenceBundle.to_canonical_json()` and
`EvidenceBundle.from_canonical_json(...)` use the shared governance
serialization primitive. The `evidence_bundle_id` is regenerated during
validation and must match the canonical content.

## Evidence-Ready Gate

`validate_evidence_ready_gate(...)` and `assert_evidence_ready(...)` provide the
phase-local gate predicate. They return a validated `EvidenceBundle` or raise
`GovernanceValidationError`.

The gate evaluates only:

```text
DIAGNOSTICS_RUN -> EVIDENCE_READY
```

It blocks when the bundle is missing, malformed, lacks trial references, lacks a
well-formed manifest, or fails any required-field validation. The gate does not
implement the later promotion state machine and does not decide candidate,
validated, or factor-library status.
