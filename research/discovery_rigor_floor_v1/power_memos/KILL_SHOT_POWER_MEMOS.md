# Kill-Shot Per-Study Power Memos (Planning Priors)

Compass v4.4 §3.C readiness precondition 4: a minimum-detectable-effect (MDE)
memo on real N_eff, written **before** any Track A rerun metric is computed.
This file is that memo for the 6 re-locked prior-INCONCLUSIVE Core Pilot
studies (re-lock report:
`research/futures_substrate_scaleout_v1/rerun/studyspec_relock.md`; lock JSONs:
`research/futures_substrate_scaleout_v1/rerun/study_specs/`).

Claim boundary (per `docs/RESEARCH_INTERPRETATION_POLICY.md` and compass §2):
everything below is a **planning prior / power heuristic**, never a pass/fail
threshold, never a promotion rule, and never an alpha, profitability,
tradability, or capital-allocation statement. No market, return, signal, cost,
or diagnostic values appear here — only lock metadata counts, contract
formulas, and pre-declared expectations.

P110000_RELOCK_V2 addendum (2026-06-12): the memo content remains the
pre-metric planning prior for the P022000 re-lock anchors. For execution after
P110000_RELOCK_V2, use the successor StudySpec ids below; the prior ids remain
historical anchors only.

| P022000 re-lock anchor | P110000_RELOCK_V2 successor |
| --- | --- |
| `sspec_652fcc23a6f725b405612b8e` | `sspec_f6cbd88caa0445f0f56d81fd` |
| `sspec_676a012a4a4cdf3d169cd981` | `sspec_1604b063f3a3401208ee0239` |
| `sspec_1d87dfbe3d24810720f75014` | `sspec_dec89a327a9c50957adca780` |
| `sspec_c2114a3c6c90595350151af0` | `sspec_840e8342564226f2c3257903` |
| `sspec_950ad6bb7063928d9ff8ea4f` | `sspec_c237c6a8ce40c2585836fae0` |
| `sspec_6088f0ed5b02b161bfb54943` | `sspec_533f665ec4ac063dbb664a54` |

---

## 1. Shared dataset scope and N_eff basis

All six rerun candidates lock the identical label substrate (the studies differ
in features, mechanism, and variant axes, not in label scope):

- Symbols: ES, NQ, RTY (equity index futures — one shared beta complex).
- Years: 2019 through 2026, where 2026 is partial
  (label windows end `2026-05-29`); effective span ≈ **7.4 years per symbol**.
- Horizons: `fwd_ret_5m / 10m / 15m / 30m` on 1m sampling cadence.
- Per horizon: 24 symbol-year label pack locks (3 symbols × 8 years).
- Variant budget: 4 pre-declared parameter combinations per study.

### Measured rows (registry lock metadata, not approximation)

Rows below are the sums of `value_record_count` carried in each StudySpec's
committed `label_pack_locks` — measured, value-free registry metadata, identical
across the six specs:

| Horizon | Rows (3 symbols, 2019–2026) | Rows per symbol (≈) |
| --- | ---: | ---: |
| 5m  | 7,455,294 | ES 2,537,821 / NQ 2,538,401 / RTY 2,379,072 |
| 10m | 7,416,879 | ~2.47M |
| 15m | 7,379,178 | ~2.46M |
| 30m | 7,294,349 | ~2.43M |

### N_eff basis (stated approximation)

No measured per-study `label_n_eff_report` exists yet — the only committed
N_eff artifact (`research/futures_substrate_scaleout_v1/wiring/n_eff_sample_report.md`)
is a tiny synthetic contract demo. We therefore apply the P25 estimator
contract (`docs/futures_substrate_scaleout/N_EFF.md`) to the measured rows:

```text
implied_discount_factor = max(1, horizon / sampling_cadence)   # cadence = 1m
n_eff = floor(rows / discount_factor)
```

| Horizon | Discount factor | N_eff (3 symbols) | N_eff (per symbol, ≈) |
| --- | ---: | ---: | ---: |
| 5m  | 5  | ≈ 1,491,000 | ≈ 480k–510k |
| 10m | 10 | ≈ 741,700 | ≈ 240k–250k |
| 15m | 15 | ≈ 491,900 | ≈ 160k–164k |
| 30m | 30 | ≈ 243,100 | ≈ 78k–81k |

Honesty notes on this approximation (conservatism direction matters):

1. **Upper bound.** The contract formula discounts only horizon overlap. It
   applies no session/day clustering discount. The day/session unit count is
   far smaller: ≈ 252 trade days/yr × 7.4 yr ≈ **1,870 trade days per symbol**
   (≈ 5,600 symbol-days, and the three symbols are not independent).
2. **Event-conditioned sparsity.** Four of the six studies are
   event/condition-triggered (VWAP reclaim, RTH-open context, sweep
   close-back-inside, failed breakout). The realized evaluable sample is the
   event count, a small subset of label rows. Event counts are deliberately
   not computed here (that would require running the signal pipeline and this
   memo must precede any Track A metric); the rerun itself must report the
   measured `label_n_eff_report` and the event-conditioned counts.
3. **Cross-symbol dependence.** ES/NQ/RTY share one equity-index beta
   (compass §3.D, hypothesis (c)). For pooled-across-symbol planning we use an
   effective symbol multiplier k_eff ∈ [1.0, 1.5], not 3.

## 2. MDE math (compass §2 heuristic — planning prior only)

```text
t ≈ SR_annual × sqrt(years)                     (planning prior only)
```

The heuristic implicitly works in day-aggregated units, which is why the
years-based MDE is the honest planning number despite six-figure bar-level
N_eff: the bar-level N_eff above is the substrate-coverage basis, not a license
to shrink the detectable effect by sqrt(rows).

- **Single-test 2σ, one study, per-symbol span 7.4 yr:**
  MDE ≈ 2 / sqrt(7.4) ≈ **SR 0.73** (compass band 0.75–0.85; we sit at the
  optimistic edge of the band because 7.4 yr exceeds the 7-yr planning case).
- **Single-test 2σ, pooled across symbols (k_eff 1.0–1.5):**
  MDE ≈ 2 / sqrt(7.4 × k_eff) ≈ **SR 0.60–0.73**.
- **Multiplicity-corrected bar** (Track A universe ≈ 6 studies × variant
  budget 4 = 24 pre-declared tests; Bonferroni-style two-sided z ≈ 3.1;
  compass §2 band for 6 families × bounded variants):
  MDE ≈ 3.1 / sqrt(7.4) ≈ **SR 1.13**, i.e. the compass **SR ≈ 1.1–1.2**
  effectively-required band; pooled-symbol best case ≈ SR 0.9–1.0.

Compass honest prior for this space: most real edges are weak,
**input grade SR 0.3–0.8**, and "the six families are crowded priors"
(compass §3.D). The structural conclusion of §2 follows immediately: weak
edges usually cannot clear a single-signal bar on ~7 years, which is exactly
why pre-declared pooled evaluation exists.

---

## 3. Per-study memos

### 3.1 `sspec_652fcc23a6f725b405612b8e` — vwap_session (RTH running-VWAP reclaim)

- P110000 successor: `sspec_f6cbd88caa0445f0f56d81fd`.
- Scope: ES/NQ/RTY, 2019–2026 (7.4 yr), 5m/10m/15m/30m, variant budget 4
  (opening_window × reclaim_distance_band).
- N_eff basis: shared table above (approximation per §1); realized power is
  further reduced by event conditioning (reclaim events within opening
  windows are a sparse subset of RTH bars).
- MDE: single-test 2σ ≈ SR 0.73 solo-symbol-set / 0.60–0.73 pooled;
  multiplicity bar ≈ SR 1.1–1.2.
- Plausible edge grade (crowded intraday VWAP mechanics): **SR 0.3–0.6**.
- **Pre-declared expectation:** likely **UNDERPOWERED solo** at the
  multiplicity-corrected bar; borderline at the single-test bar only if the
  true effect sits at the very top of the prior grade — **pooled retest is the
  realistic channel**.

### 3.2 `sspec_676a012a4a4cdf3d169cd981` — vwap_session (RTH open vs completed-ETH context)

- P110000 successor: `sspec_1604b063f3a3401208ee0239`.
- Scope: identical label substrate; variant budget 4
  (completed_eth_context × first_RTH_window).
- N_eff basis: shared table; strongest sparsity of the vwap pair — the
  decision context is anchored to one RTH open per trade date, so the
  effective unit count trends toward the ≈1,870 trade-days-per-symbol floor.
- MDE: single-test 2σ ≈ SR 0.73 / 0.60–0.73 pooled; multiplicity bar
  ≈ SR 1.1–1.2.
- Plausible edge grade: **SR 0.3–0.6** (crowded prior, once-per-day anchor).
- **Pre-declared expectation:** likely **UNDERPOWERED solo** at both bars at
  realistic effect sizes — **pooled retest (cross-symbol and/or
  cross-horizon) is the realistic channel**.

### 3.3 `sspec_1d87dfbe3d24810720f75014` — regime (trendiness/vol/range-compression gate)

- P110000 successor: `sspec_dec89a327a9c50957adca780`.
- Scope: identical label substrate; variant budget 4 (gate_mode × gate_window).
- N_eff basis: shared table; the mechanism is an **activation gate**, so the
  evaluable sample is the gated-active subset, smaller than the row basis by
  the (unknown, pre-declaredly uncomputed) activation fraction.
- MDE: single-test 2σ ≈ SR 0.73 / 0.60–0.73 pooled; multiplicity bar
  ≈ SR 1.1–1.2.
- Plausible edge grade as a **standalone** signal: **SR 0.2–0.5** — a regime
  gate is a conditioning mechanism, not a standalone direction source; its
  honest value is the interaction term.
- **Pre-declared expectation:** expected **UNDERPOWERED solo** at both bars;
  the realistic channel is the **conditioning/overlay role inside the
  pre-declared pooled hypotheses**, not solo detection.

### 3.4 `sspec_c2114a3c6c90595350151af0` — liquidity_pa (sweep close-back-inside)

- P110000 successor: `sspec_840e8342564226f2c3257903`.
- Scope: identical label substrate; variant budget 4
  (close_back_inside_deadline × reference_level_window).
- N_eff basis: shared table; sweep-and-reclaim events are sparse by
  construction, so the realized event count will sit far below the bar-level
  N_eff (events per session typically countable on one hand for mechanisms of
  this type — stated as a prior, not a measurement).
- MDE: single-test 2σ ≈ SR 0.73 / 0.60–0.73 pooled; multiplicity bar
  ≈ SR 1.1–1.2.
- Plausible edge grade (crowded price-action prior, sparse events):
  **SR 0.3–0.6**.
- **Pre-declared expectation:** likely **UNDERPOWERED solo**, with
  event-sparsity making the multiplicity bar implausible —
  **pooled retest is the realistic channel**.

### 3.5 `sspec_950ad6bb7063928d9ff8ea4f` — liquidity_pa (failed-breakout reversal)

- P110000 successor: `sspec_c237c6a8ce40c2585836fae0`.
- Scope: identical label substrate; variant budget 4
  (boundary_type × failure_deadline).
- N_eff basis: shared table; same sparse-event discount as 3.4.
- MDE: single-test 2σ ≈ SR 0.73 / 0.60–0.73 pooled; multiplicity bar
  ≈ SR 1.1–1.2.
- Plausible edge grade: **SR 0.3–0.6**.
- **Pre-declared expectation:** likely **UNDERPOWERED solo** —
  **pooled retest is the realistic channel**, with the liquidity_pa pair the
  natural mechanism-pooled pair (same family, distinct trigger geometry; any
  such pool must be registered before Track A metrics per §2.1 rules).

### 3.6 `sspec_6088f0ed5b02b161bfb54943` — bbo_tradability (spread-zscore + depth confirmation)

- P110000 successor: `sspec_533f665ec4ac063dbb664a54`.
- Scope: identical label substrate; variant budget 4
  (depth_gate × spread_zscore_window).
- N_eff basis: shared table; additionally constrained by BBO coverage and the
  missing-BBO fail-flag policy (rows without valid point-in-time BBO are
  excluded, not fabricated), so the evaluable subset is smaller than the
  label-row basis by the BBO-coverage fraction.
- MDE: single-test 2σ ≈ SR 0.73 / 0.60–0.73 pooled; multiplicity bar
  ≈ SR 1.1–1.2.
- Plausible edge grade as a **standalone** signal: **SR 0.2–0.4** — this is a
  tradability/confirmation overlay; it also carries structural
  `BBO_PROXY_LIMITATION` exposure under the compass reason-code taxonomy.
- **Pre-declared expectation:** expected **UNDERPOWERED solo** at both bars;
  realistic channel is the **overlay role inside pre-declared pooled
  hypotheses** (and its verdict should be read jointly with the BBO-proxy
  disclaimer gate).

---

## 4. Summary table

The `Re-lock sspec` column names the P022000 anchors retained by the
pre-registration memo. P110000_RELOCK_V2 execution must use the successor map
above.

| Re-lock sspec | Family | Scope | N_eff basis | MDE 2σ solo / pooled-symbols | MDE multiplicity bar | Prior edge grade | Pre-declared expectation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `sspec_652fcc23a6f725b405612b8e` | vwap_session | ES/NQ/RTY, 7.4y, 5–30m | rows-from-locks ÷ overlap (upper bound; event-sparse) | SR 0.73 / 0.60–0.73 | SR 1.1–1.2 | 0.3–0.6 | likely UNDERPOWERED solo — pooled retest realistic channel |
| `sspec_676a012a4a4cdf3d169cd981` | vwap_session | same | same; ~once-per-day anchor → trade-day floor | SR 0.73 / 0.60–0.73 | SR 1.1–1.2 | 0.3–0.6 | likely UNDERPOWERED solo — pooled retest realistic channel |
| `sspec_1d87dfbe3d24810720f75014` | regime | same | same; gated-active subset | SR 0.73 / 0.60–0.73 | SR 1.1–1.2 | 0.2–0.5 standalone | expected UNDERPOWERED solo — conditioning role in pooled hypotheses |
| `sspec_c2114a3c6c90595350151af0` | liquidity_pa | same | same; sparse sweep events | SR 0.73 / 0.60–0.73 | SR 1.1–1.2 | 0.3–0.6 | likely UNDERPOWERED solo — pooled retest realistic channel |
| `sspec_950ad6bb7063928d9ff8ea4f` | liquidity_pa | same | same; sparse failure events | SR 0.73 / 0.60–0.73 | SR 1.1–1.2 | 0.3–0.6 | likely UNDERPOWERED solo — pooled retest realistic channel |
| `sspec_6088f0ed5b02b161bfb54943` | bbo_tradability | same | same; BBO-coverage-limited subset | SR 0.73 / 0.60–0.73 | SR 1.1–1.2 | 0.2–0.4 standalone | expected UNDERPOWERED solo — overlay role in pooled hypotheses; BBO_PROXY_LIMITATION exposure |

## 5. Pre-registration statement

**Written before any Track A rerun metric was computed; planning priors only,
never pass/fail thresholds.** No diagnostic, return, signal, cost, or market
value was read or produced in preparing this memo; the only measured inputs
are committed value-free registry lock counts and timestamps. Track A verdicts
are decided by the rigor-floor evidence chain (pre-registered splits, measured
`label_n_eff_report`, cost stress, VariantLedger accounting, holdout
discipline, reviewer verdict) — not by anything in this file.

The structural reading of this memo: under honest priors, **all six studies
are expected to land in `INCONCLUSIVE + UNDERPOWERED` territory as solo
single-signal tests** at the multiplicity-corrected bar. That is not a defect
of the rerun — it is exactly the regime compass §2 anticipates, and the **two
mandatory Track-B pre-declared pooled hypotheses (cross-symbol and
cross-horizon mechanism pools, registered before any Track A metric is
inspected, each logged as ONE VariantLedger hypothesis) are the designed
response** to these UNDERPOWERED solo expectations. Track B supplements and
never rewrites Track A verdicts.
