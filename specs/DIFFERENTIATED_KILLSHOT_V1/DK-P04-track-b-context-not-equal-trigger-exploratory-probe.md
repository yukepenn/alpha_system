# DK-P04 — Track B Context≠Trigger SetupSpec EXPLORATORY Conditional Probe (Real Slice)

---
campaign_id: DIFFERENTIATED_KILLSHOT_V1
phase_id: DK-P04
lane: YELLOW
status: draft
dependencies: [DK-P03]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Exercise the just-completed SSRL strategy-shaped capability on a **DIFFERENTIATED** idea: author
**one** `SetupSpec` whose **context** (the regime/setup that makes the idea relevant) and
**trigger** (the event that fires the entry) are **genuinely distinct signals** (different
`factor_id` **and** different underlying signal — invariant **C1**), and run it as a bounded,
**EXPLORATORY**, variant-ledgered, surrogate-FDR + power-qualified **conditional probe** over
**MATERIALIZED path labels**. The probe must produce real value-free evidence **or** an honest
`DATA_GAP`, and can **never** be promotion evidence. The SSRL engine
(`research/conditional_probe.py`, `governance/setup_spec.py`, `governance/mechanism_card.py`) is
**USED byte-unchanged**; this phase adds only a new `MechanismCard`/`SetupSpec` JSON pair, a
`tools/`-side row-injection harness, a value-free `EVIDENCE.json`, and tests. No engine edit, no
promotion, no `PromotionDecision`, no alpha/tradability claim.

## Context

This is the single Track B phase of `DIFFERENTIATED_KILLSHOT_V1`. Track A (DK-P01..DK-P03) is
logically independent and already merged; this run keeps the DAG linear for merge-safety. DK-P04
reuses, byte-unchanged, the capability landed by `STRATEGY_SHAPED_RESEARCH_LANE_V0`:

- **Conditional probe engine (USED, not edited):**
  `src/alpha_system/research/conditional_probe.py` —
  `evaluate_setup_conditional_probe(setup_spec, *, context_factor_values, trigger_factor_values,
  path_labels, family_id, family_budget, surrogate_run_count, variant_id=..., surrogate_gate_pass_count=0,
  surrogate_error_count=0, ...)` (def at line 313). It compiles the SetupSpec
  (`compile_setup_spec_to_conditional_probe`), and the compiler **fails closed at compile time** when
  `context.factor_id == trigger.factor_id` (line ~183), then builds the path-label observation set,
  **requires** a surrogate `ZERO_PASS_MET` gate (`_require_zero_pass_surrogate_gate`, raising
  `ConditionalProbeError` otherwise — line ~664), **requires** the family-budget check to be
  `RESPECTED` (raising `ConditionalProbeError` otherwise — line ~357), and emits diagnostics
  `target_before_stop_probability` + `post_event_mfe_mae`, a `variant_ledger_binding`, a
  `surrogate_fdr_gate`, a per-factor `power` statement (`build_ic_power_statement` /
  `minimum_detectable_abs_ic`), `stamp = EXPLORATORY`, and `promotion_eligible = False`.
- **Governance declaration objects (USED, edits additive-only):**
  `governance/setup_spec.py` — `create_setup_spec(...)` (line 157), fields `entry_context`,
  `event_trigger`, `path_label` (an `lspec_*`/`lset_*` `LABEL_SPEC` governance id). Distinctness is
  enforced by `_validate_event_trigger_is_separate` (line 299): the validator only checks **declared**
  distinctness (alias / canonical-content / declared-derivation), **not** numeric identity — so C1 is
  the **author's responsibility**. `governance/mechanism_card.py` — `create_mechanism_card(...)`
  (line 151), `EXPLORATORY_STAMP = "EXPLORATORY"` (line 29).
- **Honest-gap + de-stack helpers (USED):** `research/first_light.py` —
  `build_first_light_data_gap_evidence(...)` (line 195, the `status=INCONCLUSIVE` /
  `issue_code="DATA_GAP"` pattern); the SSRL first-light EVIDENCE shape lives at
  `research/strategy_shaped_lane_v0/first_light/EVIDENCE.json`.
- **EXPLORATORY quarantine (USED):** `governance/promotion.py` —
  `reject_exploratory_promotion_artifact(...)` (line 386) fails closed on any EXPLORATORY-stamped
  artifact; the `forbidden_exploratory_promotion` canary asserts it. `governance/trusted_handoff.py` —
  `create_trusted_handoff_gap_report(probe_artifact)` (line 125) is a **checklist scaffold only**, not
  evidence.
- **Sanctioned value loader (tools/runtime-only):** `core/value_store.load_parquet_values(path)`
  (line 116) lives **outside** `research/`; the harness calls it and **injects** the resulting rows
  into the pure research probe. `research/` imports it **never**.

**Global hard invariants relevant to this phase (state and obey):**

- **FDR before metric.** No real-data metric is inspected before (a) the DK-P00 FDR active-subset
  restatement note exists (value-free pre-registration, predating any variant) **and** (b) the
  surrogate label-shuffle calibration for THIS probe yields `ZERO_PASS_MET`
  (`run_count > 0`, `gate_pass_count = 0`, `error_count = 0`). The downward FDR re-scope is a value-free
  pre-registration **NOTE**, **not** a `BudgetAmendmentRecord` (`create_budget_amendment_record`
  enforces `new_budget > prior_budget` — strictly increasing — so it cannot encode a downward
  restatement).
- **EXPLORATORY ≠ promotion.** Track B output can **never** be promotion evidence; the
  trusted/promotion path **refuses** EXPLORATORY-stamped artifacts (`reject_exploratory_promotion_artifact`
  + `forbidden_exploratory_promotion` canary). The readout stays **permanently EXPLORATORY**.
- **No research→reference-sim bridge.** `research/` imports **zero** `backtest`/`management`/
  `fast_path`/`value_store`; outcomes come **only** from materialized path labels; values are loaded by
  `tools/`/`runtime/` (`core/value_store.load_parquet_values`) and **INJECTED** into the pure probe.
  No second PnL truth.
- **Single-factor path byte-unchanged.** `SINGLE_FACTOR_THRESHOLD_TEMPLATE` and the conditional-probe
  engine are byte-unchanged; new work is strictly additive; all canaries + parity + no-lookahead +
  roll/maintenance fail-closed + surrogate zero-pass stay intact.
- **C1 / C2 / C3 disciplines.** C1: context and trigger are genuinely distinct signals (different
  `factor_id` AND different underlying signal). **C2:** SSRL first-light is an honest `DATA_GAP`, **NOT**
  real ES_2024 evidence — it may not be cited as a result; if rows do not resolve, record `DATA_GAP`,
  do **not** fabricate values. **C3:** the de-stack `ic = 0.068 / n = 6862`
  (`research/first_light.py` `DE_STACK_ISOLATED_IC` / `DE_STACK_OBSERVATION_COUNT`) is a carried
  SHIP_REFIT restatement, **NOT** fresh corroboration — do not cite it as new evidence here.
- **No new dependency / no paid data.** `numpy`/`pandas`/`polars` stay unimportable; fomc/cpi remain
  DEFERRED; `git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.
- **Allowed outputs only.** REJECT / INCONCLUSIVE+reason_code / WATCH / CANDIDATE_RESEARCH.
  Research-only language; no alpha/tradability/profitability claim; no promotion.

## Scope

1. **Author one differentiated context≠trigger MechanismCard + EXPLORATORY SetupSpec.** Via
   `create_mechanism_card(...)` and `create_setup_spec(...)`, declare:
   - `entry_context` = a range-contraction / regime **CONTEXT** predicate (e.g. a
     `liquidity_structure` range-contraction factor), and `event_trigger` = a **SEPARATE**
     prior-high-sweep-then-reclaim **TRIGGER** factor. They must have **different `factor_id`** **and**
     a different underlying signal (C1; the author owns genuine distinctness — the validator and the
     compile-time `context.factor_id == trigger.factor_id` check only verify *declared* distinctness,
     not numeric identity).
   - Each predicate dict carries `{factor_id, factor_version, value_field ∈ {value, normalized_value},
     operator ∈ {>, >=, <, <=, ==, !=}, threshold}`.
   - `path_label` = an `lspec_*` / `lset_*` governance id of an **already-materialized** path label
     whose outcome is target-before-stop; **hold ≤ 120m**; `stamp = EXPLORATORY`.
   - Persist the `MechanismCard` + `SetupSpec` as JSON under
     `research/differentiated_substrate_v1/track_b/`.
2. **Wire a `tools/` row-injection harness (NOT in `research/`).** It must:
   - Load the materialized **context** factor rows, **trigger** factor rows, and **path-label** outcome
     rows via `core/value_store.load_parquet_values(...)` (tools/runtime-only; `research/` stays
     import-clean).
   - Run a **label-shuffle surrogate calibration** (the existing surrogate path,
     `tools/discovery_rigor_floor/run_real_surrogate_calibration.py` semantics) to obtain the gate
     inputs: `surrogate_run_count > 0`, `surrogate_gate_pass_count = 0`, `surrogate_error_count = 0`
     ⇒ `ZERO_PASS_MET`. ANY shuffled pass ⇒ block and diagnose first; do not proceed.
   - Call `evaluate_setup_conditional_probe(setup, context_factor_values=..., trigger_factor_values=...,
     path_labels=..., family_id=..., family_budget=..., surrogate_run_count=..., variant_id=...,
     surrogate_gate_pass_count=0, surrogate_error_count=0)` with the **injected** rows. The surrogate
     `ZERO_PASS_MET` gate and the family-budget `RESPECTED` check are **HARD preconditions inside
     `evaluate`** (it raises `ConditionalProbeError` otherwise) — the harness must satisfy them, never
     bypass them.
   - Respect the family/variant budget (`bind_probe_variant_budget`); record `N_eff` / power / MDE.
3. **Persist a value-free `EVIDENCE.json`.** Write
   `research/differentiated_substrate_v1/track_b/EVIDENCE.json` mirroring
   `research/strategy_shaped_lane_v0/first_light/EVIDENCE.json`: `stamp: "EXPLORATORY"`,
   `promotion_eligible: false`, `outcome_source: "materialized_path_labels"`, observation/manifest
   counts, diagnostics `target_before_stop_probability` + `post_event_mfe_mae`, `variant_ledger_binding`,
   `surrogate_fdr_gate`, and `power`. The JSON is **value-free** in the sense that it carries only
   ids/counts/seeds/gate outcomes/diagnostics summaries — no raw rows, no PnL, no parquet, no registry,
   and never under a FUTSUB / core-pilot namespace.
4. **Honest `DATA_GAP` fallback (C2).** If **no** sanctioned reader path resolves real rows, record
   `status = INCONCLUSIVE` / `issue_code = "DATA_GAP"` via the `build_first_light_data_gap_evidence`
   pattern (manifest-state present, `surrogate_fdr_gate` `BLOCKED`, `power` `n_eff = 0`). **Do NOT
   fabricate values.**
5. **Trusted-handoff gap report (only if promising, checklist-only).** If the readout is promising, emit
   a `create_trusted_handoff_gap_report(probe_artifact)` checklist under `track_b/` — a scaffold of the
   trusted-lane objects that would be required, **not** evidence and **not** a promotion. No
   `PromotionDecision`, no FactorLibrary/AlphaBook entry.
6. **Tests** under `tests/**`: the SetupSpec compiles with genuinely distinct context vs trigger;
   `context.factor_id == trigger.factor_id` is rejected at compile time; the harness injects rows and
   the probe returns an EXPLORATORY readout with `promotion_eligible = False`, a `ZERO_PASS_MET`
   `surrogate_fdr_gate`, a `RESPECTED` family-budget binding, and a per-factor power statement;
   `reject_exploratory_promotion_artifact` refuses the EVIDENCE artifact; the `DATA_GAP` fallback path
   yields `status = INCONCLUSIVE` / `issue_code = "DATA_GAP"` with no fabricated values; and `research/`
   imports none of `backtest`/`management`/`fast_path`/`value_store`.

## Non-Goals

- Editing `research/conditional_probe.py` or any SSRL engine module — it is **USED byte-unchanged**
  (only NEW SetupSpec/MechanismCard JSON, the `tools/` harness, the EVIDENCE.json, and tests are added).
- Any **promotion**, `PromotionDecision`, FactorLibrary entry, AlphaBook / Strategy-Reference, or
  paper/live/broker behavior; any path that lets EXPLORATORY output become promotion evidence.
- Citing the SSRL first-light `EVIDENCE.json` as a real ES_2024 **result** (C2), or citing the de-stack
  `ic = 0.068 / n = 6862` as **fresh corroboration** (C3).
- Any **multi-bar sequence** state machine, target/stop **geometry** sweep, horizon sweep,
  per-instrument split, or any new ledger/FDR object.
- Any **research→reference-sim bridge**: no `backtest`/`management`/`fast_path`/`value_store` import
  from `research/`; no second PnL truth.
- Adding any runtime dependency (`numpy`/`pandas`/`polars` stay unimportable); any new paid data
  (fomc/cpi DEFERRED); any edit to the single-factor template, the value engine, or FUTSUB / core-pilot
  research artifacts.
- Any real-data **value** in any committed artifact beyond the value-free EVIDENCE diagnostics summary
  (no raw rows, no parquet, no registry, no DB).

## Expected Files (illustrative, not prescriptive)

NEW (added; value-free, no implementation code in this spec):

- `research/differentiated_substrate_v1/track_b/mechanism_card.json` — the EXPLORATORY `MechanismCard`
  (`create_mechanism_card(...)`, substantive rationale/expected_mechanism, `variant_budget`, stamp `EXPLORATORY`).
- `research/differentiated_substrate_v1/track_b/setup_spec.json` — the EXPLORATORY `SetupSpec` with
  **genuinely distinct** `entry_context` vs `event_trigger` signals (different `factor_id` AND different
  underlying signal), `path_label = lspec_…`, hold ≤ 120m, stamp `EXPLORATORY`.
- `research/differentiated_substrate_v1/track_b/EVIDENCE.json` — value-free `ConditionalProbeReadout`
  (stamp `EXPLORATORY`, `promotion_eligible:false`, observation_counts, diagnostics, variant binding,
  surrogate_fdr_gate, power) **or** an honest `status:INCONCLUSIVE / issue_code:DATA_GAP` (no fabricated values).
- `tools/…` — the `tools/runtime` row-injection probe harness (loads rows via
  `core.value_store.load_parquet_values`, runs the label-shuffle surrogate for `ZERO_PASS_MET`, then calls
  `evaluate_setup_conditional_probe` with the injected rows). Lives OUTSIDE `research/`.
- `tests/…` — tests for the harness, the SetupSpec context≠trigger distinctness, and the EXPLORATORY
  promotion-refusal.
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P04.md` — the commit-eligible handoff.

USED byte-unchanged (NOT edited): `src/alpha_system/research/conditional_probe.py`,
`src/alpha_system/governance/setup_spec.py`, `src/alpha_system/governance/mechanism_card.py`.

## Interfaces / Contracts

- **MechanismCard / SetupSpec authoring:** `create_mechanism_card(...)` and `create_setup_spec(...,
  entry_context={...}, event_trigger={...}, path_label="lspec_…|lset_…", stamp=EXPLORATORY_STAMP)`.
  Each predicate dict is `{factor_id, factor_version, value_field ∈ {value, normalized_value},
  operator ∈ {>, >=, <, <=, ==, !=}, threshold}`. C1 distinctness is the author's responsibility;
  `_validate_event_trigger_is_separate` + the compile-time `context.factor_id == trigger.factor_id`
  check verify only declared distinctness.
- **Probe call (engine byte-unchanged):**
  `evaluate_setup_conditional_probe(setup, context_factor_values=<injected>,
  trigger_factor_values=<injected>, path_labels=<injected>, family_id=…, family_budget=…,
  surrogate_run_count=>0, variant_id=…, surrogate_gate_pass_count=0, surrogate_error_count=0)`.
  Preconditions enforced **inside** `evaluate`: surrogate gate `ZERO_PASS_MET`
  (`_require_zero_pass_surrogate_gate`) and family-budget `RESPECTED` — both raise
  `ConditionalProbeError` if unmet. The returned `ConditionalProbeReadout` has `stamp = EXPLORATORY`,
  `promotion_eligible = False`, diagnostics `target_before_stop_probability` + `post_event_mfe_mae`,
  `variant_ledger_binding`, `surrogate_fdr_gate`, `power`.
- **Row injection boundary:** the `tools/` harness calls
  `core/value_store.load_parquet_values(path)` and passes the resulting `list[dict]` as
  `context_factor_values` / `trigger_factor_values` / `path_labels`. `research/` never sees a path,
  a loader, or a parquet; it sees only injected in-memory rows.
- **EVIDENCE.json contract:** keys mirror the SSRL first-light EVIDENCE
  (`stamp`, `status`, `issue_code`, `promotion_eligible`, `outcome_source`, `surrogate_fdr_gate`,
  `power`, `manifest_state`/`row_access`, `setup_spec`, `mechanism_card`, `compiled_probe`,
  `variant_id`, `family_id`, `family_budget`, `created_at`, `evidence_id`, `schema`). Value-free:
  ids/counts/seeds/gate outcomes/diagnostics summaries only.
- **Quarantine contract:** `reject_exploratory_promotion_artifact(EVIDENCE)` must raise; the
  `forbidden_exploratory_promotion` canary must stay green and **fail** if the guard is bypassed.
- **DATA_GAP contract:** `build_first_light_data_gap_evidence(...)` shape with
  `status = "INCONCLUSIVE"`, `issue_code = "DATA_GAP"`, `surrogate_fdr_gate.gate_status = "BLOCKED"`,
  `power.n_eff = 0`, no fabricated values.

## Forbidden Changes

- Editing `src/alpha_system/research/conditional_probe.py` or any SSRL engine module
  (`setup_spec.py` / `mechanism_card.py` edits, if any, are additive helpers only and must keep the
  engine semantics byte-unchanged). The single-factor path (`strategies/templates.py`,
  `SINGLE_FACTOR_THRESHOLD_TEMPLATE`) stays **byte-unchanged**.
- Editing any path under `forbidden_paths` (`execution/`, `broker/`, `live/`, `portfolio/`,
  `management/`, `backtest/`, `l2/`, `agent_factory/`, `core/value_store.py`,
  `strategies/templates.py`, `research/futures_substrate_scaleout_v1/**`,
  `research/futures_core_alpha_pilot_v1/**`, all `data/**`, any
  `*.sqlite`/`*.db`/`*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`).
- Importing `backtest` / `management` / `fast_path` / `value_store` from `research/`; creating a
  research→reference-sim bridge or a second PnL truth.
- Encoding the downward FDR re-scope as a `BudgetAmendmentRecord` (strictly increasing; cannot encode a
  downward restatement) — it is a value-free pre-registration NOTE only.
- Letting any EXPLORATORY artifact reach the trusted/promotion path; emitting a `PromotionDecision`, a
  FactorLibrary/AlphaBook entry, or any promotion; flipping `promotion_eligible` to `true`.
- Fabricating any real-data value when rows do not resolve (C2); citing first-light EVIDENCE as a real
  result (C2) or the de-stack `0.068/6862` as fresh corroboration (C3).
- Adding a runtime dependency (`numpy`/`pandas`/`polars`); new paid data (fomc/cpi); secrets/credentials;
  raw/canonical/factor/label data, caches, model binaries, large artifacts.
- `git add .`, `git add -A`, force push, auto-merge, deployment, PR creation, or any broker/live call.
- Weakening, skipping, or adding visible test-only branches to existing tests/checks/canaries.

## Validation

Run from the repo root. All commands are local-only, safe, and make **no** provider, network, merge,
or external calls.

```bash
# 1) Narrowest meaningful tests first — Track B probe + EXPLORATORY quarantine + DATA_GAP fallback.
python -m pytest tests -k "conditional_probe or setup or exploratory or first_light or handoff" -q

# 2) Repo smoke.
python tools/verify.py --smoke

# 3) Safety canaries must remain all-PASS, including forbidden_exploratory_promotion and
#    forbidden_second_pnl_truth (planted_fake_alpha, true-alpha pair, governance_random_target,
#    forbidden_scope_drift, forbidden_exploratory_promotion, forbidden_second_pnl_truth).
python tools/hooks/canary_runner.py

# 4) No new dependency: numpy/pandas/polars must remain unimportable.
python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"

# 5) No research->sim bridge: research/ must not import backtest/management/fast_path/value_store.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"

# 6) Conditional-probe engine byte-unchanged (review the diff; only JSON/harness/tests added).
git diff -- src/alpha_system/research/conditional_probe.py src/alpha_system/strategies/templates.py

# 7) Run-artifact discipline: must print nothing.
git ls-files runs
```

Broaden to the authoritative suite (`python tools/verify.py --all`) if shared governance, probe, or
diagnostics behavior appears affected; run it in a clean shell with `FRONTIER_*` env unset to avoid
the known driver-env false negative. Record any skipped check and its reason in the handoff.

## Artifact Policy

Run artifacts are local-only and must never be committed:

- `runs/**` is **local-only runtime state** (state, events, costs, STOP, run-local
  `handoff.md`/`review.md`/`verdict.json`, checks, repair attempts) — local audit and resume only.
- A commit-eligible handoff goes under `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P04.md`.
- `git ls-files runs` must return empty.
- Never commit: `runs/**`, any `*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`/`*.sqlite`/`*.db`,
  `data/raw/**`, `data/canonical/**`, `secrets/**`, `**/*.key`. Materialized factor/path-label rows
  loaded by the harness stay **local-only**; only the **value-free** `EVIDENCE.json` and the
  MechanismCard/SetupSpec JSON are committed.

### Allowed Paths (commit-eligible — explicit staging only)

These are the **only** paths this phase may stage and commit. Stage by explicit path; never
`git add .` / `git add -A`; never force push.

- `research/differentiated_substrate_v1/**`
- `src/alpha_system/governance/setup_spec.py`
- `src/alpha_system/governance/mechanism_card.py`
- `tools/**`
- `tests/**`
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P04.md`
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P04/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit and resume only. **No `runs/` path appears under Allowed Paths above.**

Forbidden paths: the campaign-wide `forbidden_paths` list, including `core/value_store.py`,
`strategies/templates.py`, `research/conditional_probe.py` semantics (byte-unchanged), all `data/**`,
`research/futures_substrate_scaleout_v1/**`, `research/futures_core_alpha_pilot_v1/**`, and all
DB/parquet/arrow/feather/dbn/zst artifacts.

## Allowed Test Paths

- `tests/**` (new `test_conditional_probe*` / `test_setup*` / `test_exploratory*` / `test_first_light*`
  / `test_*track_b*` and any close-by governance/research/tools-harness tests). Do not weaken or skip
  existing tests; do not add visible test-only special cases.

## Done Criteria

- One context≠trigger **EXPLORATORY** `SetupSpec` (genuinely distinct signals — different `factor_id`
  AND different underlying signal, **C1**) plus its `MechanismCard` is authored and persisted as JSON
  under `research/differentiated_substrate_v1/track_b/`.
- The SetupSpec is compiled and run over **materialized path labels** via the `tools/` row-injection
  harness (`core/value_store.load_parquet_values` → injected rows → `evaluate_setup_conditional_probe`),
  with the surrogate `ZERO_PASS_MET` gate (`run_count > 0`, `0` passes, `0` errors) and the family-budget
  `RESPECTED` check both satisfied as **hard preconditions inside `evaluate`**.
- `research/differentiated_substrate_v1/track_b/EVIDENCE.json` is **value-free**, `stamp = "EXPLORATORY"`,
  `promotion_eligible: false`, with `surrogate_fdr_gate` + `variant_ledger_binding` + per-factor `power`
  and diagnostics `target_before_stop_probability` + `post_event_mfe_mae` — **or** an honest
  `status = INCONCLUSIVE` / `issue_code = "DATA_GAP"` (no fabricated values, C2) when no row path resolves.
- **Quarantine proven:** `reject_exploratory_promotion_artifact(EVIDENCE)` refuses it and the
  `forbidden_exploratory_promotion` canary stays green (fails if the guard is bypassed).
- `research/conditional_probe.py` and the single-factor template are **byte-unchanged**; `research/`
  imports none of `backtest`/`management`/`fast_path`/`value_store`; the first-light EVIDENCE is **not**
  cited as a real result (C2) and the de-stack `0.068/6862` is **not** cited as fresh corroboration (C3).
- If promising, a `create_trusted_handoff_gap_report` checklist is emitted (scaffold only, not evidence,
  no promotion).
- `python tools/hooks/canary_runner.py` all-PASS; `numpy`/`pandas`/`polars` remain unimportable; no new
  paid data; `git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write the commit-eligible handoff at `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P04.md`: scope delivered,
exact validation commands run with results, any skipped check + reason, files changed by path, and
explicit confirmation that (a) `research/conditional_probe.py` and the single-factor template are
byte-unchanged; (b) `research/` imports no `backtest`/`management`/`fast_path`/`value_store` (the
loader is called from `tools/` and rows are injected); (c) the SetupSpec context and trigger are
genuinely distinct (C1) — name both `factor_id`s and the distinct underlying signals; (d) the
surrogate gate is `ZERO_PASS_MET` and the family-budget is `RESPECTED` (or an honest `DATA_GAP` was
recorded with no fabricated values, C2); (e) the EVIDENCE is value-free, `EXPLORATORY`,
`promotion_eligible: false`, and refused by the promotion path; and (f) neither first-light EVIDENCE
nor the de-stack `0.068/6862` is cited as a fresh result (C2/C3). The run-local
`runs/<run_id>/.../handoff.md` stays local-only and must not be staged.

## Review Requirements

YELLOW lane requires a fresh Claude Opus review. Commit-eligible review notes + verdict belong under
`reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P04/**`; run-local `review.md`/`verdict.json` stay under
`runs/<run_id>/...` and are not committed. The reviewer must adversarially confirm: **C1 genuine
distinctness** (context and trigger are different `factor_id` AND different underlying signals, not a
declared-only dodge); the EXPLORATORY **quarantine** (the EVIDENCE is `EXPLORATORY` /
`promotion_eligible: false` and the trusted/promotion path refuses it, canary fail-closed); the
**no-bridge row injection** (`research/` imports no `backtest`/`management`/`fast_path`/`value_store`;
values come from `core/value_store.load_parquet_values` called in `tools/` and injected); the
**FDR-before-metric** ordering (surrogate `ZERO_PASS_MET` precedes the readout; downward re-scope is a
NOTE, not a `BudgetAmendmentRecord`); the **engine byte-unchanged** claim
(`research/conditional_probe.py` + single-factor template); the **honest DATA_GAP** discipline (no
fabricated values when rows do not resolve, C2); that the de-stack `0.068/6862` is **not** recycled as
fresh corroboration (C3); bounded surface (variant/family budget respected, no sweep); no new
dependency; no promotion / no alpha-or-tradability claim; artifact + explicit-staging discipline
honored; `git ls-files runs` empty.

## Auto-Merge / Review Policy

This spec authorizes no PR creation, no auto-merge, and no deployment. Merge gating is the Ralph
driver's responsibility under the YELLOW lane policy (review required; block on critical /
test-tamper / boundary violation / EXPLORATORY-leak / second-PnL-bridge) and human authorization —
not this spec.

## Repair-or-Rollback

- **In-scope repair only:** fix the MechanismCard/SetupSpec JSON, the `tools/` harness, the
  EVIDENCE.json builder, additive governance helpers, or tests within the Allowed Paths; do not expand
  scope to fix unrelated findings.
- **Rollback:** the change is additive and pure-Python (plus value-free JSON); revert the new
  MechanismCard/SetupSpec JSON, the `tools/` harness, the EVIDENCE.json, any additive governance helper,
  and the new tests to restore the prior state with no migration and no data change. Materialized rows
  are local-only and untracked, so rollback touches no data artifact.
- **STOP / escalate (do not auto-proceed):** any pressure to edit the conditional-probe engine or the
  single-factor template, import `backtest`/`management`/`fast_path`/`value_store` into `research/`,
  fabricate values when rows do not resolve, encode the downward FDR re-scope as a
  `BudgetAmendmentRecord`, let EXPLORATORY output reach promotion, emit a `PromotionDecision`, cite
  first-light EVIDENCE or the de-stack `0.068/6862` as a fresh result, add a dependency or paid data, or
  commit a `runs/`/data/secret/parquet artifact — treat as out-of-scope and surface to the user.
