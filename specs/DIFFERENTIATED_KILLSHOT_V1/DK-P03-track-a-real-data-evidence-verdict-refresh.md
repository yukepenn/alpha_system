# DK-P03 — Track A Real-Data Evidence + Verdict Refresh (FIRST Metric, Post-Gate)

---
campaign_id: DIFFERENTIATED_KILLSHOT_V1
phase_id: DK-P03
lane: YELLOW
status: draft
dependencies: [DK-P02]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Run the **first real-data metric** of the campaign for the five Track A differentiated
mechanisms (day-of-week, OPEX/quad-witch pinning, month-end flow, roll-week flow, open/close
auction proximity) and map their evidence to the **closed verdict taxonomy honestly**. This is
the only phase in which a value-bearing IC/return/diagnostic may be inspected, and it is
unlocked **only because two gates strictly precede it**: the DK-P00 FDR active-subset
restatement (value-free pre-registration) and the DK-P02 surrogate-FDR `ZERO_PASS_MET`
calibration for every study. Each locked StudySpec is scored with the existing runtime factor
diagnostics (directional / point-biserial IC for the binary calendar flag + buckets +
walk-forward), every variant is ledgered, every mechanism is N_eff/power/MDE-qualified, and the
result is written as a per-mechanism verdict refresh in the closed taxonomy
(`REJECT` / `INCONCLUSIVE`+`reason_code` / `WATCH` / `CANDIDATE_RESEARCH`). The expected,
fully acceptable outcome is a **conclusive** read — including honest
`INCONCLUSIVE`+`UNDERPOWERED` for N_eff-limited mechanisms (~8–16 events/yr) — not a positive
one. No promotion, no second PnL truth, no alpha/tradability/profitability claim.

## Context

- **This is the FDR-before-metric unlock.** Per the campaign acceptance invariant, no real-data
  metric may be inspected before (a) the FDR active-subset restatement note is committed
  (DK-P00, predating the earliest variant attempt) **and** (b) the surrogate-FDR zero-pass
  calibration yields `ZERO_PASS_MET` for that study (DK-P02). Both predecessors are merged
  before this phase runs (linear dep `DK-P02 → DK-P03`); DK-P03 consumes their committed
  artifacts and is the first phase permitted to read a value.
- **Reused engines (locked by DK-P00 REUSE-MAP; this phase USES, does not modify):**
  - Runtime factor diagnostics: `alpha_system.runtime.diagnostics.factor.runtime.build_factor_diagnostics_run`
    (`src/alpha_system/runtime/diagnostics/factor/runtime.py:240`) — produces the directional /
    point-biserial IC for the binary calendar flag, bucket diagnostics, and walk-forward folds,
    with a `StudyRunResultState` status (`src/alpha_system/runtime/contracts/run_record.py`:
    `DIAGNOSTICS_COMPLETE` / `INCONCLUSIVE` / `DIAGNOSTICS_FAILED` / `REJECTED`).
  - Power: `src/alpha_system/runtime/diagnostics/power.py` —
    `estimate_ic_standard_error` (`SE(IC) = 1 / sqrt(N_eff − 1)`),
    `minimum_detectable_abs_ic`, and `build_ic_power_statement` (deterministic, value-free
    `mde_abs_ic` statement with `statistical_validity_claim: false`).
  - Variant ledger: `src/alpha_system/governance/variant_ledger.py` —
    `VariantLedger` / `VariantLedgerRecord`, `VariantLedgerStatus.COMPLETED` (`:113`), and the
    fail-closed family-budget hook. Every scored variant is ledgered `COMPLETED`.
  - Verdict taxonomy (human/reviewer layer): `src/alpha_system/governance/verdict_reason_code.py`
    (`VerdictReasonCode`: `UNDERPOWERED`, `SUBSTRATE_GAP`, `COST_FRAGILE`, `DATA_QUALITY`,
    `LEAKAGE_BLOCKED`, `DUPLICATE_EXPOSURE`, `REGIME_UNSTABLE`, `BBO_PROXY_LIMITATION`) and
    `src/alpha_system/governance/reviewer_verdict.py`
    (`create_reviewer_verdict`, `ReviewerVerdictOutcome`, `reason_code`).
  - Value loader (tools/runtime-only): `core/value_store.load_parquet_values`
    (`src/alpha_system/core/value_store.py:116`) lives **outside** `research/`.
- **Two-layer verdict reality (mirror FUTSUB, do not invent an enum).** The runtime emits a
  `StudyRunResultState` (`DIAGNOSTICS_COMPLETE` / `INCONCLUSIVE` / `DIAGNOSTICS_FAILED` /
  `REJECTED`). There is **no `CANDIDATE_RESEARCH` runtime enum**. The closed campaign taxonomy
  (`REJECT` / `INCONCLUSIVE`+code / `WATCH` / `CANDIDATE_RESEARCH`) is the **document-level
  human/reviewer verdict layer**, exactly as `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md`
  does it. This phase maps each runtime status → a closed-taxonomy `primary_state` in the
  `verdict_refresh.md`; it never adds a runtime enum member.
- **No research→reference-sim bridge (HARD).** `research/` imports **zero**
  `backtest`/`management`/`fast_path`/`value_store`. Outcomes come only from materialized path
  / forward-return labels; values are loaded by a `tools/`-or-`runtime/`-side harness via
  `core/value_store.load_parquet_values` and **injected** into the pure research probe. No
  second PnL truth (`forbidden_second_pnl_truth` canary + the AST import guard stay green).
- **Bounded surface.** Per the DK-P00 restatement, the **active** effective pooled surface this
  run is **6** — event-calendar{opex 1 + month_end 1}=2 plus flow-seasonality{day_of_week 1 +
  roll_week 1 + open_close 2}=4. The carried per-family budget CAPS are unchanged (event-calendar
  `family_budget` 6, which still includes the **deferred** fomc/cpi horizons; flow-seasonality
  `family_budget` 4) — the active event-calendar surface this run is only 2 (opex+month_end), and
  un-deferring fomc/cpi toward the cap would require a strictly-increasing `BudgetAmendmentRecord`.
  Pooled ES/NQ/RTY is **one test per mechanism**; per-mechanism `variant_budget` = horizon count
  (day_of_week 1, opex 1, month_end 1, roll_week 1, open_close 2). NO grid, NO horizon sweep, NO
  per-instrument split without a (strictly-increasing) `BudgetAmendmentRecord` — this phase authors none.
- **Asymmetric survivor gate.** A `WATCH` / `CANDIDATE_RESEARCH` survivor is the only outcome
  that requires extra evidence: it **must** carry a `reviewer_verdict` artifact + `reason_code`
  and is **surfaced** to the coordinator/user, **never auto-promoted**. `REJECT` and
  `INCONCLUSIVE`+code stand on the diagnostics alone.
- **Expected N_eff reality.** Calendar mechanisms are rare events (OPEX 12/yr, quad-witch 4/yr,
  month-end 12/yr, quarter-end 4/yr, roll-week ~4/yr). Pooled across ES/NQ/RTY they remain
  thin; `minimum_detectable_abs_ic` will frequently exceed any plausible effect, so
  `INCONCLUSIVE`+`UNDERPOWERED` is the honest, expected verdict for several mechanisms. This is
  a successful, conclusive read, not a failure.

## Scope

1. **Score each locked StudySpec with the runtime factor diagnostics.** For each of the five
   StudySpecs authored/locked in DK-P02
   (`research/differentiated_substrate_v1/study_specs/`), call
   `build_factor_diagnostics_run` with the calendar flag as the declared conditioning
   factor-under-test, forward-return labels at the card's pre-registered horizon(s), pooled
   ES/NQ/RTY as one test. Produce the directional / point-biserial IC, bucket diagnostics, and
   walk-forward folds, and read the resulting `StudyRunResultState`.
2. **Inject values via the tools/runtime path only.** Add or reuse a `tools/`-side harness that
   resolves the locked pack/label rows via `core/value_store.load_parquet_values`
   (`core/value_store.py:116`) and **injects** the loaded rows into the pure research scorer.
   `research/` modules must **not** import `value_store`/`backtest`/`management`/`fast_path`;
   the loader stays on the `tools/`-or-`runtime/` side and hands rows in.
3. **N_eff / power / MDE per mechanism.** For every mechanism, compute and record `N_eff`,
   `SE(IC) = 1/sqrt(N_eff − 1)` (`estimate_ic_standard_error`), and the
   `minimum_detectable_abs_ic` / `build_ic_power_statement` MDE statement (carrying
   `statistical_validity_claim: false`). The power statement is part of every readout.
4. **Ledger every variant.** Record each scored variant in the `VariantLedger` with status
   `VariantLedgerStatus.COMPLETED`, bound to the pre-registered family/variant budget from the
   DK-P00 restatement (event-calendar 6, flow-seasonality 4). Do not exceed budget; do not
   author a `BudgetAmendmentRecord`.
5. **Write the verdict refresh.** Produce
   `research/differentiated_substrate_v1/verdict_refresh.md` mapping each mechanism's evidence
   to a closed-taxonomy `primary_state` + (for `INCONCLUSIVE`) a `VerdictReasonCode`. Mirror the
   FUTSUB `verdict_refresh.md` structure: evidence inputs, a boundary roll-up table across
   `REJECT` / `INCONCLUSIVE`+code / `WATCH` / `CANDIDATE_RESEARCH`, and a per-mechanism row with
   `primary_state`, `reason_code`, `N_eff`, `MDE`, and the runtime `StudyRunResultState` it was
   derived from. **Value-bearing diagnostics are permitted here (post-gate)** but the prose stays
   research-only: no tradability / profitability / alpha claim, no promotion.
6. **Survivor handling (asymmetric).** If any mechanism lands `WATCH` or `CANDIDATE_RESEARCH`,
   also write a `reviewer_verdict` artifact (`create_reviewer_verdict` with a `reason_code`) for
   that mechanism under `research/differentiated_substrate_v1/**`, and surface it explicitly in
   the handoff for the coordinator/user survivor-gate decision. Do **not** promote, build a
   FactorLibrary entry, or take any next-layer action.
7. **Tests** under `tests/**` asserting: the scorer runs over an injected synthetic row fixture
   and emits a `StudyRunResultState`; the verdict mapping produces only closed-taxonomy
   `primary_state` values; an `INCONCLUSIVE` row always carries a `VerdictReasonCode`; an
   N_eff-limited fixture maps to `INCONCLUSIVE`+`UNDERPOWERED`; a `WATCH`/`CANDIDATE_RESEARCH`
   fixture requires a `reviewer_verdict`+`reason_code`; every readout carries an
   `ic_power_statement`; each scored variant is ledgered `COMPLETED`; and `research/` imports
   none of `backtest`/`management`/`fast_path`/`value_store`.

## Non-Goals

- Any **promotion**, `PromotionDecision`, FactorLibrary entry, AlphaBook/Strategy-Reference
  write, or paper/live/broker action. A survivor is surfaced, never auto-promoted.
- Any **per-instrument split** (ES/NQ/RTY stay pooled as one test) or any **horizon sweep** /
  grid / geometry expansion. No new variant beyond the pre-registered budget; no
  `BudgetAmendmentRecord`.
- Any **second PnL truth**: `research/` must not import the value engine
  (`backtest`/`management`/`fast_path`/`value_store`); values are injected from the
  tools/runtime side only.
- Re-running, re-locking, or editing the **DK-P02 StudySpecs / surrogate calibration**; editing
  the `SINGLE_FACTOR_THRESHOLD_TEMPLATE` / `StudyConfig` single-factor path (byte-unchanged);
  weakening any gate (parity, no-lookahead, surrogate zero-pass, roll/maintenance fail-closed).
- Adding any **runtime enum** (no `CANDIDATE_RESEARCH` runtime state — the taxonomy stays
  doc-level); adding a new ledger/FDR object; the Track B EXPLORATORY probe (that is **DK-P04**)
  or the campaign aggregation / survivor-gate closeout (that is **DK-P05**).
- Adding a runtime dependency (`numpy`/`pandas`/`polars` stay unimportable); any new paid data
  (`fomc`/`cpi` stay DEFERRED); editing FUTSUB / core-pilot research artifacts; any
  alpha/profitability/tradability claim.

## Expected Files (illustrative, not prescriptive)

- `research/differentiated_substrate_v1/verdict_refresh.md` — new (per-mechanism `primary_state`
  + `reason_code` + `N_eff`/MDE roll-up; mirrors the FUTSUB verdict_refresh structure)
- `research/differentiated_substrate_v1/diagnostics/*.md|*.json` — new (per-mechanism value-free
  diagnostics summary the verdict refresh cites)
- `research/differentiated_substrate_v1/reviewer_verdicts/*.json` — new, **only if** a
  `WATCH`/`CANDIDATE_RESEARCH` survivor exists (`reviewer_verdict` + `reason_code` artifact)
- `tools/differentiated_killshot_v1/score_track_a.py` (or similar) — new/edited
  (tools/runtime-side row-injection harness that loads via `core/value_store.load_parquet_values`
  and injects rows into the pure research scorer; this is where the value loader lives)
- `tests/.../test_track_a_diagnostics.py`, `tests/.../test_verdict_refresh.py`,
  `tests/.../test_research_no_value_engine.py` — new
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P03.md` — new (commit-eligible handoff)
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P03/**` — new (YELLOW review artifacts)

## Interfaces / Contracts

- **Scoring entrypoint.** Diagnostics are produced by
  `build_factor_diagnostics_run(...)` (`runtime/diagnostics/factor/runtime.py:240`), returning a
  result carrying a `StudyRunResultState` (`DIAGNOSTICS_COMPLETE` / `INCONCLUSIVE` /
  `DIAGNOSTICS_FAILED` / `REJECTED`). The phase consumes that status; it does not add or rename
  a state.
- **Value injection (no bridge).** A `tools/`-side harness calls
  `load_parquet_values(path)` (`core/value_store.py:116`) and passes the resulting
  `list[dict]` rows into the pure research scorer. The research scorer signature accepts injected
  rows (e.g. `score_mechanism(study_spec, *, rows, label_rows) -> MechanismDiagnostics`); it
  never opens a Parquet, never imports `value_store`, and never computes a PnL value.
- **Power statement.** Each readout attaches `build_ic_power_statement(n_eff=..., factor_id=...)`
  (`runtime/diagnostics/power.py:43`) with `SE(IC) = estimate_ic_standard_error(n_eff)` and
  `mde_abs_ic = minimum_detectable_abs_ic(n_eff)`; the statement keeps
  `statistical_validity_claim: false`.
- **Variant ledger.** Each scored variant is recorded as a `VariantLedgerRecord` with
  `VariantLedgerStatus.COMPLETED` (`variant_ledger.py:113`), bound to the pre-registered
  family/variant budget; the fail-closed family-budget hook is not weakened.
- **Verdict taxonomy mapping.** The `verdict_refresh.md` maps each runtime `StudyRunResultState`
  to a closed-taxonomy `primary_state` in {`REJECT`, `INCONCLUSIVE`, `WATCH`,
  `CANDIDATE_RESEARCH`}. Any `INCONCLUSIVE` row carries a `VerdictReasonCode`
  (`verdict_reason_code.py`) — typically `UNDERPOWERED` for N_eff-limited mechanisms. This is
  doc-level only; no runtime enum is added.
- **Asymmetric survivor artifact.** A `WATCH`/`CANDIDATE_RESEARCH` survivor requires a
  `create_reviewer_verdict(...)` artifact with `reason_code` (`reviewer_verdict.py:191`), and is
  surfaced in the handoff for the coordinator/user; the trusted/promotion path is not invoked.

## Forbidden Changes

- Editing any path under `forbidden_paths` (`execution/`, `broker/`, `live/`, `portfolio/`,
  `management/`, `backtest/`, `l2/`, `agent_factory/`, `core/value_store.py`,
  `strategies/templates.py`, the FUTSUB / core-pilot research trees, all `data/**`, any
  `*.sqlite`/`*.db`/`*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`).
- **FDR-before-metric.** Inspecting or recording a real-data metric in a way that bypasses the
  predecessor gates — the DK-P00 FDR active-subset restatement and the DK-P02
  `ZERO_PASS_MET` surrogate calibration must both already be committed; this phase consumes them
  and does not re-open, re-scope, or amend them. The downward re-scope was a value-free
  pre-registration note, **not** a `BudgetAmendmentRecord` (`create_budget_amendment_record`
  enforces `new_budget > prior_budget`, strictly increasing, so it cannot encode a downward
  restatement — do not attempt one).
- Importing `backtest` / `management` / `fast_path` / `value_store` from `research/`; creating a
  second PnL truth; opening any Parquet/registry inside `research/`.
- Adding a runtime enum member (no `CANDIDATE_RESEARCH` runtime state); weakening the
  `StudyRunResultState` semantics; weakening the single-factor template, surrogate zero-pass,
  no-lookahead/`available_ts`, roll/maintenance fail-closed, or parity gates; weakening or
  skipping any existing test or canary, or adding a visible test-only branch.
- Promoting any artifact, writing a `PromotionDecision`/FactorLibrary/AlphaBook entry, auto-merge,
  PR creation, deployment, or any broker/live call.
- Per-instrument split, horizon sweep, grid, or any variant beyond the pre-registered budget;
  authoring a `BudgetAmendmentRecord`.
- Adding a dependency (`numpy`/`pandas`/`polars`); new paid data (`fomc`/`cpi`);
  secrets/credentials; raw/canonical/factor/label data, caches, model binaries, large artifacts.
- `git add .`, `git add -A`, force push; any alpha/profitability/tradability claim.

## Validation

Run from the repo root. All commands are local-only, safe, and make **no** provider, network,
merge, or external calls.

```bash
# 1) Narrowest meaningful tests first — Track A diagnostics + verdict mapping + power + ledger.
python -m pytest tests -k "diagnostics or verdict or variant_ledger or power" -q

# 2) Repo smoke.
python tools/verify.py --smoke

# 3) Safety canaries must remain all-PASS (planted_fake_alpha, true-alpha pair,
#    forbidden_second_pnl_truth, forbidden_exploratory_promotion, governance_random_target,
#    forbidden_scope_drift).
python tools/hooks/canary_runner.py

# 4) No new dependency: numpy/pandas/polars must remain unimportable.
python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"

# 5) No research->sim bridge: research/ must not import backtest/management/fast_path/value_store.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" --include=*.py src/alpha_system/research 2>/dev/null && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"

# 6) FDR-before-metric ordering: both predecessor gates are committed before this phase.
test -f research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md && echo "FDR restatement present"
grep -rl "ZERO_PASS_MET" research/differentiated_substrate_v1/ && echo "surrogate zero-pass evidence present"

# 7) Single-factor + value engine untouched (must print nothing).
git diff -- src/alpha_system/strategies/templates.py src/alpha_system/core/value_store.py

# 8) Run-artifact discipline: must print nothing.
git ls-files runs
```

Broaden to the authoritative suite (`python tools/verify.py --all`) if shared governance,
diagnostics, or power behavior appears affected; run it in a clean shell with `FRONTIER_*` env
unset to avoid the known driver-env false negative. Record any skipped check and its reason in
the handoff.

## Artifact Policy

Run artifacts are local-only and must never be committed:

- `runs/**` is **local-only runtime state**; `run_dir` artifacts are for local audit only.
- The run-local `handoff.md` / `review.md` / `verdict.json` under `runs/<run_id>/...` must
  **never** be staged or committed.
- A commit-eligible handoff goes under `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P03.md`.
- `runs/.gitkeep`, `runs/README.md`, and `runs/**` must **not** appear in Allowed Paths.
- `git ls-files runs` must return empty.
- Never commit: `runs/**`, any `*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`/`*.sqlite`/`*.db`,
  `data/raw/**`, `data/canonical/**`, `secrets/**`, `**/*.key`. The materialized values scored
  here stay **local-only** and are loaded via the tools/runtime path; only the value-free /
  research-only diagnostics summary and the verdict refresh are committed.

### Allowed Paths (commit-eligible — explicit staging only)

These are the **only** paths this phase may stage and commit. Stage by explicit path; never
`git add .` / `git add -A`; never force push.

- `research/differentiated_substrate_v1/**`
- `tools/**`
- `tests/**`
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P03.md`
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P03/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` (run state, events, costs, STOP, run-local `handoff.md`/`review.md`/`verdict.json`,
  checks, repair attempts) — local audit and resume only. **No `runs/` path appears under Allowed
  Paths above.**

## Allowed Test Paths

- `tests/**` (new `test_track_a_diagnostics*` / `test_verdict_refresh*` /
  `test_research_no_value_engine*` and any close-by governance/runtime-diagnostics/power tests).
  Do not weaken or skip existing tests; do not add visible test-only special cases.

## Done Criteria

- All five Track A mechanisms scored on **real data**, post FDR-restatement + surrogate
  zero-pass (both predecessor gates committed and consumed, not re-opened).
- Each mechanism has a closed-taxonomy `primary_state` + (for `INCONCLUSIVE`) a
  `VerdictReasonCode` + `N_eff` + `SE(IC)` + `MDE` power statement; N_eff-limited mechanisms land
  `INCONCLUSIVE`+`UNDERPOWERED` honestly.
- `research/differentiated_substrate_v1/verdict_refresh.md` committed with a per-mechanism
  roll-up (research-only language; value-bearing diagnostics permitted here; **no** tradability /
  profitability / alpha claim; no promotion).
- Every scored variant is ledgered `VariantLedgerStatus.COMPLETED` within the pre-registered
  family/variant budget; no `BudgetAmendmentRecord`; no per-instrument split; no horizon sweep.
- Any `WATCH`/`CANDIDATE_RESEARCH` survivor carries a `reviewer_verdict` + `reason_code` artifact
  and is **surfaced** in the handoff; nothing is auto-promoted.
- `research/` imports **zero** `backtest`/`management`/`fast_path`/`value_store`; values are
  injected from the tools/runtime harness; no runtime enum added; single-factor path + value
  engine byte-unchanged.
- `python tools/hooks/canary_runner.py` all-PASS; `numpy`/`pandas`/`polars` remain unimportable;
  no new paid data.
- `git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write the commit-eligible handoff at `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P03.md`: scope
delivered, exact validation commands run with results, any skipped check + reason, files changed
by path, and explicit confirmation that (a) both predecessor gates (DK-P00 FDR restatement,
DK-P02 `ZERO_PASS_MET`) were committed and consumed before any metric was read; (b) `research/`
imports no `backtest`/`management`/`fast_path`/`value_store` and values were injected from the
tools/runtime harness; (c) every mechanism's `primary_state` + `reason_code` + `N_eff`/MDE are
recorded and the verdict mapping used only the closed taxonomy (no runtime enum added);
(d) every scored variant is ledgered `COMPLETED` within the pre-registered budget with no
amendment, split, or sweep; and (e) any `WATCH`/`CANDIDATE_RESEARCH` survivor has a
`reviewer_verdict`+`reason_code` artifact and is surfaced (never auto-promoted). The run-local
`runs/<run_id>/.../handoff.md` stays local-only and must not be staged.

## Review Requirements

YELLOW lane requires a fresh Claude Opus review. Commit-eligible review notes + verdict belong
under `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P03/**`; run-local `review.md`/`verdict.json` stay
under `runs/<run_id>/...` and are not committed. The reviewer must adversarially confirm:
the FDR-before-metric ordering held (no metric read before the DK-P00 restatement and DK-P02
zero-pass were committed); `research/` imports no value engine and values were injected from the
tools/runtime side (no second PnL truth; `forbidden_second_pnl_truth` green); each mechanism's
`primary_state` maps faithfully from the runtime `StudyRunResultState` into the closed taxonomy
with a `reason_code` on every `INCONCLUSIVE` (reason-code fidelity; `UNDERPOWERED` where N_eff is
thin); variants are ledgered `COMPLETED` within the pre-registered budget with no amendment /
per-instrument split / horizon sweep; any `WATCH`/`CANDIDATE_RESEARCH` survivor is gated behind a
`reviewer_verdict`+`reason_code` and surfaced (never auto-promoted); the single-factor path,
value engine, and all gates are unchanged; no new dependency; no paid data; no
alpha/profitability/tradability claim; and artifact + explicit-staging discipline are honored.

## Auto-Merge / Review Policy

This spec authorizes no PR creation, no auto-merge, and no deployment. Merge gating is the Ralph
driver's responsibility under the YELLOW lane policy (review required; block on critical /
test-tamper / boundary violation / second-PnL-truth / FDR-ordering violation) and human
authorization — not this spec.

## Repair-or-Rollback

- **In-scope repair only:** fix the scoring harness, verdict mapping, power/ledger wiring, the
  verdict refresh document, or tests within the Allowed Paths; do not expand scope to fix
  unrelated findings.
- **Rollback:** the change is additive and pure-Python plus committed Markdown/JSON; revert the
  tools-side scoring harness, the new tests, the `verdict_refresh.md` / diagnostics summary, and
  any `reviewer_verdict` artifact to restore the prior state with no migration and no data
  change (materialized values were local-only and uncommitted).
- **STOP / escalate (do not auto-proceed):** any pressure to read a metric before both
  predecessor gates are committed, build the research→sim bridge or import the value engine into
  `research/`, add a runtime `CANDIDATE_RESEARCH` enum, split per-instrument or sweep horizons,
  author a `BudgetAmendmentRecord` (especially a downward one — the object is strictly
  increasing), auto-promote a `WATCH`/`CANDIDATE_RESEARCH` survivor, weaken a truth-chain
  invariant or canary, add a dependency or paid data, or commit a `runs/`/data/secret artifact —
  treat as out-of-scope and surface to the user.
