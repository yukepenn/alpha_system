# FUTSUB-P02 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P02` - DatasetVersion Inventory and Acceptance-Lock Contract  
Executor: Codex  
Lane: Yellow

## Status

Executor implementation scope is complete for canonical-evidence computation,
policy/config, docs, tests, README snapshot, value-free summary, and this
handoff. This handoff does not mark the phase PASS.

Local registry persistence was attempted through the sanctioned CLI path and is
blocked in this executor environment because the DatasetVersion registry opened
as read-only:

```text
dataset acceptance error: could not persist DatasetVersion acceptance lock: dsv_databento_bbo_22c49fbf57cceea6: attempt to write a readonly database
```

Ralph or an unsandboxed local operator must rerun the persist command with a
writable `$ALPHA_DATA_ROOT/registry/datasets.sqlite` before downstream phases
can treat these acceptance locks as persisted.

No live trading, paper trading, broker operation, order routing, provider call,
raw provider file read, feature/label materialization, diagnostics run, PR
creation, merge, reviewer call, `review.md`, or `verdict.json` was performed by
Codex.

## Scope Completed

- Extended `_coverage_evidence_from_registry_metadata` to compute the five P02
  evidence dimensions from the canonical manifest row count, sanctioned
  `canonical_partition_path` / `load_canonical_ohlcv_rows`, and registry
  metadata.
- Added policy-normalized canonical root/partition-schema mapping and value-free
  coverage thresholds for row counts, symbol-minute coverage, trading-day
  coverage, and quality-flag ratios.
- Added partial-year warning semantics so 2026 resolves to
  `ACCEPTED_WITH_WARNINGS` when otherwise within tolerance.
- Made `roll_metadata` explicit and degradable: the P02 policy defers exact
  approximate roll-boundary records to FUTSUB-P03 without fabricating records or
  forcing a uniform blocked grid.
- Regenerated the value-free acceptance summary from read-only inventory.
- Added unit tests for computed canonical evidence, fail-closed missing evidence,
  partial-year warnings, roll defer warnings, persistence/no-network behavior,
  and three-state verdict mapping.

## Inventory Result

Read-only inventory command:

```bash
PYTHONPATH=src python -m alpha_system.cli registry dataset-acceptance inventory --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --config configs/data/dataset_acceptance/futsub_p02_policy.json --summary-out research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md --json
```

Result:

- Expected schema/year matrix complete: `yes`.
- In-scope Databento DatasetVersions inventoried: `27`.
- `ACCEPTED`: `20`.
- `ACCEPTED_WITH_WARNINGS`: `5`.
- `BLOCKED`: `2`.

The two blocked locks are the sparse 2018 OHLCV/BBO DatasetVersions. Both block
because RTY is below the 0.90 row-count and minute-coverage blocking floor
against the on-disk ES/NQ/RTY union-minute grid. Sparse 2019 OHLCV/BBO warn for
RTY below the 0.95 warning floor; the three 2026 versions warn because they are
partial-year windows. Dense OHLCV full years are accepted.

## Files Created Or Modified

Codex staged no files. Ralph stage candidates for this phase, by explicit path:

| Path | Outcome |
| --- | --- |
| `src/alpha_system/data/foundation/datasets.py` | Computes canonical evidence dimensions, policy thresholds, partial-year warnings, and roll defer evidence. |
| `configs/data/dataset_acceptance/futsub_p02_policy.json` | Adds canonical partition schema mapping and acceptance thresholds; defers roll metadata to P03. |
| `docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md` | Documents canonical evidence method, verdict semantics, and P03 roll metadata interaction. |
| `research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md` | Regenerated value-free read-only inventory summary. |
| `tests/unit/futures_substrate_scaleout/test_dataset_acceptance.py` | Adds synthetic canonical fixture tests for computed evidence and warning/block mapping. |
| `README.md` | Updates compact campaign snapshot for P02 and next P03. |
| `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P02.md` | Updated this executor handoff. |

No review artifact was created by Codex because the executor prompt explicitly
forbids calling the reviewer, creating `review.md`, creating `verdict.json`, or
marking the phase PASS. Ralph owns Yellow-lane review routing.

## Git And Artifact Hygiene

- `git status --short`: not run; forbidden by executor safety override.
- `git diff`, `git diff --cached --name-only`, `git add`, `git commit`,
  `git push`, force push: not run.
- Staging: Codex performed no staging.
- `git ls-files runs`: passed with empty output.
- `git ls-files '**/*.sqlite' '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'`: passed with empty output.
- No `runs/` path, forbidden data path, DB/cache/log/heavy artifact, or
  `ACTIVE_CAMPAIGN.md` was staged by Codex.

## Validation

Commands run from the provided WSL2 worktree root:

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP && test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P02/STOP` | PASS; STOP absent. |
| `python -m py_compile src/alpha_system/data/foundation/datasets.py src/alpha_system/cli/registry.py src/alpha_system/cli/data.py tests/unit/futures_substrate_scaleout/test_dataset_acceptance.py` | PASS. |
| `python -m pytest tests/unit/futures_substrate_scaleout/test_dataset_acceptance.py -q` | PASS; `6 passed`. |
| `PYTHONPATH=src python -m alpha_system.cli registry dataset-acceptance inventory --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --config configs/data/dataset_acceptance/futsub_p02_policy.json --json` | PASS; 27 locks; state counts `20/5/2`; expected matrix complete. |
| `PYTHONPATH=src python -m alpha_system.cli data accept-datasets --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --config configs/data/dataset_acceptance/futsub_p02_policy.json --summary-out research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md --json` | BLOCKED; exit code `2`; SQLite reported `attempt to write a readonly database`. |
| `PYTHONPATH=src python -m alpha_system.cli registry dataset-acceptance inventory --registry-path "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --config configs/data/dataset_acceptance/futsub_p02_policy.json --summary-out research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md --json` | PASS; regenerated value-free read-only summary. |
| `python tools/verify.py --smoke` | PASS. |
| `python tools/verify.py --lint` | ENV-ONLY SKIP; exit code `0`; `ruff is not installed; run pip install -e ".[dev]" to enable lint. Skipping.` |
| `python tools/verify.py --typecheck` | PASS; ran compileall across `src`, `tests`, and `tools`. |
| `python tools/hooks/canary_runner.py` | PASS; all Frontier canaries passed. |
| `test -f research/futures_substrate_scaleout_v1/dataset_acceptance/acceptance_summary.md && test -f docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md` | PASS. |
| `git ls-files runs && git ls-files '**/*.sqlite' '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'` | PASS; output empty. |

`python tools/verify.py --all` was not run because the spec says to broaden to
`--all` only if shared behavior beyond the acceptance path changes; this work
stayed within the DatasetVersion acceptance path.

## Boundary Confirmation

No forbidden modules were edited. No external provider/network call, re-pull,
raw-provider file read, materialized feature/label value, diagnostics run,
StudySpec lock, alpha ideation, broker/live/paper/order/deployment action, PR,
merge, review artifact, local SQLite/Parquet/heavy artifact commit candidate,
or `ACTIVE_CAMPAIGN.md` edit was performed by Codex.
