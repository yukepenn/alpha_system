# DK-P02 — Track A StudySpecs + Declared-Conditioning-Factor Admission + Surrogate-FDR Zero-Pass

---
campaign_id: DIFFERENTIATED_KILLSHOT_V1
phase_id: DK-P02
lane: YELLOW
status: draft
dependencies: [DK-P01]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Author and lock the **five Track A StudySpecs** — one per active differentiated mechanism, each
declaring the **calendar flag as the conditioning factor-under-test**, pooled across ES/NQ/RTY —
then make the **minimal scoped change** that lets an **explicitly-declared calendar-conditioning
factor** be admitted as the factor-under-test in the surrogate calibration path (today
`session_calendar_*` is classified as a *support* family and skipped, raising
`declared_factor_family_missing`), and finally run the **surrogate-FDR zero-pass calibration** that
**gates all later real-data evidence** in DK-P03. This phase is the surrogate-FDR half of the
campaign's `FDR-before-metric` invariant: after DK-P00 committed the value-free FDR active-subset
restatement, **no real-data metric may be inspected until every Track A study reaches
`ZERO_PASS_MET` here**. This phase inspects **no** real-data IC/return/diagnostic value; its
calibration reports are value-free (ids / run-counts / seeds / gate outcomes only).

## Context

- **Reused engines (locked by DK-P00 REUSE-MAP; do not rebuild):**
  - StudySpec contract: `src/alpha_system/governance/study_spec.py`
    (`StudySpec`, `create_study_spec`, `validate_study_spec`, `generate_study_spec_id`,
    `variant_budget`, optional `family_budget`). `variant_budget` is validated as a **positive
    bounded integer cap** (`_validate_variant_budget`).
  - Surrogate-FDR engine: `src/alpha_system/governance/surrogate_run.py`
    (`SurrogatePerturbationType.LABEL_SHUFFLE` / `.TRADE_DATE_BLOCK_SHUFFLE` /
    `.TRADE_DATE_BLOCK_BOOTSTRAP`; `calibrate_surrogate_fdr`; `SurrogateCalibrationReport`;
    `ZERO_PASS_MET = "zero-pass-met"`; `LEAKAGE_BLOCKED`;
    `study_config_for_surrogate_scope(...) -> StudyConfig`;
    `require_isolated_namespace`; `render_value_free_calibration_report` /
    `write_value_free_calibration_report`).
  - Calibration driver: `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
    (CLI `--study-spec`, `--alpha-data-root`, `--namespace` (REQUIRED — an isolated scratch
    namespace; `require_isolated_namespace`), `--runs-per-config` (the pre-registered **K** per
    perturbation config), `--base-seed`, `--report-out`). It stages real packs, builds the
    surrogate `StudyConfig` via `study_config_for_surrogate_scope`, runs the perturbations, and
    writes a **value-free** Markdown report.
  - Runtime resolver / pack locking: `src/alpha_system/runtime/input_resolver.py`
    (`FeatureLabelPackResolver`) for the resolver-smoke that locks pack/label resolutions.
  - Value loader: `core/value_store.load_parquet_values` is a **tools/runtime-only** loader
    (imported by `run_real_surrogate_calibration.py`); `research/` never imports it.
- **The classification skip this phase narrowly opens.** In
  `run_real_surrogate_calibration.py`, `_support_feature_family` (≈ line 1928) returns `True` for
  any family in `SUPPORT_FEATURE_FAMILIES` **or any family whose name `startswith("session_calendar")`**.
  `_declared_feature_family` (≈ lines 547–559) then filters support families out and raises
  `declared_factor_family_missing` when **no** non-support family remains — which is exactly what
  happens for a calendar-conditioning study whose only non-support lock is a `session_calendar_*`
  family. The minimal change must admit **only** a feature family that the StudySpec **explicitly
  declares** as its conditioning factor-under-test, while leaving the support rule intact for every
  other (incidentally-present) `session_calendar_*` lock.
- **The factor_id identity gate.** The driver enforces `runtime_factor_id_mismatch`
  (≈ line 386): the **staged** calibration `factor_id` (`_lock_text(feature_lock, "feature_id", ...)`)
  must equal the runtime `StudyConfig.factor_id` construction path. Equivalently, the staged
  calibration `factor_id` MUST equal `study_config_for_surrogate_scope(...).factor_id`. The
  admission must not break this identity.
- **Isolated, value-free report namespace.** `_FORBIDDEN_REPO_NAMESPACE_ROOTS`
  (`surrogate_run.py` ≈ line 141) bans `registry/`, `metadata/`, `data/raw`, `data/canonical`,
  `artifacts/`, `runs/`, `research/futures_core_alpha_pilot_v1`,
  `research/futures_substrate_scaleout_v1`. `require_isolated_namespace` requires an **existing
  isolated directory** (not a DB/Parquet file). `--report-out` must target a **fresh** value-free
  directory under `research/differentiated_substrate_v1/**`, outside every forbidden root.
- **Gate semantics.** `ZERO_PASS_MET` (`"zero-pass-met"`) means **run_count > 0, zero shuffled
  statistic passes, zero errors**. **ANY** shuffled statistic pass ⇒ `LEAKAGE_BLOCKED` ⇒ the
  pipeline is leaking; **diagnose FIRST** (full autonomy, document the root cause), do **not**
  proceed to real-data evidence. (DK-P03 is the *only* phase that may inspect a real-data metric,
  and only after `ZERO_PASS_MET` here.)
- **Global hard invariants relevant to this phase (state, do not weaken):**
  - **FDR before metric.** No real-data metric before DK-P00's FDR active-subset restatement
    **and** this phase's `ZERO_PASS_MET` gate for that study.
  - The FDR downward re-scope is a **value-free pre-registration NOTE, not a
    `BudgetAmendmentRecord`** (`create_budget_amendment_record` enforces
    `new_budget > prior_budget`, strictly increasing, so it cannot encode a downward restatement).
    This phase carries — never re-creates — that restatement.
  - **No `research/` → reference-sim bridge.** `research/` imports zero
    `backtest`/`management`/`fast_path`/`value_store`. Values are loaded by `tools/`/`runtime/`
    (e.g. `core/value_store.load_parquet_values`, which lives **outside** `research/`) and injected;
    the StudySpecs and reports under `research/differentiated_substrate_v1/**` are pure
    declarations/value-free artifacts.
  - **Single-factor path byte-unchanged.** `SINGLE_FACTOR_THRESHOLD_TEMPLATE` and
    `StudyConfig.factor_id` construction stay byte-unchanged; the admission is **strictly additive**
    and preserves every gate (parity, no-lookahead/`available_ts`, zero-pass,
    constant/all-null exclusion).
  - **EXPLORATORY ≠ promotion** (Track B, DK-P04); not exercised here but unviolated.
  - **No new dependency** (`numpy`/`pandas`/`polars` stay unimportable); **no new paid data**
    (`fomc`/`cpi` DEFERRED, `needs_paid_data`); `git ls-files runs` empty; explicit staging only;
    no edits under `forbidden_paths`.
  - **Allowed outputs only:** REJECT / INCONCLUSIVE+reason_code / WATCH / CANDIDATE_RESEARCH.
    Research-only language; no alpha/tradability/profitability claim; no promotion. (No verdict is
    *emitted* here — verdicts are DK-P03 — but the phase produces no claim either.)

## Scope

Bounded by the locked `campaigns/DIFFERENTIATED_KILLSHOT_V1/campaign.yaml` DK-P02 entry. Allowed
work, and **only** this work:

1. **Author five Track A StudySpecs** under
   `research/differentiated_substrate_v1/study_specs/` (one per active mechanism), each via the
   `create_study_spec`/`validate_study_spec` contract and JSON-locked. Each StudySpec:
   - declares the **calendar flag as the conditioning factor-under-test** (the explicitly-declared
     conditioning feature family + factor lock), pooled **ES/NQ/RTY as ONE test per mechanism**;
   - binds **forward-return labels** (`fixed_horizon` / `midprice_forward`) at the **card's
     pre-registered horizon(s)**;
   - sets `variant_budget` = **horizon count**, and `family_budget` per the DK-P00 restatement
     (**event-calendar family = 6** for `opex` + `month_end`; **flow-seasonality family = 4** for
     `day_of_week` + `roll_week` + `open_close`);
   - locks pack/label resolutions verified by **resolver-smoke** (`FeatureLabelPackResolver`).

   | StudySpec | mechanism | conditioning flag (factor-under-test) | horizon(s) | `variant_budget` | `family_budget` (family) |
   |---|---|---|---|---|---|
   | day_of_week | `day_of_week_effect` | existing `day_of_week` member (DK-P01: no new build) | 30m | 1 | 4 (flow-seasonality) |
   | opex | `opex_pinning` | `is_opex_day_flag` / `is_quad_witch_day_flag` (DK-P01) | 30m | 1 | 6 (event-calendar) |
   | month_end | `month_end_flow` | `is_month_end_session_flag` / `is_quarter_end_session_flag` (DK-P01) | 30m | 1 | 6 (event-calendar) |
   | roll_week | `roll_week_flow` | `in_roll_window_flag` (DK-P01) | 30m | 1 | 4 (flow-seasonality) |
   | open_close | `open_close_auction_flow` | existing open/close members (DK-P01: no new build) | 5m, 30m | 2 | 4 (flow-seasonality) |

2. **Minimal declared-conditioning-factor admission** in the surrogate calibration path so that an
   **explicitly-declared** calendar-conditioning factor is admitted as the factor-under-test where
   `session_calendar_*` is otherwise skipped as support. The change must:
   - admit **only** a feature family the StudySpec **explicitly declares** as the conditioning
     factor (e.g. an opt-in `declared_conditioning_feature_family` field on the surrogate scope, or
     equivalent explicit declaration the StudySpec carries) — never blanket-admit `session_calendar_*`;
   - **NOT weaken** `_support_feature_family` / `SUPPORT_FEATURE_FAMILIES` for any other
     (incidentally-present, non-declared) `session_calendar_*` lock;
   - preserve the `runtime_factor_id_mismatch` identity: the staged calibration `factor_id` MUST
     equal `study_config_for_surrogate_scope(...).factor_id`;
   - preserve **every** other gate (no-lookahead/`available_ts`, parity, zero-pass,
     constant-factor / all-null exclusion);
   - be **mutation-tested** (a test that fails if the admission is widened to accept a
     *non-declared* support family, and a test that fails if the support rule is otherwise weakened).
3. **Run the surrogate-FDR zero-pass calibration** per StudySpec via
   `tools/discovery_rigor_floor/run_real_surrogate_calibration.py` with **`label_shuffle` +
   `trade_date_block`** nulls, **K pre-registered** on the StudySpec/runbook (`--runs-per-config`),
   a non-negative `--base-seed`, and `--report-out` pointing at a **FRESH value-free directory**
   under `research/differentiated_substrate_v1/**` (NOT under any registry path nor
   `research/futures_substrate_scaleout_v1` / `research/futures_core_alpha_pilot_v1` — the
   `_FORBIDDEN_REPO_NAMESPACE_ROOTS`). Gate each study on **`ZERO_PASS_MET`** (the literal
   `"zero-pass-met"`). **ANY** shuffled statistic pass ⇒ `LEAKAGE_BLOCKED` ⇒ **diagnose FIRST**
   (document the root cause, full autonomy), do **not** proceed.
4. **Tests** under `tests/**` covering: the five StudySpecs validate + resolver-smoke lock; the
   declared-conditioning-factor admission is minimal and mutation-tested (admits only the declared
   family, support rule otherwise intact, `factor_id` identity preserved); the calibration path
   reaches `ZERO_PASS_MET` on a synthetic/fixture study and emits a **value-free** report; the
   report namespace rejects a forbidden root.

## Non-Goals

- Inspecting any **real-data IC / return / diagnostic value** — that is DK-P03. Calibration reports
  here are **value-free** (ids / run-counts / seeds / gate outcomes only).
- Any **per-instrument split** (ES/NQ/RTY pooled as one test), any **horizon sweep** beyond the
  card's pre-registered horizon(s), any **grid**.
- Any **new ledger or FDR object**; any `BudgetAmendmentRecord` (strictly-increasing — cannot
  encode the downward re-scope); re-authoring the DK-P00 FDR restatement.
- Editing `SINGLE_FACTOR_THRESHOLD_TEMPLATE`, `StudyConfig` core, the value engine
  (`core/value_store.py`), or the SSRL/Track B engines; any external date feed; any new paid data
  (`fomc`/`cpi` stay DEFERRED).
- Weakening `_support_feature_family` for non-declared families, or any gate
  (parity / no-lookahead / zero-pass / constant / all-null).
- Emitting any verdict, promotion, FactorLibrary/AlphaBook entry, or alpha/tradability claim.

## Expected Files (illustrative, not prescriptive)

- `research/differentiated_substrate_v1/study_specs/day_of_week.json` — new (locked StudySpec)
- `research/differentiated_substrate_v1/study_specs/opex.json` — new
- `research/differentiated_substrate_v1/study_specs/month_end.json` — new
- `research/differentiated_substrate_v1/study_specs/roll_week.json` — new
- `research/differentiated_substrate_v1/study_specs/open_close.json` — new
- `research/differentiated_substrate_v1/surrogate_fdr/<mechanism>_calibration.md` — new, **value-free**
  calibration reports (fresh isolated dir; ids / run-counts / seeds / gate outcomes only)
- `research/differentiated_substrate_v1/study_specs/RUNBOOK.md` (or similar) — new, records the
  pre-registered **K**, seeds, and exact CLI invocations per study
- `tools/discovery_rigor_floor/run_real_surrogate_calibration.py` — edit (minimal declared-conditioning
  admission; support rule otherwise unchanged)
- `src/alpha_system/governance/surrogate_run.py` and/or
  `src/alpha_system/governance/study_spec.py` — edit **only if** the explicit conditioning-family
  declaration must be carried on the surrogate scope / StudySpec contract (additive field;
  `factor_id` identity preserved)
- `src/alpha_system/runtime/**` — edit only if the runtime factor-id construction needs the additive
  declared-conditioning field threaded (no single-factor-template change)
- `tests/.../test_dk_studyspecs.py`, `tests/.../test_declared_conditioning_admission.py`,
  `tests/.../test_surrogate_zero_pass_value_free.py` — new

## Interfaces / Contracts

- **StudySpec contract.** Each Track A StudySpec is built/validated via `create_study_spec` /
  `validate_study_spec` (`governance/study_spec.py`), carries a positive bounded-integer
  `variant_budget` = horizon count, an optional `family_budget` (6 / 4 per family), and a
  `dataset_scope` with feature/label pack locks plus the `surrogate_fdr` sub-scope that
  `study_config_for_surrogate_scope` reads.
- **Declared-conditioning admission.** The admission accepts a feature family **only** when the
  StudySpec **explicitly declares** it as the conditioning factor-under-test (an opt-in declaration
  the spec carries); `_support_feature_family` / `SUPPORT_FEATURE_FAMILIES` are otherwise unchanged.
  The admitted family yields exactly one non-support declared family for `_declared_feature_family`
  (no `declared_factor_family_missing` / `declared_factor_family_ambiguous`).
- **factor_id identity (HARD).** The staged calibration `factor_id` MUST equal
  `study_config_for_surrogate_scope(study_spec, scope=..., seed=..., shuffled_labels_path=...,
  output_dir=...).factor_id`; a mismatch raises `runtime_factor_id_mismatch`. The admission must not
  alter this construction path.
- **Calibration CLI (per study).**
  ```bash
  python tools/discovery_rigor_floor/run_real_surrogate_calibration.py \
      --study-spec research/differentiated_substrate_v1/study_specs/<mechanism>.json \
      --alpha-data-root <LOCAL_DATA_ROOT> \
      --namespace <ISOLATED_SCRATCH_NAMESPACE> \
      --runs-per-config <K> \
      --base-seed <NON_NEGATIVE_SEED> \
      --report-out research/differentiated_substrate_v1/surrogate_fdr/<mechanism>_calibration.md
  ```
  Perturbations include `label_shuffle` + `trade_date_block` nulls. The `--report-out` path resolves
  through `require_isolated_namespace` and is rejected if it lands under any
  `_FORBIDDEN_REPO_NAMESPACE_ROOTS` entry.
- **Gate.** `SurrogateCalibrationReport.accepted` is `True` iff `threshold_verdict == ZERO_PASS_MET`
  (`"zero-pass-met"`). The phase done-state requires `ZERO_PASS_MET` for **every** study; any
  `LEAKAGE_BLOCKED` blocks progression and triggers diagnosis FIRST.
- **Value-free reports.** Reports carry ids / run-counts / seeds / gate outcomes only — **no** IC,
  return, or diagnostic value (rendered by `render_value_free_calibration_report` /
  `write_value_free_calibration_report`).

## Forbidden Changes

- Editing any path under `forbidden_paths` (`execution/`, `broker/`, `live/`, `portfolio/`,
  `management/`, `backtest/`, `l2/`, `agent_factory/`, `core/value_store.py`,
  `strategies/templates.py`, `research/futures_substrate_scaleout_v1/**`,
  `research/futures_core_alpha_pilot_v1/**`, all `data/**`, any
  `*.sqlite`/`*.db`/`*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`).
- Modifying `SINGLE_FACTOR_THRESHOLD_TEMPLATE`, the `StudyConfig.factor_id` construction, or the
  value engine; weakening `_support_feature_family` / `SUPPORT_FEATURE_FAMILIES` for any
  **non-declared** family; widening the admission to accept any `session_calendar_*` family that the
  StudySpec did not explicitly declare as the conditioning factor.
- **Inspecting, recording, or rendering any real-data IC / return / diagnostic value** in this phase
  (that is DK-P03); writing a non-value-free calibration report.
- Writing `--report-out` (or any calibration artifact) under a `_FORBIDDEN_REPO_NAMESPACE_ROOTS`
  entry (`registry/`, `metadata/`, `data/raw`, `data/canonical`, `artifacts/`, `runs/`,
  `research/futures_core_alpha_pilot_v1`, `research/futures_substrate_scaleout_v1`).
- Proceeding past a `LEAKAGE_BLOCKED` result without diagnosing the leak first.
- Importing `backtest`/`management`/`fast_path`/`value_store` from `research/`; creating a second
  PnL truth.
- Encoding the FDR downward re-scope as a `BudgetAmendmentRecord` (strictly-increasing — invalid for
  a downward restatement); re-creating the DK-P00 restatement.
- Adding a runtime dependency (`numpy`/`pandas`/`polars`); new paid data; secrets/credentials; raw /
  canonical / factor / label data, caches, DB/Parquet artifacts.
- `git add .`, `git add -A`, force push, auto-merge, deployment, PR creation, or any broker/live call.
- Weakening, skipping, or adding visible test-only branches to existing tests / checks / canaries.

## Validation

Run from the repo root. All commands are local-only and make **no** provider, network, merge, or
external calls. Run the narrowest meaningful tests first, then broaden.

```bash
# 1) Narrowest meaningful tests — StudySpecs, admission, surrogate zero-pass, budgets.
python -m pytest tests -k "study_spec or surrogate or variant_ledger or family_budget or calibrat" -q

# 2) Mutation check intent: the admission must FAIL closed if widened to a non-declared support
#    family, and the support rule must stay intact otherwise (asserted by the new admission tests).

# 3) Repo smoke.
python tools/verify.py --smoke

# 4) Safety canaries must remain all-PASS (planted_fake_alpha + true-alpha pair,
#    forbidden_second_pnl_truth, forbidden_exploratory_promotion, governance_random_target,
#    forbidden_scope_drift).
python tools/hooks/canary_runner.py

# 5) Per-study surrogate-FDR calibration — value-free report into a FRESH isolated dir.
#    Repeat for each of: day_of_week, opex, month_end, roll_week, open_close.
python tools/discovery_rigor_floor/run_real_surrogate_calibration.py \
    --study-spec research/differentiated_substrate_v1/study_specs/<mechanism>.json \
    --alpha-data-root <LOCAL_DATA_ROOT> \
    --namespace <ISOLATED_SCRATCH_NAMESPACE> \
    --runs-per-config <K> --base-seed <SEED> \
    --report-out research/differentiated_substrate_v1/surrogate_fdr/<mechanism>_calibration.md
#    Gate: every report's threshold_verdict == "zero-pass-met" (ZERO_PASS_MET). ANY pass => LEAKAGE_BLOCKED.

# 6) Report-namespace discipline: reports must NOT land under a forbidden root.
git ls-files research/differentiated_substrate_v1/surrogate_fdr | grep -E "futures_(core_alpha_pilot|substrate_scaleout)_v1|registry|metadata|artifacts|/runs/" && echo "FORBIDDEN NAMESPACE" && exit 1 || echo "namespace ok"

# 7) No research->sim bridge: research/ must not import backtest/management/fast_path/value_store.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" --include=*.py src/alpha_system/research && echo "FORBIDDEN IMPORT" && exit 1 || echo "research import-clean"

# 8) No new dependency: numpy/pandas/polars must remain unimportable.
python -c "import importlib.util,sys; bad=[m for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]; sys.exit('forbidden dependency importable: '+','.join(bad) if bad else 0)"

# 9) Single-factor path byte-unchanged.
git diff -- src/alpha_system/strategies/templates.py

# 10) Run-artifact discipline: must print nothing.
git ls-files runs
```

Broaden to `python tools/verify.py --all` if shared governance / surrogate / runtime behavior
appears affected; run it in a clean shell with `FRONTIER_*` env unset to avoid the known driver-env
false negative. Record any skipped check and its reason in the handoff.

## Artifact Policy

Run artifacts are local-only and must never be committed:

- `runs/**` is **local-only runtime state**; `run_dir` artifacts are for local audit/resume only.
- The run-local `handoff.md` / `review.md` / `verdict.json` under `runs/<run_id>/...` must **never**
  be staged.
- A commit-eligible handoff goes under `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P02.md`.
- Commit-eligible: Track A StudySpecs, the declared-conditioning-factor admission, **value-free**
  surrogate calibration reports, and tests.
- `git ls-files runs` must return empty.
- Never commit: `runs/**`, any `*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`/`*.sqlite`/`*.db`,
  `data/raw/**`, `data/canonical/**`, `secrets/**`, `**/*.key`. The materialized factor/label packs
  the calibration reads remain **local-only and uncommitted**; only the value-free Markdown report
  is staged.

### Allowed Paths (commit-eligible — explicit staging only)

These are the **only** paths this phase may stage and commit. Stage by explicit path; never
`git add .` / `git add -A`; never force push.

- `research/differentiated_substrate_v1/**`
- `src/alpha_system/governance/study_spec.py`
- `src/alpha_system/governance/surrogate_run.py`
- `src/alpha_system/runtime/**`
- `tools/discovery_rigor_floor/**`
- `tests/**`
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P02.md`
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P02/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` (run state, events, costs, STOP, run-local `handoff.md`/`review.md`/`verdict.json`,
  checks, repair attempts) — local audit and resume only. **No `runs/` path appears under Allowed
  Paths above.**

### Allowed Test Paths

- `tests/**` (new `test_dk_studyspecs*` / `test_declared_conditioning_admission*` /
  `test_surrogate_zero_pass*` and any close-by governance/surrogate/runtime tests). Do not weaken or
  skip existing tests; do not add visible test-only special cases.

## Done Criteria

- **Five Track A StudySpecs** authored under `research/differentiated_substrate_v1/study_specs/`
  (`day_of_week`, `opex`, `month_end`, `roll_week`, `open_close`), each declaring the calendar flag
  as the conditioning factor-under-test, pooled ES/NQ/RTY, with forward-return labels at the card's
  pre-registered horizon(s), `variant_budget` = horizon count (1,1,1,1,2), and `family_budget` per
  the restatement (event-calendar 6, flow-seasonality 4); **resolver-smoke green** (pack/label
  resolutions locked).
- The **declared-conditioning-factor admission** is minimal, admits **only** an explicitly-declared
  conditioning family, does **not** weaken `_support_feature_family` otherwise, preserves the
  `factor_id` identity (`runtime_factor_id_mismatch` intact) and every other gate, and is
  **mutation-tested**.
- **Surrogate-FDR zero-pass calibration** run per StudySpec with `label_shuffle` + `trade_date_block`
  nulls at the pre-registered **K**; **`ZERO_PASS_MET` for every study**; any `LEAKAGE_BLOCKED`
  diagnosed FIRST (not proceeded past). Reports are **value-free** (ids / run-counts / seeds / gate
  outcomes only) in a **fresh isolated dir** outside every `_FORBIDDEN_REPO_NAMESPACE_ROOTS`.
- **No real-data IC / return / diagnostic value inspected** in this phase.
- `python tools/hooks/canary_runner.py` all-PASS; `numpy`/`pandas`/`polars` remain unimportable; no
  new paid data; `research/` imports no `backtest`/`management`/`fast_path`/`value_store`;
  single-factor path + value engine byte-unchanged.
- `git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write the commit-eligible handoff at `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P02.md`: scope
delivered; the five StudySpecs by path with their declared conditioning factor / horizon(s) /
`variant_budget` / `family_budget`; the resolver-smoke result; the exact admission change and the
mutation-test evidence (admits only the declared family, support rule otherwise intact,
`factor_id` identity preserved); the exact per-study calibration CLI invocations with the
pre-registered **K**, seeds, and report paths; the `ZERO_PASS_MET` outcome per study (and any
`LEAKAGE_BLOCKED` diagnosis); confirmation that (a) no real-data metric was inspected, (b) reports
are value-free and outside every forbidden namespace, (c) the single-factor path + value engine are
byte-unchanged, (d) `research/` imports no second-PnL-truth module, and (e) `numpy`/`pandas`/`polars`
stay unimportable. Record any skipped check and its reason. The run-local `runs/<run_id>/.../handoff.md`
stays local-only and must not be staged.

## Review Requirements

YELLOW lane requires a fresh Claude Opus review. Commit-eligible review notes + verdict belong under
`reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P02/**`; run-local `review.md`/`verdict.json` stay under
`runs/<run_id>/...` and are not committed. The reviewer must adversarially confirm: the five
StudySpecs declare the calendar flag as the conditioning factor (pooled ES/NQ/RTY, correct
horizons/budgets) and lock real pack/label resolutions; the **admission is minimal** — it admits
**only** an explicitly-declared conditioning family and does **not** weaken `_support_feature_family`
for any non-declared `session_calendar_*` family (mutation tests prove both); the `factor_id` identity
(`runtime_factor_id_mismatch`) and all gates (no-lookahead, parity, zero-pass, constant/all-null)
are intact; **every** study reaches `ZERO_PASS_MET` with reports that are **value-free** and live in
a **fresh isolated dir** outside every `_FORBIDDEN_REPO_NAMESPACE_ROOTS`; **no real-data metric was
inspected**; the FDR re-scope is the carried value-free note (not a `BudgetAmendmentRecord`); the
single-factor path + value engine are byte-unchanged; `research/` imports no
`backtest`/`management`/`fast_path`/`value_store`; no new dependency / paid data; no promotion or
alpha/tradability claim; artifact + staging discipline honored.

## Auto-Merge / Review Policy

This spec authorizes no PR creation, no auto-merge, and no deployment. Merge gating is the Ralph
driver's responsibility under the YELLOW lane policy (review required; block on critical /
test-tamper / boundary violation / any `LEAKAGE_BLOCKED` or non-value-free report) and human
authorization — not this spec.

## Repair-or-Rollback

- **In-scope repair only:** fix StudySpec/admission/calibration or test issues within the Allowed
  Paths; do not expand scope to fix unrelated findings.
- **LEAKAGE_BLOCKED:** if any shuffled statistic passes, the calibration is `LEAKAGE_BLOCKED` —
  **diagnose the leak FIRST** (document root cause; full autonomy within scope), do not proceed to
  any real-data metric, and surface the diagnosis. Do not relax the gate to force `ZERO_PASS_MET`.
- **Rollback:** the change is additive and pure-Python; revert the five StudySpecs, the
  declared-conditioning admission edit, the value-free calibration reports, and the new tests to
  restore the prior state with no migration and no data change.
- **STOP / escalate (do not auto-proceed):** any pressure to inspect a real-data metric before
  `ZERO_PASS_MET`, widen the admission to non-declared `session_calendar_*` families, weaken
  `_support_feature_family` / any gate, encode the downward FDR re-scope as a `BudgetAmendmentRecord`,
  write a non-value-free report or a report under a forbidden namespace, modify the single-factor
  path or value engine, add a dependency or paid data, or commit a `runs/`/data/secret artifact —
  treat as out-of-scope and surface to the user.
