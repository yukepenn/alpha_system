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

# IVL-P03 — Fast Exploratory Lane Bridge: one generic `fast_probe(card, setup, slice_spec)`

---
campaign_id: ALPHA_IDEA_TO_VERDICT_LOOP_V0
phase_id: IVL-P03
lane: YELLOW
status: draft
dependencies: [IVL-P02]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Build the missing slice-bounded BRIDGE: ONE generic `fast_probe(card, setup, slice_spec)` (outside `research/`) that loads a bounded **existing** materialized slice via `core.value_store.load_parquet_values` + `FeatureLabelPackResolver`, maps rows to the governance row schema, and feeds the unchanged loader-free research primitives in-memory (`build_factor_diagnostics_run` for `main_effect`; `evaluate_setup_conditional_probe` for `context_not_equal_trigger`). `promotion_eligible=False`; no materialization, no scaleout-driver call, no second value loader. Generalize `first_light.py` and fold the hardcoded `dk_p04_track_b_probe.py` loader into `slice_spec` inputs — **migrate-then-retire** (retire the bespoke bridges only later, once subsumed with tests; IVL-P06 is the subsumption proof).

YELLOW: this is the load-bearing bridge that decides what real compute runs.

## Context

Verified live:

- **Boundary forces placement:** `tests/unit/research/test_research_no_value_engine.py` fails on any `core.value_store` import under `research/**` and on the `load_parquet_values` token in the scorer. ⇒ `fast_probe` MUST live under the NEW `src/alpha_system/research_lane/` package (started in IVL-P02), importing `load_parquet_values` there and injecting in-memory rows into the research engines.
- **Loader-agnostic engines (USED byte-unchanged):** `runtime/diagnostics/factor/runtime.py:240 build_factor_diagnostics_run(observations: Iterable[Mapping[str,Any]])` (loader-free; delegates to `research.ic`/`research.buckets`); `research/conditional_probe.py:313 evaluate_setup_conditional_probe(...)` — surrogate `ZERO_PASS_MET` (`:348 _require_zero_pass_surrogate_gate`) and family-budget `RESPECTED` (`:357`) are HARD preconditions inside `evaluate` (raise `ConditionalProbeError` otherwise); `promotion_eligible=False` is hardcoded (`:398`); plus the IVL-P02 ≥2-class guard.
- **Row loaders (USED):** `core/value_store.py:116 load_parquet_values(path) -> list[dict]` (requires `polars` via `require_dependency` `:119` — fail closed if absent); `runtime/input_resolver.py:395 FeatureLabelPackResolver` / `:433 resolve_feature_packs` / `:507 resolve_label_packs` (governed pack-ref → handle, lazy, no materialization).
- **Bespoke bridges to generalize (migrate-then-retire, do NOT edit/delete now):** `tools/differentiated_killshot_v1/dk_p04_track_b_probe.py` (STOPPED, do-not-edit) hardcodes `CONTEXT_REL_PATH`/`TRIGGER_REL_PATH`/`PATH_LABEL_REL_PATH` (ES_2024), `NORMALIZED_INSTRUMENT_ID='ES'`, `PATH_LABEL_VERSIONS`, `CREATED_AT`; `research/first_light.py:38-49` is frozen to one SSRL idea via `FIRST_LIGHT_*` constants + manifest paths and has the honest DATA_GAP fallback (`:195`). `fast_probe` parameterizes these as `slice_spec` inputs (data root + pack-refs/rel-paths + instrument/session + label-version map). `first_light.py` itself stays under `research/` and remains row-injected (no loader) — it is generalized in behavior by the new bridge, not edited here.
- **DATA_GAP discipline:** `research/first_light.py:195 build_first_light_data_gap_evidence` — when rows do not resolve (e.g. `polars` absent / `ALPHA_DATA_ROOT` unset), return an honest DATA_GAP, never fabricated values.

## Scope

1. **New `src/alpha_system/research_lane/slice_spec.py`**: a validated `SliceSpec` value object parameterizing the bounded existing slice (data root, feature/label pack-refs or rel-paths, normalized instrument/session ids, path-label version map, optional `created_at`/seeds) — de-hardcoding the constants baked into `dk_p04_track_b_probe.py` and `first_light.py`.
2. **New `src/alpha_system/research_lane/fast_probe.py`**: one generic `fast_probe(card, setup, slice_spec)` that:
   - resolves the bounded slice via `FeatureLabelPackResolver` (governance/lifecycle validation), loads rows via `load_parquet_values`, maps the value-store schema → governance row schema (`factor_id/factor_version/instrument_id/event_ts/session_id/data_version/bar_index/value`), exactly the mapping `dk_p04_track_b_probe.py` performs;
   - routes by `study_kind`: `main_effect → build_factor_diagnostics_run`; `context_not_equal_trigger → evaluate_setup_conditional_probe` (which enforces surrogate `ZERO_PASS_MET` + family-budget `RESPECTED` + the ≥2-class guard internally — the bridge must satisfy, never bypass, these; it runs the existing label-shuffle surrogate to obtain the gate inputs);
   - emits a readout with `promotion_eligible=False`; performs **no** materialization, **no** scaleout-driver call, and uses **no** second value loader;
   - **fails closed to an honest DATA_GAP** (the `build_first_light_data_gap_evidence` shape) when `polars` is absent, `ALPHA_DATA_ROOT` is unset, or rows do not resolve — never fabricates values.
3. **Tests:** the bridge maps value-store rows to governance rows and feeds the engines in-memory; `main_effect` and `context_not_equal_trigger` both route correctly; the surrogate `ZERO_PASS_MET` + family-budget `RESPECTED` + ≥2-class preconditions are satisfied (and a single-class / non-zero-pass / budget-exceeded slice raises, not bypassed); `promotion_eligible=False` on every readout; the DATA_GAP fallback returns `status=INCONCLUSIVE`/`issue_code=DATA_GAP` with no fabricated values when rows do not resolve; `test_research_no_value_engine.py` still passes (the loader import lives in `research_lane/`, not `research/`).

## Non-Goals

- Editing `research/conditional_probe.py` semantics, `build_factor_diagnostics_run`, `first_light.py`, the single-factor template, or the value engine.
- Editing or deleting the bespoke bridges (`tools/differentiated_killshot_v1/dk_p04_track_b_probe.py` is STOPPED; `first_light.py` stays) — retirement is a later, post-subsumption, test-gated step, not V0.
- Calling the scaleout driver, materializing/recomputing any feature/label, writing a registry entry, or sourcing paid data.
- Introducing a second value loader, a research→sim bridge, or any geometry/horizon sweep.
- Any promotion, FactorLibrary entry, or downstream-module charter.

## Expected Files (illustrative)

- `src/alpha_system/research_lane/slice_spec.py`, `src/alpha_system/research_lane/fast_probe.py` — new.
- `tests/unit/research_lane/test_fast_probe.py`, `tests/unit/research_lane/test_slice_spec.py` — new.
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03.md`, `reviews/.../IVL-P03/**`.

USED byte-unchanged: `core/value_store.py` (imported, not edited), `runtime/input_resolver.py`, `runtime/diagnostics/factor/runtime.py`, `research/conditional_probe.py`, `research/first_light.py`.

## Interfaces / Contracts

- **`fast_probe(card, setup, slice_spec)`** lives in `research_lane/`; imports `load_parquet_values` + `FeatureLabelPackResolver`; injects in-memory `list[dict]` rows into the engines; returns a readout (or an honest DATA_GAP).
- **Engine preconditions are hard and internal:** for `context_not_equal_trigger`, `evaluate_setup_conditional_probe` requires surrogate `ZERO_PASS_MET` (`run_count>0`, `gate_pass_count=0`, `error_count=0`) + family-budget `RESPECTED` + (IVL-P02) `class_count≥2`; the bridge satisfies them and never bypasses; `promotion_eligible=False` is hardcoded in the readout.
- **Row schema map:** value-store record → `{factor_id, factor_version, instrument_id, event_ts, session_id, data_version, bar_index, value}`, mirroring the `dk_p04_track_b_probe.py` mapping, parameterized by `slice_spec`.
- **DATA_GAP contract:** `polars` absent / `ALPHA_DATA_ROOT` unset / rows unresolved ⇒ `build_first_light_data_gap_evidence` shape (`status=INCONCLUSIVE`, `issue_code=DATA_GAP`, `surrogate_fdr_gate=BLOCKED`, `power.n_eff=0`), no fabricated values.

## Forbidden Changes

- Placing `fast_probe`/`slice_spec` under `research/`; importing `core.value_store`/`load_parquet_values` into any `research/` module; a second value loader or research→sim bridge.
- Editing the engines, `first_light.py`, the bespoke bridges, the single-factor template, or the value engine; calling the scaleout driver; materializing/recomputing/registry-writing.
- Flipping `promotion_eligible` to true; emitting a PromotionDecision/FactorLibrary entry.
- Fabricating values when rows do not resolve; bypassing the surrogate/budget/≥2-class preconditions.
- Adding a runtime dependency beyond the already-optional `polars` invoked via `require_dependency` (no `numpy`/`pandas` import); sourcing paid data; un-deferring fomc/cpi.
- `git add .` / `git add -A`, force push, auto-merge, deployment, PR self-approval, broker/live calls; weakening/skipping existing tests/canaries; any alpha/tradability/profitability claim or second-PnL truth.

## Validation

```bash
# 1) Narrowest meaningful tests first.
python -m pytest tests -k "fast_probe or slice_spec" -q
# 2) Boundary test green (loader lives in research_lane/, not research/).
python -m pytest tests/unit/research/test_research_no_value_engine.py -q
# 3) No research->sim bridge.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"
# 4) Engines + single-factor template byte-unchanged.
git diff -- src/alpha_system/research/conditional_probe.py src/alpha_system/research/first_light.py src/alpha_system/runtime/diagnostics/factor/runtime.py src/alpha_system/strategies/templates.py
# 5) Smoke + canaries.
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
# 6) No numpy/pandas import (polars stays optional via require_dependency).
python -c "import importlib,sys; [sys.exit('numpy/pandas must NOT import') for m in ('numpy','pandas') if importlib.util.find_spec(m)]"
# 7) Run-artifact discipline.
git ls-files runs
```

Broaden to `python tools/verify.py --all` if shared probe/diagnostics behavior appears affected; clean shell, `FRONTIER_*` unset. Record skipped checks + reasons.

## Artifact Policy

`runs/**` local-only, never staged. Commit-eligible handoff `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03.md`; review under `reviews/.../IVL-P03/**`. Loaded materialized rows stay local-only/untracked; only value-free readouts (later phases) are committed. Never commit `runs/**`, parquet/arrow/feather/dbn/zst/sqlite/db, `data/raw/**`, `data/canonical/**`, secrets, `**/*.key`. `git ls-files runs` empty.

### Allowed Paths (commit-eligible — explicit staging only)

- `src/alpha_system/research_lane/slice_spec.py`
- `src/alpha_system/research_lane/fast_probe.py`
- `tests/unit/research_lane/test_fast_probe.py`
- `tests/unit/research_lane/test_slice_spec.py`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03.md`
- `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit/resume only.

## Allowed Test Paths

- `tests/unit/research_lane/**`. Do not weaken/skip existing tests (including `test_research_no_value_engine.py`) or add visible test-only branches.

## Done Criteria

- One generic `fast_probe(card, setup, slice_spec)` exists in `research_lane/` (outside `research/`), loads a bounded existing slice via `load_parquet_values` + `FeatureLabelPackResolver`, maps to governance rows, and feeds `build_factor_diagnostics_run` (main_effect) | `evaluate_setup_conditional_probe` (context≠trigger) in-memory; `promotion_eligible=False`; no materialization / no scaleout-driver call / no second value loader.
- The surrogate `ZERO_PASS_MET` + family-budget `RESPECTED` + ≥2-class preconditions are satisfied (and a degenerate/over-budget slice raises, not bypassed); honest DATA_GAP fallback (no fabricated values) when `polars`/`ALPHA_DATA_ROOT`/rows unresolved.
- `test_research_no_value_engine.py` still passes; no research→sim grep hit; engines + `first_light.py` + single-factor template byte-unchanged (diff); the bespoke bridges (STOPPED DK tool, `first_light.py`) are untouched (retire later); smoke + canaries pass; `git ls-files runs` empty; explicit staging; no `forbidden_paths` edits.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03.md`: scope delivered; exact validation commands + results; skipped checks + reasons; files changed by path; explicit confirmation that (a) `fast_probe`/`slice_spec` live in `research_lane/` and `research/` imports no value loader (boundary test green), (b) the engines/`first_light.py`/single-factor template are byte-unchanged (diff) and the bespoke bridges are untouched (migrate-then-retire deferred), (c) the surrogate/budget/≥2-class preconditions are satisfied not bypassed and `promotion_eligible=False`, (d) DATA_GAP fallback fabricates no values, (e) no materialization/scaleout/registry/paid-data, `git ls-files runs` empty, explicit staging, no `forbidden_paths` edits. Run-local handoff stays local-only.

## Review Requirements

YELLOW fresh Claude Opus review under `reviews/.../IVL-P03/**`. Reviewer adversarially confirms: the bridge is outside `research/` and only `research_lane/` imports the loader (boundary test genuinely green); the engines, `first_light.py`, and single-factor template are byte-unchanged (diff); the row-schema map matches the `dk_p04` mapping; the surrogate `ZERO_PASS_MET` + family-budget + ≥2-class preconditions are satisfied via the real label-shuffle surrogate (not bypassed/stubbed) and `promotion_eligible=False`; the DATA_GAP fallback fabricates no values; no materialization / scaleout-driver / registry write / second loader; the bespoke bridges remain untouched (retirement is correctly deferred); no paid data; research-only language; smoke + canaries pass; `git ls-files runs` empty; explicit staging.

## Auto-Merge / Review Policy

No PR creation, auto-merge, or deployment authorized. Merge gating is the Ralph driver's responsibility under YELLOW lane policy (block on critical / test-tamper / boundary violation / second-PnL-bridge) + human authorization.

## Repair-or-Rollback

- **In-scope repair only:** fix `fast_probe`/`slice_spec`/tests within Allowed Paths; no scope expansion.
- **Rollback:** the bridge is additive new modules in `research_lane/`; revert to restore prior state with no migration/data change (the bespoke bridges and all data are untouched).
- **STOP / escalate:** any pressure to place the bridge under `research/`, import a loader into `research/`, edit the engines/`first_light.py`/bespoke bridges/single-factor template, call the scaleout driver/materialize/registry-write, bypass a precondition, fabricate values, add `numpy`/`pandas` or paid data, or commit a `runs/`/data/secret artifact — surface to the user.

---
---

---

## ERRATA (coordinator review fix — surrogate loop for context!=trigger lane)
`research/conditional_probe.py:evaluate_setup_conditional_probe` REQUIRES surrogate args (`surrogate_run_count`/`surrogate_gate_pass_count`) and enforces a ZERO_PASS gate (`_require_zero_pass_surrogate_gate`). So the fast_probe context!=trigger lane MUST run a bounded conditioned label-shuffle surrogate loop by REUSING the existing surrogate primitives (`governance/surrogate_run.py`) — port/wrap them; do NOT bypass the gate and do NOT build a second surrogate engine. `tests/unit/research_lane/test_slice_spec.py` is in-scope (allowed_paths).

