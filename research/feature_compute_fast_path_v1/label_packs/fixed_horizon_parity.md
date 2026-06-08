# FCFP-P10 Fixed-Horizon Label Pack Parity Report

Value-free synthetic-fixture report for the V1 `fixed_horizon` label pack. This
report contains no per-row label values, prices, materialized value files,
registry databases, provider responses, or alpha/tradability claims.

## Scope

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P10`
- Pack: `alpha_system.labels.fast.fixed_horizon`
- Reference oracle: `alpha_system.labels.families.fixed_horizon.family`
- Fixture: `tests/fixtures/feature_compute_fast_path/fixed_horizon_label.py`
- Shared panel: 36 synthetic OHLCV rows plus 36 synthetic BBO rows
- Governed labels covered: all current `FixedHorizonLabelName` entries

The governed oracle boundary is the reference enum: trade-price
`fwd_ret_{1,3,5,10,15,30}m` and midprice
`mid_fwd_ret_{1,3,5,10,30}m`. Longer FUTSUB narrative horizons up to 240m are
not currently governed by the fixed-horizon family and remain an explicit
governance gap; this phase did not create new labels or new identities.

## Results

All label values matched the reference exactly on the synthetic fixture.
No floating-point tolerance was needed.

| Label | Basis | Horizon | N_eff | Null / gap rows | Value result | Availability / flags | Identity |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `fwd_ret_1m` | close | 1m | 35 | 4 | exact | exact | exact |
| `fwd_ret_3m` | close | 3m | 33 | 4 | exact | exact | exact |
| `fwd_ret_5m` | close | 5m | 31 | 3 | exact | exact | exact |
| `fwd_ret_10m` | close | 10m | 26 | 2 | exact | exact | exact |
| `fwd_ret_15m` | close | 15m | 21 | 2 | exact | exact | exact |
| `fwd_ret_30m` | close | 30m | 6 | 2 | exact | exact | exact |
| `mid_fwd_ret_1m` | mid | 1m | 35 | 4 | exact | exact | exact |
| `mid_fwd_ret_3m` | mid | 3m | 33 | 4 | exact | exact | exact |
| `mid_fwd_ret_5m` | mid | 5m | 31 | 3 | exact | exact | exact |
| `mid_fwd_ret_10m` | mid | 10m | 26 | 2 | exact | exact | exact |
| `mid_fwd_ret_30m` | mid | 30m | 6 | 2 | exact | exact | exact |

## Contract Checks

- `label_available_ts` parity: exact for every governed label and record.
- Terminal-row policy: exact; trailing rows without an exact horizon terminal
  are excluded, yielding `N_eff = 36 - horizon_minutes`.
- Gap / quality flags: exact, including `source_not_trade`,
  `horizon_not_trade`, `roll_splice_boundary`, `maintenance_crossing`,
  `bbo_gap`, `source_bbo_gap`, `horizon_bbo_gap`, `missing_bbo`, and
  `bbo_quarantined`.
- Guard preparation: trade and BBO guard columns are prepared once on the shared
  panel and reused across all horizons.
- Horizon-overlap metadata: recorded per label; each governed label has
  overlapping source events with at least one same-basis peer horizon.
- `label_version_id` equality: exact for every governed label. The fast pack
  uses the reference `LabelContractSpec` / `LabelVersion` and mints no V1
  identity.
- Persistence/registry path: the test materializes only to a pytest temp root
  and registers each label through `LabelRegistry.register_materialized_label`
  with serial writes and fast producer/value-schema provenance.

## Artifact Boundary

Temporary value-store outputs and the synthetic label registry are created only
under pytest temp directories during tests. No label values, registry files,
raw/canonical data, provider responses, run-local artifacts, or heavy artifacts
are commit-eligible.
