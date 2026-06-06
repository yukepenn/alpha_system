# Runtime CLI

`alpha runtime ...` is the local-only command surface for the Research Runtime.
It is a thin dispatch layer over the runtime modules built in RT-P01 through
RT-P17. It parses local JSON command envelopes, calls existing runtime
contracts/builders, and prints compact summaries.

The CLI does not call providers, does not use network access, does not read raw
provider files, and has no broker, live, paper, order, account, deployment, or
background-worker behavior. It makes no alpha, tradability, profitability,
promotion, strategy, portfolio, or production claim.

## Common Options

Every runtime subcommand supports:

- `--input PATH`: local JSON command envelope or runtime payload.
- `--json`: emit a deterministic JSON console summary.
- `--help`: show command help without running runtime work.

Missing or malformed input fails closed with a non-zero exit and a compact
stderr message. Help and missing-input paths are CI-safe and do not dispatch
runtime computation.

## Commands

`alpha runtime plan`

- Input: JSON envelope accepted by `alpha_system.runtime.contracts.plan`.
  When `runtime_request` is supplied as a mapping, the CLI builds the
  `RuntimeRequest` object and calls `validate_runtime_plan`.
- Output: `RuntimePlanValidationResult` summary, including status and visible
  reasons when validation does not advance.

`alpha runtime validate-inputs`

- Input: `entry_request` mapping for `RuntimeEntryRequest`. Optional
  `resolution` mapping may include local resolver arguments such as
  `registry_path`, pack refs, partition scope, and session scope.
- Output: `RuntimeEntryResult`, or `RuntimeInputResolutionResult` when
  `resolution` is present.
- Boundary: the entry-only path performs contract validation only. Resolution
  consumes local registries through the existing runtime resolver and never
  calls providers.

`alpha runtime run-diagnostics`

- Input: local diagnostics envelope with `diagnostics_run_spec`,
  `observations`, and `lineage_refs`.
- Option: `--family factor|splits|session-split|regime-split|cross-market`.
- Output: existing diagnostics report/run-result payloads from the runtime
  diagnostics modules.

`alpha runtime run-label-diagnostics`

- Input: label diagnostics envelope with `diagnostics_run_spec`,
  `runtime_input_pack`, and optional feature/label report summaries or label
  observations.
- Output: `LabelDiagnosticsReport` from
  `alpha_system.runtime.diagnostics.label`.

`alpha runtime run-signal-probe`

- Input: probe envelope with `signal_probe_spec`, `observations`,
  `cost_diagnostics_run_spec`, and `lineage_refs`.
- Output: `SignalProbeReport` from `alpha_system.runtime.probe`.
- Boundary: this is a descriptive fast path only and is not a strategy or
  candidate surface.

`alpha runtime run-cost-stress`

- Input: cost-stress envelope with `diagnostics_run_spec`, `fills`,
  `lineage_refs`, `cost_model_version`, and `cost_stress_config`.
- Output: `CostSensitivityReport` from `alpha_system.runtime.cost`.
- Boundary: cost and slippage are descriptive proxy summaries delegated to
  existing backtest primitives.

`alpha runtime build-evidence-draft`

- Input: evidence draft envelope with manifest, run record, trial refs,
  negative controls, optional audit result, decision, reasons, limitations, and
  artifact refs.
- Output: `EvidenceDraft` from `alpha_system.runtime.evidence`.
- Boundary: the draft is an evidence input only and does not create a candidate
  or promotion.

`alpha runtime build-reference-handoff`

- Input: reference handoff envelope with `evidence_draft_input`,
  `study_run_manifest`, `runtime_artifact_manifest`, optional audit result,
  decision, reasons, and limitations.
- Output: `ReferenceCandidateHandoff` from `alpha_system.runtime.handoff`.
- Boundary: the handoff is reference-only packaging. It does not run Reference
  validation or imply any trading readiness.

`alpha runtime summarize`

- Input: any local runtime JSON payload.
- Output: compact schema/status/id/reason summary. No runtime work is replayed.

`alpha runtime inspect`

- Input: local runtime contract JSON. Known StudyRun manifest, StudyRun record,
  and artifact manifest schemas are reconstructed through their existing
  contracts before summarization.
- Output: compact metadata plus the value-free contract payload.

`alpha runtime replay-summary`

- Input: `StudyRunManifest` payload, optionally paired with
  `study_run_record`.
- Output: reproducibility summary including run id, manifest id, dataset
  version id, pack counts, optional record state, and `rerun_performed: false`.

## JSON Envelope Posture

The CLI intentionally does not invent alternate runtime semantics. If a runtime
constructor requires a real contract object, the CLI either rebuilds that object
from a value-free JSON envelope using the existing constructor or fails closed.
It does not emulate diagnostics math, cost models, audits, grids, decisions,
evidence assembly, or handoff rules.

Raw, canonical, feature, label, runtime value tables, local DBs, provider
responses, and heavy artifacts are outside this surface and must remain
local-only.
