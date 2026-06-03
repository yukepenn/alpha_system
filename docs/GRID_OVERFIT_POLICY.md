# Grid Overfit Policy

Strategy grids are evidence, not approval. A leaderboard row is a sortable
fixture result for review; it is not a promotion decision, deployment signal, or
claim about future market behavior.

## Controls

- Every grid declares `max_combinations`.
- Every parameter dimension is an explicit finite list.
- Exceeding the bound raises before materialization.
- Rejected configurations are written to `rejected_configs.csv` with reasons.
- Fast-path use requires ASV1-P19 accelerated parity for the selected feature
  set.
- Reference fallback is visible through `engine_used=reference_fallback`.
- Registry records retain warnings and failed-step visibility.

## Language Rules

Grid outputs and summaries must use research-evidence language. They must not
claim that a configuration is suitable for trading, production execution, or
future outperformance. Candidate promotion remains outside this MVP and requires
later review gates.

## Review Focus

Review should check bounded search discipline, rejected-config visibility,
versioned inputs, cost-model presence, fast/reference routing, artifact policy,
and whether any text could be misread as a promotion decision.
