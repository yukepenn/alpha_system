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

# IVL-P02 — Executable Testability Gate + `alpha idea testability` (PASS / FAIL / DATA_GAP, pre-test)

---
campaign_id: ALPHA_IDEA_TO_VERDICT_LOOP_V0
phase_id: IVL-P02
lane: YELLOW
status: draft
dependencies: [IVL-P01]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Build the **pre-test gate**: `alpha idea testability <idea.yaml>` runs fail-closed checks and returns **PASS / FAIL / DATA_GAP BEFORE any real metric** so a degenerate or unready idea never spends a probe shot. Add the genuinely-missing **≥2-distinct-class precondition** to `research/conditional_probe.py` empty-set guards, reusing the label-runtime class-count logic. DATA_GAP is a pre-test verdict (shot not spent).

YELLOW: the gate decides whether real compute is spent and adds a fail-closed guard to a shared engine.

## Context

Verified live:

- **Bridge boundary (load-bearing):** `tests/unit/research/test_research_no_value_engine.py:16,49` rglobs `src/alpha_system/research/**` and **fails** on any `core.value_store` import (`:23`) and on the literal token `load_parquet_values` in the scorer (`:61`). Therefore the gate orchestrator MUST live in a NEW package **outside** `research/` — `src/alpha_system/research_lane/` (absent today). The ≥2-class guard added inside `research/conditional_probe.py` introduces no loader import, so the boundary stays green.
- **Class-count reuse:** `runtime/diagnostics/label/runtime.py:646 _distribution_summary` and `:693 _class_balance_summary` emit `class_count` (`:687`), `majority_class_count` (`:688`), `minority_class_count` (`:689`). The conditional probe currently has **only** empty-set guards (`conditional_probe.py:299-304`), no class-count check.
- **Reusable resolver (no materialization):** `runtime/input_resolver.py:395 FeatureLabelPackResolver`, `:433 resolve_feature_packs`, `:507 resolve_label_packs` resolve handles by pack-ref and validate dataset-version/partition/lifecycle without materializing values — usable to answer "features/labels materialized?" without computing a metric.
- **DATA_GAP discipline:** `research/first_light.py:195 build_first_light_data_gap_evidence` (status `INCONCLUSIVE`, issue_code `DATA_GAP`, no fabricated values) is the honest-gap pattern.

## Scope

1. **New `src/alpha_system/research_lane/testability_gate.py`** (outside `research/`) implementing the gate over an IdeaDraft + a `slice_spec`, returning a structured `PASS | FAIL | DATA_GAP` result per check, with **DATA_GAP as a pre-test verdict** (no probe run). Checks (all fail-closed; a missing precondition ⇒ DATA_GAP, not a fabricated pass):
   - features materialized (resolvable via `FeatureLabelPackResolver` without materializing);
   - labels / path-labels exist;
   - **path-label ≥2-distinct-class non-degeneracy** (reusing the class-count logic);
   - N_eff / MDE plausible;
   - dedup known (the `duplicate_exposure` declaration is present);
   - no-lookahead / `available_ts` satisfiable;
   - surrogate-FDR requirement known (the probe will require `ZERO_PASS_MET`).
2. **Add the ≥2-distinct-class precondition** to `research/conditional_probe.py` as a new fail-closed guard alongside the existing empty-set guards (`:299-304`): when the conditioned path-label set has `class_count < 2`, raise `ConditionalProbeError` with a clear message — reusing the class-count computation pattern from `_distribution_summary`/`_class_balance_summary` (re-implemented loader-free inside `research_lane/` or imported only from the diagnostics package, never a value loader). This is the only edit to `conditional_probe.py` and must be **additive** (no change to existing pass/fail semantics).
3. **`alpha idea testability` subcommand** added to `cli/idea.py` (mirroring the `validate` subcommand), delegating to the gate and printing the per-check PASS/FAIL/DATA_GAP result; wraps domain errors → exit 2.
4. **Tests:** the 5/7 checks each independently produce PASS / FAIL / DATA_GAP; DATA_GAP is returned **before** any probe call (assert the probe engine is not invoked on a degenerate slice); the new `conditional_probe.py` ≥2-class guard rejects a single-class conditioned set with `ConditionalProbeError`; the boundary test `test_research_no_value_engine.py` still passes (no loader import introduced under `research/`).

## Non-Goals

- Computing or recording any real IC / return / metric value (the gate is pre-test; it loads no values for scoring).
- Putting the gate orchestrator under `research/` (boundary test forbids loader imports there).
- Materializing features/labels, calling the scaleout driver, or sourcing paid data.
- Changing existing `conditional_probe.py` pass/fail semantics beyond adding the additive ≥2-class guard.
- Any promotion or downstream-module charter.

## Expected Files (illustrative)

- `src/alpha_system/research_lane/__init__.py`, `src/alpha_system/research_lane/testability_gate.py` — new.
- `src/alpha_system/research/conditional_probe.py` — edit (additive ≥2-class guard only).
- `src/alpha_system/cli/idea.py` — edit (add `testability` subcommand).
- `tests/unit/research_lane/test_testability_gate.py`, `tests/unit/research/test_conditional_probe_class_guard.py`, `tests/unit/cli/test_idea_cli.py` — new/extend.
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P02.md`, `reviews/.../IVL-P02/**`.

USED unchanged: `runtime/input_resolver.py`, `runtime/diagnostics/label/runtime.py` (read/import only), `research/first_light.py` (DATA_GAP pattern reference).

## Interfaces / Contracts

- **Gate result:** a structured object per check `{check_id, status ∈ {PASS, FAIL, DATA_GAP}, detail}` + an overall verdict; DATA_GAP at any precondition ⇒ overall DATA_GAP (pre-test, shot not spent).
- **≥2-class guard:** `conditional_probe.py` raises `ConditionalProbeError` when the conditioned path-label set has `class_count < 2` (computed via the reused class-count logic), additive to the existing empty-set guards at `:299-304`.
- **No-loader-in-research boundary:** the gate orchestrator imports `FeatureLabelPackResolver` (existence/lifecycle checks) and class-count logic from `runtime/**`, never `core.value_store` from under `research/`. `research_lane/` is the new home.

## Forbidden Changes

- Placing the gate orchestrator under `research/`; importing `core.value_store`/`load_parquet_values` into any `research/` module; introducing a research→sim bridge or second-PnL truth.
- Changing existing `conditional_probe.py` semantics beyond the additive ≥2-class guard; editing `strategies/templates.py` or the value engine.
- Materializing features/labels, calling the scaleout driver, computing a scoring metric in the gate, or sourcing paid data; un-deferring fomc/cpi.
- Adding a runtime dependency (`numpy`/`pandas`/`polars` stay unimportable); fabricating values on DATA_GAP.
- `git add .` / `git add -A`, force push, auto-merge, deployment, PR self-approval, broker/live calls.
- Weakening/skipping existing tests/canaries or adding visible test-only branches; any alpha/tradability/profitability claim.

## Validation

```bash
# 1) Narrowest meaningful tests first.
python -m pytest tests -k "testability or conditional_probe or class_guard or idea" -q
# 2) Boundary test stays green (no loader import under research/).
python -m pytest tests/unit/research/test_research_no_value_engine.py -q
# 3) CLI testability returns PASS/FAIL/DATA_GAP.
python -m alpha_system.cli.main idea testability research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml
# 4) No research->sim bridge.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"
# 5) Smoke + canaries + no new dependency.
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"
# 6) conditional_probe edit is additive only (review diff).
git diff -- src/alpha_system/research/conditional_probe.py
# 7) Run-artifact discipline.
git ls-files runs
```

Broaden to `python tools/verify.py --all` if shared probe/diagnostics behavior appears affected; clean shell, `FRONTIER_*` unset. Record skipped checks + reasons.

## Artifact Policy

`runs/**` local-only, never staged. Commit-eligible handoff `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P02.md`; review under `reviews/.../IVL-P02/**`. Never commit `runs/**`, parquet/arrow/feather/dbn/zst/sqlite/db, `data/raw/**`, `data/canonical/**`, secrets, `**/*.key`. `git ls-files runs` empty.

### Allowed Paths (commit-eligible — explicit staging only)

- `src/alpha_system/research_lane/**`
- `src/alpha_system/research/conditional_probe.py`
- `src/alpha_system/cli/idea.py`
- `tests/unit/research_lane/test_testability_gate.py`
- `tests/unit/research/test_conditional_probe_class_guard.py`
- `tests/unit/cli/test_idea_cli.py`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P02.md`
- `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P02/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit/resume only.

## Allowed Test Paths

- `tests/unit/research_lane/**`, `tests/unit/research/test_conditional_probe_class_guard.py`, `tests/unit/cli/test_idea_cli.py`. Do not weaken/skip existing tests (including `test_research_no_value_engine.py`) or add visible test-only branches.

## Done Criteria

- `research_lane/testability_gate.py` (outside `research/`) returns PASS / FAIL / **DATA_GAP** across the 5 checks (features materialized; labels/path-labels exist; path-label ≥2-class; N_eff/MDE plausible; dedup known; no-lookahead/`available_ts`; surrogate-FDR requirement known), with DATA_GAP as a pre-test verdict (probe not run, asserted by test).
- The additive ≥2-distinct-class guard in `conditional_probe.py` rejects a single-class conditioned set with `ConditionalProbeError`, reusing the label-runtime class-count logic; existing pass/fail semantics unchanged (diff proves additive).
- `alpha idea testability` subcommand registered and delegates to the gate.
- `test_research_no_value_engine.py` still passes (no loader import under `research/`); no research→sim grep hit; `numpy`/`pandas`/`polars` unimportable; smoke + canaries pass; `git ls-files runs` empty; explicit staging; no `forbidden_paths` edits.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P02.md`: scope delivered; exact validation commands + results; skipped checks + reasons; files changed by path; explicit confirmation that (a) the gate lives in `research_lane/` not `research/` and imports no value loader under `research/` (boundary test green), (b) the ≥2-class guard is additive (diff shown) and reuses the label-runtime class-count logic, (c) DATA_GAP is returned pre-test (probe not invoked, asserted), (d) no metric/materialization/paid-data, (e) `git ls-files runs` empty, explicit staging, no `forbidden_paths` edits. Run-local handoff stays local-only.

## Review Requirements

YELLOW fresh Claude Opus review under `reviews/.../IVL-P02/**`. Reviewer adversarially confirms: the gate orchestrator is outside `research/` and introduces no loader import there (boundary test genuinely green, not skipped); the `conditional_probe.py` change is strictly additive (the ≥2-class guard) with unchanged existing semantics; DATA_GAP is a real pre-test verdict (the probe is not run on a degenerate slice — assert by test, not prose); the gate computes no scoring metric and materializes nothing; class-count reuse is faithful to `_distribution_summary`/`_class_balance_summary`; no paid data; research-only language; smoke + canaries pass; `git ls-files runs` empty; explicit staging.

## Auto-Merge / Review Policy

No PR creation, auto-merge, or deployment authorized. Merge gating is the Ralph driver's responsibility under YELLOW lane policy (block on critical / test-tamper / boundary violation) + human authorization.

## Repair-or-Rollback

- **In-scope repair only:** fix the gate, the additive guard, the CLI subcommand, or tests within Allowed Paths; no scope expansion.
- **Rollback:** the new package + additive guard + CLI subcommand are reversible with no migration/data change; reverting the `conditional_probe.py` guard restores prior semantics exactly.
- **STOP / escalate:** any pressure to place the gate under `research/`, import a value loader into `research/`, compute a scoring metric/materialize in the gate, weaken `conditional_probe.py` semantics or the boundary test, add a dependency or paid data, or commit a `runs/`/data/secret artifact — surface to the user.

---
---

---

## ERRATA (coordinator review fix — `alpha idea gate` lives in THIS phase)
IVL-P02 OWNS the `alpha idea gate <idea.yaml> [--slice <id>]` CLI subcommand (the executable testability gate IS the `gate` command). The IVL-P06 dogfood invokes it, and the GOAL/ACCEPTANCE/RUNBOOK references to `alpha idea gate` resolve to this phase.

