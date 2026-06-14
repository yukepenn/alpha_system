# ALPHA_IDEA_TO_VERDICT_LOOP_V0 — Phase Specs (IVL-P00 .. IVL-P06)

> Shape source: these specs follow the live phase-spec shape used by `specs/DIFFERENTIATED_KILLSHOT_V1/DK-P00..DK-P05` — YAML front-matter (`campaign_id, phase_id, lane, status, dependencies, executor, reviewer, verifier`) then the `tools/frontier/spec_schema.py:REQUIRED_SECTIONS` (Purpose, Context, Scope, Non-Goals, Expected Files, Forbidden Changes, Validation, Done Criteria, Handoff Requirements, Review Requirements) plus the DK convention sections (Interfaces/Contracts, Allowed Paths, Allowed Test Paths, Artifact Policy, Auto-Merge/Review Policy, Repair-or-Rollback). `REQUIRED_SECTIONS` is a review convention, not an automated gate; the enforced gates are `require_campaign_files` (6-file bundle), `load_campaign_yaml` + `parse_campaign_phases` (`just frontier-plan ALPHA_IDEA_TO_VERDICT_LOOP_V0`), and a fresh mock run.
>
> Research-only language throughout: no alpha / profitability / tradability / production claims. Lanes GREEN/YELLOW only — no RED. Allowed verdict outputs: REJECT / DATA_GAP / INCONCLUSIVE / WATCH / CANDIDATE. `runs/**` is local-only and never staged.
>
> **Shared `forbidden_paths` (YAML anchor in `campaign.yaml`):** `src/alpha_system/execution/**`, `broker/**`, `live/**`, `portfolio/**`, `management/**`, `backtest/**`, `l2/**`, `agent_factory/**`, `src/alpha_system/core/value_store.py` (import allowed, EDITS forbidden), `src/alpha_system/strategies/templates.py`, `src/alpha_system/research/conditional_probe.py` semantics (additive guard only — see IVL-P02), `src/alpha_system/research/track_a_scorer.py`, `tools/differentiated_killshot_v1/**`, `research/futures_substrate_scaleout_v1/**`, `research/futures_core_alpha_pilot_v1/**`, all `data/**`, any `*.sqlite`/`*.db`/`*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`.
> **Shared commit-eligible globs (every phase):** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>.md`, `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>/**`. `campaign.yaml` `allowed_paths` MAY list `runs/**`; the spec's Allowed Paths MUST NOT (local-only; `git ls-files runs` stays empty).

---
---

---

# IVL-P05 — Memory Wiring + `alpha idea run` End-to-End

---
campaign_id: ALPHA_IDEA_TO_VERDICT_LOOP_V0
phase_id: IVL-P05
lane: YELLOW
status: draft
dependencies: [IVL-P04]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Close the loop: `alpha idea run <idea.yaml>` chains validate → testability → fast_probe → report → **memory**, routing the verdict to memory: REJECT → rejected-idea graveyard; DATA_GAP → requeue; WATCH/CANDIDATE → reviewer-gated promotion (requires `reviewer_verdict_id`). FactorLibrary stays survivor-only; an exploratory readout is never auto-promoted (`reject_exploratory_promotion_artifact` fails closed).

YELLOW: this wires the governed memory + the never-auto-promote rail.

## Context

Verified live:

- **Memory factories (REUSED):** `governance/rejected_idea.py:404 create_rejected_idea_record(*, alpha_spec_id_or_hypothesis_id, reason_category, evidence_references, duplicate_links, leakage_cost_weakness_notes, reviewer, created_at)` — graveyard key is the dual field, so a REJECT requires the always-minted `alpha_spec_id` (IVL-P01); `governance/requeue.py:269 validate_requeued_verdict_record(...)` — DATA_GAP requeue; `governance/promotion.py:217 create_promotion_decision(*, alpha_spec_id, evidence_bundle_id, trial_ledger_refs, previous_state, next_state, decision, rationale, reviewer_verdict_id, warnings, timestamp, reason_code=None)` — **`reviewer_verdict_id` is required** (no auto-promote).
- **Never-auto-promote rail (REUSED):** `governance/promotion.py:386 reject_exploratory_promotion_artifact` (+ `:410 reject_exploratory_promotion_artifacts`) fail closed on any `EXPLORATORY`-stamped artifact reaching a trusted/promotion input; the `forbidden_exploratory_promotion` canary asserts it. The IVL-P03 fast readout is `promotion_eligible=False` and `EXPLORATORY`-stamped.
- **Graveyard precondition (from IVL-P00/P01):** because the front door always mints an AlphaSpec, `REJECT → graveyard` writes via `alpha_spec_id_or_hypothesis_id`; the router must assert the AlphaSpec ID exists before any graveyard write (fail closed otherwise).
- **Placement:** the memory router lives under `research_lane/`; `alpha idea run` is the orchestration entrypoint in `cli/idea.py`.

## Scope

1. **New `src/alpha_system/research_lane/memory_router.py`**: a router `route_verdict_to_memory(verdict, idea_draft, readout, ...)` mapping the verdict to a memory action:
   - **REJECT** → `create_rejected_idea_record(alpha_spec_id_or_hypothesis_id=<minted AlphaSpec id>, reason_category=..., ...)`; assert the AlphaSpec id is present (fail closed otherwise — no graveyard write without it).
   - **DATA_GAP** → a requeue record validated via `validate_requeued_verdict_record(...)` (evidence-accrual requeue; the shot was not spent).
   - **WATCH / CANDIDATE** → `create_promotion_decision(... reviewer_verdict_id=<required> ...)` — never created without a reviewer verdict id; the router does not mint a reviewer verdict itself (reviewer-gated).
   - In all cases, before any trusted/promotion input is touched, call `reject_exploratory_promotion_artifact(readout)` and confirm it refuses the EXPLORATORY artifact (the readout can never become promotion evidence). FactorLibrary is never written (survivor-only).
2. **`alpha idea run` subcommand** in `cli/idea.py` chaining validate → testability → fast_probe → render report → route to memory; honest DATA_GAP short-circuits to requeue without spending a probe; `promotion_eligible=False` throughout.
3. **Tests:** REJECT writes a graveyard record keyed by the AlphaSpec id (and fails closed if the id is absent); DATA_GAP writes a valid requeue record (no probe spent); WATCH/CANDIDATE requires a `reviewer_verdict_id` (fails closed without it) and never auto-promotes; `reject_exploratory_promotion_artifact` refuses the readout (and the `forbidden_exploratory_promotion` canary stays green); FactorLibrary is never written; `alpha idea run` end-to-end on a fixture produces a report + a memory record with `promotion_eligible=false`.

## Non-Goals

- Auto-promoting any verdict; minting a reviewer verdict id inside the router; writing a FactorLibrary/AlphaBook entry.
- Letting an EXPLORATORY readout reach a trusted/promotion input; flipping `promotion_eligible` to true.
- Editing the memory factories' semantics, the engines, the single-factor template, or the value engine.
- Materializing/recomputing data, calling the scaleout driver, or sourcing paid data; any downstream-module charter.

## Expected Files (illustrative)

- `src/alpha_system/research_lane/memory_router.py` — new.
- `src/alpha_system/cli/idea.py` — edit (add `run` subcommand chaining the loop).
- `tests/unit/research_lane/test_memory_router.py`, `tests/unit/cli/test_idea_cli.py` — new/extend.
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05.md`, `reviews/.../IVL-P05/**`.

USED unchanged: `governance/rejected_idea.py`, `governance/requeue.py`, `governance/promotion.py` (called, not edited), the IVL-P02/P03/P04 components.

## Interfaces / Contracts

- **REJECT:** `create_rejected_idea_record(alpha_spec_id_or_hypothesis_id=<AlphaSpec id>, ...)`; precondition: AlphaSpec id present (fail closed).
- **DATA_GAP:** `validate_requeued_verdict_record(payload)` with a valid `requeue_reason` (evidence-accrual trigger); the shot was not spent.
- **WATCH/CANDIDATE:** `create_promotion_decision(... reviewer_verdict_id=<required>, reason_code=<optional VerdictReasonCode> ...)`; never created without `reviewer_verdict_id`.
- **Never-auto-promote:** `reject_exploratory_promotion_artifact(readout)` must refuse the EXPLORATORY readout; the `forbidden_exploratory_promotion` canary stays green and fails if the guard is bypassed. FactorLibrary is never written.

## Forbidden Changes

- Auto-promoting; minting a reviewer verdict id in the router; writing a FactorLibrary/AlphaBook entry; flipping `promotion_eligible` to true.
- Letting an EXPLORATORY readout reach a trusted/promotion input; editing the memory factories' semantics, the engines, the single-factor template, or the value engine.
- Materializing/recomputing data, calling the scaleout driver, sourcing paid data, un-deferring fomc/cpi.
- Adding a runtime dependency (`numpy`/`pandas`/`polars` unimportable beyond IVL-P03's optional polars at probe time); committing data/secrets.
- `git add .` / `git add -A`, force push, auto-merge, deployment, PR self-approval, broker/live calls; weakening/skipping existing tests/canaries (esp. `forbidden_exploratory_promotion`); any alpha/tradability/profitability claim.

## Validation

```bash
# 1) Narrowest meaningful tests first.
python -m pytest tests -k "memory_router or idea_run or idea" -q
# 2) End-to-end run on a fixture idea (DATA_GAP path short-circuits to requeue).
python -m alpha_system.cli.main idea run research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml
# 3) Smoke + canaries (forbidden_exploratory_promotion MUST stay green).
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
# 4) No research->sim bridge; no new dependency.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"
python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"
# 5) Memory factories byte-unchanged (called, not edited).
git diff -- src/alpha_system/governance/rejected_idea.py src/alpha_system/governance/requeue.py src/alpha_system/governance/promotion.py
# 6) Run-artifact discipline.
git ls-files runs
```

Broaden to `python tools/verify.py --all` if shared governance behavior appears affected; clean shell, `FRONTIER_*` unset. Record skipped checks + reasons.

## Artifact Policy

`runs/**` local-only, never staged. Commit-eligible handoff `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05.md`; review under `reviews/.../IVL-P05/**`. Memory records written by the loop are value-free governance objects (ids/counts/reasons only). Never commit `runs/**`, parquet/arrow/feather/dbn/zst/sqlite/db, `data/raw/**`, `data/canonical/**`, secrets, `**/*.key`. `git ls-files runs` empty.

### Allowed Paths (commit-eligible — explicit staging only)

- `src/alpha_system/research_lane/memory_router.py`
- `src/alpha_system/cli/idea.py`
- `tests/unit/research_lane/test_memory_router.py`
- `tests/unit/cli/test_idea_cli.py`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05.md`
- `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit/resume only.

## Allowed Test Paths

- `tests/unit/research_lane/test_memory_router.py`, `tests/unit/cli/test_idea_cli.py`. Do not weaken/skip existing tests/canaries (esp. `forbidden_exploratory_promotion`) or add visible test-only branches.

## Done Criteria

- `alpha idea run` chains validate → testability → fast_probe → report → memory; REJECT → graveyard (keyed by the minted AlphaSpec id; fails closed if absent); DATA_GAP → requeue (shot not spent); WATCH/CANDIDATE → `create_promotion_decision` requiring `reviewer_verdict_id` (never auto).
- `reject_exploratory_promotion_artifact` refuses the EXPLORATORY readout and the `forbidden_exploratory_promotion` canary stays green; FactorLibrary is never written; `promotion_eligible=false` throughout.
- Memory factories byte-unchanged (called, not edited); no research→sim grep hit; `numpy`/`pandas`/`polars` unimportable; smoke + canaries pass; `git ls-files runs` empty; explicit staging; no `forbidden_paths` edits.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05.md`: scope delivered; exact validation commands + results; skipped checks + reasons; files changed by path; explicit confirmation that (a) REJECT writes a graveyard record keyed by the AlphaSpec id and fails closed without it, (b) DATA_GAP requeues without spending a probe, (c) WATCH/CANDIDATE require a `reviewer_verdict_id` and never auto-promote, (d) `reject_exploratory_promotion_artifact` refuses the readout (canary green) and FactorLibrary is never written, (e) memory factories byte-unchanged, no paid data, `git ls-files runs` empty, explicit staging, no `forbidden_paths` edits. Run-local handoff stays local-only.

## Review Requirements

YELLOW fresh Claude Opus review under `reviews/.../IVL-P05/**`. Reviewer adversarially confirms: REJECT is keyed by the always-minted AlphaSpec id (graveyard precondition satisfied; fails closed if absent); DATA_GAP requeues without a probe; WATCH/CANDIDATE genuinely require a `reviewer_verdict_id` (the router does not mint one) and never auto-promote; the EXPLORATORY readout is refused by `reject_exploratory_promotion_artifact` and the `forbidden_exploratory_promotion` canary is green (not bypassed); FactorLibrary stays survivor-only (never written); memory factories are byte-unchanged; no paid data; research-only language; smoke + canaries pass; `git ls-files runs` empty; explicit staging.

## Auto-Merge / Review Policy

No PR creation, auto-merge, or deployment authorized. Merge gating is the Ralph driver's responsibility under YELLOW lane policy (block on critical / test-tamper / EXPLORATORY-leak) + human authorization.

## Repair-or-Rollback

- **In-scope repair only:** fix the memory router / `run` subcommand / tests within Allowed Paths; no scope expansion.
- **Rollback:** additive router + CLI subcommand; revert to restore prior state with no migration/data change (memory factories untouched).
- **STOP / escalate:** any pressure to auto-promote, mint a reviewer verdict id in the router, write a FactorLibrary entry, let an EXPLORATORY artifact reach promotion, flip `promotion_eligible`, edit a memory factory's semantics, add a dependency or paid data, or commit a `runs/`/data/secret artifact — surface to the user.

---
---
