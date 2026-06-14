# IVL-P00 Executor Handoff

Campaign: `ALPHA_IDEA_TO_VERDICT_LOOP_V0`
Phase: `IVL-P00`
Executor: Codex
Date: 2026-06-14

## Scope Delivered

- Authored `decisions/ADR-IVL-0001-role-unification.md`.
- Authored `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`.
- Added the missing standalone generated-spec path
  `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00-role-unification-adr.md`.
- Verified the role contract against current source before writing:
  - `study_kind` is absent from `src/alpha_system/governance/`.
  - `HypothesisCard`, `AlphaSpec`, `MechanismCard`, `SetupSpec`, and
    `StudySpec` are frozen/slotted governance dataclasses with closed-schema
    validation.
  - `AlphaSpec` requires a `hypothesis_id`, so the ADR includes HypothesisCard
    as the required parent while keeping AlphaSpec as the front-door kill-trunk.
  - `StudySpec` is keyed by `alpha_spec_id` and `label_spec_id`, not by
    MechanismCard or SetupSpec.
  - `RejectedIdeaRecord` accepts only AlphaSpec or HypothesisCard IDs, so REJECT
    memory must write via an existing AlphaSpec/HypothesisCard ID and IVL-P05
    must fail closed if the AlphaSpec ID is missing.
- Recorded the REUSE-MAP symbols by name after verifying each exists in current
  code:
  `validate_mechanism_card`, `create_mechanism_card`,
  `validate_setup_spec`, `create_setup_spec`, `validate_alpha_spec`,
  `generate_mechanism_id`, `create_rejected_idea_record`,
  `validate_requeued_verdict_record`, `create_promotion_decision`,
  `reject_exploratory_promotion_artifact`,
  `reject_exploratory_promotion_artifacts`, `_class_balance_summary`,
  `_distribution_summary`, `build_factor_diagnostics_run`,
  `evaluate_setup_conditional_probe`, `load_parquet_values`,
  `FeatureLabelPackResolver`, `VerdictReasonCode`, and
  `validate_verdict_reason_code`.
- Marked the eight Track-A JSON cards as legacy doc-convention records,
  migrate-then-retire, read-only in V0.
- Preserved research-only language and made no result, profitability,
  tradability, or production-readiness claim.

## Files Changed

- `decisions/ADR-IVL-0001-role-unification.md`
- `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`
- `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00-role-unification-adr.md`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`

No `src/**`, `tests/**`, legacy Track-A card JSON, stopped-campaign artifact,
data, DB, cache, log, review, verdict, PR, merge, or `runs/**` artifact was
created or modified by this executor pass.

## Source-Grounded Discrepancy

The generated IVL-P00 prompt expected this Track-A partition:

- `existing_substrate x1`
- `derivable_from_exchange_calendar x5`
- `needs_paid_data x2`

The current JSON files actually declare:

- `existing_substrate x2`: `day_of_week_effect`, `open_close_auction_flow`
- `derivable_from_exchange_calendar x4`: `roll_week_flow`,
  `month_end_flow`, `month_end_rebalance_flow`, `opex_pinning`
- `needs_paid_data x2`: `fomc_drift`, `cpi_surprise_reversion`

The mismatch is `open_close_auction_flow`, whose current
`data_dependency.class` is `existing_substrate`. The ADR/schema map document the
current-file truth and note that `day_of_week_effect` remains the selected live
exemplar. Later phases should reconcile this deliberately rather than silently
changing a legacy card or repeating the stale count as fact.

## Validation

Passed:

- `test -f decisions/ADR-IVL-0001-role-unification.md`
- `test -f docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`
- `test -f specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00-role-unification-adr.md`
- `test -f campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/GOAL.md`
- `test -f campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/campaign.yaml`
- `python -c "import yaml; yaml.safe_load(open('campaigns/ALPHA_IDEA_TO_VERDICT_LOOP_V0/campaign.yaml'))"`
- `grep -q "ALPHA_IDEA_TO_VERDICT_LOOP_V0" ACTIVE_CAMPAIGN.md`
- `git ls-files runs` passed and printed no tracked `runs/` paths.
- `just frontier-plan ALPHA_IDEA_TO_VERDICT_LOOP_V0` passed:
  7 waves, IVL-P00 through IVL-P06, max width 1, parallelizable false.
- `python tools/verify.py --smoke` passed.
- `python tools/hooks/canary_runner.py` passed; all Frontier canaries passed.
- `python tools/verify.py --artifacts` passed.
- `grep -nP "[^\\x00-\\x7F]" decisions/ADR-IVL-0001-role-unification.md docs/IDEA_TO_VERDICT_SCHEMA_MAP.md specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00-role-unification-adr.md`
  returned no matches.
- After this handoff was written, `test -f handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`
  passed, `grep -nP "[^\\x00-\\x7F]" handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`
  returned no matches, and `python tools/verify.py --artifacts` passed again.

Source verification commands also run:

- `rg -n "study_kind" src/alpha_system/governance` returned no matches.
- `rg -n` symbol checks confirmed the REUSE-MAP functions/classes listed above.
- `jq` over `research/differentiated_substrate_v1/cards/*.json` confirmed the
  Track-A `data_dependency.class` partition recorded above.

Skipped by explicit executor prompt:

- `git status --porcelain` was not run.
- `git diff --stat` was not run.
- `git diff --cached --name-only` was not run.
- No `git add`, `git commit`, `git push`, PR creation, merge, or phase PASS
  marking was performed.
- No reviewer was called; no `review.md` or `verdict.json` was created.
- `README.md` was not updated because the generated README snapshot policy says
  to apply the "IVL-P00 complete, 1/7" snapshot after merge, while this executor
  pass is pre-review/pre-merge and was explicitly instructed not to mark the
  phase PASS.

## Run Artifact Note

The prompt-supplied run artifact directory
`runs/2026-06-14T200245Z_ALPHA_IDEA_TO_VERDICT_LOOP_V0/phases/IVL-P00` was not
present in this worktree, and there is no accessible `runs/` directory here. No
run-local handoff, review, verdict, checks file, or repair artifact was written.
The commit-eligible handoff is this file.
