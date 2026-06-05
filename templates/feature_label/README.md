# Feature/Label YAML Templates

These YAML templates are reusable request skeletons for the Feature/Label
Foundation substrate. They are placeholders for authors and agents; the
governance contracts and feature/label contract docs remain authoritative.

Templates:

- `feature_request.template.yaml`
- `feature_spec.template.yaml`
- `label_spec.template.yaml`

Guardrails:

- use governed `freq_`, `lspec_`, `aspec_`, and `sspec_` references only where
  those objects already exist or are explicitly planned;
- do not create alternate governance objects or id prefixes;
- do not include raw provider paths, provider responses, local data-root paths,
  materialized values, registry DB paths, logs, caches, or heavy artifacts;
- do not use a template as evidence, approval, implementation permission, a
  study result, or a trading claim.
