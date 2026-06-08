# 2018 BLOCKED Diagnosis — DatasetVersion Acceptance

Value-free diagnosis. Contains only aggregate coverage statistics (counts,
ratios), no raw rows, canonical values, feature/label values, provider
responses, or SQLite content.

## Question

After the FUTSUB-P02 acceptance-evidence fix (PR #264), live acceptance is
`20 ACCEPTED` / `5 ACCEPTED_WITH_WARNINGS` / `2 BLOCKED` over the 27 in-scope
yearly DatasetVersions. The two `BLOCKED` locks are:

- `ohlcv_1m` 2018 (`dsv_databento_ohlcv_321568572236ef4a`)
- `bbo_1m` 2018 (`dsv_databento_bbo_514d0f3b3fc7d48a`)

Is this a genuine sparse-history coverage gap, or an over-strict / missing-evidence
acceptance-policy bug?

## Method

Recomputed the acceptance coverage report for each 2018 version from the on-disk
canonical partitions via sanctioned readers (`canonical_loader` + per-version
canonical `manifest.json`). Compared against an accepted full year (`ohlcv_1m`
2024) as a control.

## Exact blocking dimensions

Both 2018 versions block on exactly two dimensions, and only because of **RTY**:

- `row_count_sanity`: BLOCKING
- `gap_coverage` (per-symbol minute coverage): BLOCKING

All other dimensions PASS: `year_date_range` (covered, full year),
`required_field_presence` (all 8 field groups + all schema columns present),
`missingness_quality_flags` (zero nulls across all required columns),
`continuous_provenance` (PASS), `roll_metadata` (deferred to P03, not required).

### Per-symbol coverage vs the ES/NQ/RTY union-minute grid

`ohlcv_1m` 2018 (expected_bar_floor from union grid = 314,783; floor ratio 0.90):

| symbol | observed bars | coverage ratio | status |
| --- | ---: | ---: | --- |
| ES  | 348,929 | 0.9976 | PASSING |
| NQ  | 349,143 | 0.9982 | PASSING |
| RTY | 305,906 | **0.8746** | **BLOCKING** |

`bbo_1m` 2018 shows the identical RTY shortfall (0.8746). The control
`ohlcv_1m` 2024: ES 0.9994 / NQ 0.9997 / RTY 0.9610 — all PASS.

- manifest `row_count` matches observed (2018 = 1,003,978) — no truncation, no
  read error.
- 2018 distinct trading days = 312 (trading-day coverage 0.855, above the 0.75
  floor), zero duplicate minutes, zero null required fields.

## Verdict: REAL sparse-history coverage gap (not a policy bug)

RTY (E-mini Russell 2000) genuinely traded fewer 1-minute bars in 2018 than
ES/NQ. Measured against the ES/NQ/RTY **union**-minute grid, RTY 2018 reaches
only 87.5%, below the 0.90 per-symbol blocking floor. ES and NQ 2018 are clean
(>99%). Every other quality dimension passes with zero nulls and a manifest match.
This is an honest property of the early RTY history, not over-strict thresholds
or missing evidence:

- The data is present and well-formed (no nulls, fields complete, manifest match).
- The shortfall is isolated to one thinner instrument in the earliest year.
- 2019 RTY warns (below the 0.95 warning floor) and the 2026 versions warn
  (partial-year) — a smooth, monotonic coverage gradient consistent with real
  market history, not a threshold artifact.

## Decision

- **Keep 2018 `ohlcv_1m` + `bbo_1m` excluded** from the full accepted
  materialization window, documented as a coverage gap.
- **Do NOT lower the blocking floor** to force 2018 inclusion.
- **Do NOT block the campaign** on 2018.
- The acceptance policy is **not** changed; the floors stand.
- Full accepted materialization window = `ACCEPTED` + `ACCEPTED_WITH_WARNINGS`
  versions (2019–2026; the 2018 `ohlcv_dense_research_grid` version is ACCEPTED
  and remains in scope).

Note: acceptance is per-DatasetVersion (each yearly version bundles ES/NQ/RTY),
so the RTY 2018 shortfall blocks the whole 2018 `ohlcv_1m` / `bbo_1m` versions
(ES/NQ 2018 are individually clean but share the version-level lock). Per-symbol
acceptance is out of scope for this campaign; 2018 is simply excluded.
