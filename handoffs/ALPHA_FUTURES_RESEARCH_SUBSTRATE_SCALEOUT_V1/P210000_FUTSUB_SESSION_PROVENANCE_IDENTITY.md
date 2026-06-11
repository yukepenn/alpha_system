# P210000_FUTSUB_SESSION_PROVENANCE_IDENTITY Handoff

## Branch / State

- Branch: `repair/futsub-session-identity`
- Base / HEAD: `origin/main` @ `6a4244da15bed79f5ea41c43b9c8d31cdca9e1e8`
- Commits: none. Changes are intentionally unstaged and uncommitted per executor instruction.
- Review artifacts: none created per executor instruction (`no commits/PRs/reviews`), despite the Yellow-lane default.

## Scope Completed

- Extended Base OHLCV feature contract construction so session-truth provenance is included whenever an OHLCV feature is session-conditioned:
  - inherently session-truth features (`session_minute`, `rth_flag`, `eth_flag`, `opening_range`, `overnight_range`, `vwap`, `anchored_vwap`, `distance_to_vwap`);
  - all `reset_on_session=True` OHLCV features, including returns/log-returns/rolling and resettable reduce features.
- The injected identity-bearing provenance comes from `alpha_system.data.foundation.sessions.load_session_template_by_id()`:
  `session_template_id`, `session_timezone`, `rth_open_time_local`, `rth_close_time_local`, and `session_truth_source`.
- Added a `vwap_session_auction` fast-pack guard that rejects governed pack specs missing or mismatching that session-truth provenance.
- Added identity tests proving:
  - session-conditioned specs rotate from legacy absent session truth;
  - `reset_on_session=False` plain returns do not rotate when the session template changes.
- Added a temp-registry supersession test proving a deprecated old id and a new session-truth id can coexist, with the old row carrying a replacement pointer to the new row.
- Fixed an order-sensitive CLI test isolation issue exposed by the required `-k 'identity or version ...'` command: the affected tests now clear provider-client modules before asserting their plan path did not import them.

## Files Changed

- `src/alpha_system/features/families/ohlcv/family.py`
- `src/alpha_system/features/fast/vwap_session_auction.py`
- `tests/unit/features/test_feature_identity_invariant.py`
- `tests/unit/features/test_feature_store.py`
- `tests/unit/cli/test_feature_cli.py`
- `tests/unit/cli/test_label_cli.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P210000_FUTSUB_SESSION_PROVENANCE_IDENTITY.md`

## Validation

- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features -q`
  - PASS: `135 passed in 1.27s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k 'identity or version or vwap or ohlcv or session' -q`
  - PASS: `262 passed, 2363 deselected in 3.75s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q`
  - EXPECTED ENV FAILURES ONLY: `3 failed, 2861 passed, 1 skipped in 57.17s`
  - Known pre-existing failures:
    - `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`
    - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`
    - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`
- `python tools/verify.py --smoke`
  - PASS: no output
- `python tools/hooks/canary_runner.py .`
  - PASS: 21 canaries, final line `All Frontier canaries passed.`

Extra focused checks:

- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features/test_feature_identity_invariant.py -q`
  - PASS: `13 passed in 0.20s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features/test_feature_store.py -q`
  - PASS: `9 passed in 0.95s`
- `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py tests/unit/features/families/ohlcv/test_ohlcv_family.py -q`
  - PASS: `16 passed in 0.42s`

## Artifact / Boundary Audit

- `git diff --cached --name-only`: empty.
- `git ls-files runs`: empty.
- `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.sqlite3' '**/*.db' '**/*.dbn' '**/*.zst'`: empty.
- `git diff --check`: no output.
- No edits under forbidden paths: `src/alpha_system/labels/**`, canonicalize/dataset configs, registry write paths/schema, or `governance/duplicate_exposure.py`.
- No materialization, registry mutation outside temp test registries, data rewrite, PR, review artifact, or commit was created.
- No `git worktree` command was run and `.git` config was not modified.
- The phase spec file remains untracked task input in this worktree.

## Expected Supersession Behavior

After merge, re-materializing `vwap_session_auction` and any `reset_on_session=True` OHLCV features produces new `feature_version_id`s because the session template id and resolved RTH window/timezone are now part of the content-addressed contract. Coordinator deprecation should mark old registered ids deprecated with replacement pointers to the new ids through the sanctioned FeatureStore/registry API. Non-session-conditioned features such as `reset_on_session=False` plain returns should keep their existing identities.

## Risks / Caveats

- The full suite still has the three documented environment failures listed above.
- Fast packs outside `vwap_session_auction` may still have their own session-label grouping follow-ups from P194500 W2; this phase only changes OHLCV contract identity and the vwap/session-auction pack guard.
