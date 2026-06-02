# Domain Boundaries

## Invariants

The platform enforces separation between research domains:

- Data is not factor.
- Factor is not signal.
- Signal is not strategy.
- Strategy is not portfolio.
- Portfolio is not execution.
- Backtest is not live trading.
- Fast research simulation is not execution truth.
- Draft factor values are not automatically long-term stored.
- Only validated and reviewed factors may be materialized into the long-term
  factor store.

These statements are not naming preferences. They are reviewable invariants for
later implementation phases.

## Boundary Meanings

Data contains point-in-time market or derived canonical observations. A factor
is a declared transformation over valid inputs. A signal converts factor state
into a decision primitive. A strategy defines entry, exit, and management
rules. A portfolio layer handles sizing, exposure, and portfolio constraints.
Execution truth is measured by the approved backtest tier.

Crossing a boundary requires an explicit versioned artifact, declared inputs,
timestamp semantics, and reviewable metadata.

## Materialization Rules

Exploratory factor values may exist as local draft artifacts. They do not enter
the long-term factor store by default. Materialization requires validation,
review state, factor version, data version, config hash, code hash, and a run
manifest.

## Reproducibility Boundary

Every result must be reproducible through:

- git commit
- code hash
- config hash
- data version
- factor version
- label version
- engine version
- run manifest

If any required version or hash is missing, the result is incomplete for
review.

## No Execution Scope Creep

Backtest outputs are not live trading. No broker, paper trading, live trading,
order routing, or production execution is part of the v1 boundary.
