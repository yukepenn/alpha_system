# Phase Spec - IVL-P00: Role-Unification ADR + Canonical Idea-Object Schema Map

Campaign: `ALPHA_IDEA_TO_VERDICT_LOOP_V0`
Phase ID: `IVL-P00`
Lane: YELLOW
Change class: Documentation / ADR only. No code, no schema mutation, no
behavior change.

This standalone spec file records the generated IVL-P00 execution contract at
the path requested by the Workflow 2 executor prompt. The campaign also contains
the pre-existing combined spec file
`specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00-role-unification-adr-schema-map.md`.

## Purpose

Record the decided canonical idea-object hierarchy as a durable ADR plus a
field-level schema map, grounded against current code, so IVL-P01..P06 have one
authoritative role contract.

The phase establishes:

- AlphaSpec is the front-door kill-trunk and is always minted after the required
  HypothesisCard parent is available.
- MechanismCard and optional SetupSpec are emitted EXPLORATORY sub-objects and
  lineage sidecars, not replacements for AlphaSpec.
- `study_kind` lives only on a new `IdeaDraft` intake wrapper.
- The eight Track-A JSON cards are legacy doc-convention records,
  migrate-then-retire, and read-only in V0.

## Scope

Author:

- `decisions/ADR-IVL-0001-role-unification.md`
- `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`

The ADR and schema map must record:

- Per-object role contracts for `idea.yaml` / `IdeaDraft`,
  HypothesisCard, AlphaSpec, MechanismCard, SetupSpec, FeatureRequest,
  LabelSpec, StudySpec, TrialLedgerRecord, EvidenceBundle, ReviewerVerdict,
  RejectedIdeaRecord, RequeuedVerdictRecord, PromotionDecision, and
  FactorLibrary as survivor-only gated memory.
- The AlphaSpec-always-minted rule and the reason current memory/evidence
  objects key off `alpha_spec_id`.
- The three conflict resolutions:
  - `study_kind` is wrapper-only and absent from current governance dataclasses.
  - Shape-bearing ideas still ride the AlphaSpec trunk.
  - REJECT graveyard writes via AlphaSpec because RejectedIdea accepts only
    AlphaSpec/HypothesisCard IDs.
- The Track-A-to-canonical field map.
- The four fail-closed gaps: `source`, `cost_sensitivity`, `variant_budget`,
  and `duplicate_exposure`.
- The `mech_<24-hex>` canonical ID rule and the
  `track_a:<legacy_slug>` source-lineage rule.
- The current `data_dependency.class` partition for the eight legacy cards.
- A REUSE-MAP verifying all cited reuse symbols exist in current code.

## Non-Goals

- No source code, tests, schema changes, CLI, migration mapper, probe, metric,
  materialization, recompute, registry write, paid data, broker, paper/live
  operation, PR, merge, or reviewer artifact.
- No edit to `src/**`, `tests/**`, legacy Track-A card JSON, FUTSUB/DK stopped
  campaign paths, `core/value_store.py`, data files, caches, logs, DBs, or
  secrets.
- No second card class and no downstream module charter.

## Allowed Paths

Commit-eligible outputs for this executor pass:

- `decisions/ADR-IVL-0001-role-unification.md`
- `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`
- `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00-role-unification-adr.md`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`

Reviewer artifacts, PRs, staging, commits, pushes, and merges are driver-owned
or reviewer-owned and are not created by Codex in this executor pass.

## Validation

Requested local validation:

```bash
test -f decisions/ADR-IVL-0001-role-unification.md
test -f docs/IDEA_TO_VERDICT_SCHEMA_MAP.md
test -f specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00-role-unification-adr.md
test -f campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/GOAL.md
test -f campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/campaign.yaml
python -c "import yaml; yaml.safe_load(open('campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/campaign.yaml'))"
grep -q "ALPHA_IDEA_TO_VERDICT_LOOP_V0" ACTIVE_CAMPAIGN.md
just frontier-plan ALPHA_IDEA_TO_VERDICT_LOOP_V0
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
python tools/verify.py --artifacts
git ls-files runs
```

The executor prompt for this run forbids `git status`, `git diff`, `git add`,
`git commit`, `git push`, PR creation, merge, reviewer execution,
`review.md`, and `verdict.json`. Those checks and artifacts are skipped by
Codex and remain Ralph/reviewer-owned.

## Done Criteria

- ADR and schema map are written and grounded against current code.
- REUSE-MAP symbols are verified by symbol name.
- Legacy cards are marked read-only legacy/migrate-then-retire.
- No code, tests, schemas, data, legacy card JSON, or forbidden paths are
  changed.
- Commit-eligible handoff records delivered scope, validations, skips, and
  residual discrepancies.

This phase is research-only and asserts no edge, profitability, tradability, or
production readiness.
