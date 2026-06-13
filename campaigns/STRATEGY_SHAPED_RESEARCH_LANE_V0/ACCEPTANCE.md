# ACCEPTANCE — STRATEGY_SHAPED_RESEARCH_LANE_V0

## Campaign-level invariants (every phase)

- `python tools/hooks/canary_runner.py` all-PASS (incl. `planted_fake_alpha`, true-alpha pair,
  `forbidden_second_pnl_truth`, `forbidden_scope_drift`, `governance_random_target`).
- Surrogate-FDR **zero-pass** criterion + no-lookahead/`available_ts` + roll/maintenance
  fail-closed guards intact.
- The existing **single-factor** study path (`SINGLE_FACTOR_THRESHOLD_TEMPLATE`,
  `StudyConfig.factor_id`) is **byte-unchanged** — the conditional capability is strictly additive.
- **No new dependency** (numpy/pandas/polars stay unimportable). No new paid data.
- `git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.

## Per-phase acceptance

### SSRL-P00 (GREEN)
Bundle consistent; pointer set; YAML parses; smoke + canaries pass; `REUSE_MAP.md` + `V0_SCOPE.md`
committed with the OUT-of-scope list explicit.

### SSRL-P01 (YELLOW)
`MechanismCard` + `SetupSpec` classes exist, content-addressed, validated, EXPLORATORY-stampable;
**`event_trigger` is a SEPARATE field from `entry_context`**; tests cover validation + the
content-addressing; no engine/sim code touched; canaries PASS.

### SSRL-P02 (YELLOW) — the load-bearing gate
- A `SetupSpec` with **context ≠ trigger** compiles and runs an **EXPLORATORY** probe whose
  outcome comes from a **materialized path label** (target-before-stop / MFE / MAE).
- **Quarantine proven:** the trusted/promotion path **refuses** an EXPLORATORY-stamped artifact
  (a dedicated canary asserts this fail-closed).
- **No second PnL truth:** `research/` has **zero** import of `backtest`/`management`/`fast_path`
  (asserted in CI).
- Single-factor path unchanged; surrogate-FDR + per-factor MDE/power attached to the readout;
  variants bounded by VariantLedger/family_budget (no grid); canaries PASS; numpy/pandas/polars absent.

### SSRL-P03 (YELLOW)
One context≠trigger idea expressed + explored end-to-end on a small real slice, EXPLORATORY-stamped,
variant-ledgered, surrogate-FDR + power-qualified; the **de-stack** diagnostic recorded as value-free
evidence; **no promotion**, no profitability/tradability claim; canaries PASS.

### SSRL-P04 (YELLOW)
Handoff scaffold emits trusted-lane spec **gaps** without promoting; EXPLORATORY-refusal holds;
AI-researcher happy-path + `PA_GRAMMAR_SUBSTRATE_V1` naming docs committed; canaries PASS.

## Campaign done

P00–P04 merged with the above met (or P00–P03 if P04 deferred to a docs PR); `RUN_SUMMARY` written;
no promotion, no profitability/tradability claim; sequence / geometry-sweep / sim-bridge / feature
fast lane remain DEFERRED behind their later trigger.
