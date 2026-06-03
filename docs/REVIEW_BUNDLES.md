# Review Bundles

Review bundles collect local evidence for a run into an inspectable directory. They are for research governance and AI Agent review, not for promotion-state changes or execution actions.

The builder is available through:

```bash
alpha report build --run-id <run_id> --registry-path <registry.sqlite3> --artifact-manifest <artifact_manifest.json> --run-manifest <run_manifest.json> --output-dir <local_dir>
```

`--source-root` can point at the repository root used for source-map discovery. `--config` defaults to `configs/reports/review_bundle.yaml`. `--include-html` writes a small static index in addition to Markdown, CSV, and JSON outputs.

Bundles include the run manifest, source map, config and code hashes, data/factor/label versions, engine version, registry records, diagnostics, optional backtest/cost/monthly sections, rejected configs, warnings, failed-step visibility, promotion decision status, no-lookahead validation status, artifact manifest, known limitations, and review status.

Generated bundle directories are local-only. Repo-local outputs must stay under `artifacts/review_bundles/`; temp directories are allowed for tests and one-off inspection. Full generated bundles are not commit artifacts.

Missing artifacts, failed runs, and rejected configs are first-class bundle sections. The builder surfaces them as warnings instead of filtering them out.

