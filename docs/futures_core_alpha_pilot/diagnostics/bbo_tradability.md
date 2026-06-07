# FUTCORE-P20 BBO Tradability Diagnostics

`FUTCORE-P20` records value-free BBO confirmation diagnostics for the single approved BBO StudySpec from `FUTCORE-P14`.

## Scope

Covered StudySpec:

- `sspec_9f6f741192a4b534f06e51c0` / `aspec_1284e49b083df11eeb0481ea`: spread-zscore and top-book depth confirmation overlay with missing-BBO and bad-quote guards.

Diagnostics used the Research Runtime tool surface only: runtime entry/input resolution, factor diagnostics, label diagnostics, signal-probe contract checks, cost stress diagnostics, `RuntimeToolResult`, and `RuntimeRunSummary`.

The resolved locked input surface references DatasetVersion `dsv_databento_ohlcv_05404069799decb0`, two session-context FeaturePacks, and three LabelPacks for `5m`, `10m`, and `30m`. P15-G5 is governed but no locked BBO FeaturePack resolves in this input pack. No source primitive, runtime, feature, label, data, broker, execution, or CLI code was edited.

## Reports

Commit-eligible report artifacts:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/FUTCORE-P20_bbo_tradability_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/sspec_9f6f741192a4b534f06e51c0/runtime_reports.json`

Runtime status is `INCONCLUSIVE`. The joined resolved horizons contain 20,406 observations across `5m`, `10m`, and `30m`. Materialized value coverage is ES-only in this lock; NQ and RTY cells are zero-count limitations and are not inferred or substituted.

## BBO Quality

No locked BBO FeaturePack resolves for spread, spread ticks, spread zscore, top-book depth, wide-spread flag, low-depth flag, missing-BBO flag, or bad-quote flag. The report preserves these buckets as unresolved cells:

- valid BBO: zero observed because the locked BBO feature binding is absent;
- missing BBO: explicit fallback required for all resolved-horizon denominator rows until a locked BBO pack resolves;
- crossed, locked, stale, quarantined, wide-spread, and thin-depth buckets: not observed without a locked BBO pack;
- fabricated quotes: zero.

The BBO overlay remains confirmation and risk evidence only. It is not a standalone directional rule, execution result, fill-capacity result, or promotion state.

## Session And Horizon Matrix

Each report contains the required session views:

`full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`, and `RTH_with_ETH_context`.

Joined observations by primary horizon are:

| Horizon | Joined observations | Status |
| --- | ---: | --- |
| `5m` | 6,862 | Locked LabelVersion resolved. |
| `10m` | 6,832 | Locked LabelVersion resolved. |
| `15m` | 0 | Governed LabelSpec exists, but no locked LabelVersion resolves in this pack. |
| `30m` | 6,712 | Locked LabelVersion resolved. |

In the locked development partition, RTH-related cells have zero eligible observations under the locked session flag and are preserved as zero-count diagnostics. The `1m` and `3m` horizons are flagged diagnostic-only and are not a promotion basis.

## Cost Boundary

Cost diagnostics use the pinned nonzero profiles `base`, `stress_1`, `stress_2`, and `double_cost`. Thin-session stress is represented through runtime ETH and illiquid-session penalties for ETH, pre-RTH, and post-RTH views where the runtime supports the overlay.

`zero_cost` is recorded only as diagnostic context and is not a promotion basis. Cost outputs are representative unit-fill sensitivity summaries with BBO-unavailable fallback markers; they are not signal outcome, deployment, broker, order, or capital-allocation evidence.

## Boundary Confirmation

The diagnostics are value-free summary and metadata artifacts only. They include counts, split keys, report references, pack ids, hashes, statuses, and limitations, but no row-level feature values, label values, provider responses, heavy artifacts, or local run artifacts. No promotion decision, reviewer action, PR, merge, live operation, paper operation, broker call, order routing, or deployment action was performed by the executor.
