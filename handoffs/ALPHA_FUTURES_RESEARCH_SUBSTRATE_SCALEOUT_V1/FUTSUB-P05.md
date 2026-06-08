# FUTSUB-P05 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Phase: `FUTSUB-P05` - Materialization Budget, Batch Plan, and Resource Guard
Executor: Codex

## Scope Completed

- Added value-free FeaturePack and LabelPack scaleout configs under
  `configs/features/scaleout/` and `configs/labels/scaleout/`.
- Defined bounded batch grids for the eight governed FeaturePack families and
  the governed LabelPack groups over ES/NQ/RTY and years 2018 through 2026.
- Defined per-unit and aggregate row/file budgets.
- Defined deterministic content-addressed `mbu_` batch unit identities.
- Defined `ALPHA_DATA_ROOT`-relative local-only checkpoint roots, per-unit
  completion markers, and completed-unit manifests.
- Defined the serial `materialization_registry` resource guard and restart-safe
  registry backup/restore recovery procedure.
- Added a value-free dry-run identity preview over representative units.
- Updated the README campaign snapshot for P05 and next phase P06.

No materialization was executed. No `alpha feature materialize --execute`,
`alpha label materialize --execute`, provider read, raw/canonical data read,
Parquet write, SQLite registry write, checkpoint marker write, live/paper/broker
operation, order routing, deployment, PR, merge, reviewer call, `review.md`, or
`verdict.json` was performed by Codex.

## Executor Staging

Codex staged no files. The explicit staged file list from Codex is empty.

Ralph stage candidates, by explicit path:

- `configs/features/scaleout/dataset_version_inventory.json`
- `configs/features/scaleout/base_ohlcv.json`
- `configs/features/scaleout/session_calendar_maintenance.json`
- `configs/features/scaleout/vwap_session_auction.json`
- `configs/features/scaleout/regime_volatility_compression.json`
- `configs/features/scaleout/liquidity_sweep_pa_structure.json`
- `configs/features/scaleout/volume_activity.json`
- `configs/features/scaleout/bbo_tradability_top_book.json`
- `configs/features/scaleout/cross_market_alignment.json`
- `configs/labels/scaleout/dataset_version_inventory.json`
- `configs/labels/scaleout/fixed_horizon.json`
- `configs/labels/scaleout/extended_horizon.json`
- `configs/labels/scaleout/session_close_maintenance_flat.json`
- `configs/labels/scaleout/cost_adjusted.json`
- `configs/labels/scaleout/path.json`
- `research/futures_substrate_scaleout_v1/materialization/batch_plan.md`
- `docs/futures_substrate_scaleout/MATERIALIZATION_PLAN.md`
- `README.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P05.md`

No review artifacts were created by Codex; Ralph owns Yellow-lane review
routing and any promotion under
`reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P05/**`.

## Batch Plan Summary

Feature plan:

- Unit grain: `family x symbol x year`.
- Families: `base_ohlcv`, `session_calendar_maintenance`,
  `vwap_session_auction`, `regime_volatility_compression`,
  `liquidity_sweep_pa_structure`, `volume_activity`,
  `bbo_tradability_top_book`, `cross_market_alignment`.
- Universe: ES, NQ, RTY; years 2018 through 2026.
- Budget: `216` units, `118,800,000` output rows, `216` Parquet files.

Label plan:

- Unit grain: `family x symbol x year x horizon` or event horizon.
- Groups: `fixed_horizon`, `extended_horizon`,
  `session_close_maintenance_flat`, `cost_adjusted`, `path`.
- Budget: `729` units, `400,950,000` output rows, `729` Parquet files.

Total governed plan: `945` units and `945` research-scale Parquet value files.
All configs require Parquet for research scale and reject JSONL as the
research-scale storage format.

## Dataset Gate

The committed P02 acceptance summary currently records:

- `ACCEPTED`: `0`
- `ACCEPTED_WITH_WARNINGS`: `0`
- `BLOCKED`: `27`

The configs therefore enumerate the governed DatasetVersion ids as inventory
references and require exact local acceptance-lock resolution before execute.
Downstream materialization must fail closed unless the resolved state is
`ACCEPTED` or `ACCEPTED_WITH_WARNINGS`; registered-only ids are not executable.

## Checkpoint And Recovery Contract

Completion markers and manifests are local-only under
`ALPHA_DATA_ROOT/materialization/futures_substrate_scaleout_v1/checkpoints/`.
A unit can be skipped on resume only when the completion marker, registry
record, DatasetVersion id, and value content hash all match. Inflight units
without a valid completion marker are incomplete and must run recovery before
retry.

The serial registry contract is:

- one writer at a time through `resource_class: materialization_registry`;
- family configs are `parallel_safe: false`;
- registry backups are local-only under
  `materialization/futures_substrate_scaleout_v1/registry_backups/`;
- registry writes occur through sanctioned feature/label materialization APIs;
- the per-unit completion marker is written only after registry commit and hash
  verification.

If interruption occurs during or after registry write, the next run verifies
SQLite integrity, compares the exact registry record against the value-store
hash and DatasetVersion id, restores the local-only registry backup if needed,
and stops rather than continuing if the registry cannot be proven valid.

## Dry-Run Identity Preview

The representative identity preview is value-free and was derived from
canonical JSON descriptors only; it did not execute materialization.

| Kind | Family | Symbol | Year | Variant | Unit id | Plan id preview | Version id preview |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| feature | `base_ohlcv` | `ES` | 2024 | `full_year` | `mbu_7b0557507c0a752391b01652` | `fmat_52b755e02092aad364a26478` | `fver_preview_4becfbd4e7c5c6451d69` |
| feature | `bbo_tradability_top_book` | `NQ` | 2024 | `full_year` | `mbu_a5813a5d38bbab128f565055` | `fmat_a5b5149a5af75931d3978cd8` | `fver_preview_474eabb715b8d0bee1fd` |
| feature | `cross_market_alignment` | `RTY` | 2024 | `full_year` | `mbu_649f69a98d3ce0ad392a46da` | `fmat_08ecdee80a1e294a5a6bceb0` | `fver_preview_f3ce80dbc47cd5ad4df7` |
| label | `fixed_horizon` | `ES` | 2024 | `5m` | `mbu_47797ab6f9871a3945d7709f` | `lmat_140efbcdd0d626099b38ff60` | `lver_preview_4482fcb23f2b9464470d` |
| label | `extended_horizon` | `NQ` | 2024 | `240m` | `mbu_261af5d4c9fab961c6f45555` | `lmat_5de2dadb8dc7372bfdf8239e` | `lver_preview_7a2c91e22d4758f5fe08` |
| label | `session_close_maintenance_flat` | `RTY` | 2024 | `maintenance_flat` | `mbu_f791cf293c412cc1cff01379` | `lmat_4146983a8ba738d95df4591e` | `lver_preview_2562823b74d73f60b611` |
| label | `cost_adjusted` | `ES` | 2024 | `30m` | `mbu_28ef22dffe7489b838372519` | `lmat_380e1a9b1d2071a61c0afadf` | `lver_preview_9b59d67f65ba1ffc9e06` |
| label | `path` | `NQ` | 2024 | `60m_triple_barrier` | `mbu_07e128c12bcf174fb2d9598f` | `lmat_9cd2d2bc777127966cd76077` | `lver_preview_adc4f803f84a2580c4ba` |

## Validation

Commands run from the provided WSL2 worktree root:

Exact JSON parse check:

```bash
python - <<'PY'
import json
from pathlib import Path
for path in sorted(Path('configs/features/scaleout').glob('*.json')) + sorted(Path('configs/labels/scaleout').glob('*.json')):
    with path.open() as fh:
        json.load(fh)
    print(path)
PY
```

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/STOP` | PASS; STOP absent. |
| JSON parse check shown above | PASS; all new JSON configs parsed. |
| `git status --short` | Not run; forbidden by executor safety override. |
| `python tools/verify.py --smoke` | PASS; exit code `0`; no output. |
| `python tools/hooks/canary_runner.py` | PASS; output ended with `All Frontier canaries passed.` |
| `test -f research/futures_substrate_scaleout_v1/materialization/batch_plan.md && test -f docs/futures_substrate_scaleout/MATERIALIZATION_PLAN.md` | PASS; exit code `0`; no output. |
| `PYTHONPATH=src python -m alpha_system.cli feature plan --help` | PASS; read-only help inspection; exit code `0`. |
| `PYTHONPATH=src python -m alpha_system.cli label plan --help` | PASS; read-only help inspection; exit code `0`. |
| `git ls-files runs` | PASS; exit code `0`; output empty. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'` | PASS; exit code `0`; output empty. |

Commands intentionally not run by Codex due to the explicit executor override:

- `git status --short`
- `git diff`
- `git diff --cached --name-only`
- `git add`
- `git commit`
- `git push`
- any PR, merge, review, verdict, or PASS-marking command

## Artifact Boundary

No `runs/**` path, run-local handoff, review artifact, verdict artifact,
Parquet, Arrow, Feather, DB, SQLite, DBN, Zstd, provider response, raw data,
canonical data, feature value, label value, checkpoint marker, registry backup,
secret, credential, cache, or log file was created as a commit candidate by
Codex.

`git ls-files runs` returned empty. The heavy artifact `git ls-files` glob
returned empty. Codex did not stage anything, so no staged set exists from the
executor side.
