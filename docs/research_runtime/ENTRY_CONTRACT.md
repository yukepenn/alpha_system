# Runtime Entry Contract

`alpha_system.runtime.entry_contract` is the single sanctioned pre-execution
front door for the Research Runtime campaign. It accepts governed references and
metadata only, then returns one contract-level decision before any resolver,
diagnostics, probe, cost stress, or evidence path can run.

The entry request is a `RuntimeEntryRequest` containing:

- an `AlphaSpec` reference with the governance `aspec_` prefix;
- a `StudySpec` reference with the governance `sspec_` prefix;
- the governance `StudyInputPack` from
  `alpha_system.governance.study_input_pack`;
- a target accepted `DatasetVersion` id;
- explicit partition or dataset scope metadata.

The request carries references and metadata only. It never carries canonical
rows, FeatureStore rows, LabelStore rows, provider payloads, registry records,
or materialized runtime values.

## Outcomes

The contract returns a `RuntimeEntryResult` with exactly one pre-execution
status:

- `INPUTS_RESOLVED`: the required references are present, valid at the contract
  boundary, and internally consistent. This is not data resolution and not a
  runtime run.
- `INPUTS_BLOCKED`: a hard admission rule failed. Later phases must not execute
  from this request.
- `INPUTS_INCONCLUSIVE`: required references are present, but metadata is
  under-determined for governed execution. Later phases must resolve the
  ambiguity before execution.

Each result includes structured `RuntimeEntryReason` records. Non-resolved
results use the same decision-state vocabulary that later rejection-reason
contracts build on.

## Admission Rules

The contract is fail closed:

- no `AlphaSpec` reference means `INPUTS_BLOCKED`;
- no `StudySpec` reference means `INPUTS_BLOCKED`;
- no governance `StudyInputPack` means `INPUTS_BLOCKED`;
- no target accepted `DatasetVersion` id or no dataset scope means
  `INPUTS_BLOCKED`;
- any raw provider source, raw provider file path (`.dbn`, `.zst`, `.parquet`,
  `.arrow`, `.feather`), or external provider call request means
  `INPUTS_BLOCKED`;
- a declared DatasetVersion lifecycle state outside `VERSIONED` or
  `READY_FOR_RESEARCH` means `INPUTS_BLOCKED`;
- a request that merges Databento and IBKR DatasetVersion source families means
  `INPUTS_BLOCKED`;
- locked-test partition use without governance contamination metadata means
  `INPUTS_INCONCLUSIVE`;
- references that conflict with the governance `StudyInputPack` are
  `INPUTS_INCONCLUSIVE` until reconciled.

Actual DatasetVersion lookup, lifecycle evidence checking, FeatureStore/LabelStore
handle resolution, and locked-partition gate execution are delegated to `RT-P03`.
The resolver must honor this boundary: only DatasetVersions in lifecycle state
`VERSIONED` or `READY_FOR_RESEARCH` are admissible; Databento and IBKR
DatasetVersions remain separate provenance lines; locked-test partition use
requires governance contamination metadata.

## Non-Promotional Framing

`INPUTS_RESOLVED` means only that the pre-execution reference contract admitted
the request for downstream local resolution. It does not validate alpha, create
a candidate, imply tradability or profitability, promote a factor, create a
strategy, authorize paper or live trading, or make any production-readiness
claim. The runtime entry path never opens onto raw provider data, external
provider calls, broker scope, order routing, account operations, or committed
runtime values.
