# ADF1 Post-Closeout Audit And Consolidation Handoff

## Scope Summary

Completed the requested consolidation pass without git, network, pip, real data
pulls, or broker/live scope. This pass reconciles stale status docs after
`ALPHA_DATA_FOUNDATION_V1`, deduplicates IBKR JSON/connection helpers, moves the
materializer under the IBKR operator namespace, adds artifact/data-root guards,
and documents how the next feature/label campaign should consume accepted
DatasetVersions.

## Files Changed Or Added

- Status/docs: `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGELOG.md`, `README.md`,
  `docs/AI_AGENT_GUIDE.md`, `docs/ONBOARDING.md`,
  `docs/data_foundation/README.md`,
  `docs/data_foundation/DATASET_VERSION.md`,
  `docs/data_foundation/DATASET_CONSUMPTION.md`,
  `docs/data_foundation/BACKFILL_RUNBOOK.md`,
  `campaigns/ALPHA_DATA_FOUNDATION_V1/RUNBOOK.md`.
- Handoffs: `handoffs/ADF1_LOCAL_RESEARCH_DATA_BACKFILL.md`,
  `handoffs/ADF1_POST_CLOSEOUT_AUDIT_AND_CONSOLIDATION.md`.
- Code: `src/alpha_system/data/ibkr/_json_utils.py`,
  `src/alpha_system/data/ibkr/_connection.py`,
  `src/alpha_system/data/ibkr/smoke_connect.py`,
  `src/alpha_system/data/ibkr/backfill_connect.py`,
  `src/alpha_system/data/ibkr/pull.py`,
  `src/alpha_system/data/ibkr/backfill.py`,
  `src/alpha_system/data/ibkr/manifest_builder.py`,
  `src/alpha_system/data/foundation/dry_run.py`.
- Moved: `src/alpha_system/data/materialize.py` to
  `src/alpha_system/data/ibkr/materialize.py`.
- Tests/guards: `tests/unit/data/test_materialize.py`,
  `tests/tools/test_artifact_guard.py`, `tools/hooks/artifact_guard.py`,
  `tools/hooks/canary_runner.py`.

## Consolidation Details

- Added `json_ready_base(...)` and `json_ready(...)` in
  `src/alpha_system/data/ibkr/_json_utils.py`; replaced duplicate private
  helpers in smoke/backfill/pull/backfill/dry-run/manifest/materialize call
  sites. `data/universe.py` was intentionally not touched.
- Added shared connection helpers in
  `src/alpha_system/data/ibkr/_connection.py`: doctor block message, required
  env lookup, and the read-only access gate preserving the authorization-before
  probe ordering.
- Moved materialize to `alpha_system.data.ibkr.materialize`, adjusted repo-root
  path parents to `parents[4]`, updated imports/docs, added strict template
  calendar documentation, and kept connector provider-ts formatting separate
  from materialize provider-ts parsing.
- Added `_validate_data_root(...)` so materialize fails closed when
  `ALPHA_DATA_ROOT` resolves inside the repository before raw reads or registry
  writes.
- Extended artifact guard suffix blocking to `.raw` and `.arrow`, added tests,
  and added a canary for a stray root-level `.raw`.
- Review note (non-blocking): in `backfill_connect`, the shared access gate now
  runs the read-only reachability probe before manifest/pacing load (previously
  after). Observable outcomes (messages, exit codes, fail-closed semantics) are
  unchanged because `probe_ibkr_host_port` never raises; the only delta is that
  an invalid-manifest run performs a harmless read-only TCP probe first.

## Docs And Status

- `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGELOG.md`, and `README.md` now agree
  that `ALPHA_DATA_FOUNDATION_V1` is complete (`25/25`), Workflow 2 is paused,
  governance is already complete, and the next intended campaign is
  `ALPHA_FEATURE_LABEL_FOUNDATION_V1`.
- Added `docs/data_foundation/DATASET_CONSUMPTION.md` covering registry lookup,
  `dsv_ibkr_es_nq_rty_eth_20260603_v1`, canonical five-timestamp semantics,
  partitions/contamination metadata, `ALPHA_DATA_ROOT`, and no-claims language.
- Added short data-heavy phase pointers to the AI agent and onboarding guides.

## Intentional Non-Changes

- Did not weaken quality gates, read-only IBKR boundary, forbidden-method list,
  clientId `101`/`102` guard, canonical timestamp contract, partition rules, or
  contamination metadata requirements.
- Did not add alpha, feature, label, strategy, broker, live, paper, account, or
  order-routing code.
- Did not touch `src/alpha_system/data/universe.py` `_json_ready`.
- Did not run real IBKR pulls, write real data, commit raw/canonical data,
  commit registries, or create local data artifacts.

## Deferred Low-Priority Items

- Wrap direct `python -m alpha_system.data.ibkr.*` operator modules under a
  reviewed `alpha data ...` CLI group.
- Replace the materialize ETH template shim with a reviewed holiday/half-day
  aware calendar path.

## Validation

- `python -m compileall src tests tools` - PASS.
- `python -m ruff check src/alpha_system/data/ibkr/_json_utils.py src/alpha_system/data/ibkr/_connection.py src/alpha_system/data/ibkr/smoke_connect.py src/alpha_system/data/ibkr/backfill_connect.py src/alpha_system/data/ibkr/pull.py src/alpha_system/data/ibkr/backfill.py src/alpha_system/data/ibkr/manifest_builder.py src/alpha_system/data/ibkr/materialize.py src/alpha_system/data/foundation/dry_run.py tests/unit/data/test_materialize.py tools/hooks/artifact_guard.py tests/tools/test_artifact_guard.py tools/hooks/canary_runner.py` - PASS.
- `python tools/hooks/canary_runner.py` - PASS, including
  `forbidden_stray_raw_suffix`.
- `python -m pytest -q` - PASS (`1735 passed`).
- `CI=true python -m pytest -q` - PASS (`1735 passed`).
- `python -m alpha_system.data.ibkr.materialize --help` - FAIL in this shell:
  `ModuleNotFoundError: No module named 'alpha_system'`. Reason: the repo uses
  a `src` layout, the package is not installed in this shell, and pip/install is
  forbidden by task scope.
- `python -m alpha_system.data.ibkr.backfill_connect --help` - same bare-command
  importability failure for the same reason.
- `PYTHONPATH=src python -m alpha_system.data.ibkr.materialize --help` - PASS.
- `PYTHONPATH=src python -m alpha_system.data.ibkr.backfill_connect --help` -
  PASS.

## Readiness Statement

The DatasetVersion consumption path is now documented for
`ALPHA_FEATURE_LABEL_FOUNDATION_V1`. Loading a DatasetVersion remains
data-admissibility only and carries no alpha, profitability, tradability,
broker, paper/live, or production-readiness claim.
