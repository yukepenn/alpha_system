# ML Leakage Policy

The ML MVP follows the same no-lookahead boundary as the rest of the research harness. Its primary controls are enforced in `FeatureSetSpec`, `LabelSpec`, split utilities, and the run orchestrator.

## Feature Inputs

ML features must reference versioned factor inputs only. A feature entry must resolve to a declared `factor_id` and `factor_version` in `factor_versions`.

Rejected inputs include:

- raw or ad hoc columns;
- canonical bar columns used directly as model features;
- dataframe expressions;
- label, target, or outcome fields;
- feature specs whose factor version does not match `factor_versions`.

## Label Exclusion

Labels are never features. `LabelSpec.label_id` is checked against factor ids and feature ids before a run can score fixture rows. Any feature entry with label-style source fields is rejected.

## Label Availability

Each scored row must include a decision timestamp and a label-availability timestamp. `label_available_ts` must be no later than `decision_ts` for the row. Rows that violate this rule are rejected before fitting.

## Split Discipline

Train/validation splits are chronological. Training indices precede validation indices, and train/validation overlap is rejected.

Walk-forward splits use a finite train window followed by a finite validation window. Each fold records explicit sample positions.

Purge and embargo gaps remove training indices around the validation window. This prepares the MVP for stricter event-window leakage controls in later phases without adding model-serving or execution behavior.

## Promotion Boundary

ML scores are research outputs, not promotion decisions. The ML run registry records `ml_recorded`; reviewed promotion remains a separate gate.
