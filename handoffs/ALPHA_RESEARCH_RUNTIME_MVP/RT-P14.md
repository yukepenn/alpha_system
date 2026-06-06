# ALPHA_RESEARCH_RUNTIME_MVP / RT-P14 Handoff

## Curated file list for Ralph staging

Codex staged no files. Per the executor override, Ralph should stage only these
commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/audit/__init__.py`
- `src/alpha_system/runtime/audit/no_lookahead.py`
- `tests/unit/runtime/audit/test_no_lookahead_audit.py`
- `tests/no_lookahead/research_runtime/test_no_lookahead_runtime_audit.py`
- `docs/research_runtime/NO_LOOKAHEAD_AUDIT.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P14.md`

No `runs/` path is included. No
`reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P14/**` files were created by Codex;
fresh review and verdict artifacts are owned by Ralph/reviewer.

## Implementation summary

RT-P14 adds `alpha_system.runtime.audit` with `NoLookaheadRuntimeAudit`.
The audit inspects resolved runtime metadata and scalar signal-probe metadata,
then returns a visible `NoLookaheadAuditResult` with
`NoLookaheadAuditReason` records.

Covered fail-closed classes:

- missing or invalid feature `available_ts`, including availability after the
  decision timestamp;
- missing or invalid label `label_available_ts`;
- label-valued fields or refs exposed as live features/signals;
- centered or future live feature windows;
- same-bar optimistic probe fill metadata;
- locked/shadow partition use without governance contamination metadata, plus
  forbidden locked-test selection.

The result is integrity-only and recordable. Rejected audits carry
`leakage_risk` or `blocked_by_policy` categories and expose
`runtime_entry_reasons` in the existing `RuntimeEntryReason` shape.

## Scope and primitive boundary

The audit consumes `RuntimeInputPack`, optional `SignalProbeSpec` /
`SignalProbeReport`, feature/label metadata, window metadata, and partition
governance metadata. It does not resolve DatasetVersions, read FeatureStore or
LabelStore values, read raw provider files, import provider readers, call
external providers, calculate diagnostics, run probes, or duplicate research,
experiments, governance, backtest, feature, label, data, cost, or grid
primitive math.

No files under forbidden primitive, broker, live, paper, order-routing, raw
data, canonical data, metadata DB, cache, or artifacts paths were edited by
Codex.

## README snapshot

`README.md` now records the RT-P14 No-Lookahead Runtime Audit snapshot, sets the
active/next pointer to `RT-P15` - RejectionReasonRecord and Runtime Decision
States, lists `alpha_system.runtime.audit` and
`docs/research_runtime/NO_LOOKAHEAD_AUDIT.md`, and keeps the unchanged
local-first, accepted-DatasetVersion-only, no raw-provider, no external
provider-call, no broker/live/paper/order/account, and non-promotional safety
boundaries.

## Validation

- `find runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP -maxdepth 1 -name STOP -print`
  - Result: exit 1; the run directory was absent in this checkout, so no STOP
    file was found there.
- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP`
  - Result: exit 0; no run-level STOP marker exists at the specified path.
- `python -m ruff format src/alpha_system/runtime/audit tests/unit/runtime/audit tests/no_lookahead/research_runtime/test_no_lookahead_runtime_audit.py`
  - Result: exit 0; `3 files reformatted, 1 file left unchanged`.
- `python -m ruff check src/alpha_system/runtime/audit tests/unit/runtime/audit tests/no_lookahead/research_runtime/test_no_lookahead_runtime_audit.py`
  - Result: exit 0; `All checks passed!`.
- `python -c "import alpha_system.runtime.audit"`
  - Result: exit 1; `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this executor shell does not put `src` on `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.audit"`
  - Result: exit 0.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime/audit -q`
  - Result: exit 0; `2 passed in 0.13s`.
- `python -m pytest tests/no_lookahead/research_runtime -q`
  - Result: exit 0; `14 passed in 0.15s`.
- `test -f docs/research_runtime/NO_LOOKAHEAD_AUDIT.md`
  - Result: exit 0.
- `git ls-files runs`
  - Result: exit 0 with empty output.
- `python -m ruff format --check src/alpha_system/runtime/audit tests/unit/runtime/audit tests/no_lookahead/research_runtime/test_no_lookahead_runtime_audit.py`
  - Result: exit 0; `4 files already formatted`.
- `rg -n "ALPHA_VALIDATED|FACTOR_PROMOTED|STRATEGY_READY|PORTFOLIO_READY|LIVE_READY|PAPER_READY|PROFITABLE|TRADABLE|PRODUCTION_READY" src/alpha_system/runtime/audit tests/unit/runtime/audit tests/no_lookahead/research_runtime/test_no_lookahead_runtime_audit.py docs/research_runtime/NO_LOOKAHEAD_AUDIT.md README.md`
  - Result: exit 1 with empty output; no prohibited MVP state token matched.
- `find src/alpha_system/runtime/audit tests/unit/runtime/audit tests/no_lookahead/research_runtime -type f -size +1M -print`
  - Result: exit 0 with empty output.
- `python -m pytest tests/unit/runtime -q`
  - Result: exit 0; `155 passed in 0.41s`.

Skipped:

- `git status --short`
  - Reason: explicitly forbidden by the executor safety override.
- `git diff --cached --name-only` and any staged-set inspection using `git diff`
  - Reason: explicitly forbidden by the executor safety override, and Codex
    staged no files.
- `python tools/verify.py --all`
  - Reason: the generated RT-P14 executor prompt requested only safe,
    phase-listed validation. Focused audit tests, the required no-lookahead
    suite, smoke, scoped lint/format, artifact checks, and a broader
    `tests/unit/runtime` sweep passed. Ralph owns merge-gate broad validation.
- `python tools/hooks/canary_runner.py`
  - Reason: not listed in the generated RT-P14 validation commands for Codex;
    Ralph owns merge-gate validation.
- Claude review, `review.md`, and `verdict.json`
  - Reason: explicitly forbidden by the executor safety override; Ralph owns
    reviewer orchestration and verdict parsing.

## Artifact audit

- `git ls-files runs` returned empty output.
- No `runs/**` artifact was created or edited by Codex.
- No files were staged by Codex; therefore this executor introduced no staged
  `runs/` path and no staged forbidden heavy/data/cache/log/DB artifact.
- The touched source/test paths contain no file larger than 1 MB by the scoped
  `find ... -size +1M` check.
- No raw/canonical/feature/label/runtime value artifact, local DB, parquet,
  arrow, feather, DBN, ZST, log, cache bundle, model binary, broker, live,
  paper, order-routing, provider-response, or deployment file is in the Ralph
  staging list above.

## Caveats and review needs

- The exact bare import command from the generated spec fails in this executor
  shell unless `PYTHONPATH=src` is supplied. The supplemental import with
  `PYTHONPATH=src`, pytest, and smoke validation passed.
- Formal RT-P15 `RejectionReasonRecord` and runtime decision states remain later
  phase scope. RT-P14 exposes audit reasons in a compatible current-runtime
  shape without implementing RT-P15.
- Yellow-lane review artifacts are still required before merge, but Codex was
  explicitly forbidden from calling Claude, running reviewer, or creating
  `review.md` / `verdict.json`.
