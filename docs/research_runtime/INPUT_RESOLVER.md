# Runtime Input Resolver

`alpha_system.runtime.input_resolver` is the RT-P03 resolver that turns an
already-admitted `RuntimeEntryResult` into a value-free `RuntimeInputPack`.
It is the first runtime layer that may touch the local DatasetVersion registry
and registered Feature/Label pack metadata.

Resolution is local and deterministic. It implies no diagnostics run, no signal
probe, no evidence result, no alpha, no strategy, no tradability, no
profitability, and no paper/live/broker/order/account scope.

## Contract

The resolver consumes:

- a `RuntimeEntryResult` from `alpha_system.runtime.entry_contract`;
- the governance `StudyInputPack` already carried by that entry result;
- one target DatasetVersion id;
- explicit partition and session scope;
- versioned feature pack refs (`fver_...`) and label pack refs (`lver_...`);
- optional governance contamination metadata for locked or shadow partition use.

It returns `RuntimeInputResolutionResult` with one of the entry-contract states:

- `INPUTS_RESOLVED`: a `RuntimeInputPack` exists and contains handles only;
- `INPUTS_BLOCKED`: a hard boundary failed;
- `INPUTS_INCONCLUSIVE`: required governance or scope metadata is missing.

Rejection causes reuse the entry-contract `RuntimeEntryReason` shape:
`code`, `message`, `field`, `decision_state`, `expected`, and `actual`. The
resolver does not introduce a parallel governance reason type.

## Sanctioned Boundary

DatasetVersion lookup goes through
`alpha_system.data.foundation.version_registry.resolve_dataset_version`. A
missing DatasetVersion blocks resolution. A DatasetVersion lifecycle state is
admissible only when it is `VERSIONED` or `READY_FOR_RESEARCH`.

Feature packs resolve through the FeatureStore / FeatureRegistry surfaces.
Label packs resolve through the LabelRegistry surface. The resolver reads
registered metadata and produces handles; it does not read materialized output
files, FeatureValueRecord rows, LabelValueRecord rows, provider payloads, or
heavy artifacts.

The `RuntimeInputPack` records canonical input-view handles for:

- `CanonicalBarRecord`;
- `CanonicalBBORecord`;
- `DenseGridBarRecord`.

Those are record type references only. The resolver does not construct
canonical rows and does not open raw provider files.

## Availability Discipline

Every feature handle must carry an `available_ts` window. Every label handle
must carry a `label_available_ts` window. Resolver checks fail closed when:

- a feature pack is missing `first_available_ts` or `last_available_ts`;
- a label pack is missing `first_label_available_ts` or
  `last_label_available_ts`;
- availability is earlier than the corresponding event timestamp;
- a label version ref is supplied as a feature pack ref;
- a live feature contract references label fields or label input views.

Labels stay in `label_packs`; they are not exposed as live feature inputs.

## Partition Handling

Callers must provide explicit partition and session scope. Missing scope is
`INPUTS_INCONCLUSIVE`.

`locked_test_candidate` and `latest_shadow_candidate` require substantive
governance contamination metadata. Selection on `locked_test_candidate` is
refused. Development and validation partitions remain ordinary resolution
scope; they still carry the chosen partition id into every feature and label
handle.

## Source Separation

Databento and IBKR DatasetVersions are never merged into one runtime input
bundle. The accepted DatasetVersion id must match every resolved feature and
label pack. A pack bound to another DatasetVersion blocks resolution.

Raw-provider and external-provider requests are rejected by metadata and suffix
guards. The resolver does not import Databento or IBKR client modules, request
provider reads, or reach outside local registries.

## Value-Free Output

`RuntimeInputPack.to_dict()` serializes a stable JSON-compatible mapping with:

- approved AlphaSpec and StudySpec refs;
- the governance `StudyInputPack` payload;
- DatasetVersion id, lifecycle state, source, and reproducibility hashes;
- canonical record-type handles;
- feature and label pack handles with availability metadata;
- partition, session, and governance metadata.

It does not embed raw data, canonical records, feature values, label values,
provider responses, local databases, parquet/arrow/feather/dbn/zst payloads, or
runtime result artifacts.

No `alpha runtime` CLI is added by RT-P03; the runtime CLI remains scoped to
RT-P18.
