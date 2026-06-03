# Audit Reports

Audit reports summarize review-bundle completeness and policy warnings. They reuse the bundle validation result so humans and AI Agents see the same structured evidence.

The audit report covers:

- provenance completeness,
- missing required sections,
- missing versions or hashes,
- missing artifacts,
- failed runs and failed steps,
- rejected configs,
- promotion decision status,
- no-lookahead validation status,
- review status,
- known limitations.

Audit reports are document-only outputs. They do not change candidate lifecycle state, call external systems, create PRs, merge branches, or perform broker/live/paper/deployment work.

The release-validation variant in `src/alpha_system/reports/release_report.py` reuses the same bundle and audit primitives. It records local validation status for review and has no release action attached to it.
