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

# IVL-P04 — Human-Readable Verdict `REPORT.md` Renderer

---
campaign_id: ALPHA_IDEA_TO_VERDICT_LOOP_V0
phase_id: IVL-P04
lane: YELLOW
status: draft
dependencies: [IVL-P03]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Render a human-readable governed `REPORT.md` from an idea's intake + testability + fast-probe outputs: idea summary, `study_kind`, slice, data/features/labels used, dedup outcome, the 5 gate verdicts, the fast readout (including `class_count` / `minority_count` so a single-class slice is self-evident), N_eff/MDE, surrogate state, the verdict (**REJECT / DATA_GAP / INCONCLUSIVE / WATCH / CANDIDATE**) + why + next action. Reuse the verdict reason-code enum.

YELLOW: the report is the governed human-facing artifact whose honesty (no leaked/overclaimed values, self-evident degeneracy) is load-bearing.

## Context

Verified live:

- **Verdict reason codes (REUSED):** `governance/verdict_reason_code.py:11 VerdictReasonCode` (closed StrEnum: `UNDERPOWERED`, `SUBSTRATE_GAP`, `COST_FRAGILE`, `DATA_QUALITY`, `LEAKAGE_BLOCKED`, `DUPLICATE_EXPOSURE`, `REGIME_UNSTABLE`, `BBO_PROXY_LIMITATION`); `:24 validate_verdict_reason_code`. The 5 verdict outputs (REJECT/DATA_GAP/INCONCLUSIVE/WATCH/CANDIDATE) carry a reason code from this enum where applicable.
- **Class-count surfacing:** the fast readout / class-balance summary expose `class_count`/`majority_class_count`/`minority_class_count` (`runtime/diagnostics/label/runtime.py:687-689`) — the renderer surfaces `class_count` + `minority_count` so a single-class (degenerate) slice is self-evident in the report.
- **DATA_GAP shape:** the honest-gap readout (`research/first_light.py:195` pattern; IVL-P03 fast_probe DATA_GAP) renders as a DATA_GAP verdict with `surrogate_fdr_gate=BLOCKED`/`n_eff=0`, not a fabricated metric.
- **Placement:** the renderer lives under `research_lane/` (it consumes the IVL-P03 readout objects; no value loader needed at render time — it renders already-computed value-free summaries).

## Scope

1. **New `src/alpha_system/research_lane/verdict_report.py`**: a pure renderer `render_verdict_report(...) -> str` that takes the IdeaDraft + testability-gate result + fast-probe readout (or DATA_GAP) and produces `REPORT.md` text with sections: idea summary; `study_kind`; slice (instrument/session/window/pack-refs); data/features/labels used; dedup outcome (the `duplicate_exposure` declaration outcome); the 5 gate verdicts (PASS/FAIL/DATA_GAP each); fast readout incl. `class_count` + `minority_count`; N_eff / MDE; surrogate state (`ZERO_PASS_MET` / `BLOCKED`); the verdict (REJECT/DATA_GAP/INCONCLUSIVE/WATCH/CANDIDATE) + why (citing a `VerdictReasonCode` where applicable) + next action.
2. **`alpha idea report` subcommand** (or `--report` on an existing subcommand) added to `cli/idea.py` that renders the `REPORT.md` for a given idea/readout. Research-only language enforced (no alpha/tradability/profitability wording in the template).
3. **Tests:** a golden-file test on a fixed (fixture) readout asserting the rendered sections and that a single-class slice renders `class_count=1`/`minority_count=0` self-evidently and yields a DATA_GAP (not INCONCLUSIVE/WATCH); a reason-code-bearing verdict renders a valid `VerdictReasonCode`; the renderer fabricates no value when given a DATA_GAP input.

## Non-Goals

- Loading parquet / computing any metric at render time (the renderer consumes already-computed value-free summaries).
- Promoting any verdict, writing memory records (IVL-P05), or emitting a PromotionDecision/FactorLibrary entry.
- Any downstream-module charter; any alpha/tradability/profitability claim.

## Expected Files (illustrative)

- `src/alpha_system/research_lane/verdict_report.py` — new.
- `src/alpha_system/cli/idea.py` — edit (add `report` subcommand / `--report`).
- `tests/unit/research_lane/test_verdict_report.py` — new (golden-file).
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P04.md`, `reviews/.../IVL-P04/**`.

USED unchanged: `governance/verdict_reason_code.py` (imported), the IVL-P03 readout/DATA_GAP shapes.

## Interfaces / Contracts

- **`render_verdict_report(idea_draft, testability_result, fast_readout) -> str`** — pure, deterministic, value-free in the sense that it surfaces only ids/counts/gate outcomes/diagnostics summaries already present in the inputs.
- **Verdict + reason code:** verdict ∈ {REJECT, DATA_GAP, INCONCLUSIVE, WATCH, CANDIDATE}; reason cites a `VerdictReasonCode` validated via `validate_verdict_reason_code` where applicable.
- **Self-evident degeneracy:** the report always shows `class_count` and `minority_count`; `class_count < 2` ⇒ rendered as DATA_GAP with the degeneracy explicit.

## Forbidden Changes

- Loading parquet / computing a metric in the renderer; importing a value loader at render time.
- Promoting a verdict, writing memory records, or emitting a PromotionDecision/FactorLibrary entry (IVL-P05 owns memory; promotion stays reviewer-gated there).
- Editing the engines, `verdict_reason_code.py`, the single-factor template, or the value engine.
- Adding a runtime dependency (`numpy`/`pandas`/`polars` unimportable at render time); fabricating any value on DATA_GAP.
- `git add .` / `git add -A`, force push, auto-merge, deployment, PR self-approval, broker/live calls; weakening/skipping existing tests/canaries; any alpha/tradability/profitability claim.

## Validation

```bash
# 1) Narrowest meaningful tests first (golden-file).
python -m pytest tests -k "verdict_report or report" -q
# 2) CLI renders a REPORT.md from a fixture readout.
python -m alpha_system.cli.main idea report research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml
# 3) Boundary + smoke + canaries.
python -m pytest tests/unit/research/test_research_no_value_engine.py -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
# 4) No new dependency.
python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"
# 5) Run-artifact discipline.
git ls-files runs
```

Broaden to `python tools/verify.py --all` if shared behavior appears affected; clean shell, `FRONTIER_*` unset. Record skipped checks + reasons.

## Artifact Policy

`runs/**` local-only, never staged. Commit-eligible handoff `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P04.md`; review under `reviews/.../IVL-P04/**`. Rendered `REPORT.md` for the dogfood lands in IVL-P06's evidence dir (value-free). Never commit `runs/**`, parquet/arrow/feather/dbn/zst/sqlite/db, `data/raw/**`, `data/canonical/**`, secrets, `**/*.key`. `git ls-files runs` empty.

### Allowed Paths (commit-eligible — explicit staging only)

- `src/alpha_system/research_lane/verdict_report.py`
- `src/alpha_system/cli/idea.py`
- `tests/unit/research_lane/test_verdict_report.py`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P04.md`
- `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P04/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit/resume only.

## Allowed Test Paths

- `tests/unit/research_lane/test_verdict_report.py`. Do not weaken/skip existing tests or add visible test-only branches.

## Done Criteria

- `verdict_report.py` renders `REPORT.md` with all required sections (idea summary, study_kind, slice, data/features/labels, dedup outcome, 5 gate verdicts, fast readout incl. `class_count`+`minority_count`, N_eff/MDE, surrogate state, verdict + why + next action), citing a `VerdictReasonCode` where applicable.
- A single-class slice renders `class_count=1`/`minority_count=0` self-evidently and yields a DATA_GAP verdict (not INCONCLUSIVE/WATCH); a DATA_GAP input fabricates no value.
- `alpha idea report` subcommand registered; golden-file test passes; renderer loads no parquet and computes no metric; smoke + canaries pass; `numpy`/`pandas`/`polars` unimportable; `git ls-files runs` empty; explicit staging; no `forbidden_paths` edits.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P04.md`: scope delivered; exact validation commands + results; skipped checks + reasons; files changed by path; explicit confirmation that (a) the renderer loads no parquet / computes no metric (consumes value-free summaries), (b) `class_count`+`minority_count` are surfaced so degeneracy is self-evident and a single-class slice renders DATA_GAP, (c) verdicts cite a valid `VerdictReasonCode`, (d) research-only language with no promotion/memory write here, (e) `git ls-files runs` empty, explicit staging, no `forbidden_paths` edits. Run-local handoff stays local-only.

## Review Requirements

YELLOW fresh Claude Opus review under `reviews/.../IVL-P04/**`. Reviewer adversarially confirms: the renderer is pure / value-free (no parquet load, no metric computation, no value fabrication on DATA_GAP); degeneracy is self-evident (`class_count`+`minority_count` always shown; single-class ⇒ DATA_GAP); verdicts use the closed `VerdictReasonCode` enum (validated); the report contains no alpha/tradability/profitability language and no promotion; the golden-file test is meaningful (not a trivial assert); smoke + canaries pass; `git ls-files runs` empty; explicit staging.

## Auto-Merge / Review Policy

No PR creation, auto-merge, or deployment authorized. Merge gating is the Ralph driver's responsibility under YELLOW lane policy + human authorization.

## Repair-or-Rollback

- **In-scope repair only:** fix the renderer / CLI subcommand / golden-file test within Allowed Paths; no scope expansion.
- **Rollback:** additive renderer + CLI subcommand; revert to restore prior state with no migration/data change.
- **STOP / escalate:** any pressure to load parquet / compute a metric in the renderer, fabricate a value on DATA_GAP, promote a verdict, write a memory record here, add a dependency, or commit a `runs/`/data/secret artifact — surface to the user.

---
---
