# Request-To-Study Workflow

This page describes the governed path from a request to a future `StudySpec`
input reference. It is descriptive substrate guidance; it does not run a study
or produce evidence.

## Step 1: FeatureRequest

Every feature starts with an existing governance `FeatureRequest` record. The
id prefix is `freq_`. The authoritative contract is
`../../governance/FEATURE_REQUEST.md`.

The Feature/Label layer consumes that record through the FLF-P05 gate described
in `../FEATURE_REQUEST_GATE.md`. The gate admits implementation only when the
governance request validates, duplicate-exposure notes are checked, and the
approval status is `APPROVED`.

Rejected or unchecked request states fail closed:

- `PENDING`
- `NEEDS_REVIEW`
- `BLOCKED_DUPLICATE`

The duplicate-exposure guard is governance-owned. Feature templates must record
the guard result and matched exposure notes; they must not define a parallel
duplicate detector.

## Step 2: FeatureSpec And FeatureVersion

A `FeatureSpec` binds the approved `freq_` handle to feature-layer metadata:
input views, transform, window, normalization, family, availability
assumptions, and an explicit `available_ts` derivation rule. The authoritative
contract is `../FEATURE_CONTRACTS.md`.

Feature contracts follow these rules:

- no `FeatureSpec` means no feature values;
- live feature windows must be causal;
- centered and future windows are offline-only and cannot be live-feature
  inputs;
- the `available_ts` rule must state how output availability is derived from
  input availability;
- `FeatureVersion` is deterministic metadata derived from the complete spec
  payload.

`FeatureVersion` and `FeatureStore` records are substrate references. They do
not imply a result, promotion, trading use, or deployment use.

## Step 3: LabelSpec And LabelVersion

Every label starts with an existing governance `LabelSpec` record. The id
prefix is `lspec_`. The authoritative contract is
`../../governance/LABEL_SPEC.md`.

The label-layer contract adapts that governance record into label metadata as
described in `../LABEL_CONTRACTS.md`. It consumes:

- horizon metadata;
- path rules;
- cost model;
- target/stop rules;
- `availability_time`;
- `forbidden_feature_overlap`;
- leakage checks, including `label_as_feature` and `availability_time`.

Label contracts follow these rules:

- no `LabelSpec` means no label values;
- every label value carries `label_available_ts`;
- future observations are legal only inside the governed label horizon;
- label values, aliases, specs, and versions cannot be exposed as live
  features;
- `LabelVersion` is deterministic metadata derived from the complete label
  contract payload.

## Step 4: Local Stores

The FeatureStore and LabelStore are local-only discoverability and lineage
surfaces. Their docs are `../FEATURE_STORE.md` and `../LABEL_STORE.md`.

Feature and label registries store metadata, lineage, summary timestamps,
quality/audit status, and deprecation metadata. They do not store raw data,
canonical rows, materialized value payloads, provider files, or broker state.

The terminal study-consumable state is `READY_FOR_STUDY`. That state means the
substrate object can be referenced by a governed study input. It is not a
research result.

## Step 5: StudySpec Input

A future `StudySpec` consumes handles and dataset-scope metadata. It does not
copy FeatureRequest, FeatureSpec, LabelSpec, FeatureVersion, or LabelVersion
schemas into a new object.

Use the StudySpec input-pack guidance in `../governance_integration.md`:

- feature request handles use `freq_`;
- label spec handles use `lspec_`;
- the AlphaSpec handle uses `aspec_`;
- the StudySpec handle uses `sspec_`;
- `dataset_scope` remains explicit and canonically serializable.

The pack is an input bundle only. It does not create evidence, run diagnostics,
or change lifecycle states.

## Templates

Researcher-facing forms live in `../templates/`. Reusable YAML templates live in
`../../../templates/feature_label/`. They reference governance contracts and id
prefixes, but they do not replace those contracts.
