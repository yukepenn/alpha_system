# DK-P04 Handoff — Track B Context≠Trigger EXPLORATORY Conditional Probe (Real Slice)

- campaign_id: `DIFFERENTIATED_KILLSHOT_V1`
- phase_id: `DK-P04`
- lane: YELLOW
- branch: `dk-p04-track-b`

## Scope Delivered

Ran the campaign's single Track B bet: authored **one** DIFFERENTIATED, **EXPLORATORY**
`context ≠ trigger` `SetupSpec` + `MechanismCard` and executed it through the SSRL conditional-probe
engine (`research/conditional_probe.py`), **byte-unchanged**, over **real, locally-materialized**
ES_2024 path labels. Rows are loaded by a new `tools/`-side harness via
`core.value_store.load_parquet_values` and **injected** into the pure probe; `research/` imports no
value engine. The readout is permanently `EXPLORATORY`, `promotion_eligible: false`, and is refused by
the promotion path.

### Probe outcome (EXPLORATORY)

The probe ran on real materialized rows (this is NOT the SSRL first-light `DATA_GAP` fixture — that
gap was an executor-import limitation; here the `tools/` loader actually reads the Parquet).

- **observation counts:** aligned `25,219`, conditioned (context-passing) `2,348`,
  missing_context `965`, missing_trigger `0`.
- **diagnostics (research-only summaries, value-free):**
  - `target_before_stop_probability` = **0.0** over `131` events (context-passing AND trigger-firing).
  - `post_event_mfe_mae`: mean_mfe = `0.00150`, mean_mae = `-0.00114` over `131` events
    (`mfe_n = mae_n = 131`).
- **power:** `N_eff = 2,348`, `MDE(|IC|) = 0.0405`, `SE(IC) = 0.0206`, `statistical_validity_claim:
  false`.
- **HONEST SUBSTRATE FINDING (not alpha, not a failure):** the materialized 120m
  `target_before_stop` path-label slice (`ES_2024_120m_lcfp_p08_es_202406`) is **single-class** — every
  one of the 26,184 outcomes is `False`, all flagged `horizon_no_barrier` (the 120m barrier was never
  hit in this LCFP-P08 June-2024 benchmark slice). So the conditioned target-before-stop probability is
  degenerate (`0.0`). The MFE/MAE labels in the same slice carry real numeric variance. This is a
  **substrate-coverage observation**, recorded in `EVIDENCE.json` under `outcome_caveats`
  (`single_class_path_outcome: true`), with **no fabricated values**.

The output is **EXPLORATORY only**: it is not promotion evidence, not a survivor, does not enter
FactorLibrary, and emits no `PromotionDecision`. No alpha / tradability / profitability claim.

### Surrogate calibration verdict — `ZERO_PASS_MET`

The probe's HARD precondition (a label-shuffle surrogate reaching `ZERO_PASS_MET`) was satisfied
**FDR-before-metric**: the harness shuffles the path-label `target_before_stop` outcomes across event
rows `64` times and recomputes the probe's **conditional uplift** statistic (conditioned share −
aligned share); a run "passes" only if its shuffled `|uplift|` strictly exceeds the observed `|uplift|`.
Result: `run_count = 64`, `gate_pass_count = 0`, `error_count = 0` ⇒ `threshold_verdict =
zero-pass-met`, `gate_status = PASSED`. On the degenerate slice the observed uplift is `0.0` and no
shuffle can strictly exceed it, so the gate holds honestly (not a forced pass). The family-budget check
is `RESPECTED` (`observed_count = 1`, `family_budget = 1`).

## C1 / C2 / C3 Confirmations

- **C1 — genuinely distinct context vs trigger (different `factor_id` AND different underlying signal):**
  - `entry_context.factor_id` = `liquidity_structure_range_contraction`
    (feature_set `feature_set_futures_scaleout_regime_volatility_compression`, content_hash
    `91454e766dfd05f9…`) — a **continuous trailing range-compression regime descriptor**.
  - `event_trigger.factor_id` = `liquidity_structure_failed_high_breakout_flag`
    (feature_set `feature_set_futures_scaleout_liquidity_sweep_pa_structure`, content_hash
    `4ddce8ae65388f46…`) — a **discrete prior-high sweep then close-back-inside event flag**.
  - Different `factor_id`, different FeaturePack family, different materialized content hash, and
    different signal type (continuous regime descriptor vs. discrete event flag). Not a declared-only
    dodge. The compile-time `context.factor_id == trigger.factor_id` check fails closed if collapsed
    (test `test_compiler_rejects_context_equal_trigger`).
- **C2 — real materialized ES_2024 data, no fabrication:** rows resolved from three real local
  Parquet stores (context 346,858 rows, trigger 346,858 rows / 38,957 fires, path label 26,184
  target-before-stop outcomes) via `core.value_store.load_parquet_values`. The SSRL first-light
  `EVIDENCE.json` (a `DATA_GAP`) was **NOT** cited as a real result. No values were fabricated; the
  single-class outcome was reported honestly.
- **C3 — de-stack not recycled:** the de-stack `ic = 0.068 / n = 6862` is **not** referenced anywhere
  in the Track B artifacts or this handoff as fresh corroboration.

## Files Changed (by path)

- `research/differentiated_substrate_v1/track_b/mechanism_card.json` — EXPLORATORY `MechanismCard` (value-free).
- `research/differentiated_substrate_v1/track_b/setup_spec.json` — EXPLORATORY `SetupSpec`, distinct context vs trigger (value-free).
- `research/differentiated_substrate_v1/track_b/EVIDENCE.json` — value-free EXPLORATORY `ConditionalProbeReadout` summary.
- `tools/differentiated_killshot_v1/dk_p04_track_b_probe.py` — `tools/`-side row-injection probe harness + label-shuffle surrogate + EVIDENCE builder (loader called here; rows injected into the pure probe).
- `tests/unit/differentiated_killshot/test_dk_p04_track_b_probe.py` — Track B tests.
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P04.md` — this handoff.

USED byte-unchanged (NOT edited): `src/alpha_system/research/conditional_probe.py`,
`src/alpha_system/governance/setup_spec.py`, `src/alpha_system/governance/mechanism_card.py`,
`src/alpha_system/strategies/templates.py`, `src/alpha_system/research/first_light.py`.

## Validation Commands + Results

| Command | Result |
| --- | --- |
| `pytest tests/unit/differentiated_killshot/test_dk_p04_track_b_probe.py -q` | 14 passed |
| `pytest tests -k "conditional_probe or setup or exploratory or first_light or handoff or track_b" -q` | 138 passed, 3487 deselected |
| `tools/verify.py --smoke` | exit 0 |
| `tools/hooks/canary_runner.py` | All canaries PASS (incl. `forbidden_exploratory_promotion`, `forbidden_second_pnl_truth`, `planted_fake_alpha`, `true_alpha_detection`, `governance_random_target`) |
| `git diff -- src/alpha_system/research/conditional_probe.py src/alpha_system/strategies/templates.py …` | empty (byte-unchanged) |
| no research→sim bridge grep | no forbidden research→sim imports |
| `git ls-files runs` | empty (0) |
| peak RAM (real run, `/usr/bin/time -v`) | 731,280 KB ≈ 0.73 GB (40 GB box; RAM-safe) |

**Dependency note (invariant #4):** `numpy` / `pandas` remain unimportable. `polars` IS importable in
the research venv, but it was **already present** as the runtime dependency of the sanctioned
`core.value_store` Parquet loader (added by `FEATURE_LABEL_PARQUET_SINK_V1`, not by this phase). The
harness and JSON add **no** direct `numpy` / `pandas` / `polars` import; polars is reached only through
`core.value_store.load_parquet_values` on the tools side. No new dependency was added.

The spec's verbatim check #4 one-liner has a pre-existing bug (`importlib.util` is not imported, so it
`AttributeError`s regardless of the project state). Re-ran the corrected check
(`import importlib.util as u; …find_spec(m)`): `numpy`/`pandas` not importable; `polars` importable
(pre-existing, as above). No skipped meaningful checks otherwise.

## Boundary / Invariant Confirmations

- (a) `research/conditional_probe.py` and the single-factor template (`strategies/templates.py`,
  `SINGLE_FACTOR_THRESHOLD_TEMPLATE`) are **byte-unchanged** (empty `git diff`).
- (b) `research/` imports **none** of `backtest` / `management` / `fast_path` / `core.value_store`;
  the loader is called from `tools/` and rows are **injected** into the pure probe. The harness defines
  no second PnL/value truth (`test_harness_defines_no_second_pnl_truth`); `forbidden_second_pnl_truth`
  canary green.
- (c) context and trigger are genuinely distinct (C1) — see above (different `factor_id`s + distinct
  underlying signals).
- (d) surrogate gate `ZERO_PASS_MET` and family-budget `RESPECTED` (both enforced as hard preconditions
  inside `evaluate_setup_conditional_probe`); rows resolved, so **no** `DATA_GAP` was needed — but the
  honest `DATA_GAP` fallback path exists and is tested.
- (e) the EVIDENCE is value-free (ids / counts / seeds / gate outcomes / diagnostics summaries only —
  no raw rows, no parquet payload, no PnL, no absolute data root), `EXPLORATORY`,
  `promotion_eligible: false`, and **refused** by `reject_exploratory_promotion_artifact`
  (`test_evidence_is_refused_by_promotion_path`).
- (f) neither the first-light `EVIDENCE` (a `DATA_GAP`, C2) nor the de-stack `0.068 / 6862` (C3) is
  cited as a fresh result.

Explicit staging only (no `git add .` / `-A`); no `runs/` / data / parquet / sqlite / scratch staged;
`git ls-files runs` empty. The run-local `runs/<run_id>/.../handoff.md` stays local-only and is not
staged.
