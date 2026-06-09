# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Workflow: `workflow2`
Run: `workflow2 active` — resumed on the V1 fast producer path after FEATURE_COMPUTE_FAST_PATH_V1 closed (CLOSEOUT COMPLETE_WITH_WARNINGS, 17/17).
Status: `resuming` — FCFP delivered the V1 Polars producer fast path + benchmark-driven CPU worker parallelism and is the default producer engine. The feature/label registries were reset to a single V1 engine substrate (reference engine retained as the parity oracle only). FUTSUB-P14 was amended to materialize all 8 feature families on V1+workers (bounded-real 2024 first, then full accepted window) before registry integration / coverage audit / resolver smoke, then continue P15→P33. Ralph owns staging, commit, review routing, PR/CI/merge gates, and run summaries.
