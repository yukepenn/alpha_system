# Data Configs

Configuration for the data foundation: provider instrument masters, validation
configs, and small reference examples. (Originally reserved by `DATA-P01`; it now
holds active configs used by the IBKR and Databento adapters.)

Contents include IBKR and Databento instrument / validation configs (e.g.
`ibkr_*`, `databento_*`) and `*_example` reference files. The
`request_pacing_policy_to_be_verified.json` filename is intentional — its
`to_be_verified` status is a governance-honesty marker (see `configs/README.md`).

This root must never contain credentials, account details, provider secrets, real
market data, committed local paths, raw provider responses, or production settings.
Real data stays local-only under `ALPHA_DATA_ROOT`.
