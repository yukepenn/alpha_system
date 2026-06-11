# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. Campaign state is tracked in
`ACTIVE_CAMPAIGN.md`, which is coordinator-owned in Workflow 2.

`REFERENCE_LABEL_PARALLEL_COMPUTE_V1` is closed as historical context: it added
an opt-in reference-worker path, measured workers=8 at 2.14x for
`cost_adjusted`, and kept default reference workers at 1 outside the documented
FUTSUB-P19 resume deviation.

Current campaign progress:
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is the active Workflow 2
campaign. `FUTSUB-P19` materialized and registered the cost-adjusted
LabelPacks for ES/NQ/RTY across the accepted 2019-2026 window, alongside the
fixed-horizon (P16), extended-horizon (P17), and session-close /
maintenance-flat (P18) packs already in the `label_materialization` gate.

Active / next phase after this branch: Ralph owns validation, review, staging,
PR creation, CI, merge, and live run state transitions for `FUTSUB-P19`. The
next serial label-materialization phase is `FUTSUB-P20` for path labels before
P21/P22/P23 perform guard audit, resolver integration, and coverage matrices.

New durable surfaces through this `FUTSUB-P19` executor snapshot:

- `configs/labels/scaleout/cost_adjusted.json` is the governed cost-adjusted
  label scaleout config for ES/NQ/RTY accepted windows, including documented
  cost/fee/slippage assumptions, BBO-proxy semantics, reference-engine
  selection, and the one-off P19 worker opt-in record.
- `src/alpha_system/labels/families/cost_adjusted/family.py` applies the shared
  roll-splice and maintenance-crossing terminal guard and records cost,
  BBO-proxy, bar-end terminal resolution, and guard metadata in the label
  contract. Ambiguous duplicate BBO source or terminal keys become gap metadata
  rather than a silent quote choice.
- `src/alpha_system/features/scaleout/driver.py` owns the P19 reference-engine
  cost-adjusted materialization path, registry-truth skip checks, and
  supersession metadata for bar-end-aligned BBO terminals.
- `research/futures_substrate_scaleout_v1/label_packs/cost_adjusted/coverage_summary.md`
  is the value-free coverage summary for the completed accepted-window
  materialization, including documented cost/fee/slippage versions, BBO-proxy
  gap counts, `label_available_ts`, registry metadata, and overlap-aware
  N_eff summaries.
- `tests/unit/futures_substrate_scaleout/labels/test_cost_adjusted_scaleout.py`
  covers synthetic variant emission, intra-bar BBO terminal resolution,
  `label_available_ts`, guard drops, duplicate BBO-key gaps, cost-version
  metadata, and checkpoint skip behavior.
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P19.md`
  records materialization evidence, validation, and residual review focus for
  reviewer and coordinator use.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Campaign bundle: `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Value-free research evidence root:
  `research/reference_label_parallel_compute_v1/`
- Commit-eligible handoffs:
  `handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/`
- Campaign bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`
- Futures substrate scaleout docs: `docs/futures_substrate_scaleout/`
- Value-free research evidence root: `research/futures_substrate_scaleout_v1/`
- Commit-eligible handoffs:
  `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Safety Boundaries

The project remains research-only and local-first. This campaign does not
authorize live trading, paper trading, broker operations, order routing,
production deployment, account operations, capital allocation, or autonomous
trading behavior.

The per-row reference label engine remains the correctness oracle. RLPC-P03 does
not edit the reference engine, label families, roll guard, label versioning, or
any data artifact. Registry writes remain parent-only and serial; the benchmark
uses isolated local namespaces under the data root and leaves production
registry row counts unchanged. Later phases must preserve exact identity, serial
registry writes, roll/maintenance guards, default workers=1, and
`label_available_ts` no-lookahead behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

This campaign makes no alpha, profitability, tradability, execution-quality, or
production-trading claim. Workflow 2 orchestration, validation routing, review,
staging, commit, PR, CI, merge, and done-check actions are owned by Ralph.
