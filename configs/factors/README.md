# Factor Configs

This directory holds factor-definition configuration, parallel to
`configs/features/` and `configs/labels/`.

- `configs/factors/examples/` — illustrative factor config samples.
- `configs/factors/microstructure/` — microstructure factor configs.

Factor configs must stay local-first, declarative, and versioned. They declare
factor inputs and parameters only; value/accounting math stays in the sanctioned
reference engine, and any fast-path producer remains reference-parity-gated.
Place new family-scoped files under `configs/factors/<family>/`.
