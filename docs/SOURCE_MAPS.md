# Source Maps

Source maps describe which files and artifact references were used to assemble a review bundle. They are deterministic over the supplied source root, manifest references, registry reference, and configured file patterns.

Default patterns come from `configs/reports/review_bundle.yaml` and include the report modules, the report CLI, report config, and review-bundle tests. Callers may pass a different source root or config when inspecting a worktree.

Each source-map file entry records:

- repo-relative path when the file is under the source root,
- file kind: source, config, or test,
- existence at build time,
- content hash when the file exists,
- size in bytes,
- warnings for missing files.

Artifact references are listed separately from source/config/test files. Their entries preserve the manifest key, path, existence status when discoverable, content hash when available, and policy warnings.

Source maps are evidence indexes. They do not run validation, alter registry rows, or create a second result calculation path.

