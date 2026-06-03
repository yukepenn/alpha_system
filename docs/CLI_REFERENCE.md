# CLI Reference

## Scope

This reference summarizes the current `alpha` command surface required for the
v0.1 research workflow. It is intentionally concise. Use `--help` as the source
of truth for exact flags and required arguments:

```bash
alpha --help
alpha <group> <command> --help
```

If the package is not installed, use:

```bash
PYTHONPATH=src python -m alpha_system --help
```

Commands are local-first. Generated outputs, local SQLite DBs, reports,
bundles, data files, factor stores, label stores, logs, and caches are
local-only unless a later phase explicitly authorizes a curated exception.

## Commands

| Command | Purpose | Main inputs | Main outputs | Artifact restrictions |
| --- | --- | --- | --- | --- |
| `alpha data validate` | Validate local CSV data or tiny fixtures against data-quality and timestamp rules. | Validation config, local input path, optional schema/calendar ids, optional temp/local registry path. | Console summary and optional local-only JSON, Markdown, or CSV summary. | Summaries and registry DBs are local-only. Do not commit raw inputs, generated summaries, or SQLite files. |
| `alpha data build-bars` | Build canonical 1-minute bars from allowed local fixture input. | Input path, instrument config, calendar config, output path, data version, optional validation config and temp/local registry path. | Local-only canonical bar output and optional registry entry. | Canonical generated data is local-only. Do not commit data payloads, DB files, Parquet, Arrow, or Feather. |
| `alpha factor validate` | Validate a `FactorSpec`, declared inputs, hashes, lifecycle eligibility, and optional registry entry. | Factor spec path, optional code path, validation artifact reference, used-field checks, summary path, temp/local registry path. | Console summary, optional local-only summary, optional temp/local registry records. | Registry DBs and summaries are local-only. Do not commit SQLite files or generated validation artifacts unless a later spec allows a curated doc artifact. |
| `alpha factor materialize` | Compute factor values from canonical local bars using a validated spec. | Factor spec, canonical data path, data version, optional instrument/session/time filters, output policy, output dir, manifest path, registry path. | Dry-run summary or local-only factor store/manifests depending on output policy. | Materialized factor values, manifests, and registry DBs are local-only. Prefer temp/local paths outside the repository for experiments. |
| `alpha study run` | Run Tier 0 factor diagnostics over versioned factor values and labels. | Study config or overrides, factor values path, labels path, factor/label/data versions, filters, output dir, manifest, registry path. | `diagnostic_summary.json`, run manifest, optional registry records. | Default generated study artifacts are under local-only artifact roots. Do not commit reports, manifests, generated outputs, or registry DBs. |
| `alpha grid run` | Run bounded strategy grids on declared versioned inputs. | Grid config, declared strategy/management/portfolio/execution specs, data/factor/label versions, engine selection, output dir, manifest, registry path. | Leaderboard, summary, monthly/cost outputs, top configs, rejected configs, run manifest. | Grid artifacts and registry DBs are local-only. Rejected configs and failed steps must remain visible. Fast mode is acceleration-only and parity-gated. |
| `alpha management grid` | Run survivor-gated bounded position-management grids. | Management-grid config, survivor/source-grid reference, engine selection, output paths, manifest, registry path. | Baseline comparison, leaderboard, rejected configs, warnings, survivor eligibility summary, run manifest. | Management-grid outputs are local-only. Survivor gating is evidence for review, not approval. Fast requests must pass parity or fall back/fail closed according to config. |
| `alpha ml run` | Run local ML or factor-combination fixture workflows on versioned factor inputs. | ML run config or component specs, observations, feature set, label spec, model spec, split config, data/factor/label versions, output dir, registry path. | Local ML summary/artifacts and optional registry record. | ML outputs and registry DBs are local-only. Labels are never features. Scores are not promotion decisions. |
| `alpha backtest run` | Run the Tier 1 Reference 1-minute backtest truth model. | Strategy id/version, bars path, signals path, data version, factor versions, execution config, optional management/portfolio specs, output dir, run manifest, registry path. | Trade journal, equity curve, summary, run manifest, optional registry row. | Full backtest outputs are local-only. The Reference engine is the single PnL truth. It is not broker/live trading, paper trading, or order routing. |
| `alpha report build` | Build local reports, factor cards, study reports, or review bundles. | Report kind, run id, registry path, artifact manifest, run manifest, config, source root, diagnostic summaries, metadata, output path/dir. | Markdown, CSV, JSON, and optional static HTML report artifacts. | Generated reports and bundles are local-only. Review bundles support audit and review; they do not approve or promote candidates. |
| `alpha registry status` | Inspect local metadata registry state. | Registry path or tiny config with registry path. | Console or JSON status summary. | Registry DBs are local-only. Do not commit SQLite, DB, journal, or WAL files. |

## Command Boundaries

No CLI command is a broker adapter, paper-trading adapter, live-trading
system, order router, account sync tool, deployment tool, PR creator, merge
tool, or hidden cleanup tool.

Fixture outputs are correctness validation only. They are not market evidence
and do not support alpha, profitability, robustness, tradability, approval, or
production-readiness claims.

## Local-Only Output Roots

Some commands have conservative local defaults or documented local roots. These
paths are for inspection and audit, not git:

- factor stores default outside the repo under `/tmp/alpha_system/factors`
  when persistence is explicitly requested.
- study outputs may use `artifacts/factor_studies/` inside the repo, which is
  local-only for generated artifacts.
- strategy grid outputs may use `artifacts/strategy_grids/` inside the repo,
  which is local-only for generated artifacts.
- backtest outputs default outside the repo under `/tmp/alpha_system/backtests`
  in the Reference backtest layer.
- ML outputs default outside the repo under a temp `alpha_system_ml_experiments`
  root when no output directory is supplied.
- review bundles may use `artifacts/review_bundles/` inside the repo, which is
  local-only for generated bundles.

If a command accepts an output path, prefer `/tmp` or another temp/local path
for experiments. If a repo-local generated output root is used, keep it
unstaged and confirm artifact policy before any commit.
