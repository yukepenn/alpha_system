# Idea-To-Verdict Canonical Schema Map

Campaign: ALPHA_IDEA_TO_VERDICT_LOOP_V0
Phase: IVL-P00
Status: Canonical map for IVL-P01..P06 after YELLOW review and merge.

This map pins the object roles and the Track-A legacy-card migration rules for
the idea-to-verdict loop. It is documentation only. It does not change any
schema, validator, data, metric, registry, or runtime behavior.

## Canonical Object Contracts

| Object | Source | Canonical role | Key fields and links |
| --- | --- | --- | --- |
| `idea.yaml` | New intake document in IVL-P01 | User-authored front-door input. | Supplies source text, author, lineage, study intent, and required governed fields. |
| `IdeaDraft` | New intake wrapper in IVL-P01 | Holds intake-only metadata. | `study_kind` lives here only: `main_effect` or `context_not_equal_trigger`. |
| `HypothesisCard` | `governance/hypothesis_card.py` | Required parent for valid AlphaSpec creation. | `hypothesis_id`, `title`, `family`, `rationale`, `expected_mechanism`, `falsification_criteria`, `risks`, `author`, `created_at`. |
| `AlphaSpec` | `governance/alpha_spec.py` | Always-minted front-door trunk and kill-trunk. | `alpha_spec_id`, `hypothesis_id`, `target_instruments`, `data_assumptions`, `factor_inputs`, `label_references`, `exclusion_rules`, `timestamp_assumptions`, `cost_assumptions`, `expected_failure_modes`, `promotion_criteria`, `created_by`, `created_at`. |
| `MechanismCard` | `governance/mechanism_card.py` | EXPLORATORY mechanism sidecar. | `mechanism_id`, `source`, `rationale`, `expected_mechanism`, `expected_direction`, `horizon`, `session`, `required_features`, `required_labels`, `cost_sensitivity`, `variant_budget`, `duplicate_exposure`, `stamp`. |
| `SetupSpec` | `governance/setup_spec.py` | Optional EXPLORATORY setup sidecar for shape-bearing ideas. | Setup shape fields plus `mechanism_id` and `stamp`; linked by orchestration, not by StudySpec mutation. |
| `FeatureRequest` | `governance/feature_request.py` | Governed request for missing feature inputs. | `feature_request_id`, `alpha_spec_id`, requested inputs and approval metadata. No IVL-P00/P01 implementation for missing substrate. |
| `LabelSpec` | `governance/label_spec.py` | Governed label definition contract. | `label_spec_id`, label rules, availability, leakage checks, optional `alpha_spec_id`. |
| `StudySpec` | `governance/study_spec.py` | Pre-diagnostic study plan. | `study_spec_id`, `alpha_spec_id`, `label_spec_id`, dataset scope, split protocol, metrics, budget and policy fields. |
| `TrialLedgerRecord` | `governance/trial_ledger.py` | Attempt and variant accounting. | AlphaSpec-keyed and StudySpec-keyed. |
| `EvidenceBundle` | `governance/evidence_bundle.py` | Evidence-ready manifest and limitations record. | AlphaSpec-keyed and StudySpec-keyed. |
| `ReviewerVerdict` | `governance/reviewer_verdict.py` | Independent semantic review result. | Records reviewer judgment only; no market-truth claim. |
| `RejectedIdeaRecord` | `governance/rejected_idea.py` | REJECT memory. | `alpha_spec_id_or_hypothesis_id` accepts only AlphaSpec or HypothesisCard IDs. |
| `RequeuedVerdictRecord` | `governance/requeue.py` | DATA_GAP/accrual memory. | Validated by `validate_requeued_verdict_record`. |
| `PromotionDecision` | `governance/promotion.py` | Reviewer-gated WATCH/CANDIDATE transition. | Requires `alpha_spec_id`, evidence refs, trial refs, and `reviewer_verdict_id`. |
| `FactorLibrary` | Compass-stage survivor memory | Out of V0; survivor-only and gated. | No module was chartered by IVL-P00; current survivor status belongs to `status_doctor` plus the freshest research-state decision ledger. |

## Role And Link Rules

- The front door always mints or resolves a HypothesisCard and then mints an
  AlphaSpec before any StudySpec, evidence, verdict, or memory write.
- AlphaSpec is the trunk for kill, evidence, promotion, and graveyard routing.
- MechanismCard and optional SetupSpec are sidecars emitted by intake. They
  carry lineage and shape information but do not replace AlphaSpec.
- `study_kind` lives only on `IdeaDraft`. It never appears on AlphaSpec,
  MechanismCard, SetupSpec, StudySpec, or any existing governance dataclass.
- StudySpec remains keyed by `alpha_spec_id` and `label_spec_id`. No
  `MechanismCard -> SetupSpec -> StudySpec` chain exists in V0.
- REJECT memory writes through AlphaSpec. IVL-P05 must fail closed if an
  AlphaSpec ID is unavailable before graveyard routing.

## Track-A Legacy Card Inventory

The eight files under `research/differentiated_substrate_v1/cards/*.json` are a
legacy doc-convention schema. They remain read-only in V0 and migrate into the
canonical line later. Retirement is a later parity-test-gated step.

Verified current `data_dependency.class` values:

| Legacy card | Class | V0 migration route |
| --- | --- | --- |
| `day_of_week_effect` | `existing_substrate` | Historical main-effect exemplar selected by the IVL campaign. |
| `open_close_auction_flow` | `existing_substrate` | Existing-substrate legacy record, but not selected as the IVL dogfood exemplar. |
| `roll_week_flow` | `derivable_from_exchange_calendar` | DATA_GAP / requeue until a later FeatureRequest implementation exists. |
| `month_end_flow` | `derivable_from_exchange_calendar` | DATA_GAP / requeue until a later FeatureRequest implementation exists. |
| `month_end_rebalance_flow` | `derivable_from_exchange_calendar` | DATA_GAP / requeue until a later FeatureRequest implementation exists. |
| `opex_pinning` | `derivable_from_exchange_calendar` | DATA_GAP / requeue until a later FeatureRequest implementation exists. |
| `fomc_drift` | `needs_paid_data` | Record-only, RED-deferred, never tested in V0. |
| `cpi_surprise_reversion` | `needs_paid_data` | Record-only, RED-deferred, never tested in V0. |

Partition note: the generated IVL-P00 prompt expected
`existing_substrate x1`, `derivable_from_exchange_calendar x5`,
`needs_paid_data x2`. The current JSON source declares
`existing_substrate x2`, `derivable_from_exchange_calendar x4`,
`needs_paid_data x2`. The mismatch is `open_close_auction_flow`, which is
currently `existing_substrate`. Later implementation must reconcile that
explicitly and must not rewrite a legacy card in V0.

## Track-A Field Map

| Track-A field | Canonical field or object | Migration rule |
| --- | --- | --- |
| `mechanism_id` | `MechanismCard.source` | Convert kebab slug to `track_a:<slug>`. Do not reuse as canonical `mechanism_id`. |
| `hypothesis.economic_rationale` | `MechanismCard.rationale`; HypothesisCard rationale source | Preserve the substantive economic rationale as research hypothesis text. |
| `hypothesis.statement` | `MechanismCard.expected_mechanism`; HypothesisCard expected mechanism source | Preserve as falsifiable mechanism text. |
| `expected_sign` | `MechanismCard.expected_direction` | Copy as direction text such as `undirected` or `reversion`. |
| `expected_horizon[]` | `MechanismCard.horizon` | Collapse list to string by minting one MechanismCard per horizon or by recording a pre-registered primary horizon. |
| `expected_session` | `MechanismCard.session` | Copy session text. |
| `required_features.existing[]` | `MechanismCard.required_features`; AlphaSpec factor inputs | Flatten to list of existing feature names. |
| `required_features.new[]` | FeatureRequest candidate metadata | Record as missing substrate. IVL charters no FeatureRequest implementation. |
| `required_labels.existing[]` | `MechanismCard.required_labels`; AlphaSpec label references | Flatten to list of existing label family names. |
| `required_labels.new[]` | LabelSpec candidate metadata | Record as a future label need only; no label implementation in P00. |
| `data_dependency.class` | AlphaSpec `data_assumptions`; routing status | `existing_substrate`, `derivable_from_exchange_calendar`, or `needs_paid_data` controls fail-closed routing. |
| `data_dependency.detail` | AlphaSpec `data_assumptions` | Preserve detail and deferred-approval notes. |
| `lookahead_controls` or lookahead-risk notes | AlphaSpec `timestamp_assumptions`; `exclusion_rules` | Preserve timing assumptions and blockers. |
| orthogonality notes | AlphaSpec `expected_failure_modes`; `promotion_criteria`; `data_assumptions` | Preserve as interpretation and gating notes. Do not populate `duplicate_exposure` from vague orthogonality prose. |
| conditioning notes | `IdeaDraft.study_kind`; optional `SetupSpec` fields | Main-effect cards stay `main_effect`; context-vs-trigger ideas emit SetupSpec sidecars. |
| `promotion_criteria` | AlphaSpec `promotion_criteria` | Preserve criteria when present; otherwise require explicit governed defaults. |
| `failure_modes` | AlphaSpec `expected_failure_modes` | Preserve when present; otherwise require explicit governed defaults. |

## Fail-Closed Gaps

The Track-A documents do not provide reliable canonical sources for these
required fields:

| Canonical field | Why it is a gap | Required IVL-P01 behavior |
| --- | --- | --- |
| `MechanismCard.source` | No field named `source`; only legacy kebab slug exists. | Populate only by the explicit lineage rule `track_a:<slug>` or fail closed. |
| `MechanismCard.cost_sensitivity` | Track-A cards do not carry a canonical cost-sensitivity object. | Require explicit intake/governance value; do not synthesize. |
| `MechanismCard.variant_budget` | Track-A cards do not carry the canonical integer budget. | Require a pre-registered budget; do not default silently. |
| `MechanismCard.duplicate_exposure` | Track-A cards do not carry the canonical duplicate-exposure object. | Require dedup metadata or fail closed. |

These gaps are validation blockers, not TODO placeholders.

## Mechanism ID Lineage Rule

Canonical MechanismCard IDs are deterministic `mech_<24-hex>` IDs generated from
canonical content. Legacy Track-A slugs are not canonical IDs. The migration
must preserve them as lineage:

| Legacy slug | Canonical ID | Canonical source |
| --- | --- | --- |
| `day_of_week_effect` | Fresh `mech_<24-hex>` | `track_a:day_of_week_effect` |
| `roll_week_flow` | Fresh `mech_<24-hex>` | `track_a:roll_week_flow` |
| `fomc_drift` | Fresh `mech_<24-hex>` | `track_a:fomc_drift` |
| `open_close_auction_flow` | Fresh `mech_<24-hex>` | `track_a:open_close_auction_flow` |
| `month_end_rebalance_flow` | Fresh `mech_<24-hex>` | `track_a:month_end_rebalance_flow` |
| `cpi_surprise_reversion` | Fresh `mech_<24-hex>` | `track_a:cpi_surprise_reversion` |
| `opex_pinning` | Fresh `mech_<24-hex>` | `track_a:opex_pinning` |
| `month_end_flow` | Fresh `mech_<24-hex>` | `track_a:month_end_flow` |

The stopped DK tooling can continue to read legacy
`study_spec.dataset_scope["mechanism_id"]` strings without confusing those
strings for canonical MechanismCard IDs.

## Data Dependency Routing

| Class | Rule |
| --- | --- |
| `existing_substrate` | May be considered for a load-only existing slice only after the testability gate and explicit campaign selection. In IVL history, the selected exemplar was `day_of_week_effect`. |
| `derivable_from_exchange_calendar` | Return DATA_GAP / requeue in V0. No FeatureRequest implementation is chartered. |
| `needs_paid_data` | Migrate as record-only metadata. RED-deferred and never tested in V0. |

## REUSE-MAP

| Reuse symbol | Current module |
| --- | --- |
| `validate_mechanism_card` | `alpha_system.governance.mechanism_card` |
| `create_mechanism_card` | `alpha_system.governance.mechanism_card` |
| `generate_mechanism_id` | `alpha_system.governance.mechanism_card` |
| `validate_setup_spec` | `alpha_system.governance.setup_spec` |
| `create_setup_spec` | `alpha_system.governance.setup_spec` |
| `validate_alpha_spec` | `alpha_system.governance.alpha_spec` |
| `create_rejected_idea_record` | `alpha_system.governance.rejected_idea` |
| `validate_requeued_verdict_record` | `alpha_system.governance.requeue` |
| `create_promotion_decision` | `alpha_system.governance.promotion` |
| `reject_exploratory_promotion_artifact` | `alpha_system.governance.promotion` |
| `reject_exploratory_promotion_artifacts` | `alpha_system.governance.promotion` |
| `_distribution_summary` | `alpha_system.runtime.diagnostics.label.runtime` |
| `_class_balance_summary` | `alpha_system.runtime.diagnostics.label.runtime` |
| `build_factor_diagnostics_run` | `alpha_system.runtime.diagnostics.factor.runtime` |
| `evaluate_setup_conditional_probe` | `alpha_system.research.conditional_probe` |
| `load_parquet_values` | `alpha_system.core.value_store` |
| `FeatureLabelPackResolver` | `alpha_system.runtime.input_resolver` |
| `VerdictReasonCode` | `alpha_system.governance.verdict_reason_code` |
| `validate_verdict_reason_code` | `alpha_system.governance.verdict_reason_code` |

## Out Of Scope

This map does not authorize code, schema mutation, tests, CLI commands, runtime
metrics, paid-data sourcing, materialization, registry writes, FeatureRequest
implementation, LabelSpec implementation, legacy-card deletion, FUTSUB/DK edits,
FactorLibrary ingestion, broker/paper/live operations, or any production
deployment.

All language here is research-only and does not assert edge, profitability,
tradability, or production readiness.
