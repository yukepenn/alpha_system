# Feature/Label Diagnostics

`alpha_system.research.feature_label_diagnostics` composes existing Feature and
Label substrate evidence into a single descriptive report. It consumes:

- FLF-P15 `FeatureQualityReport` outputs;
- FLF-P15 `FeatureCoverageReport` outputs;
- FLF-P23 `LabelLeakageAuditReport` outputs.

The module does not compute features, compute labels, materialize values, read
raw provider files, open registry databases, call external providers, or
duplicate governance checks. It accepts report objects or serialized report
mappings and returns row-free summaries.

## Report Sections

`FeatureLabelDiagnosticsReport` has three sections.

`availability_alignment` reports:

- shared and one-sided dataset-version ids;
- shared and one-sided partitions;
- feature `available_ts` defects already surfaced by feature quality reports;
- label `label_available_ts` and availability-time findings already surfaced by
  label audits;
- label-as-feature findings already surfaced by label audits.

`coverage_overlap` reports shared and one-sided coverage by:

- symbol;
- session;
- partition.

Feature symbols and sessions come from `FeatureCoverageReport`. Label symbols
and sessions are consumed only when they are present in the supplied audit
output mapping. If label audit outputs do not report symbol or session coverage,
the diagnostics record that absence instead of deriving coverage from value
rows.

`missingness_exposure` reports:

- `missing_bbo` count;
- `bbo_quarantined` count;
- synthetic dense-grid no-trade exposure when a supplied report carries a
  `synthetic_no_trade_count`, `no_trade_count`, or equivalent count field.

If synthetic no-trade exposure is not present in the supplied reports, the
diagnostics record that it was not reported. They do not inspect materialized
rows to fill that gap.

## Status And Findings

Each section separates `blocking` and `non_blocking` findings. The top-level
report status is `blocked` when any section has a blocking finding; otherwise it
is `clear`.

Blocking examples include:

- missing feature quality, feature coverage, or label audit inputs;
- no shared dataset version or partition between feature reports and label
  audits;
- feature `available_ts` defects reported upstream;
- label `label_available_ts`, availability-time, or label-as-feature blocking
  findings reported upstream;
- missing label symbol/session coverage when feature coverage has those
  dimensions and label audit outputs do not report them.

Non-blocking examples include:

- one-sided but still overlapping dataset-version, partition, symbol, or session
  scope;
- BBO missingness or quarantine exposure counts;
- recorded synthetic dense-grid no-trade exposure;
- absence of synthetic no-trade exposure fields in the supplied reports.

## Interpretation Boundary

The diagnostics describe coverage and availability consistency for the
Feature/Label substrate. They do not rank features or labels and do not state or
imply predictive value, profitability, tradability, promotion, deployment, or
live-use suitability. A clear diagnostic report is still only substrate
evidence; review and later governed study inputs remain separate gates.

Tiny synthetic fixtures used by tests validate report composition and boundary
behavior only. Fixture outputs are not market evidence.

## Artifact Policy

Diagnostics are curated source and documentation only. Do not commit
materialized feature values, label values, raw/canonical data, provider
responses, report bundles, local registry databases, caches, logs, parquet,
arrow, feather, DBN, Zstd, or run-local `runs/**` artifacts.
