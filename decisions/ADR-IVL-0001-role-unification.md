# ADR-IVL-0001 - Role Unification For The Idea-To-Verdict Loop

Status: Accepted by campaign contract; YELLOW review is required before merge.
Date: 2026-06-14
Campaign: ALPHA_IDEA_TO_VERDICT_LOOP_V0
Phase: IVL-P00

## Context

The existing governance spine already contains the durable objects needed for an
idea-to-verdict loop, but they are not one researcher-facing line yet. The IVL
campaign must assemble that line without changing the frozen governance record
schemas, creating a second card class, or making any research result claim.

Verified current-code facts:

- `HypothesisCard`, `AlphaSpec`, `MechanismCard`, `SetupSpec`, and `StudySpec`
  are frozen, slotted governance dataclasses validated through closed field
  sets.
- `AlphaSpec` requires a `hypothesis_id`; a valid front door therefore needs a
  HypothesisCard parent or a pre-existing HypothesisCard ID before it can mint a
  valid AlphaSpec.
- `StudySpec` accepts `alpha_spec_id` and `label_spec_id`; it has no
  `mechanism_id`, `setup_spec_id`, or `study_kind` field.
- `TrialLedgerRecord`, `EvidenceBundle`, and `PromotionDecision` all carry
  `alpha_spec_id`.
- `RejectedIdeaRecord` accepts only `alpha_spec_id_or_hypothesis_id`, validated
  as an AlphaSpec or HypothesisCard governance ID. It does not accept
  MechanismCard or SetupSpec IDs.
- `MechanismCard`, `SetupSpec`, and `AlphaSpec` deterministic IDs hash all
  non-ID content fields through the governance ID generator. Adding a new field
  would re-hash locked IDs and break closed-schema validation.
- `study_kind` is absent from `src/alpha_system/governance/`; it is greenfield
  intake metadata, not a governance dataclass field.
- Governance ID prefixes are content-addressed 24-hex tokens such as `hyp_`,
  `aspec_`, `mech_`, `setup_`, and `sspec_`.

## Decision

The canonical IVL object line is:

```text
idea.yaml / IdeaDraft
  -> HypothesisCard
  -> AlphaSpec front-door trunk
  -> emitted EXPLORATORY MechanismCard sidecar
  -> optional EXPLORATORY SetupSpec sidecar
  -> FeatureRequest / LabelSpec
  -> StudySpec
  -> TrialLedgerRecord / EvidenceBundle / ReviewerVerdict
  -> RejectedIdeaRecord / RequeuedVerdictRecord / PromotionDecision
  -> FactorLibrary only after a survivor gate, outside V0
```

`AlphaSpec` is the kill-trunk. The front door always mints or resolves the
HypothesisCard and then mints an AlphaSpec before any verdict can be routed to
memory. Shape-bearing ideas still ride the AlphaSpec trunk; `MechanismCard` and
optional `SetupSpec` are emitted sub-objects carried as lineage sidecars by the
intake/orchestration layer.

There is no `MechanismCard -> SetupSpec -> StudySpec` replacement path in V0.
`SetupSpec` can reference a `mechanism_id`, but `StudySpec` remains
AlphaSpec-keyed. The orchestration layer owns any cross-object bundle metadata.

## Role Contracts

| Object | Current or V0 role | Linkage rule | Not allowed in V0 |
| --- | --- | --- | --- |
| `idea.yaml` | Human or AI authored intake document. | Parsed into `IdeaDraft` in IVL-P01. | Not a governance ID and not a second card class. |
| `IdeaDraft` | New wrapper for intake-only routing metadata. | Holds `study_kind` (`main_effect` or `context_not_equal_trigger`) and source lineage. | Must not mutate existing governance dataclasses. |
| `HypothesisCard` | Existing parent governance record required by `AlphaSpec.hypothesis_id`. | Front door mints or resolves `hyp_<24-hex>` before AlphaSpec validation. | Not a substitute for AlphaSpec in the kill-trunk. |
| `AlphaSpec` | Always-minted front-door trunk and memory key. | Carries `hypothesis_id`; downstream StudySpec, TrialLedger, EvidenceBundle, PromotionDecision, and graveyard routing use `alpha_spec_id`. | No `study_kind`, `mechanism_id`, or `setup_spec_id` field. |
| `MechanismCard` | EXPLORATORY mechanism sidecar emitted from intake. | Mint canonical `mech_<24-hex>` from content. Legacy kebab slugs move to `source`. | Not a front-door trunk and not a FactorLibrary entry. |
| `SetupSpec` | Optional EXPLORATORY setup sidecar for shape-bearing ideas. | References `mechanism_id` and stays sidecar-linked by orchestration metadata. | No direct StudySpec replacement path. |
| `FeatureRequest` | Existing governance request for unmaterialized feature inputs. | AlphaSpec-keyed; later phases may request but IVL-P00 implements nothing. | No FeatureRequest implementation or materialization in P00. |
| `LabelSpec` | Existing governed label contract. | May optionally reference `alpha_spec_id`; StudySpec references `label_spec_id`. | No new label family or label materialization in P00. |
| `StudySpec` | Pre-diagnostic study plan. | Accepts `alpha_spec_id` and `label_spec_id`; the AlphaSpec is mandatory. | No schema mutation for mechanism/setup/study_kind. |
| `TrialLedgerRecord` | Attempt and variant accounting. | AlphaSpec-keyed and StudySpec-keyed. | No metric or trial created in P00. |
| `EvidenceBundle` | Evidence-ready manifest and limitations record. | AlphaSpec-keyed and StudySpec-keyed. | No evidence bundle created in P00. |
| `ReviewerVerdict` | Independent semantic review record. | Review process is driver/reviewer-owned. | Codex executor does not create review artifacts. |
| `RejectedIdeaRecord` | Graveyard memory for rejected ideas. | Must write via `alpha_spec_id_or_hypothesis_id`; IVL-P05 must assert an AlphaSpec ID exists before a REJECT write. | No MechanismCard or SetupSpec graveyard IDs. |
| `RequeuedVerdictRecord` | DATA_GAP or accrual memory. | Validated by the existing requeue record validator. | No fabricated data closure. |
| `PromotionDecision` | Reviewer-gated WATCH/CANDIDATE routing. | Requires AlphaSpec, EvidenceBundle, trial refs, and reviewer verdict ID. | No auto-promotion of EXPLORATORY artifacts. |
| `FactorLibrary` | Survivor-only memory after a gated downstream decision. | Current campaign survivor count remains 0. | No FactorLibrary module or ingestion in V0. |

## Conflict Resolutions

1. `study_kind` lives only on `IdeaDraft`.

   `study_kind` is greenfield intake metadata. It routes the loop:
   `main_effect` uses the main-effect diagnostics path and
   `context_not_equal_trigger` uses the setup conditional probe path. It must not
   be added to `MechanismCard`, `SetupSpec`, `AlphaSpec`, or `StudySpec`, because
   those records have deterministic content-hash IDs and closed schemas.

2. Shape-bearing ideas still ride the AlphaSpec trunk.

   `MechanismCard` and optional `SetupSpec` are lineage sidecars emitted by the
   front door. They do not replace AlphaSpec and do not form a new StudySpec
   parent chain. V0 links them at the orchestration layer.

3. REJECT writes through AlphaSpec.

   The graveyard accepts only AlphaSpec or HypothesisCard IDs. Because most
   later memory and evidence surfaces are already AlphaSpec-keyed, the front door
   must mint an AlphaSpec before any REJECT path. IVL-P05 must fail closed if an
   AlphaSpec ID is missing.

## Track-A Legacy Card Decision

The eight files under `research/differentiated_substrate_v1/cards/*.json` are a
legacy doc-convention schema. They are read-only references for IVL. They must
migrate into the canonical line and retire only after parity tests prove the
canonical line reproduces their content. They are not deleted in V0 and are not
a second card class.

The migration keeps the legacy kebab slug as lineage:

```text
legacy mechanism_id: day_of_week_effect
canonical mechanism_id: mech_<24-hex>
canonical source: track_a:day_of_week_effect
```

This preserves the stopped DK seam that stores the legacy slug in
`study_spec.dataset_scope["mechanism_id"]` without treating that slug as a
canonical MechanismCard ID.

## Track-A Field Map

| Legacy Track-A field | Canonical target | Rule |
| --- | --- | --- |
| `mechanism_id` | `MechanismCard.source` | Store as `track_a:<slug>`; do not reuse as `mechanism_id`. |
| `hypothesis.economic_rationale` | `MechanismCard.rationale`; HypothesisCard rationale source text | Preserve substantive rationale text. |
| `hypothesis.statement` | `MechanismCard.expected_mechanism`; HypothesisCard expected mechanism source text | Preserve as falsifiable mechanism text. |
| `expected_sign` | `MechanismCard.expected_direction` | Copy value as direction text. |
| `expected_horizon[]` | `MechanismCard.horizon` | Collapse by one MechanismCard per horizon or by a pre-registered primary horizon. |
| `expected_session` | `MechanismCard.session` | Copy session text. |
| `required_features.existing[]` | `MechanismCard.required_features` and AlphaSpec factor inputs | Flatten existing names. |
| `required_features.new[]` | Future FeatureRequest candidate metadata | P00/P01 do not implement FeatureRequest generation for missing substrate. |
| `required_labels.existing[]` | `MechanismCard.required_labels` and AlphaSpec label references | Flatten existing label family names. |
| `required_labels.new[]` | Future LabelSpec candidate metadata | No new label implementation in P00. |
| lookahead material | `AlphaSpec.timestamp_assumptions` and `exclusion_rules` | Preserve no-lookahead assumptions and blockers. |
| orthogonality material | `AlphaSpec.expected_failure_modes`, `promotion_criteria`, and `data_assumptions` | Preserve as gating and interpretation metadata; do not fabricate `duplicate_exposure`. |
| conditioning material | `IdeaDraft.study_kind` routing and optional `SetupSpec` | Shape-bearing context/trigger ideas emit SetupSpec sidecars. |
| `data_dependency.class` | Migration routing | Existing substrate may be tested only when selected; derivable and paid-data gaps fail closed or remain record-only. |

The four fields with no reliable Track-A doc source are `source`,
`cost_sensitivity`, `variant_budget`, and `duplicate_exposure`. IVL-P01 must
fail closed if it cannot populate them from explicit intake defaults or governed
pre-registration metadata. It must not synthesize placeholders.

## Data Dependency Partition

Verified against the current JSON files on 2026-06-14:

| Class | Count | Cards | V0 routing |
| --- | ---: | --- | --- |
| `existing_substrate` | 2 | `day_of_week_effect`, `open_close_auction_flow` | `day_of_week_effect` is the live exemplar selected by the campaign. `open_close_auction_flow` is current-file existing-substrate but is not selected as the IVL dogfood live exemplar. |
| `derivable_from_exchange_calendar` | 4 | `roll_week_flow`, `month_end_flow`, `month_end_rebalance_flow`, `opex_pinning` | DATA_GAP / requeue until a later, separately authorized FeatureRequest implementation exists. |
| `needs_paid_data` | 2 | `fomc_drift`, `cpi_surprise_reversion` | Record-only, RED-deferred, never tested in V0. |

The generated IVL-P00 prompt expected `existing_substrate x1` and
`derivable_from_exchange_calendar x5`. The current repository files instead
declare `open_close_auction_flow` as `existing_substrate`, so the source-grounded
partition is `2/4/2`. Later phases must reconcile this deliberately rather than
silently changing a legacy card or treating the stale count as fact.

## REUSE-MAP

| Symbol | Module | Verified role |
| --- | --- | --- |
| `validate_mechanism_card` | `alpha_system.governance.mechanism_card` | Closed-schema MechanismCard validation. |
| `create_mechanism_card` | `alpha_system.governance.mechanism_card` | Factory that mints canonical `mech_<24-hex>` IDs. |
| `generate_mechanism_id` | `alpha_system.governance.mechanism_card` | Deterministic MechanismCard ID generation. |
| `validate_setup_spec` | `alpha_system.governance.setup_spec` | Closed-schema SetupSpec validation. |
| `create_setup_spec` | `alpha_system.governance.setup_spec` | Factory for optional setup sidecars. |
| `validate_alpha_spec` | `alpha_system.governance.alpha_spec` | Closed-schema AlphaSpec validation. |
| `create_rejected_idea_record` | `alpha_system.governance.rejected_idea` | Graveyard record creation. |
| `validate_requeued_verdict_record` | `alpha_system.governance.requeue` | DATA_GAP/requeue record validation. |
| `create_promotion_decision` | `alpha_system.governance.promotion` | Reviewer-gated promotion decision creation. |
| `reject_exploratory_promotion_artifact` | `alpha_system.governance.promotion` | Fail-closed EXPLORATORY promotion guard. |
| `reject_exploratory_promotion_artifacts` | `alpha_system.governance.promotion` | Batch EXPLORATORY promotion guard. |
| `_distribution_summary` | `alpha_system.runtime.diagnostics.label.runtime` | Label distribution summary used by later gate logic. |
| `_class_balance_summary` | `alpha_system.runtime.diagnostics.label.runtime` | Class-balance summary used by later gate logic. |
| `build_factor_diagnostics_run` | `alpha_system.runtime.diagnostics.factor.runtime` | Existing main-effect diagnostics engine. |
| `evaluate_setup_conditional_probe` | `alpha_system.research.conditional_probe` | Existing context-vs-trigger conditional probe. |
| `load_parquet_values` | `alpha_system.core.value_store` | Existing value loader; import-only in later bridge, no edit here. |
| `FeatureLabelPackResolver` | `alpha_system.runtime.input_resolver` | Existing governed pack resolver. |
| `VerdictReasonCode` | `alpha_system.governance.verdict_reason_code` | Closed reason-code enum. |
| `validate_verdict_reason_code` | `alpha_system.governance.verdict_reason_code` | Fail-closed reason-code validator. |

## Out Of Scope

IVL-P00 creates no code, no schema mutation, no tests, no CLI, no migration
mapper, no FeatureRequest implementation, no label implementation, no paid-data
sourcing, no materialization, no registry write, no real-data metric, and no
downstream module. It does not touch FUTSUB, DK tooling, stopped campaign
artifacts, legacy card JSON, or `core/value_store.py`.

This ADR is research-only architecture. It asserts no edge, no profitability, no
tradability, and no production readiness.
