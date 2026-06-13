# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing
and validating offline research substrate under Frontier Harness Generic
`0.3.0-rc1`.

## Current Snapshot

The repository-level campaign pointer targets
`SHIP_REFIT_V1`. Campaign state is tracked in `ACTIVE_CAMPAIGN.md`, which is
coordinator-owned in Workflow 2.

`SHIP_REFIT-P04` is the current refit phase on this branch. It is the GREEN,
non-gating second-wave cleanup/provenance landing after P00-P03. The load-bearing
cores remain P01 provider-watchdog resilience, P02 diagnostics fast-path parity,
and P03 Detection-Power / N_eff rigor.

Durable surfaces added so far are the provider watchdog in
`tools/frontier/command_runner.py`, the Ralph watchdog wiring and first-light
preflight in `tools/frontier/ralph_driver.py`, the permutation-index diagnostics
fast path in `src/alpha_system/governance/surrogate_run.py` and
`src/alpha_system/research/diagnostics.py`, the IC power helper in
`src/alpha_system/runtime/diagnostics/power.py`, the purge/embargo-aware N_eff
estimator in `src/alpha_system/runtime/diagnostics/splits/n_eff.py`, the parity
harness in `tests/unit/governance/test_surrogate_run.py`, and the design notes
`docs/ship_refit_v1/PROVIDER_WATCHDOG.md` and
`docs/ship_refit_v1/DIAGNOSTICS_FAST_PATH.md`. P04 adds the shared
`tools/frontier/cleanup.py` path, `tools/frontier/runs_retention.py`,
`tools/frontier/runtime_paths.py`, the `just frontier-clean` and
`just frontier-clean-dry-run` recipes, post-merge stale-worktree/run-retention
cleanup wiring, the done-check provenance fix, and persistent Frontier scratch
under `$ALPHA_SYSTEM_ROOT/.tmp`; see
`docs/ship_refit_v1/CLEANUP_PROVENANCE.md`. The provider timeout is `3600s`; the
first-light pre-run check remains callable with
`python tools/frontier/ralph_driver.py first-light`.

The committed campaign pointer and README are snapshots. For authoritative
in-flight Workflow 2 state, use `python tools/frontier/status_doctor.py` or the
run-local state owned by Ralph.

## Source Of Truth

- Root campaign pointer: `ACTIVE_CAMPAIGN.md`
- Active campaign bundle: `campaigns/SHIP_REFIT_V1/`
- Campaign overview docs: `docs/ship_refit_v1/`
- Value-free research evidence root:
  `research/ship_refit_v1/`
- Commit-eligible handoffs: `handoffs/SHIP_REFIT_V1/`
- Strategy and roadmap compass: `docs/OPERATING_COMPASS_V4.md`

## Safety Boundaries

The project remains research-only and local-first. `SHIP_REFIT_V1` authorizes
harness and diagnostics hardening only. It does not authorize live trading,
paper trading, broker operations, order routing, deployment, account operations,
funding decisions, or autonomous trading behavior.

Artifact discipline is unchanged: explicit staging only and value-free evidence
only. `runs/**` is local-only and never committed. Raw or canonical data,
feature or label values, provider responses, heavy artifacts, local databases,
logs, caches, secrets, and credentials are never committed.

The refit does not authorize new alpha ideation, FactorLibrary ingestion,
AlphaBook construction, paper/live behavior, broker access, deployment,
profitability claims, tradability claims, or execution-readiness claims.
`pyproject.toml` dependencies remain empty, so numpy, pandas, and polars stay
absent. Truth-chain invariants are preserved, including the sanctioned reference
engine as the only value/accounting truth. Workflow 2 orchestration, validation
routing, review, staging, commit, PR, CI, merge, and done-check actions are owned
by Ralph.
