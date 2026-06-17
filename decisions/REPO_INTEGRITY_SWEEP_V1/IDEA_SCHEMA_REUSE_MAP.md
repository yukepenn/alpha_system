# Repo Integrity Sweep V1 - Idea Schema Reuse Map

## Canonical Intake

| Object | Canonical owner | Duplicates found | Action |
| --- | --- | --- | --- |
| `idea.yaml` / authored payload | `alpha_system.cli.idea` + governance validators | Fixture and historical campaign examples | Keep; validate front-door now audits versioned pack refs. |
| `IdeaDraft` | `governance/idea_draft.py` | Historical Track-A card forms | Keep canonical wrapper; Track-A remains historical input data. |
| `HypothesisCard` | `governance/hypothesis_card.py` | Legacy narrative hypothesis fields | Keep; legacy text maps into canonical fields only through intake. |
| `AlphaSpec` | `governance/alpha_spec.py` | None requiring a second trunk | Keep as front-door trunk. |
| `MechanismCard` | `governance/mechanism_card.py` | Legacy mechanism slugs | Keep as exploratory sidecar; legacy slugs remain lineage, not IDs. |
| `SetupSpec` | `governance/setup_spec.py` | Shape-bearing setup prose in older cards | Keep as sidecar; no second intake universe. |
| `SliceSpec` | `research_lane/slice_spec.py` | `slice_spec`, `fast_probe_slice`, `slices` payload spellings | Keep compatibility; `pack_pin_audit` iterates known spellings and normalizes through `SliceSpec`. |
| `FeatureRequest` | `governance/feature_request.py` | Future/missing-feature prose | Preserve as governed request object; no implementation added. |
| `LabelSpec` | `governance/label_spec.py` | Future/missing-label prose | Preserve as governed request object; no implementation added. |
| `EvidenceBundle` | `governance/evidence_bundle.py` | None in this sweep | Keep. |
| `ReviewerVerdict` | `governance/reviewer_verdict.py` | Review docs | Keep; no self-promotion changes. |
| `TrialLedgerRecord` | `governance/trial_ledger.py` | Historical ledgers | Keep. |

## Decision

No schema was forked. The new `pack_pin_audit` is a value-free validation helper
that consumes existing `SliceSpec` shape and existing `FeatureLabelPackResolver`
semantics. Frozen content-hash governance objects were not mutated.
