# SUBSTRATE REALITY REPORT

> **SUPERSEDED for live data state (banner added 2026-06-15).** The value-layer
> coverage tables below were measured **2026-06-07, BEFORE the
> `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` materialization**. They no longer
> describe what is on disk: ES/NQ/RTY 2019–2026 features (8 families) + labels
> (`cost_adjusted` / `path` / `fixed` / `extended` / `session`) are now
> materialized. Do **not** read the "no values" / "single 2024 week, ES-only"
> verdicts as current. The authoritative data-existence truth is the tool
> `alpha data inventory` (`tools/frontier/data_inventory.py`) — built specifically
> to kill the "config `BLOCKED:27` vs disk full of values.parquet" misread this
> snapshot embodies. This document is retained only as the historical 2026-06-07
> substrate snapshot; its tables are intentionally **not** hand-updated (they would
> only re-drift).
>
> Repo-grounded measurement of what the local data / feature / label / runtime
> substrate **actually contains today**, taken before authoring
> `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.
>
> - **Date measured:** 2026-06-07
> - **Method:** direct inspection of the local `ALPHA_DATA_ROOT` Parquet tree and
>   SQLite registries, plus `src/` source reads. No code changed, nothing
>   materialized.
> - **Companion document:** `research/futures_core_alpha_pilot_v1/closeout/SUBSTRATE_SCALEOUT_V1_HANDOFF.md`
>   (the pilot's own failure-mode handoff). This report is the *measured reality*
>   behind that handoff; where they overlap they agree.
> - **Roots inspected:**
>   - `FULL`  = `/home/yuke_zhang/alpha_data/alpha_system` (real Databento history)
>   - `SMOKE` = `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke` (pilot lock target)
>
> All paths below are **local-only runtime state** and must never be committed
> (raw/canonical/feature/label values, SQLite DBs). This document records facts
> about them; it does not move them into git.

---

## 0. Headline

The **raw market-data layer is deep and real** (ES/NQ/RTY, OHLCV-1m **and**
BBO-1m, **2018-01 → 2026-05**). The **feature/label *value* layer is a single
week of 2024, ES-only, OHLCV-family-only**. The substrate *code* (5 feature
families, 4 label families, full diagnostics) is implemented and proven
materializable — what is missing is **materialized values at scale**, two
**new guards** (roll-splice, multiple-testing), and a few **wirings**. The
binding constraint is not data acquisition and not platform code; it is
materialization + two guards + wiring.

---

## 1. DatasetVersions

**29 DatasetVersions registered** in `registry/datasets.sqlite` (identical set in
FULL and SMOKE roots): 9 OHLCV "TRADES", 9 OHLCV "TRADES_DENSE_RESEARCH_GRID",
9 BBO, 2 IBKR validation. Each Databento yearly version is partitioned
`schema=<…>/root={ES,NQ,RTY}` → **3 Parquet files each** (one per symbol).
Row counts are the 3-symbol totals; per-symbol ≈ total ÷ 3 (ES ≈ 344k–356k/full
year, ≈ 140k for 2026-partial).

### 1a. Databento OHLCV-1m — `schema=ohlcv_1m` (registered name: `…:1 min:TRADES`)

| Year | dataset_version_id | rows (ES+NQ+RTY) | files | Parquet path (under FULL/databento/canonical/glbx_mdp3/) |
|---|---|---|---|---|
| 2018 | `dsv_databento_ohlcv_321568572236ef4a` | 1,003,978 | 3 | `dsv_databento_ohlcv_321568572236ef4a/schema=ohlcv_1m/root=*` |
| 2019 | `dsv_databento_ohlcv_a483cc0cc282474b` | 1,028,218 | 3 | `…a483cc0cc282474b/schema=ohlcv_1m/root=*` |
| 2020 | `dsv_databento_ohlcv_bac95e92f1bb1850` | 1,036,622 | 3 | `…bac95e92f1bb1850/…` |
| 2021 | `dsv_databento_ohlcv_8aeb50fb409fc691` | 1,046,651 | 3 | `…8aeb50fb409fc691/…` |
| 2022 | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | 1,053,393 | 3 | `…dc7c86c813fe0dfe/…` |
| 2023 | `dsv_databento_ohlcv_ec144f9a02a64774` | 1,048,947 | 3 | `…ec144f9a02a64774/…` |
| 2024 | `dsv_databento_ohlcv_05404069799decb0` | 1,027,390 | 3 | `…05404069799decb0/…` |
| 2025 | `dsv_databento_ohlcv_35ffead770498acd` | 1,022,647 | 3 | `…35ffead770498acd/…` |
| 2026 (→05-29) | `dsv_databento_ohlcv_a0342ee6a412622b` | 419,842 | 3 | `…a0342ee6a412622b/…` |

### 1b. Databento OHLCV-1m DENSE grid — `schema=ohlcv_1m_dense` (`…:1 min:TRADES_DENSE_RESEARCH_GRID`)

Gap-filled research grid (named, not hash-addressed). Slightly higher row counts
than 1a because empty minutes are filled to a dense bar grid.

| Year | dataset_version_id | rows (3 sym) | files |
|---|---|---|---|
| 2018 | `dsv_databento_ohlcv_dense_2018_v1` | 1,068,030 | 3 |
| 2019 | `dsv_databento_ohlcv_dense_2019_v1` | 1,068,120 | 3 |
| 2020 | `dsv_databento_ohlcv_dense_2020_v1` | 1,071,900 | 3 |
| 2021 | `dsv_databento_ohlcv_dense_2021_v1` | 1,072,260 | 3 |
| 2022 | `dsv_databento_ohlcv_dense_2022_v1` | 1,068,113 | 3 |
| 2023 | `dsv_databento_ohlcv_dense_2023_v1` | 1,068,120 | 3 |
| 2024 | `dsv_databento_ohlcv_dense_2024_v1` | 1,041,254 | 3 |
| 2025 | `dsv_databento_ohlcv_dense_2025_v1` | 1,037,108 | 3 |
| 2026 (→05-29) | `dsv_databento_ohlcv_dense_2026_v1` | 421,920 | 3 |

### 1c. Databento BBO-1m — `schema=bbo_1m` (`…:1 min:BBO`)

| Year | dataset_version_id | rows (3 sym) | files |
|---|---|---|---|
| 2018 | `dsv_databento_bbo_514d0f3b3fc7d48a` | 1,003,978 | 3 |
| 2019 | `dsv_databento_bbo_f91f510a8d6fa87b` | 1,028,218 | 3 |
| 2020 | `dsv_databento_bbo_af9511d169b0aead` | 1,036,622 | 3 |
| 2021 | `dsv_databento_bbo_d5cb08f949e7ff28` | 1,046,651 | 3 |
| 2022 | `dsv_databento_bbo_7b5595d5030462ab` | 1,053,393 | 3 |
| 2023 | `dsv_databento_bbo_8772e3b47aa5fb98` | 1,048,947 | 3 |
| 2024 | `dsv_databento_bbo_f9e1d70a04d9dae4` | 1,027,390 | 3 |
| 2025 | `dsv_databento_bbo_35d4417c086be53f` | 1,022,647 | 3 |
| 2026 (→05-29) | `dsv_databento_bbo_22c49fbf57cceea6` | 419,842 | 3 |

### 1d. IBKR validation (read-only broker truth, not a primary alpha source)

| dataset_version_id | scope |
|---|---|
| `dsv_ibkr_es_nq_rty_eth_2026…` | ES/NQ/RTY 1m TRADES, ETH, recent validation |
| `dsv_ibkr_es_dated_202404_val…` | ES dated April-2024 validation slice |

### 1e. "Accepted" status — IMPORTANT CAVEAT

Every row carries `status_message = "DATA-P17 dataset version registry record"`.
There is **no per-version accept/reject verdict or coverage report persisted in
the registry** — this is the known `STRUCTURAL_BACKLOG.md` gap ("dataset registry
doesn't persist quality/coverage reports — only stores hashes"). So:

- **Registered:** yes — all 29 (DATA-P17).
- **Formally accepted + locked (with a persisted coverage/quality verdict):**
  **not represented in the registry today.** The scaleout handoff's requirement
  for "**accepted, locked** DatasetVersions" therefore implies an explicit
  acceptance-lock step is part of the next campaign, not a thing already on disk.

---

## 2. Continuous series facts

| Fact | Value (from `configs/data/databento_es_nq_rty_instruments.json` + `data/foundation/rolls.py`) |
|---|---|
| Symbol form / stype | Databento **continuous**: `ES.v.0`, `NQ.v.0`, `RTY.v.0` (`v` = volume-based front selection; `0` = front rank) |
| Adjustment | **Unadjusted.** Config flags: `provider_continuous: true`, `unadjusted: true`, `not_roll_truth: true`; series ids `series_databento_{es,nq,rty}_front_unadjusted` |
| Consequence | Each roll point is a **real, unadjusted price splice (jump)** from old contract to new contract |
| Roll rule metadata | `roll_policy_id = roll_cme_index_futures_quarterly` declared. `rolls.py` defines `RollPolicy` + `RollCalendarRecord` contracts with adjustment methods {`none`, `back_adjusted`, `ratio_adjusted`} and triggers {`calendar_days_before_expiration`, `open_interest_crossover`, `volume_crossover`, `volume_open_interest_hybrid`} |
| Roll calendar **data** materialized? | **No.** No roll-date records exist under `ALPHA_DATA_ROOT` (only feature dirs incidentally named `rolling_*`). `rolls.py` is contracts-only; nothing writes a roll calendar. |
| Roll boundaries recoverable? | **Partially.** The CME equity-index quarterly roll schedule is deterministic (3rd-Friday expiry; roll = the preceding Monday) and can be computed analytically. The **exact** volume-based splice point Databento used inside `.v.0` is **provider-internal and not captured** — so boundaries are *analytically approximable, not provider-exact*. (Per-contract ESM26/ESU26 data, which would give exact splices, is **not** held — only the continuous series.) |

---

## 3. BBO coverage

| Question | Answer |
|---|---|
| BBO DatasetVersions by symbol/year | **Full 2018→2026, ES/NQ/RTY**, 9 yearly versions (see §1c). ~1.0M rows/yr across 3 symbols. This is the *expensive* schema and it is fully present. |
| BBO values materialized into FeaturePacks? | **No.** Zero BBO feature values are registered. All 8 registered feature versions are `base_ohlcv_*` (see §5). The committed FeatureRequest `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json` is a **spec only**. |
| BBO semantics caveat | Databento BBO-on-interval is **time-sampled + forward-filled** top-of-book (no record when an interval has no trade/quote update). It is a tradability/spread proxy — **not** proof of passive fill, queue priority, or event-level slippage. Cost stress must treat it as a proxy. |
| Core Pilot BBO StudySpec lock status | BBO tradability AlphaSpecs (`FUTCORE-P11`) and diagnostics (`FUTCORE-P20`) ran but resolved **INCONCLUSIVE** — the locked smoke substrate has no BBO values, so studies could not be evaluated (zero fabricated values). This is the single hardest data gap the pilot surfaced. |

---

## 4. FeatureSpecs / LabelSpecs (code implemented)

**Feature families in code** (`src/alpha_system/features/families/`): `ohlcv`,
`bbo`, `session`, `cross_market`, `structure` (liquidity/PA) — **5 families,
~5,100 LOC**.

**Label families in code** (`src/alpha_system/labels/families/`): `fixed_horizon`,
`cost_adjusted`, `path`, `event` — **4 families, ~2,900 LOC**.

| Layer | Implemented in code | Values exist? |
|---|---|---|
| OHLCV feature family | yes | **partial** — 6 base OHLCV features, 1 week, ES only |
| Session/calendar feature family | yes | partial — only `rth_flag`, `session_minute` materialized |
| BBO feature family | yes | **no values** |
| Cross-market feature family | yes (richest diagnostics, 1,692 LOC runtime) | **no values** |
| Structure / liquidity-PA feature family | yes | **no values** |
| `fixed_horizon` labels | yes (incl. 15m engine added in pilot P15-G1) | partial — only 5m/10m/30m, 1 week |
| `cost_adjusted` labels | yes | **no values** |
| `path` labels (MFE/MAE, triple-barrier) | yes | **no values** |
| `event` labels | yes | **no values** |

Identity/versioning is content-addressed (`fver_…`, `lver_…`), `available_ts` /
`label_available_ts` tracked per value, leakage guard + availability-ordering
audit are **fail-closed** and implemented.

---

## 5. Materialized values (the real bottleneck)

**Authoritative registry truth** (`registry/features.sqlite`,
`registry/labels.sqlite`, FULL root):

**Features — 8 versions registered, all `base_ohlcv_*`, all `REGISTERED`:**

| feature_id | records | dataset_version | event_ts span |
|---|---|---|---|
| `base_ohlcv_returns` | 6,896 | `…ohlcv_05404069` (2024) | 2024-01-02 → 2024-01-09 |
| `base_ohlcv_log_returns` | 6,896 | 〃 | 〃 |
| `base_ohlcv_rolling_volatility` | 6,896 | 〃 | 〃 |
| `base_ohlcv_rolling_range` | 6,896 | 〃 | 〃 |
| `base_ohlcv_volume_zscore` | 6,896 | 〃 | 〃 |
| `base_ohlcv_range_position` | 6,896 | 〃 | 〃 |
| `base_ohlcv_rth_flag` | 6,896 | 〃 | 〃 |
| `base_ohlcv_session_minute` | 6,896 | 〃 | 〃 |

**Labels — 3 versions registered, all `REGISTERED`:**

| label_id | records | event_ts span |
|---|---|---|
| `fwd_ret_5m` | 6,862 | 2024-01-02 → 2024-01-08 |
| `fwd_ret_10m` | 6,832 | 2024-01-02 → 2024-01-08 |
| `fwd_ret_30m` | 6,712 | 2024-01-02 → 2024-01-08 |

**Coverage verdict:** the registered, lock-resolvable substrate is a
**single week (2024-01-02 → 2024-01-09), ES-only, OHLCV-family-only** seed pack
(materialized set `fset_es_ohlcv_session_smoke`). ~6,900 records ≈ one week of
1-minute bars for one instrument.

**On-disk sizes:** `features/` = **27 MB**, `labels/` = **16 MB**. These exceed
the ~6.9k-record registry footprint because they include dual JSONL+Parquet
sidecars, manifests, and the smoke `fset` materialization tree — **not** more
history. **Smoke ≠ full-history: the gap from "one week / ES / OHLCV-only" to
"2018-2026 / ES+NQ+RTY / all families" is unmaterialized.**

---

## 6. Runtime wiring (what can run today)

| Capability | Status | Note |
|---|---|---|
| Factor diagnostics (IC/RankIC, decay/ICIR, buckets, monotonicity, tail, MFE/MAE) | **Runs today** | `runtime/diagnostics/factor/runtime.py` (866 LOC); blocked only by missing values for non-OHLCV families |
| Cross-market diagnostics (alignment, lead-lag, correlation, spread/residual) | **Code ready; needs values** | `runtime/diagnostics/cross_market/runtime.py` (1,692 LOC); requires cross-market feature values (none materialized) |
| Session/regime split diagnostics | **Runs today** | `runtime/diagnostics/splits/core.py`; imported by `runtime/dry_run.py`; conditioning-safety guards present |
| BBO tradability diagnostics | **Needs materialization only** | code path exists; requires BBO feature values |
| Regime / liquidity-PA diagnostics | **Needs materialization only** | family code exists; requires regime + structure feature values |
| Cost stress | **Runs today** | `runtime/cost/` (profiles + session penalties + `requires_double_cost` invariant) |

**Classification of the remaining work:**

- **Materialization only (no new code):** BBO, cross-market, regime,
  liquidity/PA, VWAP/session diagnostics — all blocked solely on values.
- **New DatasetVersion locks:** explicit *accepted + locked* verdicts for the
  27 Databento yearly versions (acceptance not persisted today — §1e).
- **New code:** roll-splice guard, multiple-testing correction, FactorLibrary
  ingestion pipeline, and wiring purge/embargo walk-forward into the runtime
  (§7, §8).

---

## 7. Validation wiring

| Question | Answer |
|---|---|
| Does `experiments/splits.py` exist? | **Yes.** Implements `train_validation_split`, `walk_forward_splits`, `apply_purge_embargo` with `purge_gap` / `embargo_gap` (`SplitWindow`). |
| Does the **research runtime** call it? | **No.** The only importers are `experiments/ml.py` and the module itself. The runtime's diagnostics path imports `runtime/diagnostics/splits` (descriptive *session/regime* splits) — **a different module**. Purged/embargoed **walk-forward is not in the evaluation path.** |
| What is missing for purge/embargo to be real? | (a) plumb `walk_forward_splits` + `apply_purge_embargo` into the StudySpec → diagnostics flow; (b) **overlap-aware effective-sample-size (N_eff)** reporting for overlapping multi-horizon labels; (c) family-specific train/calibration/OOS protocols (STRUCTURAL/MEDIUM/FAST half-lives); (d) a locked-test contamination ledger wired to actual locked-partition access. |

---

## 8. Known hard gaps

1. **Roll-splice guard — MISSING (top priority).** `labels/families/fixed_horizon.py`
   does **not** reference roll boundaries. On the **unadjusted** continuous series
   (§2), a 5–30m forward-return label can straddle a roll splice and book the
   contract-to-contract jump as a real return. Over 2018-2026 that is
   ~4 rolls/yr × ~8 yr × 3 instruments ≈ **~100 splice points per series** — a
   default-on contamination, not an edge case. The No-Lookahead audit does **not**
   catch it (it is a splice artifact, not lookahead). Needs: roll-boundary
   computation, label-window exclusion/flagging, and a `roll_window` regime split.

2. **Multiple-testing / false-discovery — MISSING.** Variant-budget audit limits
   *count*, but there is **no deflated-Sharpe / PBO / FWER correction** applied to
   survivors, and no N_eff accounting. Across families × horizons × sessions ×
   regimes this is the dominant overfitting risk and the one genuinely-new
   statistical component the next governance work needs.

3. **FactorLibrary ingestion pipeline — MISSING.** `reports/factor_card.py` can
   build cards and `factors/` has spec/lifecycle/registry **contracts**, but there
   is no `EvidenceDraft → FactorCard → registry → lifecycle` ingestion path
   (`factor_registry` rows = 0). Survivors cannot yet become durable factor memory.

4. **DatasetVersion acceptance not persisted (§1e).** Registry stores hashes, not
   accept/reject + coverage verdicts. Blocks "accepted, locked" semantics the
   scaleout handoff requires.

5. **Cross-instrument availability discipline (verify, don't assume).** Cross-market
   diagnostics must preserve per-instrument `available_ts` (no forward-fill across
   instruments). The code asserts this; it must be re-verified once real
   cross-market values are materialized (the pilot's cross-market rejections
   depended on it).

6. **Portfolio/AlphaBook activation — deferred (correctly).** `portfolio/`
   contracts exist but no marginal-contribution / combination engine. Premature
   until ≥3–5 validated factors exist; not part of substrate scaleout.

---

## Recommended exact scope for `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`

Aligned with `closeout/SUBSTRATE_SCALEOUT_V1_HANDOFF.md`, with two additions
this measurement makes non-optional. **This campaign is substrate engineering,
not alpha ideation** (AlphaSpecs/StudySpecs already exist and are reusable).

### IN SCOPE

1. **Accept + lock the existing DatasetVersions.** Produce and persist
   acceptance + coverage verdicts for the 27 Databento yearly versions
   (OHLCV-1m, OHLCV-dense, BBO-1m; ES/NQ/RTY; 2018→2026), closing the §1e /
   §8.4 gap. No re-pull needed — the data is on disk.
2. **Roll-boundary metadata + roll-splice guard (§8.1).** Compute the CME
   quarterly roll calendar, persist `RollCalendarRecord`s, exclude/flag
   forward-label windows that cross a splice, and add a `roll_window` regime
   split. Treated as a **leakage guard**, not execution tooling. (Self-built
   roll *engines*, per-contract ESM26 mapping, and the three-policy
   Research/Execution/Validation split remain **out of scope** — paper/live era.)
3. **Materialize the 8 FeaturePacks** from the handoff across the full window,
   keystone identity + resolver-smoke gate before diagnostics: base OHLCV,
   session/calendar/maintenance, VWAP/session-auction, regime/vol/compression,
   liquidity-sweep/PA, volume/activity, **BBO tradability/top-book**,
   cross-market alignment.
4. **Materialize the LabelPacks:** diagnostic 1m/3m; primary 5m/10m/15m/30m;
   extended 60m/120m/240m; session-close + maintenance-flat (never silently
   cross a maintenance break); cost-adjusted; path (MFE/MAE, triple-barrier).
5. **Overlap-aware N_eff reporting** in diagnostics (§7) — prerequisite for any
   honest OOS claim on overlapping intraday labels.
6. **Wire purged/embargoed walk-forward into the runtime** (§7) — connect the
   existing `experiments/splits.py` primitives to the StudySpec → diagnostics
   path; add family-specific STRUCTURAL/MEDIUM/FAST protocols.
7. **Coverage + diagnostics matrices:** symbol×horizon, session×horizon,
   BBO-quality, cross-market-alignment, feature-family coverage, label-family
   coverage.
8. **Re-run obligation:** re-lock and re-run the pilot's accepted StudySpecs
   (especially the 6 INCONCLUSIVE survivors and the regime/liquidity/BBO
   families) against real materialized inputs; re-issue honest
   REJECT/INCONCLUSIVE/WATCH/CANDIDATE_RESEARCH verdicts. Promotion stays
   evidence- and cost-gated; no human prior decides edge.

### EXPLICITLY OUT OF SCOPE (separate, later campaigns)

- Multiple-testing/false-discovery *correction* engine (§8.2) → belongs to
  `ALPHA_VALIDATION_GOVERNANCE_V1` (its single genuinely-new statistical core).
  *Note:* ship N_eff reporting (item 5) here so that campaign has inputs.
- FactorLibrary ingestion pipeline (§8.3) → `ALPHA_FACTOR_LIBRARY_V1`.
- Portfolio/AlphaBook activation, library-state walk-forward, shadow/paper/live,
  IBKR execution, ML meta-labeling, L1/L2 microstructure.

### DEFINITION OF DONE

Every handoff FeaturePack/LabelPack is materialized + registered with keystone
identity; **every Core-Pilot StudySpec lock resolves to a real Parquet value**
(resolver-smoke PASS, no fabricated values); the roll-splice guard is active and
demonstrated on a known roll week; N_eff and walk-forward appear in diagnostics;
all six coverage matrices exist; the pilot's INCONCLUSIVE studies have been
re-run with honest verdicts. Carry-over disciplines (fail-closed resolver,
explicit staging, no `runs/**` or value commits, incremental waves + serial
merge) hold throughout.
