# Local Data Root Policy Contract

`LocalDataRootPolicy` is the data-foundation record that pins real data artifacts to a
local, ignored, outside-repository root. It is a path policy only. It does not create
directories, write real data, read provider data, or make network calls.

## `ALPHA_DATA_ROOT`

The data root is read from `ALPHA_DATA_ROOT`. If the variable is absent, the suggested
default is:

```text
~/alpha_data/alpha_system
```

The resolved root must be:

- local to the WSL2 Linux filesystem;
- outside the repository tree;
- not under a forbidden repo data path;
- not under a Windows mount, synced/cloud folder, network path, or temporary directory;
- treated as ignored or non-committable by location.

The directory does not need to exist for policy validation. DATA-P02 validates paths
without filesystem writes.

## Required Fields

| Field | Meaning |
| --- | --- |
| `data_root` | Resolved local root for future real data artifacts. |
| `must_be_local` | Must be `true`; non-local roots fail closed. |
| `must_be_ignored` | Must be `true`; in-repo or committable roots fail closed. |
| `forbidden_repo_paths` | Repo-relative paths that must not be used as real data roots. |
| `allowed_subdirs` | Simple subdirectory names allowed below the local root. |
| `max_file_policy` | File-size policy requiring `oversize_action = fail_closed`. |

The default forbidden repo paths are:

```text
data/raw
data/canonical
data/factors
data/labels
data/cache
metadata
artifacts
```

The default allowed local-root subdirs are:

```text
raw
canonical
manifests
metadata
quality
coverage
```

These names describe future local-only layout. They do not authorize DATA-P02 to
write real data.

## Rejected Locations

`LocalDataRootPolicy` rejects:

- any root inside this repository, including `data/raw`, `data/canonical`,
  `data/cache`, `metadata`, `artifacts`, or `src`;
- Windows mount paths such as `/mnt/c`, `/mnt/d`, and `/mnt/e`;
- synced or cloud paths containing OneDrive, Dropbox, Google Drive, or
  Windows-synced markers;
- network paths such as `//server/share`;
- temporary locations such as `/tmp`, `/var/tmp`, and `/dev/shm`.

Validation is fail-closed. Invalid roots, missing required fields, false
`must_be_local`, false `must_be_ignored`, empty forbidden path lists, invalid allowed
subdir names, or non-failing max-file policies raise hard errors.

## Raw-Write Block

A missing `LocalDataRootPolicy` blocks raw writes. DATA-P02 exposes the
`require_local_data_root_policy` guard so later raw-data phases can fail before any
real-data write path proceeds without a validated policy.
