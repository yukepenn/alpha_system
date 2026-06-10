# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`LABEL_COMPUTE_FAST_PATH_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress:
`LABEL_COMPUTE_FAST_PATH_V1` is the active Workflow 2 campaign. `LCFP-P00`
adds the bootstrap documentation, value-free evidence root, and FUTSUB pause
handoff. `LCFP-P01` adds the value-free label-engine inventory, a bounded
reference-engine baseline benchmark summary, and the read-only benchmark
harness used to produce that baseline. `LCFP-P02` adds the shared label panel,
terminal-index, guard-disposition, `label_available_ts`, and quality-metadata
contract in `alpha_system.labels.fast`. `LCFP-P03` extends the fixed-horizon
fast pack to the governed fixed-minute trade-price horizons
1/3/5/10/15/30/60/120/240m, preserves the existing governed midprice minute
horizons, and routes symbolic `session_close` / `maintenance_flat` labels to
LCFP-P04 without crashing on their enum tokens.

Active / next phase after this branch: `LCFP-P04` and `LCFP-P05` continue the
parallel label-pack wave for session/maintenance/cost and path labels, followed
by LCFP-P06 integration after the pack branches merge serially.

New durable surfaces through this `LCFP-P03` executor snapshot:

- `docs/label_compute_fast_path/README.md` indexes the campaign bundle,
  durable docs, value-free evidence root, P01 artifacts, benchmark command, and
  handoffs.
- `docs/label_compute_fast_path/OVERVIEW.md` summarizes the fast-label producer
  path, reference-oracle policy, parity/no-lookahead/guard gates, and FUTSUB
  supersession condition.
- `docs/label_compute_fast_path/PANEL_TERMINAL_CONTRACT.md` documents the
  shared panel, terminal-index, roll/maintenance guard, availability, and
  quality metadata surface for P03/P04/P05.
- `src/alpha_system/labels/fast/panel.py` defines `SharedLabelPanel`,
  `TerminalRequest`, `resolve_terminal_indices`, `derive_label_available_ts`,
  and value-free quality metadata helpers.
- `src/alpha_system/labels/fast/fixed_horizon.py` declares the P03 fixed-minute
  fast pack coverage and explicit P04 routing for symbolic close-out labels.
- `tests/unit/label_compute_fast_path/test_fixed_horizon_extended_pack.py`
  covers all nine governed trade-price fixed-minute horizons plus roll and
  maintenance drop parity against the reference family.
- `research/label_compute_fast_path_v1/` is the value-free evidence root for
  inventory, baseline, parity, benchmark, integration, and closeout summaries.
- `research/label_compute_fast_path_v1/inventory/inventory.md` records the
  reference label engine, current fast-label surface, FUTSUB label needs,
  roll-guard and availability rules, overlap metadata, registry schema, and
  parity-harness surface.
- `research/label_compute_fast_path_v1/baseline/baseline_benchmark_summary.md`
  records the bounded reference-engine timing denominator for later comparison.
- `tools/label_compute_fast_path/baseline_benchmark.py` is a read-only
  reference-engine benchmark entrypoint for bounded slices.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_PAUSE_STATE.md` records the
  paused FUTSUB state without deleting or mutating run state, values, registry
  rows, or worktrees.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P03.md` records the fixed-horizon
  enum repair, shared-panel terminal implementation, parity coverage, and local
  validation results for this phase.

The repository-level campaign pointer and live Workflow 2 state are
coordinator-owned. For current in-flight status, run
`python tools/frontier/status_doctor.py` rather than relying on committed
snapshot text.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/LABEL_COMPUTE_FAST_PATH_V1/`
- Label compute fast path docs: `docs/label_compute_fast_path/`
- Value-free research evidence root: `research/label_compute_fast_path_v1/`
- Commit-eligible handoffs:
  `handoffs/LABEL_COMPUTE_FAST_PATH_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The per-row reference label engine remains the correctness oracle forever. The
fast label producer path emits values only, stays reference-parity-gated, and is
not the sanctioned production label materialization path until
`LABEL_COMPUTE_FAST_PATH_V1` acceptance passes. Resolver exact-id semantics,
official keystone registry writes, serial registry writes, roll and maintenance
guards, and `label_available_ts` no-lookahead behavior are preserved.

FUTSUB-P18/P19 historical "reference-engine-only" text is superseded only by
this campaign's explicit acceptance condition: production label materialization
may move to the fast path after LCFP acceptance and the LCFP-P09 coordinator
reintegration handoff. Until then, the reference engine remains the production
label path.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data, feature
or label values, provider responses, heavy artifacts, local databases, logs,
caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Research outputs are evidence for review only.

## Validation Commands

Default local validation commands remain:

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
```

Workflow 2 orchestration, validation routing, review, staging, commit, PR, CI,
merge, and done-check actions are owned by Ralph.
