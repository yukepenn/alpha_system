# Label Diagnostics Runtime

RT-P08 adds `alpha_system.runtime.diagnostics.label`, the Label Diagnostics
runtime for the Research Runtime MVP. The module turns a resolved
`RuntimeInputPack` plus label diagnostic summaries into a descriptive
`LabelDiagnosticsReport` and a visible `DiagnosticsRunRecord`.

The runtime is local-only. It consumes accepted DatasetVersion metadata and
registered LabelStore pack handles through `RuntimeInputPack`; it does not read
raw provider files, call Databento or IBKR, materialize labels, persist runtime
outputs, or expose label outcomes as live feature inputs.

## Inputs

Required inputs are:

- an RT-P06 `DiagnosticsRunSpec` or `DiagnosticsRunSpecRef` for
  `DiagnosticsFamily.LABEL`;
- a resolved `RuntimeInputPack` that binds an approved `AlphaSpec`, approved
  `StudySpec`, accepted DatasetVersion, and registered label pack handles;
- upstream feature quality reports, feature coverage reports, and label leakage
  audit reports for `alpha_system.research.feature_label_diagnostics`;
- scalar diagnostic observations or profiles supplied by the caller for label
  distribution, horizon, path, and cost summaries.

The runtime requires every diagnostic observation to carry `label_available_ts`.
If `label_available_ts` is missing, precedes `event_ts` or `horizon_end_ts`, or
if live feature references include label-only fields or registered label
identities, the report is rejected with a visible `leakage_risk` reason.

## Orchestrated Primitives

The runtime delegates existing diagnostic work instead of copying it:

- `alpha_system.research.feature_label_diagnostics.build_feature_label_diagnostics`
  summarizes feature/label availability alignment, coverage overlap, label audit
  findings, and missingness exposure.
- `alpha_system.research.events.post_event_mfe_mae` summarizes supplied MFE and
  MAE observations.
- `alpha_system.research.events.target_before_stop_probability` summarizes
  path-ordering observations.

The remaining scalar fields are report packing over supplied diagnostic
observations and profiles. They are counts, shares, flags, and references only;
raw label outcomes and runtime value tables are not embedded in the report.

## Report Fields

`LabelDiagnosticsReport.to_dict()` includes the shared RT-P06 report payload plus
label-specific scalar sections:

- `label_distribution_summary`
- `label_horizon_coverage`
- `label_class_balance`
- `label_mfe_mae_summary`
- `label_path_ambiguity_summary`
- `label_available_ts_validity`
- `label_cost_adjustment_sanity`
- `label_coverage_missingness`
- `diagnostics_run_record`

Failed, rejected, and inconclusive reports keep rejection reasons visible through
the shared RT-P05 `RunRejectionReason` shape. The runtime uses
`DIAGNOSTICS_FAILED`, `REJECTED`, or `INCONCLUSIVE` for terminal non-complete
outcomes.

## No-Claims Posture

A complete Label Diagnostics report means only that the supplied label
diagnostics were describable under the configured gates. It is not a promotion
decision, not a strategy result, and not evidence for deployment. Signal probes,
cost stress, evidence drafts, and reference handoffs remain later phases.
