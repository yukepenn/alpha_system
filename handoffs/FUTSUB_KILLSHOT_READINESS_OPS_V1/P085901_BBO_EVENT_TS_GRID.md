# P085901_BBO_EVENT_TS_GRID Handoff

Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
Phase: `P085901_BBO_EVENT_TS_GRID`
Lane: YELLOW
Branch: `wf1/bbo-grid`

## Scope Completed

- Changed only the BBO feature family's emitted timestamps:
  - reference BBO records now emit `FeatureValueRecord.event_ts = bar_end_ts`.
  - BBO spread-zscore primitive points now use `bar_end_ts`.
  - fast BBO tradability uses `bar_end_ts` as its internal emitted event grid.
- Preserved BBO quote-time `event_ts` as an input property in fixtures and
  tests by moving fixture quote timestamps off the minute boundary while
  asserting emitted reference and fast records stay on `bar_end_ts`.
- Added the written factor-compute contract: bar-indexed families must emit
  `FeatureValueRecord.event_ts` on the bar grid (`bar_end_ts`); quote-time
  timestamps remain canonical/input properties; `available_ts` remains the PIT
  availability guard.
- Added `registry_event_ts_grid` as a governance canary and registered it with
  `tools/hooks/canary_runner.py`.
  - CI/default canary mode uses a synthetic fixture.
  - The visible allowlist is in code as `REGISTRY_EVENT_TS_GRID_ALLOWLIST`.
  - Known debt reason codes are `BBO_PENDING_RE_MATERIALIZATION` for BBO
    feature packs and `COST_SPREAD_LABEL_MIRROR_DEFECT` for cost/spread-adjusted
    label packs.
  - Running the detector without the allowlist fails on the synthetic known-debt
    rows, preserving assertion strength.
- Added unit coverage for the synthetic pass, no-allowlist fail path,
  unallowlisted violation naming, no-registry live skip, and live-mode SQLite
  registry scanning.
- Regenerated `docs/SYSTEM_MAP.md` so the canary inventory includes the new
  canary.

## Identity And Rematerialization

Feature version IDs do not rotate in this phase. The P036000 identity-pin
coverage in `tests/unit/features/test_feature_identity_invariant.py` pins that
`feature_version_id` derives from the feature spec/config computational
contract, not from materialized value rows or producer implementation details.
This phase changes emitted BBO value content and registry first/last event
timestamps on future materialization, but it does not change the BBO feature
identity payload.

The sanctioned consumer path is re-materialization followed by re-locking new
packs. Existing registered packs must not be mutated in place.

## Validation

| Command | Outcome | Notes |
|---|---:|---|
| `PYTHONPATH=$PWD/src python -m pytest tests/unit/features/families/bbo/test_bbo_family.py tests/unit/feature_compute_fast_path/test_bbo_tradability_pack.py tests/unit/feature_compute_fast_path/test_dst_session_boundary_pack.py tests/unit/governance/test_registry_event_ts_grid_canary.py -q` | PASS | `16 passed, 2 skipped`. |
| `PYTHONPATH=$PWD/src python tools/hooks/canary_runner.py` | PASS | All Frontier canaries passed; `registry_event_ts_grid scanned=3 off_grid=4 allowed_debt=4 violations=0` with visible allowlist lines. |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features tests/unit/feature_compute_fast_path tests/unit/futures_substrate_scaleout -q` | PASS | `332 passed`. |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance -q` | PASS | `645 passed`. |
| `PYTHONPATH=$PWD/src python tools/verify.py --smoke` | PASS | Exit 0, no stdout/stderr. |
| `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_ci/bin/python -m pytest tests/tools/test_system_map.py -q` | PASS | `2 passed`; run after regenerating `docs/SYSTEM_MAP.md`. |
| `PYTHONPATH=$PWD/src PATH=$HOME/.venvs/alpha_system_ci/bin:$PATH just ci-parity` | PASS | `3309 passed, 75 skipped in 80.78s`. |
| `PYTHONPATH=$PWD/src python tools/verify.py --all` | PASS | `3309 passed, 75 skipped in 89.19s`; status doctor returned existing WARN because no live run dir exists for committed active campaign `DISCOVERY_RIGOR_FLOOR_V1`. |
| `git ls-files runs` | PASS | No output. |

## Artifact And Boundary Notes

- No BBO re-materialization was run.
- No diagnostics join semantics, label family behavior, canonical-layer
  quote-time `event_ts`, or non-BBO feature families were changed.
- Live registry canary mode was not run because no `ALPHA_DATA_ROOT` or explicit
  registry path is configured in this worktree. The no-registry live skip and
  SQLite scan path are covered by unit tests; CI/default canary execution uses
  the committed synthetic fixture.
- No `runs/`, SQLite, Parquet, Arrow, Feather, DBN, zstd, log, model, secret,
  raw/canonical data, feature values, or label values are tracked.
- Fresh Yellow-lane adversarial review artifacts under
  `reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/` were not created by Codex and
  remain required before merge/closeout.
- Per user instruction, this branch was not pushed and no PR was created.

## Curated Files

- `specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P085901_BBO_EVENT_TS_GRID-bar-grid-contract-and-canary.md`
- `handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P085901_BBO_EVENT_TS_GRID.md`
- `docs/FACTOR_COMPUTE.md`
- `docs/SYSTEM_MAP.md`
- `src/alpha_system/features/families/bbo/family.py`
- `src/alpha_system/features/fast/bbo_tradability.py`
- `src/alpha_system/governance/canaries/__init__.py`
- `src/alpha_system/governance/canaries/registry_event_ts_grid.py`
- `tools/hooks/canary_runner.py`
- `evals/canaries/registry_event_ts_grid/README.md`
- `evals/canaries/registry_event_ts_grid/synthetic_fixture.json`
- `tests/fixtures/feature_compute_fast_path/bbo_tradability.py`
- `tests/fixtures/feature_compute_fast_path/dst_session_boundary.py`
- `tests/unit/feature_compute_fast_path/test_bbo_tradability_pack.py`
- `tests/unit/features/families/bbo/test_bbo_family.py`
- `tests/unit/governance/test_registry_event_ts_grid_canary.py`
