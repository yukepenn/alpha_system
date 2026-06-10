# FUTSUB-P04 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Phase: `FUTSUB-P04` - Value Store / Registry / Keystone Identity Preflight
Executor: Codex

## Scope Completed

- Added a focused synthetic preflight test for the keystone identity chain:
  dry-run preview, executed Parquet materialization, value-store manifest,
  feature/label registry records, version locks, and runtime resolver handles.
- Verified feature and label registry metadata fields:
  `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `dataset_version_id`, and feature/label version ids.
- Verified resolver fail-closed behavior for stale and fuzzy feature/label
  locks with no substitution.
- Added a value-free preflight report and durable keystone identity contract.
- Updated the README campaign snapshot for P04 and next phase P05.

No full-window materialization, runtime diagnostics edit, alpha work, live or
paper trading, broker operation, provider call, PR, merge, reviewer call,
`review.md`, or `verdict.json` was performed by Codex.

## Commit-Eligible Files For Ralph

Codex did not stage files. Ralph should stage curated paths explicitly if this
handoff is accepted.

- `README.md`
- `docs/futures_substrate_scaleout/KEYSTONE_IDENTITY.md`
- `research/futures_substrate_scaleout_v1/preflight/keystone_identity_preflight.md`
- `tests/unit/futures_substrate_scaleout/test_keystone_identity.py`
- `handoffs/FUTSUB-P04.md`

Explicit staged file list from Codex: none. Codex did not run staging, commit,
push, status, or diff commands per the executor override.

## Local-Only Artifacts

The P04 unit test creates temporary Parquet, manifest, and SQLite registry files
only under pytest temporary directories at test runtime. No committed repository
Parquet, SQLite, Arrow, Feather, DBN, Zstd, raw provider, feature-value, or
label-value artifact was created by Codex.

No run-local `handoff.md`, `review.md`, or `verdict.json` was created.

## Validation

Commands run from the repository root:

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP` | PASS; STOP absent. |
| `git status --short` | Not run; forbidden by executor safety override. |
| `python tools/verify.py --smoke` | PASS; exit code `0`, no output. |
| `python -m pytest tests/unit/futures_substrate_scaleout/test_keystone_identity.py -q` | PASS; `1 passed in 0.54s`. |
| `python tools/hooks/canary_runner.py` | PASS; output ended with `All Frontier canaries passed.` |
| `test -f research/futures_substrate_scaleout_v1/preflight/keystone_identity_preflight.md` | PASS; exit code `0`, no output. |
| `test -f docs/futures_substrate_scaleout/KEYSTONE_IDENTITY.md` | PASS; exit code `0`, no output. |
| `git ls-files runs` | PASS; exit code `0`, output empty. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS; exit code `0`, output empty. |

Commands intentionally not run by Codex due to explicit executor override:

- `git status --short`
- `git diff --cached --name-only`
- any staging, commit, push, PR, merge, review, or verdict command

Ralph owns staged-set audit, review routing, verdict parsing, PR, CI, merge
gate, and done-check actions.
