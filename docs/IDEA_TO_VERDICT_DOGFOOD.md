# Idea-To-Verdict Dogfood Runbook

This runbook covers IVL-P06 DK Track B dogfood only. It is a research-only loop
proof over already-materialized local substrate. It does not add a mechanism,
feature, label, dataset, sweep, promotion path, or value engine.

## Fixtures

- `research/idea_to_verdict_loop_v0/dogfood/track_b_es2024_120m.idea.yaml`
  represents the burned single-class ES 2024 120m path-label slice.
- `research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml`
  represents the barrier-resolving ES 2020 120m slice from the path-label
  coverage matrix (`row_count=313156`, `overlap_rows=310547`,
  `acceptance_state=ACCEPTED`).

Both files embed slice metadata as front-door passthrough fields. Those fields
are consumed by `alpha idea gate` and `alpha idea run`, and are not folded into
the frozen content-hashed `AlphaSpec`, `MechanismCard`, or `SetupSpec` objects.

## Commands

Run from the repository root:

```bash
PYTHONPATH=src python -m alpha_system.cli.main idea gate \
  research/idea_to_verdict_loop_v0/dogfood/track_b_es2024_120m.idea.yaml

PYTHONPATH=src python -m alpha_system.cli.main idea run \
  research/idea_to_verdict_loop_v0/dogfood/track_b_es2024_120m.idea.yaml \
  --report-output research/idea_to_verdict_loop_v0/dogfood/ES_2024_120m_REPORT.md

PYTHONPATH=src python -m alpha_system.cli.main idea gate \
  research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml

PYTHONPATH=src python -m alpha_system.cli.main idea run \
  research/idea_to_verdict_loop_v0/dogfood/track_b_es2020_120m.idea.yaml \
  --report-output research/idea_to_verdict_loop_v0/dogfood/ES_2020_120m_REPORT.md
```

## Expected Outcomes

The ES 2024 slice must return `DATA_GAP` at Check-3
`path_label_two_class` before any probe is invoked. `alpha idea run` must route
that outcome to requeue with `probe_spent=false` and `promotion_eligible=false`.

The ES 2020 slice carries two-class metadata, so Check-3 must pass. In an
environment where the already-materialized local feature and label packs resolve
through the existing resolver contract, `alpha idea run` may emit a recorded
fast readout, render `REPORT.md`, and write a value-free memory action. If the
executor lacks `ALPHA_DATA_ROOT`, optional parquet support, or compatible pack
partition metadata, the accepted outcome is an honest `DATA_GAP` with
`fabricated_values=false`.

## Boundaries

Do not run `alpha feature materialize`, `alpha label materialize`,
`--force-recompute`, a scaleout driver, or a registry write. Do not edit
FUTSUB, DK, probe-engine, `first_light.py`, value-engine, strategy-template, or
FactorLibrary files. Do not promote the readout or describe it as alpha,
profitability, tradability, or production readiness.
