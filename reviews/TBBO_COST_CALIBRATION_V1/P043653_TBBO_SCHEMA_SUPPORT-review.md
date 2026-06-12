# Adversarial Review: P043653_TBBO_SCHEMA_SUPPORT

- Campaign: `TBBO_COST_CALIBRATION_V1`
- Phase: `P043653_TBBO_SCHEMA_SUPPORT`
- Branch: `wf1/tbbo-schema-support` @ `bf0c5be`
- Reviewer: fresh adversarial reviewer (Claude), 2026-06-12
- Diff reviewed: `git diff origin/main` — 6 files, +831/-86

## Verdict

**PASS_WITH_WARNINGS**

The diff does exactly what the spec scopes: `tbbo` added to the request-spec
allowlist, routed through canonicalize via the existing decode/session/write/
manifest machinery (composition, not a fork), with honest tests that the
mutation battery confirms are load-bearing. Two warnings recorded below; no
rework required.

## Scope check (spec items 1-4)

- `src/alpha_system/data/databento/request_spec.py:34` — `"tbbo"` added to
  `DATABENTO_ALLOWED_SCHEMAS`; only other change is the CLI `--schemas` help
  string (line 364). No other request_spec semantics changed. IN SCOPE.
- `src/alpha_system/data/databento/canonicalize.py` — TBBO_SCHEMA /
  TBBO_PARTITION_SCHEMA constants (lines 56, 60), `CanonicalTBBORecord`
  (line 116) carrying event_ts, trade price/size, aggressor side, bid/ask
  price+size (spec minimum met, plus mid/spread/provenance/session fields),
  `_canonicalize_tbbo` (line 812) and `_tbbo_record_from_row` (line 888).
  IN SCOPE.
- `cost_check.py` untouched; `DEFAULT_MAX_COST_USD = 110.0` unchanged
  (cost_check.py:33). `src/alpha_system/{features,labels,runtime,governance}/**`
  untouched (verified by `git diff --stat` against those paths: empty).
- No unrelated refactors found. The one structural change to existing code is
  the `run_canonicalize` conditionalization — see Warning W1.

## Composition vs fork (the +591 in canonicalize.py)

Genuine composition:

- TBBO reuses `_load_rows_by_schema` / `_load_real_dbn_rows` (allowed-set
  widened from a literal `{OHLCV_SCHEMA, BBO_SCHEMA}` to
  `CANONICALIZE_SUPPORTED_SCHEMAS`, lines 536, 569 — same logic, wider set).
- TBBO rows go through the same `sessionize_bars` session/quarantine
  machinery, the same `_write_schema_records` writer, and the same
  `_write_dataset_manifest` (`canonical_dataset_version.v1`) as ohlcv/bbo.
- Shared validators (`_price_decimal`, `_decimal_value`, `_row_timestamp`,
  `normalize_quality_flags`) are reused; new helpers (`_positive_decimal`,
  `_non_negative_decimal`, `_require_text_value`, `_normalize_aggressor_side`)
  are additive.
- `contract_id` getattr fallback in `_tbbo_record_from_row` (line 917) mirrors
  the pre-existing ohlcv pattern at line 658 — consistent, not invented.

Existing ohlcv/bbo behavior on previously-valid inputs is preserved: the
unchanged end-to-end test
`test_databento_canonicalize_quality_coverage_and_register_offline` still
passes, the per-schema write/manifest calls are argument-for-argument
identical, and `_combined_storage_format` reduces to the old
"same-or-mixed" semantics for the two-schema case.

## Findings

### W1 (warning): run_canonicalize relaxes an implicit existing-schema invariant

`run_canonicalize` was restructured from unconditional ohlcv+bbo
canonicalization to per-requested-schema conditionals
(canonicalize.py:298-424). Previously a spec requesting only `ohlcv-1m` (or
only `bbo-1m`) failed with "produced no BBO/OHLCV records"; now schema
subsets succeed. This is a real semantic change to the existing-schema flow,
not a pure addition. Mitigations verified: (a) it is required to route a
tbbo-only spec at all, (b) `run_canonicalize`/`CanonicalizeSummary` have no
consumers outside the module's own CLI `main` and tests (repo-wide grep),
(c) the bbo→ohlcv alignment dependency is preserved via `needs_ohlcv`
(line 300), (d) an all-unsupported-schema request now fails loudly
(line 420). Accepted as in-scope composition; recorded so a future agent
knows subset requests are newly legal.

### W2 (warning): latent TypeError in TBBO dedupe-key sort on mixed sequence types

`_tbbo_dedupe_key` (canonicalize.py:1099) places raw `row.get("sequence")`
(possibly `None`, possibly str vs int across rows) at tuple index 2, and
`_canonicalize_tbbo` sorts on the full key (lines 840, 866). Two rows sharing
`(root, event_ts)` with mixed `None`/int sequences raise an uncaught
`TypeError` instead of a `DataFoundationValidationError`. Real DBN decode
always supplies an int sequence, and the failure mode is a loud crash, not
silent corruption — so warning, not rework. Suggested future fix:
`str(row.get("sequence"))` in the key.

### N1 (note): `CanonicalizeSummary.to_mapping` gained two keys

`tbbo_data_version` / `tbbo_row_count` (lines 91-92, 110-111). No external
consumer hashes or strictly validates the summary mapping (repo-wide grep:
only the module CLI and tests consume it). No second-truth risk.

### N2 (note): `_normalize_aggressor_side` accepts an `"unknown"` alias

(canonicalize.py:1249-1264) slightly wider than the DBN A/B/N domain; local,
normalizes to `"none"`, harmless.

### N3 (note): research-only language respected

Spec/handoff/diff make no alpha/tradability/readiness claims; the handoff
explicitly disclaims TBBO registration/quality/coverage/research-readiness.

## Negative test (spec item: allowlist still gates)

`test_request_spec_rejects_micros_bad_schema_bad_stype_and_non_dbn`
(test_databento_ingest_clis.py:181) keeps a parametrized rejection of
`schemas=("trades",)` — a non-allowlisted schema is still refused. Mutation A
proves the allowlist line is load-bearing.

## Manifest (spec item: canonical_dataset_version.v1 parity)

TBBO partition is written through the same `_write_dataset_manifest` as
ohlcv/bbo (canonicalize.py:401-410), and
`test_databento_tbbo_canonicalize_partition_manifest_and_fields_round_trip`
asserts `partition_schema == "tbbo"`, `row_count == 3`, and path agreement
with `summary.output_paths["tbbo"]`. Parity confirmed.

## Offline discipline

No network calls, no `import databento`, no SDK objects anywhere in the diff
additions (grep over `git diff origin/main` additions: only
`DatabentoRequestSpec` constructor hits). The real-DBN loader test fakes the
`databento` module via `sys.modules` monkeypatch — the pre-existing offline
pattern. Module docstring promise holds.

## Mutation tests (run in worktree, `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/data -q`)

| Mutation | Expected | Observed |
| --- | --- | --- |
| A: remove `"tbbo"` from `DATABENTO_ALLOWED_SCHEMAS` (request_spec.py) | FAIL loudly | **4 failed, 436 passed** (tbbo round-trip, real-DBN loader routing, request-spec acceptance, file-manifest schema inference) |
| B: skip writing tbbo rows (`records=()` in the tbbo `_write_schema_records` call) | FAIL | **1 failed, 439 passed** (`test_databento_tbbo_canonicalize_partition_manifest_and_fields_round_trip`) |
| C: corrupt normalized field name (`aggressor_side` → `aggr_side` in `CanonicalTBBORecord.to_mapping`) | FAIL | **1 failed, 439 passed** (same round-trip test) |

All mutations reverted via `git checkout --`; final `git status --short` clean
and `git diff bf0c5be` empty.

## Handoff truthfulness (reproduced by reviewer)

- `pytest tests/unit/data -q`: claimed `440 passed` → reproduced
  **440 passed in 4.97s**. MATCH.
- `python tools/hooks/canary_runner.py`: claimed 25 PASS lines + "All
  Frontier canaries passed." → reproduced **25 PASS, final line matches,
  exit 0**. MATCH.
- `python tools/verify.py --smoke`: claimed exit 0 → reproduced **exit 0**.
  MATCH.
- Module audit claims (cost_check/submit_batch/download_batch/manifest_files
  already generic; coverage/quality/register_dataset intentionally untouched)
  match the diff (those files have zero hunks) and the manifest-files test
  proves allowlist-driven schema inference picks up tbbo.
- ci-parity claim not re-run by reviewer (full-suite, 83s claim is plausible
  and CI will re-prove it on PR); all reviewer-reproduced numbers matched
  exactly, so the handoff is treated as truthful.

## Artifact policy

Commit `bf0c5be` contains exactly 6 files: spec, handoff, 2 src, 2 test. No
values, SQLite, Parquet, runs/, caches, or data artifacts. `git ls-files runs`
is empty. Handoff lives at the commit-eligible
`handoffs/TBBO_COST_CALIBRATION_V1/` path.

## Maintainability

A fresh agent can inherit this: tbbo is routed symmetrically with the other
two schemas, constants/record/canonicalizer/manifest follow the existing
naming grid, the handoff states precisely which modules are NOT tbbo-aware
(coverage/quality/register_dataset), and W1/W2 above are the only
non-obvious semantics.
