# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an
Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The repository-level campaign pointer targets
`LABEL_COMPUTE_FAST_PATH_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

Current campaign progress:
`LABEL_COMPUTE_FAST_PATH_V1` is the active Workflow 2 campaign. `LCFP-P00`
adds the bootstrap documentation, value-free evidence root, and FUTSUB pause
handoff; after this phase branch is merged, P00 is complete.

Active / next phase: next `LCFP-P01` - Label Engine Inventory + Baseline
Benchmark, then `LCFP-P02` - Shared Label Panel / Terminal / Guard Contract.

New durable surfaces in this `LCFP-P00` executor snapshot:

- `docs/label_compute_fast_path/README.md` indexes the campaign bundle,
  durable docs, value-free evidence root, and handoffs.
- `docs/label_compute_fast_path/OVERVIEW.md` summarizes the fast-label producer
  path, reference-oracle policy, parity/no-lookahead/guard gates, and FUTSUB
  supersession condition.
- `research/label_compute_fast_path_v1/` is the value-free evidence root for
  later inventory, baseline, parity, benchmark, integration, and closeout
  summaries.
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_PAUSE_STATE.md` records the
  paused FUTSUB state without deleting or mutating run state, values, registry
  rows, or worktrees.

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
