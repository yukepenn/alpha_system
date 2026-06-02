# Target CLI Commands

## Status

This is design intent only. ASV1-P02 does not implement a CLI, package entry
point, parser, command module, schema, registry, engine, or test.

## Target Surface

| Command | Intended Role |
| --- | --- |
| `alpha data validate` | Validate local input data and quality rules. |
| `alpha data build-bars` | Build canonical bars from validated local inputs. |
| `alpha factor validate` | Validate factor definitions and declared inputs. |
| `alpha factor materialize` | Materialize reviewed factor values into the long-term factor store. |
| `alpha study run` | Run bounded factor diagnostics or study workflows. |
| `alpha grid run` | Run bounded parameter grids for specific hypotheses. |
| `alpha management grid` | Run constrained management-rule grids for survivors. |
| `alpha ml run` | Run versioned factor-combination or ML workflows. |
| `alpha backtest run` | Run the Reference backtest truth model. |
| `alpha report build` | Build local Markdown, CSV, or optional static HTML reports. |
| `alpha registry status` | Summarize local registry versions and run state. |

## Command Principles

Commands should be local-first, deterministic, and manifest-producing. They
should fail closed when required timestamps, versions, hashes, or configs are
missing. They should not require cloud storage, a paid database, a database
server, a workflow server, an MLflow server, or a web UI.

No command target includes broker operations, paper trading, live trading,
order routing, production deployment, PR creation, merge, or hidden cleanup.
