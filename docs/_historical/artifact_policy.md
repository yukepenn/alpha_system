# Artifact Policy

Document which generated artifacts belong in git and which should remain local.

Allowed by default:

- harness files
- source files
- tests
- docs
- specs, handoffs, reviews, decisions
- curated evals and configs

Forbidden by default:

- secrets and credentials
- raw data
- caches
- local virtual environments
- large binary artifacts
- model weights
- generated logs

The authoritative policy lives in `frontier.yaml`.
