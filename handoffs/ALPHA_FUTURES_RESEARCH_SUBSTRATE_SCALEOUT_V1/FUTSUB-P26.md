# FUTSUB-P26 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P26` - BBO Quality and Cross-Market Alignment Matrices  
Lane: Yellow  
Executor: Codex

## Intended Commit File List

All changes were left unstaged per executor instructions. Ralph owns staging,
commit, review, verdict, PR, CI, merge, and done-check routing.

- `README.md`
- `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md`
- `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md`
- `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P26.md`

No `src/**`, `tools/**`, `configs/**`, `tests/**`, `reviews/**`, or `runs/**`
path was created or edited by this executor.

## Execution Summary

- Produced the BBO quality matrix from registered P12
  `bbo_tradability_top_book` FeaturePack values.
- Produced the cross-market alignment matrix from registered P13
  `cross_market_alignment` FeaturePack values.
- Added the durable consumption document for P27...P29, Validation Governance,
  and future mining campaigns.
- Updated the README snapshot for P26 and the next nominal phase P27.
- Repair 1 reconciled the cross-market availability evidence after review:
  `Panel rows missing >=1 exact contributor` now names the counted quantity,
  the matrix/doc/handoff no longer claim zero exact-contributor gaps, and the
  state matrix defines `Quality flags` versus `Cross-market gap`.
- Used a local-only scratch helper at `/tmp/futsub_p26_matrix_builder.py`; it
  wrote intermediate drafts under `/tmp/futsub_p26_outputs/`. No scratch helper,
  intermediate dump, Parquet, SQLite, or run-local artifact was placed in the
  repository.

The generated run artifact directory named in the prompt was not present in this
worktree, and `status_doctor` reported no live `state.json`. No run-local
`handoff.md` was created.

## Matrix Inputs And Method

Shared command surface:

```bash
PYTHONPATH=src alpha feature list --alpha-data-root "$ALPHA_DATA_ROOT" --json
PYTHONPATH=src alpha feature report --kind both --feature-version-id <recorded fver> --alpha-data-root "$ALPHA_DATA_ROOT" --json
```

The aggregation helper resolved current registry rows through the CLI registry
helper in read-only mode, then filtered registered Parquet-backed value handles
by exact `feature_version_id`. It emitted only counts, rates, shares, bucket
labels, state labels, commands, and registry identities.

BBO matrix inputs:

- Accepted years: 2019-2026; 2018 expected-excluded from blocked `bbo_1m`.
- Registered P12 feature inputs per symbol/year: `spread`, `spread_ticks`,
  `top_book_depth`, `missing_bbo_flag`, `bad_quote_flag`, `wide_spread_flag`,
  and `low_depth_flag`.
- Registered P07 session inputs per symbol/year: `eth_segment_flag`,
  `rth_segment_flag`, and `halt_status_flag`.
- Full `feature_version_id` and `dataset_version_id` inventory is recorded in
  `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md` under
  "Registry Identities Used".

Cross-market matrix inputs:

- Accepted years: 2019-2026; 2018 expected-excluded from blocked `ohlcv_1m` /
  dense-grid acceptance context.
- Registered P13 state inputs: synchronized returns, NQ/ES and RTY/ES beta
  residuals, NQ-minus-ES and RTY-minus-ES return spreads, risk-on/risk-off
  rotation proxies, confirmation/divergence flags, and NQ/ES and RTY/ES rolling
  correlations.
- Registered P06 `base_ohlcv_log_returns` FeatureVersions for ES/NQ/RTY were
  used for the all-row availability-discipline check.
- Full `feature_version_id`, input `dataset_version_id`, and contributor
  identity inventory is recorded in
  `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md`
  under "Registry Identities Used".

## BBO Gating Context For FUTSUB-P28

- The matrix states that BBO-1m is a time-sampled + forward-filled tradability
  proxy and not passive-fill, queue-priority, intra-minute-impact, or execution
  truth evidence.
- Worst missingness / bad-quote cells are ES-2020, NQ-2020, RTY-2020, ES-2023,
  and NQ-2023. Rates remain low in absolute terms but are surfaced as gating
  context rather than smoothed away.
- Worst wide-spread concentration is RTY-2020, followed by NQ-2020 and RTY-2025.
- `low_depth_flag` resolved to zero across the accepted registered BBO cells;
  top-book availability is recorded separately from the materialized
  `top_book_depth` values.
- `bbo_tradability_spread_ticks` resolved all-null in this local substrate pass.
  The matrix therefore buckets `bbo_tradability_spread` and records
  spread-ticks availability as `0.000000` for every cell.
- Registered session flags collapse accepted BBO rows into `ETH_NON_RTH`
  (`eth_segment_flag=1`, `rth_segment_flag=0`, `halt_status_flag=null`). The
  matrix records this as substrate quality context and does not rederive RTH or
  maintenance-adjacent buckets from timestamps.

## Cross-Market Alignment Verification

- Materialized substrate policy recorded: `strict_intersection`.
- The `asof` default still exists in `cross_market_panel.py`, but P14 guards
  reject `asof` for FUTSUB substrate materialization; no `asof` aggregate is
  presented as substrate truth.
- All-row availability check:
  - Years checked: 2019-2026.
  - Panel rows checked: one registered `cross_market_synchronized_returns`
    panel per accepted year.
  - Panel rows missing at least one exact `event_ts` ES/NQ/RTY
    `base_ohlcv_log_returns` contributor: 2019=`27481`, 2020=`19402`,
    2021=`17643`, 2022=`10893`, 2023=`13800`, 2024=`13711`,
    2025=`12218`, 2026=`2059`. These are exact-contributor availability gaps,
    not rows treated as cross-instrument forward-filled coverage.
  - Panel rows whose `available_ts` preceded any resolved contributor
    `available_ts`: `0`.
  - Duplicate panel `event_ts`: `0`.
- Strict-intersection survival is recorded against ES/NQ/RTY session grids.
  Survival versus the minimum per-instrument grid is `1.000000` for all accepted
  years; survival versus the maximum grid is `0.999980` in 2022, `0.999997` in
  2024, `0.999986` in 2025, and `1.000000` otherwise.
- Registered session flags collapse accepted cross-market rows into
  `ETH_NON_RTH`; the matrix records this as substrate quality context and does
  not rederive session buckets.

## Substrate Findings For Coordinator Routing

No unresolvable BBO or cross-market FeaturePack blocked matrix production.
Three substrate coverage findings are explicitly recorded for downstream routing:

- `bbo_tradability_spread_ticks` resolves but is all-null across the accepted
  BBO matrix cells. P26 used the materialized `spread` field for spread buckets
  and recorded spread-ticks availability as its own coverage field.
- Registered session segmentation collapses accepted rows into `ETH_NON_RTH`.
  P26 did not rewrite session semantics; a finer RTH / maintenance-adjacent
  split should be routed to the session substrate owner if downstream consumers
  require it.
- The cross-market availability check found nonzero exact `event_ts`
  contributor gaps by accepted year, recorded in
  `cross_market_alignment.md`. P26 did not estimate around those gaps or present
  them as filled coverage; downstream diagnostics should consume them as
  availability context alongside the zero `available_ts` ordering violations.

## Validation

Commands run:

| Command | Outcome |
| --- | --- |
| `python tools/frontier/status_doctor.py` | Exit 0 with WARN: no run dir with `state.json` found for this campaign; hook floor armed; runtime contract consistent. |
| `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python /tmp/futsub_p26_matrix_builder.py` | Exit 0; generated `24` BBO identity rows, `24` BBO quality rows, `117` BBO spread rows, `51` BBO regime rows, `8` cross-market identity rows, `88` cross-market state rows, `8` cross-market survival rows, `8` availability rows; no input errors. |
| `/home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke` | Exit 0. |
| `/home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py` | Exit 0; all Frontier canaries passed. |
| `python tools/verify.py --smoke` | Repair validation exit 0. |
| `python tools/hooks/canary_runner.py` | Repair validation exit 0; all Frontier canaries passed. |
| `test -f research/futures_substrate_scaleout_v1/matrices/bbo_quality.md` | Exit 0. |
| `test -f research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md` | Exit 0. |
| `test -f docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md` | Exit 0. |
| `test -f handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P26.md` | Exit 0. |
| `LC_ALL=C rg -n '[^\x00-\x7F]' research/futures_substrate_scaleout_v1/matrices/bbo_quality.md research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md README.md handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P26.md` | Repair validation exit 1 with empty output, confirming ASCII-only committed artifacts. |
| `git status --short` | Repair validation showed only the expected phase surface: modified `README.md` and untracked `docs/futures_substrate_scaleout/BBO_AND_CROSS_MARKET_MATRICES.md`, `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P26.md`, `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md`, and `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md`. |
| `git ls-files runs` | Exit 0; empty output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | Exit 0; empty output. |
| `git diff --cached --name-only` | Exit 0; empty output. |
| `find . -path './.git' -prune -o -path './__pycache__' -prune -o -path './.pytest_cache' -prune -o -path './.ruff_cache' -prune -o -type f \( -name '*.parquet' -o -name '*.sqlite' -o -name '*.arrow' -o -name '*.feather' -o -name '*.db' -o -name '*.dbn' -o -name '*.zst' -o -name '*.log' \) -print` | Exit 0; empty output. |

Commands intentionally not run by Codex due to the executor override:

- `git add`
- `git commit`
- `git push`
- any Claude call, reviewer run, `review.md`, `verdict.json`, PR, merge, or
  phase PASS marking

## Artifact And Safety Notes

- No registry write, materialization, re-materialization, external provider
  call, raw provider read, live trading, paper trading, broker operation, order
  routing, production deployment, PR creation, or merge was performed.
- No feature values, label values, Parquet, Arrow, Feather, SQLite, DBN, Zstd,
  roll-calendar data, logs, caches, secrets, credentials, provider responses,
  or run-local artifacts were written into the repository.
- The committed artifacts are value-free markdown only and contain counts,
  rates, shares, bucket labels, state labels, commands, and registry identities.
- The executor did not mark the phase PASS.
