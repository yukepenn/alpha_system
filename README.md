# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The active campaign is `ALPHA_RESEARCH_GOVERNANCE_MVP`, defined in `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/`. Current phase progress is tracked in `ACTIVE_CAMPAIGN.md`.

This repository is not a broker, paper-trading, live-trading, order-routing, or production execution system. It must not introduce alpha, profitability, tradability, or production-readiness claims.

## Current Repo Snapshot

`ALPHA_RESEARCH_GOVERNANCE_MVP` is underway through `ARGOV-P16` of the `ARGOV-P00`...`ARGOV-P19` governance campaign. `ARGOV-P16` has completed its executor deliverables for Ralph validation and independent review: governance CLI commands now live under `src/alpha_system/cli/**`, local validation helpers live under `tools/governance/**`, and `docs/governance/CLI.md` documents the command surface. Earlier durable governance modules remain in place, including the local governance registry, canary harness, negative-control catalog, `NegativeControlResult`, `ReviewerVerdict`, `PromotionDecision`, `RejectedIdeaRecord`, `EvidenceBundle`, `TrialLedgerRecord`, `StudySpec`, `LabelSpec`, `FeatureRequest`, `AlphaSpec`, `HypothesisCard`, and their associated gates. This is the 17th of 20 planned ARGOV phases after Ralph-owned review and merge gates; no phase PASS verdict is recorded here.

The active/next planned phase is `ARGOV-P17 — Unsupported-Claim Guard and Governance Report Templates`. Governance CLI commands, validation helpers, `docs/governance/CLI.md`, registry integration, and `docs/governance/REGISTRY_INTEGRATION.md` are now durable machinery for later phases.

The prior `ALPHA_SYSTEM_V1` and `ASV1_RELEASE_HYGIENE` baselines are treated as complete. This governance campaign builds on that local-first research harness by adding the admissibility and evidence-governance protocol that future research must pass through before broader research campaigns begin.

Safety boundaries are unchanged: governance-only scope, no real data ingestion, no alpha search, no broker/live/paper work, no order routing, no production deployment behavior, no raw or heavy artifact commits, no local DB commits, explicit staging only, and no alpha, profitability, tradability, or production-readiness claims.

## Governance Docs

The governance docs root currently includes:

- `docs/governance/README.md`
- `docs/governance/GOVERNANCE_OVERVIEW.md`
- `docs/governance/NAMING.md`
- `docs/governance/PRIMITIVES.md`
- `docs/governance/ALPHA_SPEC.md`
- `docs/governance/PRE_REGISTRATION.md`
- `docs/governance/FEATURE_REQUEST.md`
- `docs/governance/DUPLICATE_EXPOSURE.md`
- `docs/governance/LABEL_SPEC.md`
- `docs/governance/LABEL_LEAKAGE_GUARD.md`
- `docs/governance/STUDY_SPEC.md`
- `docs/governance/STUDY_BUDGET.md`
- `docs/governance/TRIAL_LEDGER.md`
- `docs/governance/EVIDENCE_BUNDLE.md`
- `docs/governance/REJECTED_IDEA_LEDGER.md`
- `docs/governance/PROMOTION_GATE.md`
- `docs/governance/REVIEWER_INDEPENDENCE.md`
- `docs/governance/NEGATIVE_CONTROLS.md`
- `docs/governance/CANARY_HARNESS.md`
- `docs/governance/GOVERNANCE_STATE_MACHINE.md`
- `docs/governance/REGISTRY_INTEGRATION.md`
- `docs/governance/CLI.md`

These docs describe the admissibility protocol at a high level, define the canonical governance object names and prefixes, document the shared ID, serialization, hashing, and fail-closed validation primitives, describe the `AlphaSpec` contract plus no-code gate, describe the `HypothesisCard` plus pre-registration linkage, describe the `FeatureRequest` contract plus duplicate-exposure guard, describe the `LabelSpec` contract plus label-leakage guard, describe the `StudySpec` contract plus study-budget protocol, describe the `TrialLedgerRecord` contract plus variant accounting, describe the `EvidenceBundle` contract plus manifest contract, describe the `RejectedIdeaRecord` research graveyard ledger, describe the `PromotionDecision` contract plus promotion-gate state machine, describe the `ReviewerVerdict` contract plus reviewer-independence rule, describe the negative-control catalog plus `NegativeControlResult` contract, describe the synthetic canary harness, document governance registry persistence, and document the governance CLI. Report builders remain for later phases.

## Campaign Source Of Truth

The active campaign contract bundle lives under `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/`:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

`ACTIVE_CAMPAIGN.md` is the repository-level active-campaign pointer. Do not create a campaign-local active-campaign pointer for this campaign.

## Repository Location

Canonical repo path:

```text
~/projects/alpha_system
```

The active repo and any active worktree must live on the WSL2 Linux filesystem. Do not run active work from `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, or temporary directories.

## Workflow 2 Boundary

Frontier Workflow 2 uses Ralph as the strict autonomous driver. Codex executes generated phase specs and writes executor output and commit-eligible handoffs. Ralph owns formal validation, independent review, verdict parsing, repair orchestration, semantic done-checks, PR creation, CI, and merge gates.

Required safety defaults:

- STOP files halt the Workflow 2 loop at the configured checkpoints.
- Failed runs and rejected ideas must remain visible to the governance process.
- Yellow phases require fresh independent review before merge eligibility.
- No phase may weaken or game tests.

## Git Discipline

Use explicit staging only. Stage curated paths one by one.

Forbidden:

```bash
git add .
git add -A
git push --force
```

Before any commit, inspect:

```bash
git status --short
git diff --cached --name-only
```

The staged set must contain only commit-eligible paths for the active phase and must not include forbidden data, cache, log, DB, or heavy artifact paths.

## Artifact Policy

Never commit raw data, canonical generated data, materialized factor values, materialized label values, local SQLite or DB files, heavy artifacts, generated reports, logs, caches, local model artifacts, credential material, or local environment files.

Permitted placeholders are limited to `.gitkeep` or `README.md` files where the campaign policy allows them. Commit-eligible phase handoffs for this campaign belong under `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/`.

## Documentation Map

Project-level orientation:

- `ACTIVE_CAMPAIGN.md`
- `PROJECT_STATUS.md`
- `AGENTS.md`
- `CLAUDE.md`

Architecture and workflow docs:

- `docs/PLAN.md`
- `docs/ARCHITECTURE.md`
- `docs/ONBOARDING.md`
- `docs/RESEARCHER_GUIDE.md`
- `docs/AI_AGENT_GUIDE.md`
- `docs/CLI_REFERENCE.md`
- `docs/EXAMPLE_WORKFLOWS.md`
- `docs/TROUBLESHOOTING.md`
- `docs/RESEARCH_INTERPRETATION_POLICY.md`
- `docs/LOCAL_FIRST_STACK.md`
- `docs/RESEARCH_WORKFLOW.md`
- `docs/DOMAIN_BOUNDARIES.md`
- `docs/NO_LOOKAHEAD_POLICY.md`
- `docs/BACKTEST_TIERS.md`
- `docs/ARTIFACT_POLICY.md`
- `docs/REPRODUCIBILITY_PRINCIPLES.md`
- `docs/CLI_COMMANDS_TARGET.md`

Governance docs:

- `docs/governance/README.md`
- `docs/governance/GOVERNANCE_OVERVIEW.md`
- `docs/governance/NAMING.md`
- `docs/governance/PRIMITIVES.md`
- `docs/governance/ALPHA_SPEC.md`
- `docs/governance/PRE_REGISTRATION.md`
- `docs/governance/FEATURE_REQUEST.md`
- `docs/governance/DUPLICATE_EXPOSURE.md`
- `docs/governance/LABEL_SPEC.md`
- `docs/governance/LABEL_LEAKAGE_GUARD.md`
- `docs/governance/STUDY_SPEC.md`
- `docs/governance/STUDY_BUDGET.md`
- `docs/governance/TRIAL_LEDGER.md`
- `docs/governance/EVIDENCE_BUNDLE.md`
- `docs/governance/REJECTED_IDEA_LEDGER.md`
- `docs/governance/PROMOTION_GATE.md`
- `docs/governance/REVIEWER_INDEPENDENCE.md`
- `docs/governance/GOVERNANCE_STATE_MACHINE.md`
- `docs/governance/NEGATIVE_CONTROLS.md`
- `docs/governance/CANARY_HARNESS.md`
- `docs/governance/REGISTRY_INTEGRATION.md`
- `docs/governance/CLI.md`

## Directory Layout

Commit-eligible policy and campaign files live under:

- `campaigns/`
- `specs/`
- `handoffs/`
- `reviews/`
- `docs/`
- `decisions/`
- `evals/`
- `configs/`
- `templates/`
- `src/alpha_system/cli/`
- `src/alpha_system/governance/`
- `tools/governance/`
- `tests/unit/governance/`
- `tests/integration/governance/`
- `tests/no_lookahead/`

Local data and generated artifact roots are present for structure only:

- `data/raw/`
- `data/canonical/`
- `data/factors/`
- `data/labels/`
- `data/cache/`
- `metadata/`
- `artifacts/`

## Useful Commands

The governance CLI command group is `alpha governance`. It includes `validate-spec`, `register-trial`, `build-evidence`, `review`, and `promote`; see `docs/governance/CLI.md` for arguments and gate behavior. The batch validation helper is `python tools/governance/validate_objects.py`. Durable governance modules now include `alpha_system.governance.ids`, `alpha_system.governance.serialization`, `alpha_system.governance.validation`, `alpha_system.governance.alpha_spec`, `alpha_system.governance.hypothesis_card`, `alpha_system.governance.feature_request`, `alpha_system.governance.duplicate_exposure`, `alpha_system.governance.label_spec`, `alpha_system.governance.label_leakage_guard`, `alpha_system.governance.study_spec`, `alpha_system.governance.trial_ledger`, `alpha_system.governance.evidence_bundle`, `alpha_system.governance.rejected_idea`, `alpha_system.governance.promotion`, `alpha_system.governance.promotion_gate`, `alpha_system.governance.reviewer_verdict`, `alpha_system.governance.registry`, `alpha_system.governance.canaries`, and `alpha_system.governance.canaries.harness`. Governance templates include `templates/governance/alpha_spec.template.yaml`, `templates/governance/hypothesis_card.template.yaml`, and `templates/governance/study_spec.template.yaml`. Local validation commands include:

```bash
python -c "import alpha_system.governance"
python -m pytest tests/unit/governance/test_canary_harness.py -q
python -m pytest tests/unit/governance/test_negative_controls.py -q
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
python -m pytest tests/no_lookahead/test_governance_canaries.py -q
python -m pytest tests/no_lookahead -q
python tools/governance/validate_objects.py --object AlphaSpec:tests/fixtures/governance/alpha_spec_valid.json
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```
