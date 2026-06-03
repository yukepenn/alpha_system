# Evidence Governance Report Template

Report ID: `<report_id>`
Evidence bundle reference: `<evidence_bundle_id>`
Study specification reference: `<study_spec_id>`
Prepared by: `<name or role>`
Prepared at: `<ISO-8601 timestamp>`

## Evidence References

- Evidence bundle: `<path or registry reference>`
- Trial ledger records: `<trial_id list or registry query reference>`
- Negative controls: `<control result references>`
- Manifest entries: `<artifact logical names and content hashes>`
- Reviewer metadata: `<reviewer verdict reference or missing-review statement>`

## Limitations

- `<known limitation tied to data scope, fixture scope, or missing review>`
- `<known limitation tied to versions, hashes, controls, or manifests>`
- `<known limitation tied to incomplete governance state>`

## No-Claims Language

This report is not evidence of alpha validity, profitability, tradability, robustness,
production readiness, paper readiness, live readiness, broker readiness, or readiness
for real data.

## Required Checks

- Evidence references are present and resolvable by the governance registry or report
  reader.
- Limitations are explicit and not empty.
- Missing review, failed runs, rejected variants, and negative controls remain visible.
- The unsupported-claim guard accepts this rendered report before it is used as a
  governance artifact.

## Notes

- `<factual governance note>`
- `<open question or required follow-up review item>`
